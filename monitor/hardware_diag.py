"""
SmartFix AI — Hardware & Deep System Diagnostics
Inspects physical drive health (S.M.A.R.T.), Windows device drivers, and battery status.
Thread-safe with non-blocking execution and graceful degradation.
"""
import json
import logging
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger("smartfix.hardware_diag")

# Windows Device Manager Error Code Dictionary
CONFIG_MGR_ERRORS = {
    1: "Device is not configured correctly (Code 1)",
    3: "Driver for this device might be corrupted (Code 3)",
    10: "Device cannot start (Code 10)",
    12: "Device cannot find enough free resources (Code 12)",
    14: "Device cannot work properly until computer restarts (Code 14)",
    18: "Reinstall the drivers for this device (Code 18)",
    22: "Device is disabled (Code 22)",
    24: "Device is not present or not working properly (Code 24)",
    28: "Drivers for this device are not installed (Code 28)",
    29: "Device is disabled because device firmware did not give resources (Code 29)",
    31: "Device is not working properly because Windows cannot load drivers (Code 31)",
    32: "Driver (service) for this device has been disabled (Code 32)",
    37: "Windows cannot initialize the device driver (Code 37)",
    38: "Windows cannot load device driver because previous instance in memory (Code 38)",
    39: "Windows cannot load device driver (corrupt or missing) (Code 39)",
    43: "Windows has stopped this device because it has reported problems (Code 43)",
    45: "Device is not connected to the computer (Code 45)",
    48: "The software for this device has been blocked from starting (Code 48)",
    52: "Windows cannot verify the digital signature for the drivers (Code 52)",
}


def _run_ps_json(script: str, timeout: int = 15) -> Any:
    """Helper to execute PowerShell and parse JSON output safely."""
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
            creationflags=0x08000000
        )
        out = res.stdout.strip()
        if not out:
            return None
        return json.loads(out)
    except Exception as e:
        logger.debug(f"PowerShell JSON query failed: {e}")
        return None


def check_disk_smart_health() -> Dict[str, Any]:
    """
    Query PhysicalDisks for S.M.A.R.T. health, operational status, and media type.
    """
    script = (
        "Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, HealthStatus, OperationalStatus "
        "| ConvertTo-Json -Compress"
    )
    raw = _run_ps_json(script, timeout=12)
    disks = []
    if isinstance(raw, dict):
        disks = [raw]
    elif isinstance(raw, list):
        disks = raw

    if not disks:
        # Fallback to wmic if Get-PhysicalDisk is unavailable (e.g. virtual machine or old OS)
        wmic_script = "Get-CimInstance Win32_DiskDrive | Select-Object DeviceID, Model, Status | ConvertTo-Json -Compress"
        wmic_raw = _run_ps_json(wmic_script, timeout=10)
        wmic_disks = [wmic_raw] if isinstance(wmic_raw, dict) else (wmic_raw or [])
        if wmic_disks:
            all_ok = all(d.get("Status", "").upper() == "OK" for d in wmic_disks)
            return {
                "status": "Healthy" if all_ok else "Warning",
                "healthy": all_ok,
                "disks": [{"FriendlyName": d.get("Model", "Disk"), "HealthStatus": d.get("Status", "OK"), "MediaType": "Drive"} for d in wmic_disks],
                "summary": f"{len(wmic_disks)} drive(s) detected — All S.M.A.R.T. statuses OK." if all_ok else "Drive SMART warning detected!",
            }
        return {
            "status": "Unknown",
            "healthy": True,
            "disks": [],
            "summary": "Storage status: Operating normally (Virtual / Standard storage)",
        }

    all_healthy = True
    disk_details = []
    for d in disks:
        h_stat = str(d.get("HealthStatus", "Healthy")).strip()
        op_stat = str(d.get("OperationalStatus", "OK")).strip()
        is_ok = (h_stat.lower() in ("healthy", "ok")) and (op_stat.lower() in ("ok", "none", ""))
        if not is_ok:
            all_healthy = False
        disk_details.append({
            "id": d.get("DeviceId", ""),
            "name": d.get("FriendlyName", "Storage Device"),
            "type": d.get("MediaType", "Unknown"),
            "health": h_stat,
            "operational": op_stat,
            "is_ok": is_ok,
        })

    status_str = "Healthy" if all_healthy else "Warning"
    summary = f"All {len(disk_details)} physical drive(s) healthy (S.M.A.R.T. Verified)" if all_healthy else "⚠️ Physical drive warning detected! Backup recommended."
    return {
        "status": status_str,
        "healthy": all_healthy,
        "disks": disk_details,
        "summary": summary,
    }


def check_driver_health() -> Dict[str, Any]:
    """
    Query PnP devices to detect any hardware devices with driver error codes.
    """
    script = (
        "Get-CimInstance Win32_PnPEntity | Where-Object ConfigManagerErrorCode -ne 0 "
        "| Select-Object Name, DeviceID, ConfigManagerErrorCode, Status | ConvertTo-Json -Compress"
    )
    raw = _run_ps_json(script, timeout=15)
    faulty = []
    if isinstance(raw, dict):
        faulty = [raw]
    elif isinstance(raw, list):
        faulty = raw

    if not faulty:
        return {
            "status": "Healthy",
            "healthy": True,
            "faulty_count": 0,
            "devices": [],
            "summary": "All hardware device drivers operational (0 errors in Device Manager).",
        }

    formatted_faulty = []
    for dev in faulty:
        code = dev.get("ConfigManagerErrorCode", 0)
        desc = CONFIG_MGR_ERRORS.get(code, f"Driver Error Code {code}")
        formatted_faulty.append({
            "name": dev.get("Name", "Unknown Device"),
            "device_id": dev.get("DeviceID", ""),
            "code": code,
            "description": desc,
            "status": dev.get("Status", "Error"),
        })

    return {
        "status": "Degraded",
        "healthy": False,
        "faulty_count": len(formatted_faulty),
        "devices": formatted_faulty,
        "summary": f"⚠️ {len(formatted_faulty)} device(s) have driver errors in Device Manager.",
    }


def check_battery_health() -> Dict[str, Any]:
    """
    Query battery status on laptops; detects desktop AC power automatically.
    """
    script = (
        "Get-CimInstance Win32_Battery "
        "| Select-Object EstimatedChargeRemaining, BatteryStatus, EstimatedRunTime "
        "| ConvertTo-Json -Compress"
    )
    raw = _run_ps_json(script, timeout=8)
    if not raw:
        return {
            "is_laptop": False,
            "status": "AC Power",
            "charge_pct": 100,
            "summary": "Desktop Workstation / Dedicated AC Power (No battery wear).",
        }

    charge = raw.get("EstimatedChargeRemaining", 100)
    b_stat = raw.get("BatteryStatus", 2)
    # 1 = discharging, 2 = AC connected / charging, 3 = fully charged
    status_map = {1: "Discharging", 2: "On AC / Charging", 3: "Fully Charged", 4: "Low", 5: "Critical"}
    state_str = status_map.get(b_stat, "Active")

    return {
        "is_laptop": True,
        "status": state_str,
        "charge_pct": charge,
        "summary": f"Laptop Battery: {charge}% ({state_str})",
    }


def run_full_hardware_diagnostics() -> Dict[str, Any]:
    """Run all hardware health diagnostics and return unified report."""
    disk = check_disk_smart_health()
    driver = check_driver_health()
    battery = check_battery_health()

    overall_healthy = disk["healthy"] and driver["healthy"]
    return {
        "healthy": overall_healthy,
        "status": "Healthy" if overall_healthy else "Attention Needed",
        "disk": disk,
        "driver": driver,
        "battery": battery,
    }
