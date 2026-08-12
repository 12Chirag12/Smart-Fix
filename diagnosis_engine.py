"""Rule-based diagnosis logic for the SmartFix AI prototype."""

from __future__ import annotations

from typing import Any


def ai_diagnosis(issue: dict[str, str]) -> str:
    """Return a temporary, human-friendly explanation for a detected issue."""
    # Temporary AI simulation - will later be replaced with Ollama/Qwen LLM integration
    explanations = {
        "High CPU Usage": (
            "The processor is under sustained load. SmartFix would next compare "
            "process activity and recent system events to isolate the responsible app."
        ),
        "High Memory Usage": (
            "Most physical memory is occupied, which can make Windows use slower "
            "disk-based virtual memory and reduce responsiveness."
        ),
        "Very Low Available Memory": (
            "Windows has little immediately available memory. Saving work and reducing "
            "the number of active applications may prevent freezes."
        ),
        "Disk Almost Full": (
            "The Windows drive has limited free space. This may affect updates, temporary "
            "files, application performance, and virtual memory."
        ),
        "Network Unavailable": (
            "No active local adapter with a normal IPv4 address was detected. The cause "
            "may be a disabled adapter, disconnected cable, Wi-Fi issue, or DHCP problem."
        ),
        "Essential Network Service Stopped": (
            "A Windows service used for automatic network configuration appears stopped, "
            "which can prevent normal address or name resolution."
        ),
    }
    return explanations.get(
        issue["problem"],
        "SmartFix found a system condition that should be reviewed before any repair is attempted.",
    )


def _issue(
    problem: str,
    cause: str,
    recommendation: str,
    severity: str,
) -> dict[str, str]:
    """Create one consistent diagnosis record."""
    issue = {
        "problem": problem,
        "possible_cause": cause,
        "recommendation": recommendation,
        "severity": severity,
    }
    issue["ai_explanation"] = ai_diagnosis(issue)
    return issue


def diagnose_system(system_info: dict[str, Any]) -> list[dict[str, str]]:
    """Analyze a collector snapshot using clear, explainable rules."""
    issues: list[dict[str, str]] = []
    cpu = system_info.get("cpu", {})
    memory = system_info.get("memory", {})
    disk = system_info.get("disk", {})
    network = system_info.get("network", {})

    cpu_usage = cpu.get("usage_percent")
    if isinstance(cpu_usage, (int, float)) and cpu_usage > 85:
        issues.append(
            _issue(
                "High CPU Usage",
                "A demanding application, background task, update, or stuck process may be using the processor.",
                "Close unnecessary applications and inspect the highest-CPU processes in Task Manager.",
                "High",
            )
        )

    ram_usage = memory.get("usage_percent")
    if isinstance(ram_usage, (int, float)) and ram_usage > 85:
        issues.append(
            _issue(
                "High Memory Usage",
                "Too many applications or background processes may be running.",
                "Close unnecessary applications and check high-memory processes in Task Manager.",
                "Medium",
            )
        )

    available_memory = memory.get("available_gb")
    if isinstance(available_memory, (int, float)) and available_memory < 1.0:
        issues.append(
            _issue(
                "Very Low Available Memory",
                "Running programs have left less than 1 GB of immediately available memory.",
                "Save your work, close unused programs, and restart Windows if responsiveness remains poor.",
                "High",
            )
        )

    disk_usage = disk.get("usage_percent")
    if isinstance(disk_usage, (int, float)) and disk_usage > 90:
        issues.append(
            _issue(
                "Disk Almost Full",
                "Large files, temporary files, downloads, or installed applications may be consuming storage.",
                "Use Windows Storage settings to review files and safely remove content you no longer need.",
                "High",
            )
        )

    if network.get("available") is False:
        issues.append(
            _issue(
                "Network Unavailable",
                "No active local network adapter with a usable IPv4 address was detected.",
                "Check Wi-Fi or Ethernet, confirm Airplane mode is off, and run the Windows network troubleshooter.",
                "Medium",
            )
        )

    service_items = system_info.get("services", {}).get("items", {})
    stopped_network_services = [
        service_items[name].get("display_name", name)
        for name in ("Dhcp", "Dnscache")
        if name in service_items and service_items[name].get("status") == "stopped"
    ]
    if stopped_network_services:
        issues.append(
            _issue(
                "Essential Network Service Stopped",
                f"The following service is stopped: {', '.join(stopped_network_services)}.",
                "Open the Windows Services console and ask an administrator to review the service configuration.",
                "Medium",
            )
        )

    return issues


def get_health_summary(issues: list[dict[str, str]]) -> str:
    """Convert diagnosis results into a short overall health label."""
    if any(item["severity"] == "High" for item in issues):
        return "Attention Required"
    if issues:
        return "Review Recommended"
    return "System Looks Healthy"
