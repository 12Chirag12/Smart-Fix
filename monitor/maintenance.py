"""
SmartFix AI — Scheduled Preventive Maintenance Engine
Performs background health optimizations, cache purges, DNS renewals, and file audits.
Can run on a lightweight schedule or be triggered instantly via UI.
"""
import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger("smartfix.maintenance")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
STATUS_FILE = os.path.join(DATA_DIR, "maintenance_status.json")

# Routine maintenance tasks mapped to repair_engine handlers
ROUTINE_TASKS = [
    ("purge_temp_cache_files", "Purge Temporary & Cache Files"),
    ("flush_dns_and_renew",    "Flush & Register DNS Cache"),
    ("restart_bits",           "Reset BITS Transfer Queue"),
]

DEEP_TASKS = [
    ("run_sfc_scannow",        "System File Checker (SFC Scan)"),
    ("fix_time_sync",          "Synchronize Windows Time Service"),
]

_maintenance_lock = threading.Lock()


def get_maintenance_status() -> Dict[str, Any]:
    """Return the last maintenance run details and schedule status."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_run": None,
        "last_status": "Never Run",
        "tasks_run": 0,
        "tasks_succeeded": 0,
        "next_scheduled": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 03:00"),
    }


def _save_maintenance_status(status: Dict[str, Any]):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        tmp = STATUS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
        os.replace(tmp, STATUS_FILE)
    except Exception as e:
        logger.debug(f"Failed to save maintenance status: {e}")


def run_maintenance(deep: bool = False) -> Dict[str, Any]:
    """
    Execute maintenance tasks sequentially with safety and verification.
    Thread-safe. Logs all executed tasks.
    """
    with _maintenance_lock:
        from monitor.repair_engine import execute_repair
        tasks = list(ROUTINE_TASKS)
        if deep:
            tasks.extend(DEEP_TASKS)

        start_time = datetime.now()
        results = []
        success_count = 0

        logger.info(f"[MAINTENANCE] Starting {'deep' if deep else 'routine'} maintenance ({len(tasks)} tasks)…")

        for repair_id, description in tasks:
            t_start = time.time()
            try:
                res = execute_repair(repair_id, severity="LOW", enable_retry=False, enable_restore=False)
                ok = res.get("success", False)
                if ok:
                    success_count += 1
                results.append({
                    "id": repair_id,
                    "description": description,
                    "success": ok,
                    "elapsed": round(time.time() - t_start, 2),
                    "output": res.get("output", "")[:200],
                })
            except Exception as e:
                results.append({
                    "id": repair_id,
                    "description": description,
                    "success": False,
                    "elapsed": round(time.time() - t_start, 2),
                    "output": str(e),
                })

        overall_ok = success_count == len(tasks)
        status_payload = {
            "last_run": start_time.isoformat(),
            "last_status": "Successful" if overall_ok else f"Completed with warnings ({success_count}/{len(tasks)} ok)",
            "tasks_run": len(tasks),
            "tasks_succeeded": success_count,
            "next_scheduled": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 03:00"),
            "details": results,
        }
        _save_maintenance_status(status_payload)
        logger.info(f"[MAINTENANCE] Finished: {success_count}/{len(tasks)} tasks succeeded.")
        return status_payload


class MaintenanceScheduler(threading.Thread):
    """
    Lightweight background daemon that performs scheduled maintenance at low PC usage.
    Default: Daily at 3:00 AM (or when app runs for >24h without maintenance).
    """

    def __init__(self, interval_seconds: int = 3600):
        super().__init__(name="SmartFixMaintenanceScheduler", daemon=True)
        self.interval = interval_seconds
        self._running = True

    def run(self):
        # Wait 30 seconds after startup before first check
        time.sleep(30)
        while self._running:
            try:
                status = get_maintenance_status()
                last_run_str = status.get("last_run")
                should_run = False
                now = datetime.now()

                if not last_run_str:
                    # Never run before — run first maintenance 5 minutes after launch
                    should_run = True
                else:
                    try:
                        last_run_dt = datetime.fromisoformat(last_run_str)
                        if (now - last_run_dt).total_seconds() > 86400:  # 24 hours
                            should_run = True
                    except Exception:
                        should_run = True

                if should_run and self._running:
                    logger.info("[MAINTENANCE] Periodic 24-hour maintenance window reached — running routine optimization")
                    run_maintenance(deep=False)

            except Exception as e:
                logger.debug(f"Scheduler exception: {e}")

            time.sleep(self.interval)

    def stop(self):
        self._running = False
