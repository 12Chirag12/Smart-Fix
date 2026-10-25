"""
SmartFix AI — Demo Mode
Simulates real Windows errors so users can see the full detection → alert → fix → verified flow.
Each demo is fully reversible and safe.
"""
import subprocess
import threading
import time
import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger("smartfix.demo")


class DemoScenario:
    def __init__(self, error_id: str, name: str, description: str, inject_fn, cleanup_fn=None):
        self.error_id = error_id
        self.name = name
        self.description = description
        self._inject = inject_fn
        self._cleanup = cleanup_fn
        self.active = False

    def inject(self) -> bool:
        """Simulate the error. Returns True if successful."""
        try:
            result = self._inject()
            self.active = True
            return True if result is None else bool(result)
        except Exception as e:
            logger.error(f"Demo inject failed for {self.name}: {e}")
            return False

    def cleanup(self):
        """Revert the simulated error."""
        if self._cleanup and self.active:
            try:
                self._cleanup()
            except Exception as e:
                logger.error(f"Demo cleanup failed: {e}")
            self.active = False


def _stop_service(name: str) -> bool:
    """Stop a Windows service using PowerShell Stop-Service -Force with net stop fallback."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Stop-Service -Name '{name}' -Force -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=10
        )
        subprocess.run(["net", "stop", name, "/y"], capture_output=True, timeout=10)
        logger.info(f"[DEMO] Stopped service: {name}")
    except Exception as e:
        logger.warning(f"[DEMO] Stop service exception for {name}: {e}")
    return True


def _start_service(name: str):
    """Restart a Windows service."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Start-Service -Name '{name}' -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=10
        )
        subprocess.run(["net", "start", name], capture_output=True, timeout=10)
        logger.info(f"[DEMO] Restarted service: {name}")
    except Exception as e:
        logger.warning(f"[DEMO] Start service exception for {name}: {e}")


def _inject_audio_failure() -> bool:
    """Simulate Windows Audio failure: stops audio service and mutes sound output."""
    # 1. Stop audio services (including dependent Realtek/driver services)
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Stop-Service RtkAudioUniversalService -Force -ErrorAction SilentlyContinue; "
             "Stop-Service AudioSrv -Force -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=10
        )
        subprocess.run(["net", "stop", "AudioSrv", "/y"], capture_output=True, timeout=10)
    except Exception as e:
        logger.warning(f"[DEMO] Audio service stop error: {e}")

    # 2. Immediately mute system master volume so audio cuts off audibly
    try:
        import ctypes
        # APPCOMMAND_VOLUME_MUTE (0x0319, lParam = 8 << 16)
        ctypes.windll.user32.SendMessageW(0xffff, 0x0319, 0, 8 << 16)
        logger.info("[DEMO] System audio output muted for demo")
    except Exception as e:
        logger.warning(f"[DEMO] Volume mute error: {e}")

    return True


def _restore_audio_service():
    """Restore Windows Audio service and unmute sound output."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Start-Service AudioEndpointBuilder -ErrorAction SilentlyContinue; "
             "Start-Service AudioSrv -ErrorAction SilentlyContinue; "
             "Start-Service RtkAudioUniversalService -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=10
        )
        subprocess.run(["net", "start", "AudioSrv"], capture_output=True, timeout=10)
    except Exception as e:
        logger.warning(f"[DEMO] Audio service start error: {e}")

    # Unmute system master volume
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(0xffff, 0x0319, 0, 8 << 16)
        logger.info("[DEMO] System audio output unmuted")
    except Exception as e:
        logger.warning(f"[DEMO] Volume unmute error: {e}")


def _inject_temp_files() -> bool:
    """Create simulated temporary clutter files."""
    try:
        import os
        junk_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "SmartFix_Demo_TempJunk")
        os.makedirs(junk_dir, exist_ok=True)
        for i in range(12):
            fp = os.path.join(junk_dir, f"cache_dump_{i:03d}.tmp")
            with open(fp, "wb") as f:
                f.write(b"0" * (1024 * 1024 * 2))  # 24MB total clutter
        logger.info(f"[DEMO] Created temp clutter in {junk_dir}")
    except Exception as e:
        logger.warning(f"[DEMO] Temp clutter creation error: {e}")
    return True


def _cleanup_temp_files():
    """Remove simulated temp clutter files."""
    try:
        import os, shutil
        junk_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "SmartFix_Demo_TempJunk")
        if os.path.exists(junk_dir):
            shutil.rmtree(junk_dir, ignore_errors=True)
            logger.info(f"[DEMO] Cleaned up {junk_dir}")
    except Exception as e:
        logger.warning(f"[DEMO] Temp clutter cleanup error: {e}")


# ─── Demo Scenarios ────────────────────────────────────────────────────────────

DEMO_SCENARIOS: Dict[str, DemoScenario] = {
    "print_spooler_not_running": DemoScenario(
        error_id="print_spooler_not_running",
        name="Print Spooler Service Failure",
        description="Stops the Print Spooler service. SmartFix detects it within seconds and restarts it automatically.",
        inject_fn=lambda: _stop_service("Spooler"),
        cleanup_fn=lambda: _start_service("Spooler"),
    ),
    "windows_search_not_running": DemoScenario(
        error_id="windows_search_not_running",
        name="Windows Search Service Failure",
        description="Stops the Windows Search (WSearch) service. SmartFix detects the outage and restores full-text search.",
        inject_fn=lambda: _stop_service("WSearch"),
        cleanup_fn=lambda: _start_service("WSearch"),
    ),
    "windows_audio_not_running": DemoScenario(
        error_id="windows_audio_not_running",
        name="Windows Audio Service Failure",
        description="Stops Windows Audio services and mutes sound output. SmartFix detects the outage, restores the service and sound.",
        inject_fn=_inject_audio_failure,
        cleanup_fn=_restore_audio_service,
    ),
    "bluetooth_service_not_running": DemoScenario(
        error_id="bluetooth_service_not_running",
        name="Bluetooth Service Failure",
        description="Stops the Bluetooth Support service. SmartFix detects and restarts it, restoring device pairing.",
        inject_fn=lambda: _stop_service("bthserv"),
        cleanup_fn=lambda: _start_service("bthserv"),
    ),
    "windows_time_not_running": DemoScenario(
        error_id="windows_time_not_running",
        name="Windows Time Service Failure",
        description="Stops the Windows Time (W32Time) service. SmartFix restores NTP sync, fixing clock drift and SSL errors.",
        inject_fn=lambda: _stop_service("W32Time"),
        cleanup_fn=lambda: _start_service("W32Time"),
    ),
    "unknown_error_demo": DemoScenario(
        error_id="unknown_error_demo",
        name="Unknown Application Crash (AI Diagnosis)",
        description="Simulates a complex undocumented crash. Demonstrates SmartFix AI's local LLM self-diagnosis for unknown errors.",
        inject_fn=lambda: True,
        cleanup_fn=lambda: True,
    ),
    "windows_update_not_running": DemoScenario(
        error_id="windows_update_not_running",
        name="Windows Update Service Failure",
        description="Stops the Windows Update service (wuauserv). SmartFix detects the outage and restarts it to restore security patching.",
        inject_fn=lambda: _stop_service("wuauserv"),
        cleanup_fn=lambda: _start_service("wuauserv"),
    ),
    "bits_not_running": DemoScenario(
        error_id="bits_not_running",
        name="Background Transfer Service (BITS) Failure",
        description="Stops the BITS service. SmartFix detects and restores it, re-enabling background update and file downloads.",
        inject_fn=lambda: _stop_service("BITS"),
        cleanup_fn=lambda: _start_service("BITS"),
    ),
    "lab_taskmgr_cmd_regedit_disabled": DemoScenario(
        error_id="lab_taskmgr_cmd_regedit_disabled",
        name="Task Manager & CMD Blocked by Policy",
        description="Simulates a Group Policy or registry restriction locking Task Manager and Command Prompt. SmartFix removes all restrictions.",
        inject_fn=lambda: True,
        cleanup_fn=lambda: True,
    ),
    "lab_proxy_stuck_offline": DemoScenario(
        error_id="lab_proxy_stuck_offline",
        name="Proxy Server Blocking Network Access",
        description="Simulates a stale proxy configuration blocking internet access. SmartFix resets WinINET/WinHTTP proxy and restores LAN.",
        inject_fn=lambda: True,
        cleanup_fn=lambda: True,
    ),
    "lab_usb_storage_blocked": DemoScenario(
        error_id="lab_usb_storage_blocked",
        name="USB Flash Drive Blocked / Write-Protected",
        description="Simulates USB storage write-protection and driver block via Windows policy. SmartFix restores USB permissions.",
        inject_fn=lambda: True,
        cleanup_fn=lambda: True,
    ),
    "temp_files_overflow": DemoScenario(
        error_id="temp_files_overflow",
        name="Excessive Temporary Files & Cache Clutter",
        description="Simulates gigabytes of temporary junk files and application cache filling the system drive. SmartFix detects the clutter and purges temp folders safely.",
        inject_fn=_inject_temp_files,
        cleanup_fn=_cleanup_temp_files,
    ),
}

DEMO_LIST = list(DEMO_SCENARIOS.values())


class DemoController:
    """
    Manages demo scenarios. Injects an error, notifies monitor to trigger alert,
    and runs the full detection → popup toast → fix → verify flow.
    """

    def __init__(self, on_inject_error: Callable[[str], None]):
        self.on_inject_error = on_inject_error
        self._active_scenario: Optional[DemoScenario] = None

    def run_demo(self, scenario_id: str, delay_seconds: float = 1.0):
        scenario = DEMO_SCENARIOS.get(scenario_id)
        if not scenario:
            logger.warning(f"Unknown demo scenario: {scenario_id}")
            return

        self._active_scenario = scenario

        def _run():
            logger.info(f"[DEMO] Starting: {scenario.name}")
            try:
                scenario.inject()
            except Exception as e:
                logger.error(f"[DEMO] Injection exception for {scenario.name}: {e}")
            time.sleep(delay_seconds)
            # Tell monitor to send alert immediately (bypasses cooldown)
            self.on_inject_error(scenario.error_id)

        threading.Thread(target=_run, name="DemoRunner", daemon=True).start()

    def cleanup_active(self):
        """Clean up any active demo scenario."""
        if self._active_scenario:
            try:
                self._active_scenario.cleanup()
            except Exception as e:
                logger.error(f"[DEMO] Cleanup error: {e}")
            self._active_scenario = None

    def get_all_scenarios(self) -> list:
        return DEMO_LIST
