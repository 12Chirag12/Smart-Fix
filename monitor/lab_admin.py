"""
SmartFix AI — Lab Admin Manager
Runs on the teacher/admin PC.
- Listens for UDP broadcast announcements from client PCs.
- Polls each client for status (errors, CPU, RAM, Disk).
- Fires callbacks so the UI can update in real time.
- Sends remote repair commands.
"""
import json
import logging
import socket
import sys
import os
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitor.lab_config import (
    LAB_PORT,
    MSG_PING, MSG_PONG, MSG_GET_STATUS, MSG_STATUS,
    MSG_REPAIR, MSG_REPAIR_RESULT,
    get_known_clients, save_known_clients,
    send_message, recv_message, make_message, parse_message,
    get_auth_token, verify_discovery_message
)


# Import BROADCAST_PORT safely
try:
    from monitor.lab_agent import BROADCAST_PORT
except ImportError:
    from monitor.lab_config import DISCOVERY_PORT
    BROADCAST_PORT = DISCOVERY_PORT

logger = logging.getLogger("smartfix.lab_admin")

POLL_INTERVAL   = 20    # seconds between status polls
OFFLINE_TIMEOUT = 60    # seconds before a client is marked offline


class ClientInfo:
    """State object for one monitored client PC."""

    def __init__(self, seat: str, ip: str, port: int = LAB_PORT):
        self.seat     = seat
        self.ip       = ip
        self.port     = port
        self.online   = False
        self.last_seen: Optional[datetime] = None
        self.last_status: Optional[datetime] = None
        self.metrics: Dict[str, Any] = {}
        self.errors: List[Dict] = []
        self.error_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "seat":        self.seat,
            "ip":          self.ip,
            "port":        self.port,
            "online":      self.online,
            "last_seen":   self.last_seen.isoformat() if self.last_seen else None,
            "metrics":     self.metrics,
            "errors":      self.errors,
            "error_count": self.error_count,
        }

    def mark_seen(self):
        self.last_seen = datetime.now()
        self.online    = True


class LabAdminManager:
    """
    Manages all client PCs from the admin side.
    Thread-safe. Fires on_update(clients) whenever state changes.
    """

    def __init__(self, on_update: Optional[Callable[[List[ClientInfo]], None]] = None):
        self.on_update = on_update
        self._running  = False
        self._lock     = threading.Lock()
        self._clients: Dict[str, ClientInfo] = {}   # seat -> ClientInfo
        self._threads: List[threading.Thread] = []

        # Restore previously known clients from disk
        for entry in get_known_clients():
            seat = entry.get("seat", "")
            ip   = entry.get("ip", "")
            port = entry.get("port", LAB_PORT)
            if seat and ip:
                self._clients[seat] = ClientInfo(seat, ip, port)

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True

        threads = [
            ("LabDiscovery", self._discovery_loop),
            ("LabPoller",    self._poll_loop),
            ("LabOffline",   self._offline_check_loop),
        ]
        for name, target in threads:
            t = threading.Thread(target=target, name=name, daemon=True)
            t.start()
            self._threads.append(t)
        logger.info("[LabAdmin] Started")

    def stop(self):
        self._running = False
        logger.info("[LabAdmin] Stopped")

    def get_clients(self) -> List[ClientInfo]:
        with self._lock:
            return list(self._clients.values())

    def add_client_manual(self, seat: str, ip: str, port: int = LAB_PORT):
        """Manually register a client (e.g. from the UI). Ensures unique seat name."""
        with self._lock:
            # If seat name already exists for a different IP, disambiguate
            if seat in self._clients and self._clients[seat].ip != ip:
                last_octet = ip.split(".")[-1] if "." in ip else ip
                seat = f"{seat}-{last_octet}"
            if seat not in self._clients:
                self._clients[seat] = ClientInfo(seat, ip, port)
            else:
                self._clients[seat].ip   = ip
                self._clients[seat].port = port
            self._clients[seat].mark_seen()
        self._persist_clients()
        self._notify()

    def remove_client(self, seat: str):
        with self._lock:
            self._clients.pop(seat, None)
        self._persist_clients()
        self._notify()

    def request_repair(self, seat: str, error_id: str, on_result: Optional[Callable] = None):
        """Send a repair command to a client in a background thread."""
        client = self._get_client(seat)
        if not client:
            if on_result:
                on_result({"success": False, "message": f"Client {seat} not found"})
            return
        t = threading.Thread(
            target=self._do_repair, args=(client, error_id, on_result),
            daemon=True, name=f"LabRepair-{seat}"
        )
        t.start()

    def poll_client_now(self, seat: str):
        """Force an immediate status poll of a specific client."""
        client = self._get_client(seat)
        if client:
            threading.Thread(
                target=self._fetch_status, args=(client,),
                daemon=True, name=f"LabPollNow-{seat}"
            ).start()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _get_client(self, seat: str) -> Optional[ClientInfo]:
        with self._lock:
            return self._clients.get(seat)

    def _notify(self):
        if self.on_update:
            try:
                self.on_update(self.get_clients())
            except Exception as ex:
                logger.debug(f"[LabAdmin] on_update error: {ex}")

    def _persist_clients(self):
        with self._lock:
            entries = [{"seat": c.seat, "ip": c.ip, "port": c.port}
                       for c in self._clients.values()]
        save_known_clients(entries)

    # ── Discovery (UDP listener) ───────────────────────────────────────────────

    def _discovery_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", BROADCAST_PORT))
        except Exception as ex:
            logger.error(f"[LabAdmin] Cannot bind UDP port {BROADCAST_PORT}: {ex}")
            return

        sock.settimeout(2.0)
        while self._running:
            try:
                data, addr = sock.recvfrom(4096)
                raw_msg = json.loads(data.decode("utf-8"))
                # Verify HMAC-signed discovery message (backwards-compatible with unsigned)
                msg = verify_discovery_message(raw_msg)
                if msg is None:
                    logger.debug(f"[LabAdmin] Rejected unsigned/tampered discovery from {addr[0]}")
                    continue
                if msg.get("type") == "ANNOUNCE":
                    seat = msg.get("seat", "")
                    ip   = addr[0]   # Use actual sender IP, not what they claim
                    port = msg.get("port", LAB_PORT)
                    if seat:
                        self._handle_announce(seat, ip, port)
            except socket.timeout:
                pass
            except Exception as ex:
                logger.debug(f"[LabAdmin] Discovery error: {ex}")

        sock.close()

    def _handle_announce(self, seat: str, ip: str, port: int):
        new_client = False
        with self._lock:
            # Check if this IP is already registered under another seat name
            for s, c in list(self._clients.items()):
                if c.ip == ip and s != seat:
                    del self._clients[s]
                    break

            # If another machine with a different IP already uses this seat name, make it unique
            if seat in self._clients and self._clients[seat].ip != ip:
                last_octet = ip.split(".")[-1] if "." in ip else ip
                seat = f"{seat}-{last_octet}"

            if seat not in self._clients:
                logger.info(f"[LabAdmin] Discovered new client: {seat} @ {ip}")
                self._clients[seat] = ClientInfo(seat, ip, port)
                new_client = True
            else:
                self._clients[seat].ip   = ip
                self._clients[seat].port = port
            self._clients[seat].mark_seen()

        if new_client:
            self._persist_clients()
            # Immediately fetch status for new client
            client = self._get_client(seat)
            if client:
                threading.Thread(
                    target=self._fetch_status, args=(client,),
                    daemon=True, name=f"LabInit-{seat}"
                ).start()
        self._notify()

    # ── Status Polling ─────────────────────────────────────────────────────────

    def _poll_loop(self):
        while self._running:
            time.sleep(POLL_INTERVAL)
            if not self._running:
                break
            clients = self.get_clients()
            for client in clients:
                if client.online or (client.last_seen is None):
                    threading.Thread(
                        target=self._fetch_status, args=(client,),
                        daemon=True, name=f"LabPoll-{client.seat}"
                    ).start()

    def _fetch_status(self, client: ClientInfo):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((client.ip, client.port))
            send_message(sock, MSG_GET_STATUS)
            resp = recv_message(sock, timeout=8)
            sock.close()

            if resp and resp.get("type") == MSG_STATUS:
                pl = resp.get("payload", {})
                with self._lock:
                    client.online      = True
                    client.last_seen   = datetime.now()
                    client.last_status = datetime.now()
                    client.metrics     = pl.get("metrics", {})
                    client.errors      = pl.get("errors", [])
                    client.error_count = pl.get("error_count", 0)
                self._notify()
            else:
                self._mark_offline(client)

        except Exception:
            self._mark_offline(client)

    def _mark_offline(self, client: ClientInfo):
        changed = client.online
        with self._lock:
            client.online = False
        if changed:
            self._notify()

    # ── Offline Checker ────────────────────────────────────────────────────────

    def _offline_check_loop(self):
        while self._running:
            time.sleep(10)
            now = datetime.now()
            changed = False
            with self._lock:
                for client in self._clients.values():
                    if client.online and client.last_seen:
                        elapsed = (now - client.last_seen).total_seconds()
                        if elapsed > OFFLINE_TIMEOUT:
                            client.online = False
                            changed = True
            if changed:
                self._notify()

    # ── Remote Repair ──────────────────────────────────────────────────────────

    def _do_repair(self, client: ClientInfo, error_id: str, on_result: Optional[Callable]):
        result = {"success": False, "message": "Connection failed"}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((client.ip, client.port))
            send_message(sock, MSG_REPAIR, {
                "error_id": error_id,
                "auth_token": get_auth_token(),
            })
            resp = recv_message(sock, timeout=30)
            sock.close()
            if resp and resp.get("type") == MSG_REPAIR_RESULT:
                result = resp.get("payload", result)
        except Exception as ex:
            result = {"success": False, "message": str(ex)}

        logger.info(f"[LabAdmin] Repair {error_id} on {client.seat}: {result}")
        if on_result:
            try:
                on_result(result)
            except Exception:
                pass
