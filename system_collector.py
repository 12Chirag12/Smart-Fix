"""Read-only Windows system information collection for SmartFix AI."""

from __future__ import annotations

import os
import platform
import socket
from datetime import datetime
from typing import Any

import psutil


BYTES_PER_GB = 1024**3


def _to_gb(value: int | float) -> float:
    """Convert bytes to gigabytes and keep the UI values easy to read."""
    return round(value / BYTES_PER_GB, 2)


def _collect_processes(limit: int = 15) -> list[dict[str, Any]]:
    """Return the most memory-intensive visible processes.

    Some Windows processes are protected. Those processes are skipped instead
    of making the whole system scan fail.
    """
    processes: list[dict[str, Any]] = []

    for process in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            info = process.info
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name") or "Unknown process",
                    "cpu_percent": round(info.get("cpu_percent") or 0.0, 1),
                    "memory_percent": round(info.get("memory_percent") or 0.0, 1),
                }
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda item: item["memory_percent"], reverse=True)
    return processes[:limit]


def _collect_network() -> dict[str, Any]:
    """Collect local network status without contacting an external server."""
    interface_stats = psutil.net_if_stats()
    interface_addresses = psutil.net_if_addrs()
    active_interfaces: list[str] = []
    ipv4_addresses: list[str] = []

    for interface, addresses in interface_addresses.items():
        is_up = interface_stats.get(interface) and interface_stats[interface].isup
        if not is_up:
            continue

        interface_has_usable_address = False
        for address in addresses:
            if address.family == socket.AF_INET:
                ip_address = address.address
                # Loopback and APIPA addresses do not indicate normal connectivity.
                if not ip_address.startswith(("127.", "169.254.")):
                    ipv4_addresses.append(ip_address)
                    interface_has_usable_address = True

        if interface_has_usable_address:
            active_interfaces.append(interface)

    return {
        "available": bool(active_interfaces and ipv4_addresses),
        "hostname": socket.gethostname(),
        "active_interfaces": active_interfaces,
        "ipv4_addresses": ipv4_addresses,
        "note": "Availability is based on active local adapters; internet access is not tested.",
    }


def _collect_services() -> dict[str, Any]:
    """Read the status of a few common Windows services when supported."""
    service_names = {
        "Dhcp": "DHCP Client",
        "Dnscache": "DNS Client",
        "wuauserv": "Windows Update",
        "WinDefend": "Microsoft Defender Antivirus",
    }
    result: dict[str, Any] = {"supported": False, "items": {}}

    if platform.system() != "Windows" or not hasattr(psutil, "win_service_get"):
        return result

    result["supported"] = True
    for service_name, display_name in service_names.items():
        try:
            service_info = psutil.win_service_get(service_name).as_dict()
            result["items"][service_name] = {
                "display_name": service_info.get("display_name", display_name),
                "status": service_info.get("status", "unknown"),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as error:
            result["items"][service_name] = {
                "display_name": display_name,
                "status": "unavailable",
                "error": str(error),
            }

    return result


def collect_system_info() -> dict[str, Any]:
    """Collect a safe snapshot of system health and return it as a dictionary.

    Every section is collected independently. If one section fails, an error is
    added to ``collection_errors`` while the remaining scan continues.
    """
    info: dict[str, Any] = {
        "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": {},
        "cpu": {},
        "memory": {},
        "disk": {},
        "processes": [],
        "network": {},
        "services": {},
        "collection_errors": [],
    }

    try:
        info["system"] = {
            "operating_system": platform.system(),
            "windows_version": platform.platform(),
            "release": platform.release(),
            "computer_name": platform.node() or socket.gethostname(),
            "architecture": platform.machine(),
            "processor": platform.processor() or "Not reported by Windows",
        }
    except (OSError, RuntimeError) as error:
        info["collection_errors"].append(f"System information: {error}")

    try:
        info["cpu"] = {
            "usage_percent": round(psutil.cpu_percent(interval=0.5), 1),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
        }
    except (OSError, RuntimeError) as error:
        info["collection_errors"].append(f"CPU information: {error}")

    try:
        memory = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": _to_gb(memory.total),
            "used_gb": _to_gb(memory.used),
            "available_gb": _to_gb(memory.available),
            "usage_percent": round(memory.percent, 1),
        }
    except (OSError, RuntimeError) as error:
        info["collection_errors"].append(f"Memory information: {error}")

    try:
        system_drive = os.environ.get("SystemDrive", "C:") + "\\"
        disk = psutil.disk_usage(system_drive)
        info["disk"] = {
            "drive": system_drive,
            "total_gb": _to_gb(disk.total),
            "used_gb": _to_gb(disk.used),
            "free_gb": _to_gb(disk.free),
            "usage_percent": round(disk.percent, 1),
        }
    except (OSError, RuntimeError) as error:
        info["collection_errors"].append(f"Disk information: {error}")

    try:
        info["processes"] = _collect_processes()
    except (OSError, RuntimeError) as error:
        info["collection_errors"].append(f"Process information: {error}")

    try:
        info["network"] = _collect_network()
    except (OSError, RuntimeError) as error:
        info["network"] = {"available": False}
        info["collection_errors"].append(f"Network information: {error}")

    try:
        info["services"] = _collect_services()
    except (OSError, RuntimeError) as error:
        info["collection_errors"].append(f"Service information: {error}")

    return info


if __name__ == "__main__":
    # This makes the collector easy to test independently during development.
    from pprint import pprint

    pprint(collect_system_info())
