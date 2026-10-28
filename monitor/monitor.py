"""
SmartFix AI — Background Monitor Daemon
Continuously watches Windows for errors matching the error catalog.
Features thread watchdog for automatic crash recovery.
"""
import threading
import time
import socket
import logging
import subprocess
import json
import os
import sys
from typing import Callable, Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

import psutil


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitor.error_catalog import ERROR_CATALOG, CATALOG_LIST

logger = logging.getLogger("smartfix.monitor")

CHECK_INTERVAL_SECONDS  = int(os.getenv("SMARTFIX_MONITOR_INTERVAL", "30")) # How often each monitor thread polls
ALERT_COOLDOWN_SECONDS  = 1800      # 30 min default — prevents same alert re-firing after fix
EVENT_LOOKBACK_MINUTES  = 5         # Look back this far in Windows Event Log
WATCHDOG_INTERVAL       = 30        # How often the watchdog checks thread health


class BackgroundMonitor:
    """
    Always-on background monitor. Runs check loops in daemon threads.
    Calls on_alert(error_info) when an error is detected.
    Includes a watchdog thread that auto-restarts crashed monitor threads.
    """

    def __init__(self, on_alert: Callable[[Dict[str, Any]], None], check_interval: int = CHECK_INTERVAL_SECONDS):
        self.on_alert = on_alert
        self.check_interval = check_interval
        self._running = False
        self._threads: List[threading.Thread] = []
        self._alert_cooldowns: Dict[str, datetime] = {}  
        self._cooldown_lock = threading.Lock()
        self._demo_mode = False

        # ── Thread health tracking ────────────────────────────────────────────
        self._thread_registry: Dict[str, Dict[str, Any]] = {}
        self._registry_lock = threading.Lock()
        self._thread_restart_counts: Dict[str, int] = {}
        self._max_restarts = 5  # Max auto-restarts before giving up on a thread

    # ── Thread Health API (for self-health dashboard) ─────────────────────────

    def get_thread_health(self) -> Dict[str, Dict[str, Any]]:
        """Return health status of all monitor threads (for UI dashboard)."""
        with self._registry_lock:
            result = {}
            for name, info in self._thread_registry.items():
                thread = info.get("thread")
                result[name] = {
                    "alive": thread.is_alive() if thread else False,
                    "restarts": self._thread_restart_counts.get(name, 0),
                    "target": info.get("target_name", "unknown"),
                }
            return result

    def get_alive_thread_count(self) -> tuple:
        """Return (alive_count, total_count) for status bar."""
        health = self.get_thread_health()
        alive = sum(1 for v in health.values() if v["alive"])
        return alive, len(health)

    def start(self):
        """Start all monitor threads and the watchdog."""
        if self._running:
            return
        self._running = True
        logger.info("SmartFix Monitor starting…")

        thread_targets = [
            ("ServiceMonitor", self._loop_services),
            ("EventMonitor", self._loop_events),
            ("MetricMonitor", self._loop_metrics),
            ("NetworkMonitor", self._loop_network),
        ]
        for name, target in thread_targets:
            self._start_thread(name, target)

        # Start the watchdog thread
        watchdog = threading.Thread(target=self._watchdog, name="MonitorWatchdog", daemon=True)
        watchdog.start()

        logger.info(f"SmartFix Monitor running — {len(self._threads)} threads active + watchdog")

    def stop(self):
        """Signal all threads to stop."""
        self._running = False
        logger.info("SmartFix Monitor stopping…")

    def _start_thread(self, name: str, target: Callable):
        """Start a named daemon thread and register it in the health registry."""
        t = threading.Thread(target=self._guarded_run, args=(name, target), name=name, daemon=True)
        t.start()
        self._threads.append(t)
        with self._registry_lock:
            self._thread_registry[name] = {
                "thread": t,
                "target": target,
                "target_name": target.__name__,
                "started_at": datetime.now().isoformat(),
            }
            if name not in self._thread_restart_counts:
                self._thread_restart_counts[name] = 0

    def _guarded_run(self, name: str, target: Callable):
        """Wrapper that catches any unhandled exception in a monitor thread."""
        try:
            target()
        except Exception as ex:
            logger.critical(f"[WATCHDOG] Thread {name} crashed with unhandled exception: {ex}", exc_info=True)

    # ── Watchdog ──────────────────────────────────────────────────────────────

    def _watchdog(self):
        """Monitors all registered threads and auto-restarts any that have died."""
        logger.info("[WATCHDOG] Thread health monitor started")
        while self._running:
            time.sleep(WATCHDOG_INTERVAL)
            if not self._running:
                break

            with self._registry_lock:
                for name, info in list(self._thread_registry.items()):
                    thread = info.get("thread")
                    target = info.get("target")

                    if thread and not thread.is_alive() and self._running:
                        restarts = self._thread_restart_counts.get(name, 0)
                        if restarts >= self._max_restarts:
                            logger.error(
                                f"[WATCHDOG] Thread {name} has crashed {restarts} times — "
                                f"max restarts ({self._max_restarts}) reached, not restarting"
                            )
                            continue

                        self._thread_restart_counts[name] = restarts + 1
                        logger.warning(
                            f"[WATCHDOG] Thread {name} found dead — "
                            f"auto-restarting (attempt {restarts + 1}/{self._max_restarts})"
                        )

                        # Create and start a new thread
                        new_t = threading.Thread(
                            target=self._guarded_run, args=(name, target),
                            name=f"{name}-R{restarts + 1}", daemon=True
                        )
                        new_t.start()
                        info["thread"] = new_t
                        info["started_at"] = datetime.now().isoformat()

                        # Update the threads list
                        self._threads = [t for t in self._threads if t.is_alive()]
                        self._threads.append(new_t)

    # ── Alert System ──────────────────────────────────────────────────────────

    def inject_demo_error(self, error_id: str):
        """Force-trigger an alert for demo purposes (bypasses cooldown)."""
        if error_id == "unknown_error_demo":
            logger.info("[DEMO] Injecting error: unknown_error_demo")
            self._trigger_alert({
                "id": "unknown_error",
                "name": "Unknown Application Crash (0xc0000005)",
                "category": "Application",
                "severity": "HIGH",
                "description": "An unexpected fatal memory access violation occurred in a background process.",
                "technical": "Exception Code: 0xc0000005. Faulting module: unknown.dll.",
                "repair_id": "unknown_error",
                "is_demo": True
            }, force=True)
            return
            
        error_def = ERROR_CATALOG.get(error_id)
        if error_def:
            logger.info(f"[DEMO] Injecting error: {error_id}")
            payload = dict(error_def)
            payload["is_demo"] = True
            self._trigger_alert(payload, force=True)

    def mark_resolved(self, error_id: str, cooldown_seconds: int = ALERT_COOLDOWN_SECONDS):
        """Called by the UI after a user fixes or ignores an error.
        Sets the cooldown timestamp far in the future so this error won't re-alert."""
        with self._cooldown_lock:
            # Set timestamp to (now + cooldown_seconds - standard_cooldown) so
            # the standard cooldown check blocks re-alerting for cooldown_seconds total
            self._alert_cooldowns[error_id] = (
                datetime.now() + timedelta(seconds=cooldown_seconds - ALERT_COOLDOWN_SECONDS)
            )
        logger.info(f"[RESOLVED] {error_id} — suppressed for {cooldown_seconds // 60}m")

    def _trigger_alert(self, error_def: Dict[str, Any], context: Optional[Dict] = None, force: bool = False):
        error_id = error_def["id"]
        now = datetime.now()

        with self._cooldown_lock:
            last = self._alert_cooldowns.get(error_id)
            if not force and last and (now - last).total_seconds() < ALERT_COOLDOWN_SECONDS:
                return  
            self._alert_cooldowns[error_id] = now

        payload = dict(error_def)
        payload["detected_at"] = now.isoformat()
        if context:
            payload["context"] = context
        logger.warning(f"[ALERT] {error_def['name']} — {error_def['severity']}")
        self.on_alert(payload)

    # ── Service Monitor ───────────────────────────────────────────────────────

    def _loop_services(self):
        service_errors = [e for e in CATALOG_LIST if e.get("detection") and e["detection"].get("type") in ("service", "service_disabled")]
        while self._running:
            try:
                self._check_services(service_errors)
            except Exception as ex:
                logger.error(f"Service monitor error: {ex}", exc_info=True)
            time.sleep(self.check_interval)

    def _check_services(self, service_errors: List[Dict]):
        
        running_services: Set[str] = set()
        disabled_services: Set[str] = set()
        try:
            for svc in psutil.win_service_iter():
                try:
                    info = svc.as_dict()
                    name = info["name"].lower()
                    status = info["status"]
                    if status == "running":
                        running_services.add(name)
                    if info.get("start_type") == "disabled":
                        disabled_services.add(name)
                except Exception:
                    pass
        except Exception:
            pass

        for err in service_errors:
            det = err["detection"]
            svc_name = det.get("service_name", "").lower()
            if not svc_name:
                continue

            det_type = det["type"]
            if det_type == "service":
                if svc_name not in running_services:
                    self._trigger_alert(err, {"service": svc_name, "status": "STOPPED"})
            elif det_type == "service_disabled":
                if svc_name in disabled_services:
                    self._trigger_alert(err, {"service": svc_name, "status": "DISABLED"})

    # ── Event Log Monitor ─────────────────────────────────────────────────────

    def _loop_events(self):
        event_errors = [e for e in CATALOG_LIST if e.get("detection") and e["detection"].get("type") == "event"]
        while self._running:
            try:
                self._check_events(event_errors)
            except Exception as ex:
                logger.error(f"Event monitor error: {ex}", exc_info=True)
            time.sleep(self.check_interval)

    def _check_events(self, event_errors: List[Dict]):
        
        since = (datetime.now() - timedelta(minutes=EVENT_LOOKBACK_MINUTES)).strftime("%Y-%m-%dT%H:%M:%S")
        ps_script = f"""
$since = [DateTime]::Parse('{since}')
$result = @()
$logs = @('System','Application')
foreach ($log in $logs) {{
    try {{
        $events = Get-WinEvent -LogName $log -MaxEvents 50 -ErrorAction SilentlyContinue |
            Where-Object {{ $_.TimeCreated -gt $since -and $_.Level -le 3 }}
        foreach ($e in $events) {{
            $result += @{{
                Log=$log; Id=$e.Id; Source=$e.ProviderName; Level=$e.Level;
                Message=($e.Message -replace '\\\\n',' ' -replace '\\\\r','')
                Time=$e.TimeCreated.ToString('o')
            }}
        }}
    }} catch {{}}
}}
$result | ConvertTo-Json -Compress
"""
        try:
            out = subprocess.run(
                ["powershell", "-NonInteractive", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=20,
                creationflags=0x08000000
            )
            if not out.stdout.strip():
                return
            raw = json.loads(out.stdout)
            events = raw if isinstance(raw, list) else [raw]
        except Exception:
            return

        for err in event_errors:
            det = err["detection"]
            target_log = det.get("log", "*")
            target_ids = set(det.get("event_ids", []))
            target_source = det.get("source", "*").lower()
            target_kw = [k.lower() for k in det.get("keywords", [])]
            target_level = det.get("level")

            for ev in events:
                ev_log = ev.get("Log", "")
                ev_id = ev.get("Id", 0)
                ev_src = ev.get("Source", "").lower()
                ev_msg = ev.get("Message", "").lower()
                ev_level = ev.get("Level", 4)

                if target_log != "*" and ev_log != target_log:
                    continue
                if target_ids and ev_id not in target_ids:
                    continue
                if target_source != "*" and target_source not in ev_src:
                    continue
                if target_level is not None and ev_level > target_level:
                    continue
                
                if target_kw and not all(kw in ev_msg for kw in target_kw):
                    continue

                self._trigger_alert(err, {
                    "event_id": ev_id,
                    "source": ev.get("Source"),
                    "log": ev_log,
                    "time": ev.get("Time"),
                    "message_snippet": ev.get("Message", "")[:200],
                })
                break  

    # ── Metric Monitor ────────────────────────────────────────────────────────

    def _loop_metrics(self):
        metric_errors = [e for e in CATALOG_LIST if e.get("detection") and e["detection"].get("type") == "metric"]
        
        cpu_high_count = 0
        while self._running:
            try:
                cpu_pct = psutil.cpu_percent(interval=2)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('C:\\')

                
                top_cpu_proc = None
                top_mem_proc = None
                try:
                    procs = [(p.name(), p.cpu_percent(interval=0), p.memory_info().rss // (1024*1024))
                             for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info'])
                             if p.pid > 4]
                    if procs:
                        top_cpu_proc = max(procs, key=lambda x: x[1])
                        top_mem_proc = max(procs, key=lambda x: x[2])
                except Exception:
                    pass

                metrics = {
                    "cpu_percent": cpu_pct,
                    "memory_percent": mem.percent,
                    "disk_usage_percent": disk.percent,
                    "top_process_cpu": top_cpu_proc[1] if top_cpu_proc else 0,
                    "top_process_memory_mb": top_mem_proc[2] if top_mem_proc else 0,
                }

                for err in metric_errors:
                    det = err["detection"]
                    metric_name = det.get("metric", "")
                    threshold = det.get("threshold", 100.0)
                    val = metrics.get(metric_name, 0)

                    if val >= threshold:
                        ctx = dict(metrics)
                        if top_cpu_proc:
                            ctx["top_cpu_process"] = top_cpu_proc[0]
                        if top_mem_proc:
                            ctx["top_memory_process"] = f"{top_mem_proc[0]} ({top_mem_proc[2]}MB)"
                        self._trigger_alert(err, ctx)

                # Check for temp files & cache clutter
                self._check_temp_clutter()

            except Exception as ex:
                logger.error(f"Metric monitor error: {ex}", exc_info=True)

            time.sleep(self.check_interval)

    def _check_temp_clutter(self):
        """Check for excessive temp files and caches."""
        try:
            import os
            temp_dirs = [
                os.environ.get("TEMP", ""),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp"),
            ]
            total_bytes = 0
            file_count = 0
            seen_dirs = set()
            for td in temp_dirs:
                if not td or not os.path.isdir(td) or td.lower() in seen_dirs:
                    continue
                seen_dirs.add(td.lower())
                try:
                    with os.scandir(td) as it:
                        for entry in it:
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    total_bytes += entry.stat().st_size
                                    file_count += 1
                                elif entry.is_dir(follow_symlinks=False):
                                    try:
                                        with os.scandir(entry.path) as sub_it:
                                            for sub in sub_it:
                                                if sub.is_file(follow_symlinks=False):
                                                    total_bytes += sub.stat().st_size
                                                    file_count += 1
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                except Exception:
                    pass

            size_mb = total_bytes / (1024 * 1024)
            # Alert if temp size >= 500 MB, file count >= 1000, or demo clutter folder exists
            junk_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "SmartFix_Demo_TempJunk")
            has_demo_junk = os.path.isdir(junk_dir)
            if size_mb >= 500 or file_count >= 1000 or has_demo_junk:
                err_def = ERROR_CATALOG.get("temp_files_overflow")
                if err_def:
                    self._trigger_alert(err_def, {
                        "temp_size_mb": round(size_mb, 1),
                        "file_count": file_count,
                    })
        except Exception as ex:
            logger.debug(f"Temp clutter check error: {ex}")

    # ── Network Monitor ───────────────────────────────────────────────────────

    def _loop_network(self):
        net_errors = [e for e in CATALOG_LIST if e.get("detection") and e["detection"].get("type") in (
            "dns_check", "dns_timeout", "internet_check", "network_connectivity", "ip_check", "gateway_check"
        )]
        while self._running:
            try:
                self._check_network(net_errors)
            except Exception as ex:
                logger.error(f"Network monitor error: {ex}", exc_info=True)
            time.sleep(self.check_interval * 2)  

    def _check_network(self, net_errors: List[Dict]):
        
        dns_ok = self._dns_check("google.com")
        
        internet_ok = self._ping_check("8.8.8.8")
        
        has_apipa = self._has_apipa_address()

        for err in net_errors:
            det = err["detection"]
            det_type = det["type"]

            if det_type in ("dns_check", "dns_timeout") and not dns_ok:
                self._trigger_alert(err, {"dns_ok": dns_ok, "internet_ok": internet_ok})
            elif det_type == "internet_check" and not internet_ok:
                self._trigger_alert(err, {"internet_ok": internet_ok})
            elif det_type == "network_connectivity" and not internet_ok:
                self._trigger_alert(err, {"internet_ok": internet_ok})
            elif det_type == "ip_check" and has_apipa:
                self._trigger_alert(err, {"apipa_detected": True})

    def _dns_check(self, host: str) -> bool:
        try:
            socket.setdefaulttimeout(3)
            socket.getaddrinfo(host, None)
            return True
        except Exception:
            return False

    def _ping_check(self, ip: str) -> bool:
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "2000", ip],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _has_apipa_address(self) -> bool:
        try:
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.address and addr.address.startswith("169.254."):
                        return True
        except Exception:
            pass
        return False
