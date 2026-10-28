"""
SmartFix AI — Lab Client Agent
Runs on every client workstation. Listens on LAB_PORT for admin commands,
reports errors / metrics, and executes repairs on request.
"""
import json
import logging
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitor.lab_config import (
    LAB_PORT, MSG_PING, MSG_PONG, MSG_GET_STATUS, MSG_STATUS,
    MSG_REPAIR, MSG_REPAIR_RESULT,
    get_seat_name, get_local_ip,
    send_message, recv_message, make_message, parse_message,
    verify_auth_token, DISCOVERY_PORT, sign_discovery_message
)

logger = logging.getLogger("smartfix.lab_agent")

# UDP broadcast port for auto-discovery
BROADCAST_PORT = DISCOVERY_PORT
BROADCAST_INTERVAL = 15   # seconds between broadcasts


class LabClientAgent:
    """
    TCP server that runs on the client workstation.
    - Broadcasts its presence on the LAN via UDP every BROADCAST_INTERVAL seconds.
    - Accepts TCP connections from the admin and responds to commands.
    - Tracks locally detected errors (fed from BackgroundMonitor).
    """

    def __init__(self):
        self._running = False
        self._lock = threading.Lock()
        self._current_errors: List[Dict] = []       # live error list from BackgroundMonitor
        self._last_metrics: Dict[str, Any] = {}
        self._server: Optional[socketserver.TCPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._broadcast_thread: Optional[threading.Thread] = None

    # ── Public API (called from SmartFix main app) ────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._start_tcp_server()
        self._broadcast_thread = threading.Thread(
            target=self._broadcast_loop, name="LabBroadcast", daemon=True
        )
        self._broadcast_thread.start()
        logger.info(f"[LabAgent] Started — seat={get_seat_name()}, port={LAB_PORT}")

    def stop(self):
        self._running = False
        if self._server:
            try:
                self._server.shutdown()
                self._server.server_close()
            except Exception:
                pass
            self._server = None
        logger.info("[LabAgent] Stopped")

    def update_errors(self, errors: List[Dict]):
        """Called by BackgroundMonitor whenever the error list changes."""
        with self._lock:
            self._current_errors = list(errors)

    def update_metrics(self, metrics: Dict[str, Any]):
        """Called periodically with fresh cpu/ram/disk stats."""
        with self._lock:
            self._last_metrics = dict(metrics)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _start_tcp_server(self):
        agent = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                try:
                    buf = b""
                    self.request.settimeout(10)
                    while b"\n" not in buf:
                        chunk = self.request.recv(4096)
                        if not chunk:
                            return
                        buf += chunk
                    line = buf.split(b"\n", 1)[0]
                    msg = parse_message(line.decode("utf-8"))
                    if not msg:
                        return
                    agent._handle_message(self.request, msg)
                except Exception as ex:
                    logger.debug(f"[LabAgent] Handler error: {ex}")

        try:
            server = socketserver.TCPServer(("0.0.0.0", LAB_PORT), Handler)
            server.allow_reuse_address = True
            self._server = server
            self._server_thread = threading.Thread(
                target=server.serve_forever, name="LabTCPServer", daemon=True
            )
            self._server_thread.start()
        except Exception as ex:
            logger.error(f"[LabAgent] Failed to start TCP server: {ex}")

    def _handle_message(self, sock: socket.socket, msg: Dict):
        msg_type = msg.get("type", "")
        payload  = msg.get("payload", {})

        if msg_type == MSG_PING:
            send_message(sock, MSG_PONG, {"seat": get_seat_name(), "ip": get_local_ip()})

        elif msg_type == MSG_GET_STATUS:
            send_message(sock, MSG_STATUS, self._build_status())

        elif msg_type == MSG_REPAIR:
            auth_token = payload.get("auth_token", "")
            if not verify_auth_token(auth_token):
                logger.warning(f"[LabAgent] Unauthorized repair request rejected from {sock.getpeername()}")
                send_message(sock, MSG_REPAIR_RESULT, {
                    "error_id": payload.get("error_id", ""),
                    "success": False,
                    "message": "Authentication failed: Invalid admin passkey token.",
                    "seat": get_seat_name(),
                })
                return

            error_id = payload.get("error_id", "")
            result   = self._execute_repair(error_id)
            send_message(sock, MSG_REPAIR_RESULT, {
                "error_id": error_id,
                "success": result["success"],
                "message": result["message"],
                "seat": get_seat_name(),
            })

    def _build_status(self) -> Dict[str, Any]:
        with self._lock:
            errors  = list(self._current_errors)
            metrics = dict(self._last_metrics)

        # Fresh snapshot if metrics are empty
        if not metrics:
            try:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                dsk = psutil.disk_usage("C:\\")
                metrics = {
                    "cpu_percent": cpu,
                    "memory_percent": mem.percent,
                    "disk_percent": dsk.percent,
                }
            except Exception:
                metrics = {}

        return {
            "seat": get_seat_name(),
            "ip": get_local_ip(),
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "errors": errors,
            "error_count": len(errors),
        }

    def _execute_repair(self, error_id: str) -> Dict:
        """Run the local repair engine for the given error_id."""
        try:
            from monitor.repair_engine import execute_repair
            result = execute_repair(error_id)
            if isinstance(result, dict):
                return {
                    "success": bool(result.get("success", False)),
                    "message": result.get("output") or result.get("message") or "Repair completed"
                }
            return {"success": True, "message": str(result)}
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    # ── UDP Broadcast ─────────────────────────────────────────────────────────

    def _broadcast_loop(self):
        """Broadcast this client's presence on UDP with HMAC signature so admin can discover it."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while self._running:
            try:
                announce_data = {
                    "type": "ANNOUNCE",
                    "seat": get_seat_name(),
                    "ip": get_local_ip(),
                    "port": LAB_PORT,
                }
                signed = sign_discovery_message(announce_data)
                data = json.dumps(signed).encode("utf-8")
                sock.sendto(data, ("<broadcast>", BROADCAST_PORT))
            except Exception as ex:
                logger.debug(f"[LabAgent] Broadcast error: {ex}")
            for _ in range(BROADCAST_INTERVAL):
                if not self._running:
                    break
                time.sleep(1)

        sock.close()
