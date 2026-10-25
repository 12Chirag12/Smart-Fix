from monitor.difficult_errors import DIFFICULT_ERRORS
from monitor.learned_repairs import load_learned_errors

"""
SmartFix AI — Comprehensive Error Catalog
Covers: 90 original Windows errors + Common Windows errors + 3rd Party App errors
Total: 150+ errors across all categories
"""
from typing import Dict, Any, List

CRITICAL = "CRITICAL"
HIGH     = "HIGH"
MEDIUM   = "MEDIUM"
LOW      = "LOW"

ERROR_CATALOG: Dict[str, Dict[str, Any]] = {

    
    
    
    "windows_update_not_running": {
        "id": "windows_update_not_running", "name": "Windows Update Service Not Running",
        "severity": CRITICAL, "category": "Windows Update",
        "description": "The Windows Update service (wuauserv) has stopped. Your system cannot receive security patches or feature updates.",
        "technical": "Service: wuauserv — Status: STOPPED",
        "detection": {"type": "service", "service_name": "wuauserv", "expected_status": "running"},
        "repair_id": "restart_windows_update", "user_permission_required": True,
    },
    "bits_not_running": {
        "id": "bits_not_running", "name": "Background Transfer Service Not Running",
        "severity": HIGH, "category": "Windows Update",
        "description": "The BITS service has stopped. Windows cannot download updates in the background.",
        "technical": "Service: BITS — Status: STOPPED",
        "detection": {"type": "service", "service_name": "BITS", "expected_status": "running"},
        "repair_id": "restart_bits", "user_permission_required": True,
    },
    "windows_update_error_0x80070002": {
        "id": "windows_update_error_0x80070002", "name": "Windows Update Error — File Not Found (0x80070002)",
        "severity": HIGH, "category": "Windows Update",
        "description": "Windows Update component files are missing. Resetting update components will fix this.",
        "technical": "Error: 0x80070002 — ERROR_FILE_NOT_FOUND",
        "detection": {"type": "event", "log": "System", "source": "WindowsUpdateClient", "event_ids": [20], "keywords": ["80070002"]},
        "repair_id": "reset_windows_update_components", "user_permission_required": True,
    },
    "windows_update_access_denied_0x80070005": {
        "id": "windows_update_access_denied_0x80070005", "name": "Windows Update Access Denied (0x80070005)",
        "severity": HIGH, "category": "Windows Update",
        "description": "Windows Update is denied access. Permissions on update folders are misconfigured.",
        "technical": "Error: 0x80070005 — ERROR_ACCESS_DENIED",
        "detection": {"type": "event", "log": "System", "source": "WindowsUpdateClient", "event_ids": [20], "keywords": ["80070005"]},
        "repair_id": "fix_windows_update_permissions", "user_permission_required": True,
    },
    "windows_update_dism_source_missing": {
        "id": "windows_update_dism_source_missing", "name": "Windows Update Component Missing (0x800F081F)",
        "severity": HIGH, "category": "Windows Update",
        "description": "A required Windows Update component is missing. DISM RestoreHealth will fix this.",
        "technical": "Error: 0x800F081F — CBS_E_SOURCE_MISSING",
        "detection": {"type": "event", "log": "System", "source": "CBS", "event_ids": [4098], "keywords": ["800F081F"]},
        "repair_id": "run_dism_restore_health", "user_permission_required": True,
    },
    "windows_update_server_comm_0x8024402F": {
        "id": "windows_update_server_comm_0x8024402F", "name": "Windows Update Server Communication Failure",
        "severity": HIGH, "category": "Windows Update",
        "description": "Cannot reach Windows Update servers. May be a proxy or network configuration issue.",
        "technical": "Error: 0x8024402F",
        "detection": {"type": "event", "log": "System", "source": "WindowsUpdateClient", "event_ids": [20], "keywords": ["8024402F"]},
        "repair_id": "reset_network_proxy_wua", "user_permission_required": True,
    },
    "windows_update_service_disabled_0x80070422": {
        "id": "windows_update_service_disabled_0x80070422", "name": "Windows Update Service Disabled (0x80070422)",
        "severity": CRITICAL, "category": "Windows Update",
        "description": "Windows Update service is disabled. System is not protected against new threats.",
        "technical": "Error: 0x80070422 — ERROR_SERVICE_DISABLED",
        "detection": {"type": "service_disabled", "service_name": "wuauserv"},
        "repair_id": "enable_windows_update", "user_permission_required": True,
    },
    "windows_update_download_stuck": {
        "id": "windows_update_download_stuck", "name": "Windows Update Download Stuck",
        "severity": MEDIUM, "category": "Windows Update",
        "description": "Windows Update is stuck downloading. Clearing the cache and restarting services should fix this.",
        "technical": "BITS/wuauserv — download hung",
        "detection": {"type": "event", "log": "System", "source": "WindowsUpdateClient", "event_ids": [20], "keywords": ["0x800705B4"]},
        "repair_id": "restart_bits_clear_update_cache", "user_permission_required": True,
    },
    "windows_installer_not_running": {
        "id": "windows_installer_not_running", "name": "Windows Installer Not Running",
        "severity": HIGH, "category": "Windows Update",
        "description": "The Windows Installer service (msiserver) has stopped. Software cannot be installed.",
        "technical": "Service: msiserver — Status: STOPPED",
        "detection": {"type": "service", "service_name": "msiserver", "expected_status": "running"},
        "repair_id": "restart_windows_installer", "user_permission_required": True,
    },
    "windows_update_0x80240034": {
        "id": "windows_update_0x80240034", "name": "Windows Update Not Applicable (0x80240034)",
        "severity": LOW, "category": "Windows Update",
        "description": "Windows Update could not find applicable updates. Running troubleshooter will re-sync.",
        "technical": "Error: 0x80240034 — WU_E_DOWNLOAD_FAILED",
        "detection": {"type": "event", "log": "System", "source": "WindowsUpdateClient", "event_ids": [20], "keywords": ["80240034"]},
        "repair_id": "run_windows_update_troubleshooter", "user_permission_required": True,
    },

    
    
    
    "dns_resolution_failure": {
        "id": "dns_resolution_failure", "name": "DNS Resolution Failure",
        "severity": CRITICAL, "category": "Network",
        "description": "Your computer cannot resolve domain names. Websites may not load.",
        "technical": "DNS_PROBE_FINISHED_NXDOMAIN",
        "detection": {"type": "dns_check", "test_host": "google.com"},
        "repair_id": "flush_dns_reset_config", "user_permission_required": True,
    },
    "no_internet_connection": {
        "id": "no_internet_connection", "name": "No Internet Connection",
        "severity": CRITICAL, "category": "Network",
        "description": "No internet connectivity detected. Network adapter, gateway, or DNS may need attention.",
        "technical": "Windows Network Connectivity/NCSI check failed",
        "detection": {"type": "internet_check", "test_urls": []},
        "repair_id": "diagnose_adapter_gateway_dns", "user_permission_required": True,
    },
    "dhcp_failure": {
        "id": "dhcp_failure", "name": "DHCP Client Failure — APIPA Address",
        "severity": HIGH, "category": "Network",
        "description": "DHCP failed to obtain an IP. System has APIPA address (169.254.x.x) — cannot connect.",
        "technical": "APIPA 169.254.x.x detected — DHCP failure",
        "detection": {"type": "ip_check", "detect_apipa": True},
        "repair_id": "restart_dhcp_renew_ip", "user_permission_required": True,
    },
    "network_stack_failure": {
        "id": "network_stack_failure", "name": "Network Stack (Winsock/TCP-IP) Failure",
        "severity": CRITICAL, "category": "Network",
        "description": "The Windows network stack is corrupted. Resetting Winsock and TCP/IP will fix this.",
        "technical": "Winsock Catalog/TCP-IP stack corrupted",
        "detection": {"type": "network_connectivity", "target": "8.8.8.8"},
        "repair_id": "reset_winsock_tcpip", "user_permission_required": True,
    },
    "network_adapter_disabled": {
        "id": "network_adapter_disabled", "name": "Network Adapter Disabled (Code 22)",
        "severity": HIGH, "category": "Network",
        "description": "A network adapter is disabled. Re-enabling it should restore connectivity.",
        "technical": "Device Manager Code 22 — adapter disabled",
        "detection": {"type": "event", "log": "System", "source": "Tcpip", "event_ids": [4227], "keywords": []},
        "repair_id": "enable_network_adapter", "user_permission_required": True,
    },
    "dhcp_service_not_running": {
        "id": "dhcp_service_not_running", "name": "DHCP Client Service Not Running",
        "severity": HIGH, "category": "Network",
        "description": "The DHCP Client service stopped. Cannot obtain an IP address automatically.",
        "technical": "Service: Dhcp — Status: STOPPED",
        "detection": {"type": "service", "service_name": "Dhcp", "expected_status": "running"},
        "repair_id": "restart_dhcp_service", "user_permission_required": True,
    },
    "dns_client_not_running": {
        "id": "dns_client_not_running", "name": "DNS Client Service Not Running",
        "severity": HIGH, "category": "Network",
        "description": "The DNS Client service stopped. Name resolution and network browsing are impaired.",
        "technical": "Service: Dnscache — Status: STOPPED",
        "detection": {"type": "service", "service_name": "Dnscache", "expected_status": "running"},
        "repair_id": "restart_dns_client", "user_permission_required": True,
    },
    "windows_firewall_disabled": {
        "id": "windows_firewall_disabled", "name": "Windows Firewall Disabled",
        "severity": HIGH, "category": "Network",
        "description": "Windows Firewall service is not running. Your system is exposed to network threats.",
        "technical": "Service: MpsSvc — Status: STOPPED",
        "detection": {"type": "service", "service_name": "MpsSvc", "expected_status": "running"},
        "repair_id": "restart_windows_firewall", "user_permission_required": True,
    },
    "default_gateway_unavailable": {
        "id": "default_gateway_unavailable", "name": "Default Gateway Unavailable",
        "severity": HIGH, "category": "Network",
        "description": "Default gateway is unreachable. Renewing IP configuration should fix this.",
        "technical": "TCP/IP Default Gateway — ping failed",
        "detection": {"type": "gateway_check"},
        "repair_id": "renew_ip_reset_network", "user_permission_required": True,
    },
    "network_sharing_not_running": {
        "id": "network_sharing_not_running", "name": "Network List Service Not Running",
        "severity": MEDIUM, "category": "Network",
        "description": "The Network List service stopped. Network location detection is unavailable.",
        "technical": "Service: netprofm — Status: STOPPED",
        "detection": {"type": "service", "service_name": "netprofm", "expected_status": "running"},
        "repair_id": "restart_network_services", "user_permission_required": True,
    },

    
    
    
    "print_spooler_not_running": {
        "id": "print_spooler_not_running", "name": "Print Spooler Not Running",
        "severity": HIGH, "category": "Printing",
        "description": "The Windows Print Spooler service stopped. All printing operations are disabled.",
        "technical": "Service: Spooler — Status: STOPPED",
        "detection": {"type": "service", "service_name": "Spooler", "expected_status": "running"},
        "repair_id": "restart_print_spooler", "user_permission_required": True,
    },
    "printer_queue_stuck": {
        "id": "printer_queue_stuck", "name": "Printer Queue Stuck",
        "severity": MEDIUM, "category": "Printing",
        "description": "Print jobs are stuck in the queue. Clearing the spool folder and restarting Spooler fixes this.",
        "technical": "Windows Print Spooler Queue — stuck jobs",
        "detection": {"type": "event", "log": "System", "source": "Print", "event_ids": [372, 805], "keywords": []},
        "repair_id": "clear_print_queue_restart_spooler", "user_permission_required": True,
    },
    "printer_offline": {
        "id": "printer_offline", "name": "Printer Showing Offline",
        "severity": MEDIUM, "category": "Printing",
        "description": "Default printer is showing as Offline. Restarting Spooler and resetting printer port should help.",
        "technical": "Windows Printer Status — Offline",
        "detection": {"type": "event", "log": "System", "source": "Print", "event_ids": [23, 12], "keywords": []},
        "repair_id": "fix_printer_offline", "user_permission_required": True,
    },

    
    
    
    "windows_audio_not_running": {
        "id": "windows_audio_not_running", "name": "Windows Audio Not Running",
        "severity": HIGH, "category": "Audio",
        "description": "The Windows Audio service stopped. No sound can be played or recorded.",
        "technical": "Service: AudioSrv — Status: STOPPED",
        "detection": {"type": "service", "service_name": "AudioSrv", "expected_status": "running"},
        "repair_id": "restart_audio_services", "user_permission_required": True,
    },
    "audio_endpoint_failure": {
        "id": "audio_endpoint_failure", "name": "Audio Endpoint Builder Failed",
        "severity": HIGH, "category": "Audio",
        "description": "The Audio Endpoint Builder service stopped. Audio devices cannot be enumerated.",
        "technical": "Service: AudioEndpointBuilder — STOPPED",
        "detection": {"type": "service", "service_name": "AudioEndpointBuilder", "expected_status": "running"},
        "repair_id": "restart_audio_endpoint", "user_permission_required": True,
    },
    "audio_driver_failure": {
        "id": "audio_driver_failure", "name": "Audio Driver Failure",
        "severity": HIGH, "category": "Audio",
        "description": "Windows audio driver has failed. No sound output device is available.",
        "technical": "Device Manager — Audio device error",
        "detection": {"type": "event", "log": "System", "source": "audiodg", "event_ids": [10], "keywords": ["audio"]},
        "repair_id": "reinstall_audio_driver", "user_permission_required": True,
    },

    
    
    
    "bluetooth_service_not_running": {
        "id": "bluetooth_service_not_running", "name": "Bluetooth Service Not Running",
        "severity": MEDIUM, "category": "Bluetooth",
        "description": "The Bluetooth Support service stopped. Bluetooth devices cannot connect.",
        "technical": "Service: bthserv — Status: STOPPED",
        "detection": {"type": "service", "service_name": "bthserv", "expected_status": "running"},
        "repair_id": "restart_bluetooth_service", "user_permission_required": True,
    },
    "windows_time_not_running": {
        "id": "windows_time_not_running", "name": "Windows Time Service Not Running",
        "severity": MEDIUM, "category": "System",
        "description": "The Windows Time service stopped. System clock synchronization is disabled.",
        "technical": "Service: W32Time — Status: STOPPED",
        "detection": {"type": "service", "service_name": "W32Time", "expected_status": "running"},
        "repair_id": "restart_windows_time", "user_permission_required": True,
    },
    "windows_search_not_running": {
        "id": "windows_search_not_running", "name": "Windows Search Not Running",
        "severity": MEDIUM, "category": "System",
        "description": "The Windows Search service stopped. File and Start Menu search will not function.",
        "technical": "Service: WSearch — Status: STOPPED",
        "detection": {"type": "service", "service_name": "WSearch", "expected_status": "running"},
        "repair_id": "restart_windows_search", "user_permission_required": True,
    },
    "wmi_service_not_running": {
        "id": "wmi_service_not_running", "name": "WMI Service Not Running",
        "severity": HIGH, "category": "System",
        "description": "Windows Management Instrumentation stopped. System management tools will fail.",
        "technical": "Service: winmgmt — Status: STOPPED",
        "detection": {"type": "service", "service_name": "winmgmt", "expected_status": "running"},
        "repair_id": "restart_wmi_service", "user_permission_required": True,
    },
    "windows_defender_disabled": {
        "id": "windows_defender_disabled", "name": "Windows Defender Disabled",
        "severity": CRITICAL, "category": "Security",
        "description": "Windows Defender real-time protection is disabled. System is vulnerable to malware.",
        "technical": "Service: WinDefend — STOPPED or Disabled",
        "detection": {"type": "service", "service_name": "WinDefend", "expected_status": "running"},
        "repair_id": "enable_windows_defender", "user_permission_required": True,
    },
    "cryptographic_service_not_running": {
        "id": "cryptographic_service_not_running", "name": "Cryptographic Services Not Running",
        "severity": HIGH, "category": "Security",
        "description": "Cryptographic Services stopped. Certificate validation and Windows Update will fail.",
        "technical": "Service: CryptSvc — Status: STOPPED",
        "detection": {"type": "service", "service_name": "CryptSvc", "expected_status": "running"},
        "repair_id": "restart_cryptographic_services", "user_permission_required": True,
    },
    "service_startup_failure_7000": {
        "id": "service_startup_failure_7000", "name": "Service Startup Failure (Event 7000)",
        "severity": HIGH, "category": "Services",
        "description": "A Windows service failed to start. Service configuration or dependencies may be the cause.",
        "technical": "Service Control Manager Event ID 7000",
        "detection": {"type": "event", "log": "System", "source": "Service Control Manager", "event_ids": [7000], "keywords": []},
        "repair_id": "repair_failed_service", "user_permission_required": True,
    },
    "service_unexpected_termination_7031": {
        "id": "service_unexpected_termination_7031", "name": "Service Terminated Unexpectedly (Event 7031)",
        "severity": HIGH, "category": "Services",
        "description": "A service terminated unexpectedly. Recovery actions may have been triggered.",
        "technical": "Service Control Manager Event ID 7031",
        "detection": {"type": "event", "log": "System", "source": "Service Control Manager", "event_ids": [7031], "keywords": []},
        "repair_id": "analyze_restart_crashed_service", "user_permission_required": True,
    },
    "sysmain_not_running": {
        "id": "sysmain_not_running", "name": "SysMain (Superfetch) Not Running",
        "severity": LOW, "category": "Performance",
        "description": "SysMain service stopped. Application load times may increase.",
        "technical": "Service: SysMain — Status: STOPPED",
        "detection": {"type": "service", "service_name": "SysMain", "expected_status": "running"},
        "repair_id": "restart_sysmain", "user_permission_required": True,
    },
    "windows_installer_service_not_running": {
        "id": "windows_installer_service_not_running", "name": "Windows Installer Service Not Running",
        "severity": HIGH, "category": "Applications",
        "description": "Windows Installer stopped. Software cannot be installed or uninstalled.",
        "technical": "Service: msiserver — Status: STOPPED",
        "detection": {"type": "service", "service_name": "msiserver", "expected_status": "running"},
        "repair_id": "restart_windows_installer", "user_permission_required": True,
    },

    
    
    
    "file_explorer_crash": {
        "id": "file_explorer_crash", "name": "Windows Explorer Crash",
        "severity": HIGH, "category": "Shell",
        "description": "Windows Explorer (explorer.exe) crashed. Desktop and file browsing are unavailable.",
        "technical": "Event ID 1000 — explorer.exe Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["explorer.exe"]},
        "repair_id": "restart_explorer", "user_permission_required": False,
    },
    "taskbar_not_responding": {
        "id": "taskbar_not_responding", "name": "Taskbar Not Responding",
        "severity": HIGH, "category": "Shell",
        "description": "The Windows taskbar is not responding. Restarting Explorer will restore it.",
        "technical": "Windows Shell / explorer.exe hang",
        "detection": {"type": "event", "log": "Application", "source": "Application Hang", "event_ids": [1002], "keywords": ["explorer"]},
        "repair_id": "restart_explorer", "user_permission_required": False,
    },
    "start_menu_not_working": {
        "id": "start_menu_not_working", "name": "Start Menu Not Working",
        "severity": HIGH, "category": "Shell",
        "description": "The Windows Start Menu is unresponsive. Restarting Shell Experience Host fixes this.",
        "technical": "Windows Shell / StartMenuExperienceHost.exe hang",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["StartMenuExperienceHost"]},
        "repair_id": "restart_start_menu", "user_permission_required": False,
    },
    "windows_system_file_corruption": {
        "id": "windows_system_file_corruption", "name": "Windows System File Corruption",
        "severity": CRITICAL, "category": "System Integrity",
        "description": "Windows system files are corrupted. SFC scan and DISM will repair them.",
        "technical": "Windows Resource Protection — corruption detected",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-WER-SystemErrorReporting", "event_ids": [1001], "keywords": ["corruption"]},
        "repair_id": "run_dism_then_sfc", "user_permission_required": True,
    },
    "windows_component_store_corruption": {
        "id": "windows_component_store_corruption", "name": "Windows Component Store Corruption",
        "severity": CRITICAL, "category": "System Integrity",
        "description": "The Windows Component Store (DISM) is corrupted. RestoreHealth is required.",
        "technical": "DISM Component Store — corruption detected",
        "detection": {"type": "event", "log": "System", "source": "CBS", "event_ids": [4098], "keywords": ["corrupt"]},
        "repair_id": "run_dism_restore_health", "user_permission_required": True,
    },

    
    
    
    "high_cpu_usage": {
        "id": "high_cpu_usage", "name": "Critical CPU Usage (>90%)",
        "severity": HIGH, "category": "Performance",
        "description": "CPU usage is critically high. A runaway process may be causing system slowdown.",
        "technical": "Process CPU utilization >90% sustained",
        "detection": {"type": "metric", "metric": "cpu_percent", "threshold": 90.0, "duration_seconds": 30},
        "repair_id": "identify_high_cpu_process", "user_permission_required": False,
    },
    "high_memory_usage": {
        "id": "high_memory_usage", "name": "Critical Memory Usage (>90%)",
        "severity": HIGH, "category": "Performance",
        "description": "System memory critically low. Applications may crash or freeze.",
        "technical": "Available RAM below 10%",
        "detection": {"type": "metric", "metric": "memory_percent", "threshold": 90.0},
        "repair_id": "identify_high_memory_process", "user_permission_required": False,
    },
    "disk_full": {
        "id": "disk_full", "name": "Disk Almost Full (C: >95%)",
        "severity": CRITICAL, "category": "Performance",
        "description": "Drive C: is nearly full. System performance degrades and apps may fail to save.",
        "technical": "Disk C: >95% used",
        "detection": {"type": "metric", "metric": "disk_usage_percent", "threshold": 95.0},
        "repair_id": "identify_disk_usage_cause", "user_permission_required": False,
    },
    "slow_windows_startup": {
        "id": "slow_windows_startup", "name": "Slow Windows Startup",
        "severity": MEDIUM, "category": "Performance",
        "description": "Windows startup is taking significantly longer than normal. Too many startup items.",
        "technical": "Windows Diagnostics-Performance Event ID 100 — degraded",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Diagnostics-Performance", "event_ids": [100], "keywords": ["degraded"]},
        "repair_id": "optimize_startup_items", "user_permission_required": True,
    },
    "excessive_application_cpu": {
        "id": "excessive_application_cpu", "name": "Single App Using Excessive CPU (>50%)",
        "severity": MEDIUM, "category": "Performance",
        "description": "A single application is consuming over 50% of CPU resources.",
        "technical": "Single process CPU >50%",
        "detection": {"type": "metric", "metric": "top_process_cpu", "threshold": 50.0},
        "repair_id": "identify_cpu_hog_app", "user_permission_required": False,
    },
    "excessive_application_memory": {
        "id": "excessive_application_memory", "name": "Single App Using Excessive Memory (>1GB)",
        "severity": MEDIUM, "category": "Performance",
        "description": "An application is consuming over 1GB RAM. A memory leak may be present.",
        "technical": "Single process working set >1024MB",
        "detection": {"type": "metric", "metric": "top_process_memory_mb", "threshold": 1024.0},
        "repair_id": "identify_memory_leak_app", "user_permission_required": False,
    },
    "disk_io_warning": {
        "id": "disk_io_warning", "name": "Disk I/O Warning (Event ID 51)",
        "severity": MEDIUM, "category": "Disk",
        "description": "Disk I/O errors detected. The disk may have bad sectors or failing hardware.",
        "technical": "Event ID 51 — Disk I/O warning",
        "detection": {"type": "event", "log": "System", "source": "disk", "event_ids": [51], "keywords": []},
        "repair_id": "run_chkdsk_ntfs", "user_permission_required": True,
    },
    "disk_hardware_error": {
        "id": "disk_hardware_error", "name": "Disk Hardware Error (Event ID 7)",
        "severity": CRITICAL, "category": "Disk",
        "description": "A disk hardware I/O error detected. Data loss risk. Immediate diagnosis required.",
        "technical": "Event ID 7 — Disk I/O hardware error",
        "detection": {"type": "event", "log": "System", "source": "disk", "event_ids": [7], "keywords": []},
        "repair_id": "diagnose_disk_health", "user_permission_required": False,
    },

    
    
    
    "device_disabled_code22": {
        "id": "device_disabled_code22", "name": "Device Disabled — Code 22",
        "severity": MEDIUM, "category": "Drivers",
        "description": "A device is disabled in Device Manager. Re-enabling it restores functionality.",
        "technical": "Device Manager Code 22 — disabled",
        "detection": {"type": "event", "log": "System", "source": "Plug and Play", "event_ids": [219], "keywords": ["22"]},
        "repair_id": "enable_disabled_device", "user_permission_required": True,
    },
    "device_cannot_start_code10": {
        "id": "device_cannot_start_code10", "name": "Device Cannot Start — Code 10",
        "severity": HIGH, "category": "Drivers",
        "description": "A device cannot start. The driver may need to be updated or reinstalled.",
        "technical": "Device Manager Code 10 — cannot start",
        "detection": {"type": "event", "log": "System", "source": "Plug and Play", "event_ids": [219], "keywords": ["10"]},
        "repair_id": "reinstall_device_driver", "user_permission_required": True,
    },
    "driver_missing_code28": {
        "id": "driver_missing_code28", "name": "Device Driver Missing — Code 28",
        "severity": HIGH, "category": "Drivers",
        "description": "A device has no driver installed. The correct driver needs to be installed.",
        "technical": "Device Manager Code 28 — no driver",
        "detection": {"type": "event", "log": "System", "source": "Plug and Play", "event_ids": [219], "keywords": ["28"]},
        "repair_id": "install_missing_driver", "user_permission_required": True,
    },
    "unexpected_shutdown_kernel41": {
        "id": "unexpected_shutdown_kernel41", "name": "Unexpected System Shutdown (Kernel-Power 41)",
        "severity": CRITICAL, "category": "Power",
        "description": "System was shut down unexpectedly. Indicates a crash, power loss, or driver failure.",
        "technical": "Kernel-Power Event ID 41 — unexpected shutdown",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Kernel-Power", "event_ids": [41], "keywords": []},
        "repair_id": "analyze_power_shutdown_logs", "user_permission_required": False,
    },
    "ntfs_filesystem_error_id55": {
        "id": "ntfs_filesystem_error_id55", "name": "NTFS File-System Error (Event ID 55)",
        "severity": HIGH, "category": "Disk",
        "description": "An NTFS file system error detected. File system integrity may be compromised.",
        "technical": "Event ID 55 — NTFS file-system error",
        "detection": {"type": "event", "log": "System", "source": "Ntfs", "event_ids": [55], "keywords": []},
        "repair_id": "run_chkdsk_ntfs", "user_permission_required": True,
    },
    "distributedcom_error_10016": {
        "id": "distributedcom_error_10016", "name": "DistributedCOM Error (Event ID 10016)",
        "severity": LOW, "category": "System",
        "description": "DistributedCOM configuration error logged. May affect certain application services.",
        "technical": "Event ID 10016 — DistributedCOM",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-DistributedCOM", "event_ids": [10016], "keywords": []},
        "repair_id": "analyze_dcom_configuration", "user_permission_required": False,
    },
    "microsoft_store_failure": {
        "id": "microsoft_store_failure", "name": "Microsoft Store Failure",
        "severity": MEDIUM, "category": "Applications",
        "description": "Microsoft Store failed to load or connect. Resetting the Store cache should fix this.",
        "technical": "Microsoft Store / WSReset.exe failure",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft-Windows-AppModel-Runtime", "event_ids": [65], "keywords": []},
        "repair_id": "reset_microsoft_store", "user_permission_required": False,
    },
    "windows_activation_error": {
        "id": "windows_activation_error", "name": "Windows Activation Error",
        "severity": HIGH, "category": "System",
        "description": "Windows is not activated. The Software Licensing service may need to be restarted.",
        "technical": "Service: sppsvc — Software Protection / Activation",
        "detection": {"type": "service", "service_name": "sppsvc", "expected_status": "running"},
        "repair_id": "fix_windows_activation", "user_permission_required": True,
    },

    
    
    
    "application_crash_event1000": {
        "id": "application_crash_event1000", "name": "Application Crash Detected (Event 1000)",
        "severity": HIGH, "category": "Applications",
        "description": "An application crashed unexpectedly. Windows Error Reporting logged the event.",
        "technical": "Event ID 1000 — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": []},
        "repair_id": "analyze_repair_app_crash", "user_permission_required": True,
    },
    "application_hang_event1002": {
        "id": "application_hang_event1002", "name": "Application Not Responding (Event 1002)",
        "severity": MEDIUM, "category": "Applications",
        "description": "An application stopped responding. It may need to be terminated and restarted.",
        "technical": "Event ID 1002 — Application Hang",
        "detection": {"type": "event", "log": "Application", "source": "Application Hang", "event_ids": [1002], "keywords": []},
        "repair_id": "analyze_app_hang", "user_permission_required": True,
    },
    "missing_dll_error": {
        "id": "missing_dll_error", "name": "Missing DLL Error",
        "severity": HIGH, "category": "Applications",
        "description": "An application cannot start because a required DLL is missing. Installing the correct runtime should fix this.",
        "technical": "STATUS_DLL_NOT_FOUND / DLL load failure",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["dll"]},
        "repair_id": "repair_app_dll_dependency", "user_permission_required": True,
    },
    "dotnet_runtime_error": {
        "id": "dotnet_runtime_error", "name": ".NET Runtime Error",
        "severity": HIGH, "category": "Applications",
        "description": "A .NET application has crashed. The .NET runtime may need repair or reinstallation.",
        "technical": ".NET Runtime — application crash",
        "detection": {"type": "event", "log": "Application", "source": ".NET Runtime", "event_ids": [1026], "keywords": []},
        "repair_id": "repair_dotnet_runtime", "user_permission_required": True,
    },
    "vcredist_missing": {
        "id": "vcredist_missing", "name": "Visual C++ Runtime Missing",
        "severity": HIGH, "category": "Applications",
        "description": "Visual C++ Redistributable is missing or corrupt. Many applications require it.",
        "technical": "MSVCP*.dll / VCRUNTIME*.dll not found",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["MSVCP", "VCRUNTIME"]},
        "repair_id": "install_vcredist", "user_permission_required": True,
    },
    "directx_error": {
        "id": "directx_error", "name": "DirectX Error",
        "severity": HIGH, "category": "Applications",
        "description": "DirectX has encountered an error. Reinstalling or repairing DirectX will fix this.",
        "technical": "DirectX / d3d error — application crash",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["d3d", "dxgi", "directx"]},
        "repair_id": "repair_directx", "user_permission_required": True,
    },
    "windows_search_indexing_failure": {
        "id": "windows_search_indexing_failure", "name": "Windows Search Indexing Failure",
        "severity": LOW, "category": "System",
        "description": "Windows Search indexer failed. Search results will be incomplete.",
        "technical": "Search Event ID 3036, 3079",
        "detection": {"type": "event", "log": "Application", "source": "Search", "event_ids": [3036], "keywords": []},
        "repair_id": "rebuild_search_index", "user_permission_required": True,
    },
    "windows_error_reporting_disabled": {
        "id": "windows_error_reporting_disabled", "name": "Windows Error Reporting Issue",
        "severity": LOW, "category": "Applications",
        "description": "Windows Error Reporting service issue detected. Crash data may not be logged.",
        "technical": "WerSvc — Windows Error Reporting service issue",
        "detection": {"type": "service", "service_name": "WerSvc", "expected_status": "running"},
        "repair_id": "restart_wer_service", "user_permission_required": True,
    },

    
    
    
    "valorant_van_82": {
        "id": "valorant_van_82", "name": "Valorant Error VAN 82 — Vanguard Service Failure",
        "severity": HIGH, "category": "Valorant",
        "description": "Valorant cannot start because the Vanguard anti-cheat service (vgc) failed to start. Restarting Vanguard and running as admin fixes this.",
        "technical": "VAN 82 — vgc service failed / Vanguard not running",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["vgc", "vanguard"]},
        "repair_id": "fix_valorant_van82", "user_permission_required": True,
    },
    "valorant_van_81": {
        "id": "valorant_van_81", "name": "Valorant Error VAN 81 — Vanguard Driver Issue",
        "severity": HIGH, "category": "Valorant",
        "description": "Vanguard anti-cheat driver failed to load. Reinstalling Vanguard and enabling Secure Boot usually fixes VAN 81.",
        "technical": "VAN 81 — vgk.sys driver failed to initialize",
        "detection": {"type": "event", "log": "System", "source": "vgk", "event_ids": [7000, 7026], "keywords": ["vgk"]},
        "repair_id": "fix_valorant_van81", "user_permission_required": True,
    },
    "valorant_van_1067": {
        "id": "valorant_van_1067", "name": "Valorant Error VAN 1067 — Vanguard Startup Failure",
        "severity": HIGH, "category": "Valorant",
        "description": "Vanguard failed to start (error 1067). Reinstalling Vanguard or fixing the service startup type will resolve this.",
        "technical": "VAN 1067 — vgc service ERROR_PROCESS_ABORTED",
        "detection": {"type": "event", "log": "System", "source": "Service Control Manager", "event_ids": [7000], "keywords": ["vgc"]},
        "repair_id": "fix_valorant_van1067", "user_permission_required": True,
    },
    "valorant_van_9001": {
        "id": "valorant_van_9001", "name": "Valorant Error VAN 9001 — TPM / Secure Boot Issue",
        "severity": HIGH, "category": "Valorant",
        "description": "Valorant requires TPM 2.0 and Secure Boot. VAN 9001 means one of these is disabled in BIOS/UEFI settings.",
        "technical": "VAN 9001 — TPM 2.0 not enabled or Secure Boot disabled",
        "detection": {"type": "event", "log": "Application", "source": "ESRV", "event_ids": [1000], "keywords": ["VAN 9001", "tpm"]},
        "repair_id": "fix_valorant_van9001", "user_permission_required": True,
    },
    "valorant_van_128": {
        "id": "valorant_van_128", "name": "Valorant Error VAN 128 — Vanguard Compatibility",
        "severity": MEDIUM, "category": "Valorant",
        "description": "Vanguard compatibility error VAN 128. Running in a VM or having conflicting security software causes this.",
        "technical": "VAN 128 — incompatible environment detected",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["vgc.exe", "vanguard"]},
        "repair_id": "fix_valorant_van128", "user_permission_required": True,
    },
    "valorant_directx_error": {
        "id": "valorant_directx_error", "name": "Valorant DirectX Error",
        "severity": HIGH, "category": "Valorant",
        "description": "Valorant encountered a DirectX error. Updating GPU drivers and DirectX usually fixes this.",
        "technical": "Valorant — DirectX/GPU driver error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["VALORANT-Win64", "dxgi"]},
        "repair_id": "fix_valorant_directx", "user_permission_required": True,
    },

    
    
    
    "steam_service_not_running": {
        "id": "steam_service_not_running", "name": "Steam Client Service Not Running",
        "severity": MEDIUM, "category": "Steam",
        "description": "Steam Client Service stopped. Some Steam features and games with anti-cheat will not work.",
        "technical": "Service: Steam Client Service — STOPPED",
        "detection": {"type": "service", "service_name": "Steam Client Service", "expected_status": "running"},
        "repair_id": "fix_steam_service", "user_permission_required": True,
    },
    "steam_corrupt_files": {
        "id": "steam_corrupt_files", "name": "Steam Game Files Corrupt",
        "severity": MEDIUM, "category": "Steam",
        "description": "Steam game files are corrupted. Verifying file integrity through Steam will repair them.",
        "technical": "Steam — game file integrity check failed",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["steam.exe", "steamclient"]},
        "repair_id": "fix_steam_corrupt_files", "user_permission_required": False,
    },
    "steam_disk_write_error": {
        "id": "steam_disk_write_error", "name": "Steam Disk Write Error",
        "severity": HIGH, "category": "Steam",
        "description": "Steam cannot write to disk. Disk full, permission issues, or antivirus blocking Steam.",
        "technical": "Steam — disk write error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["steam", "disk write"]},
        "repair_id": "fix_steam_disk_write", "user_permission_required": True,
    },
    "steam_api_missing": {
        "id": "steam_api_missing", "name": "Steam API DLL Missing (steam_api.dll)",
        "severity": HIGH, "category": "Steam",
        "description": "steam_api.dll or steam_api64.dll is missing. Reinstalling the game from Steam should fix this.",
        "technical": "steam_api.dll / steam_api64.dll — not found",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["steam_api"]},
        "repair_id": "fix_steam_api_dll", "user_permission_required": False,
    },

    
    
    
    "discord_crash": {
        "id": "discord_crash", "name": "Discord Crash / Won't Open",
        "severity": MEDIUM, "category": "Discord",
        "description": "Discord has crashed or won't open. Clearing the Discord cache and reinstalling usually fixes this.",
        "technical": "Discord.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Discord.exe"]},
        "repair_id": "fix_discord_crash", "user_permission_required": False,
    },
    "discord_update_failed": {
        "id": "discord_update_failed", "name": "Discord Update Failed",
        "severity": MEDIUM, "category": "Discord",
        "description": "Discord update failed. Running the updater as administrator usually resolves this.",
        "technical": "Discord Update.exe — error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Update.exe", "discord"]},
        "repair_id": "fix_discord_update", "user_permission_required": True,
    },
    "discord_no_route": {
        "id": "discord_no_route", "name": "Discord No Route / Voice Not Working",
        "severity": MEDIUM, "category": "Discord",
        "description": "Discord voice chat shows 'No Route'. Flushing DNS and resetting network fixes this.",
        "technical": "Discord — WebRTC no route / UDP blocked",
        "detection": {"type": "dns_check", "test_host": "discord.com"},
        "repair_id": "fix_discord_no_route", "user_permission_required": True,
    },

    
    
    
    "chrome_crash": {
        "id": "chrome_crash", "name": "Google Chrome Crash / Aw, Snap!",
        "severity": MEDIUM, "category": "Browser",
        "description": "Chrome has crashed. Clearing cache, disabling hardware acceleration, or resetting Chrome profile may fix this.",
        "technical": "chrome.exe — Application Error / Aw, Snap!",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["chrome.exe"]},
        "repair_id": "fix_chrome_crash", "user_permission_required": False,
    },
    "chrome_no_sound": {
        "id": "chrome_no_sound", "name": "Chrome No Sound",
        "severity": LOW, "category": "Browser",
        "description": "Chrome has no audio output. Resetting audio settings and the audio service fixes this.",
        "technical": "Chrome — audio renderer error",
        "detection": {"type": "service", "service_name": "AudioSrv", "expected_status": "running"},
        "repair_id": "fix_chrome_no_sound", "user_permission_required": True,
    },
    "browser_ssl_error": {
        "id": "browser_ssl_error", "name": "SSL Certificate / HTTPS Error",
        "severity": MEDIUM, "category": "Browser",
        "description": "Browser shows SSL certificate errors. System date/time mismatch or corrupted certificate store causes this.",
        "technical": "NET::ERR_CERT_DATE_INVALID / SSL_ERROR",
        "detection": {"type": "service", "service_name": "CryptSvc", "expected_status": "running"},
        "repair_id": "fix_ssl_certificate_errors", "user_permission_required": True,
    },

    
    
    
    "office_activation_error": {
        "id": "office_activation_error", "name": "Microsoft Office Activation Error",
        "severity": HIGH, "category": "Office",
        "description": "Microsoft Office cannot be activated. Running the Office activation troubleshooter will fix this.",
        "technical": "Office Activation — license validation failed",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft Office", "event_ids": [2011], "keywords": ["activation"]},
        "repair_id": "fix_office_activation", "user_permission_required": True,
    },
    "office_crash": {
        "id": "office_crash", "name": "Microsoft Office Application Crash",
        "severity": HIGH, "category": "Office",
        "description": "A Microsoft Office application (Word, Excel, etc.) crashed. Running Office Repair will fix corrupted files.",
        "technical": "WINWORD.EXE / EXCEL.EXE — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["WINWORD", "EXCEL", "POWERPNT", "OUTLOOK"]},
        "repair_id": "fix_office_crash", "user_permission_required": True,
    },
    "outlook_pst_corrupt": {
        "id": "outlook_pst_corrupt", "name": "Outlook PST File Corrupted",
        "severity": HIGH, "category": "Office",
        "description": "Outlook data file (PST/OST) is corrupted. Running ScanPST (Inbox Repair Tool) will recover it.",
        "technical": "OUTLOOK.EXE — PST/OST file corruption",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["OUTLOOK.EXE", "pst"]},
        "repair_id": "fix_outlook_pst", "user_permission_required": False,
    },

    
    
    
    "epic_games_crash": {
        "id": "epic_games_crash", "name": "Epic Games Launcher Crash",
        "severity": MEDIUM, "category": "Gaming",
        "description": "Epic Games Launcher crashed or won't open. Clearing cache and reinstalling WebView2 usually fixes this.",
        "technical": "EpicGamesLauncher.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["EpicGamesLauncher"]},
        "repair_id": "fix_epic_games", "user_permission_required": False,
    },
    "ea_app_crash": {
        "id": "ea_app_crash", "name": "EA App / Origin Crash",
        "severity": MEDIUM, "category": "Gaming",
        "description": "EA App or Origin crashed. Clearing cache and reinstalling EADesktop fixes most crashes.",
        "technical": "EADesktop.exe / Origin.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["EADesktop", "Origin.exe"]},
        "repair_id": "fix_ea_app", "user_permission_required": False,
    },
    "battlenet_crash": {
        "id": "battlenet_crash", "name": "Battle.net Launcher Crash",
        "severity": MEDIUM, "category": "Gaming",
        "description": "Battle.net crashed or shows a blank screen. Clearing Battle.net cache resolves most issues.",
        "technical": "Battle.net.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Battle.net", "Battlenet"]},
        "repair_id": "fix_battlenet", "user_permission_required": False,
    },
    "minecraft_java_error": {
        "id": "minecraft_java_error", "name": "Minecraft Java Error / Won't Launch",
        "severity": MEDIUM, "category": "Gaming",
        "description": "Minecraft (Java Edition) won't launch. Missing or corrupt Java runtime is usually the cause.",
        "technical": "javaw.exe — Application Error / Java not found",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["javaw.exe", "minecraft"]},
        "repair_id": "fix_minecraft_java", "user_permission_required": False,
    },
    "roblox_crash": {
        "id": "roblox_crash", "name": "Roblox Crash",
        "severity": MEDIUM, "category": "Gaming",
        "description": "Roblox crashed unexpectedly. Reinstalling Roblox or clearing the cache fixes most crashes.",
        "technical": "RobloxPlayerBeta.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["RobloxPlayerBeta", "RobloxPlayer"]},
        "repair_id": "fix_roblox", "user_permission_required": False,
    },

    
    
    
    "bsod_critical_process_died": {
        "id": "bsod_critical_process_died", "name": "BSOD — CRITICAL_PROCESS_DIED",
        "severity": CRITICAL, "category": "BSOD",
        "description": "A critical Windows process died causing a Blue Screen. Running SFC and checking drivers usually fixes this.",
        "technical": "Stop Code: CRITICAL_PROCESS_DIED — 0x000000EF",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-WER-SystemErrorReporting", "event_ids": [1001], "keywords": ["0xEF", "critical_process"]},
        "repair_id": "fix_bsod_critical_process", "user_permission_required": True,
    },
    "bsod_system_service_exception": {
        "id": "bsod_system_service_exception", "name": "BSOD — SYSTEM_SERVICE_EXCEPTION",
        "severity": CRITICAL, "category": "BSOD",
        "description": "A BSOD with SYSTEM_SERVICE_EXCEPTION. Usually caused by a faulty driver. SFC and driver update will help.",
        "technical": "Stop Code: SYSTEM_SERVICE_EXCEPTION — 0x0000003B",
        "detection": {"type": "event", "log": "System", "source": "BugCheck", "event_ids": [1001, 1003], "keywords": ["3B", "system_service"]},
        "repair_id": "fix_bsod_system_service", "user_permission_required": True,
    },
    "bsod_irql_not_less_or_equal": {
        "id": "bsod_irql_not_less_or_equal", "name": "BSOD — IRQL_NOT_LESS_OR_EQUAL",
        "severity": CRITICAL, "category": "BSOD",
        "description": "BSOD: IRQL_NOT_LESS_OR_EQUAL. Usually caused by a driver accessing invalid memory. Update/rollback drivers.",
        "technical": "Stop Code: IRQL_NOT_LESS_OR_EQUAL — 0x0000000A",
        "detection": {"type": "event", "log": "System", "source": "BugCheck", "event_ids": [1001], "keywords": ["0xA", "IRQL"]},
        "repair_id": "fix_bsod_irql", "user_permission_required": True,
    },
    "bsod_memory_management": {
        "id": "bsod_memory_management", "name": "BSOD — MEMORY_MANAGEMENT",
        "severity": CRITICAL, "category": "BSOD",
        "description": "BSOD: MEMORY_MANAGEMENT. Indicates RAM errors or corrupted system files. Run Memory Diagnostic and SFC.",
        "technical": "Stop Code: MEMORY_MANAGEMENT — 0x0000001A",
        "detection": {"type": "event", "log": "System", "source": "BugCheck", "event_ids": [1001], "keywords": ["1A", "memory_management"]},
        "repair_id": "fix_bsod_memory", "user_permission_required": True,
    },
    "bsod_page_fault_in_nonpaged_area": {
        "id": "bsod_page_fault_in_nonpaged_area", "name": "BSOD — PAGE_FAULT_IN_NONPAGED_AREA",
        "severity": CRITICAL, "category": "BSOD",
        "description": "BSOD: PAGE_FAULT_IN_NONPAGED_AREA. Often caused by bad drivers or RAM issues.",
        "technical": "Stop Code: PAGE_FAULT_IN_NONPAGED_AREA — 0x00000050",
        "detection": {"type": "event", "log": "System", "source": "BugCheck", "event_ids": [1001], "keywords": ["0x50", "page_fault"]},
        "repair_id": "fix_bsod_page_fault", "user_permission_required": True,
    },
    "bsod_driver_power_state_failure": {
        "id": "bsod_driver_power_state_failure", "name": "BSOD — DRIVER_POWER_STATE_FAILURE",
        "severity": CRITICAL, "category": "BSOD",
        "description": "BSOD during sleep/wake caused by driver power state issues. Update or rollback GPU/network drivers.",
        "technical": "Stop Code: DRIVER_POWER_STATE_FAILURE — 0x0000009F",
        "detection": {"type": "event", "log": "System", "source": "BugCheck", "event_ids": [1001], "keywords": ["9F", "driver_power"]},
        "repair_id": "fix_bsod_driver_power", "user_permission_required": True,
    },

    
    
    
    "error_0x80004005_unspecified": {
        "id": "error_0x80004005_unspecified", "name": "Error 0x80004005 — Unspecified Error",
        "severity": HIGH, "category": "Windows",
        "description": "Generic Windows error 0x80004005 occurs with file access, network shares, or Windows Update.",
        "technical": "Error: 0x80004005 — E_FAIL / Unspecified error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["80004005"]},
        "repair_id": "fix_error_80004005", "user_permission_required": True,
    },
    "error_0xc000007b": {
        "id": "error_0xc000007b", "name": "Application Error 0xc000007b — Bad Image",
        "severity": HIGH, "category": "Windows",
        "description": "Application failed to start with 0xc000007b. Usually caused by mixing 32-bit and 64-bit DLLs or missing Visual C++ runtime.",
        "technical": "0xc000007b — STATUS_INVALID_IMAGE_FORMAT",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["c000007b"]},
        "repair_id": "fix_error_0xc000007b", "user_permission_required": True,
    },
    "windows_cannot_access_network_share": {
        "id": "windows_cannot_access_network_share", "name": "Cannot Access Network Share (0x80070035)",
        "severity": MEDIUM, "category": "Network",
        "description": "Network path not found (0x80070035). Network discovery or file sharing may be disabled.",
        "technical": "Error: 0x80070035 — Network path not found",
        "detection": {"type": "service", "service_name": "LanmanWorkstation", "expected_status": "running"},
        "repair_id": "fix_network_share_access", "user_permission_required": True,
    },
    "windows_cannot_find_device": {
        "id": "windows_cannot_find_device", "name": "Windows Cannot Find Device (Error 433)",
        "severity": MEDIUM, "category": "Drivers",
        "description": "Windows cannot find or initialize a hardware device. Device driver or hardware issue.",
        "technical": "Device Manager — device not found / error 433",
        "detection": {"type": "event", "log": "System", "source": "Plug and Play", "event_ids": [433], "keywords": []},
        "repair_id": "scan_for_hardware_changes", "user_permission_required": True,
    },
    "clock_not_syncing": {
        "id": "clock_not_syncing", "name": "System Clock Not Synchronizing",
        "severity": MEDIUM, "category": "System",
        "description": "System clock failed to sync with time server. SSL certificates and authentication may break.",
        "technical": "W32Time — time sync failed",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Time-Service", "event_ids": [47, 144, 35], "keywords": []},
        "repair_id": "fix_time_sync", "user_permission_required": True,
    },
    "windows_update_stuck_100": {
        "id": "windows_update_stuck_100", "name": "Windows Stuck at 100% / Preparing Updates",
        "severity": HIGH, "category": "Windows Update",
        "description": "Windows is stuck preparing updates at 100% or on a restart loop. Clearing update cache resolves this.",
        "technical": "Windows Update — stuck preparing / configuring",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-WindowsUpdateClient", "event_ids": [20], "keywords": ["stuck", "pending"]},
        "repair_id": "clear_windows_update_cache", "user_permission_required": True,
    },
    "low_virtual_memory": {
        "id": "low_virtual_memory", "name": "Low Virtual Memory Warning",
        "severity": HIGH, "category": "Performance",
        "description": "Windows is low on virtual memory. Increasing the page file size will prevent crashes.",
        "technical": "Virtual memory / page file — low",
        "detection": {"type": "event", "log": "Application", "source": "Application Popup", "event_ids": [26], "keywords": ["virtual memory"]},
        "repair_id": "fix_virtual_memory", "user_permission_required": True,
    },
    "corrupted_user_profile": {
        "id": "corrupted_user_profile", "name": "Corrupted User Profile",
        "severity": HIGH, "category": "System",
        "description": "User profile is corrupted (logged in as TEMP). Profile repair or recreation is needed.",
        "technical": "ProfileList registry — corrupted profile",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft-Windows-User Profiles Service", "event_ids": [1509, 1511], "keywords": []},
        "repair_id": "fix_corrupted_profile", "user_permission_required": True,
    },
    "windows_defender_update_failed": {
        "id": "windows_defender_update_failed", "name": "Windows Defender Definition Update Failed",
        "severity": MEDIUM, "category": "Security",
        "description": "Windows Defender virus definitions are out of date. Manual update or service restart fixes this.",
        "technical": "Windows Defender — definition update failed",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft Antimalware", "event_ids": [2001], "keywords": ["update failed"]},
        "repair_id": "fix_defender_definitions", "user_permission_required": True,
    },

    
    
    
    "zoom_crash": {
        "id": "zoom_crash", "name": "Zoom Crash or Won't Open",
        "severity": MEDIUM, "category": "Communication",
        "description": "Zoom has crashed or won't start. Clearing Zoom AppData cache usually fixes this.",
        "technical": "Zoom.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Zoom.exe"]},
        "repair_id": "fix_zoom", "user_permission_required": False,
    },
    "teams_crash": {
        "id": "teams_crash", "name": "Microsoft Teams Crash",
        "severity": MEDIUM, "category": "Communication",
        "description": "Microsoft Teams crashed or is frozen. Clearing Teams cache is the standard fix.",
        "technical": "Teams.exe / ms-teams.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Teams.exe", "ms-teams"]},
        "repair_id": "fix_teams", "user_permission_required": False,
    },
    "obs_crash": {
        "id": "obs_crash", "name": "OBS Studio Crash",
        "severity": MEDIUM, "category": "Media",
        "description": "OBS Studio crashed. Usually caused by driver or DirectX issues. Updating GPU drivers fixes this.",
        "technical": "obs64.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["obs64.exe", "obs.exe"]},
        "repair_id": "fix_obs", "user_permission_required": False,
    },
    "adobe_crash": {
        "id": "adobe_crash", "name": "Adobe Application Crash (Photoshop/Premiere)",
        "severity": MEDIUM, "category": "Media",
        "description": "An Adobe application crashed. Clearing Adobe cache and resetting preferences usually resolves crashes.",
        "technical": "Photoshop.exe / Premiere.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Photoshop", "Premiere", "Adobe"]},
        "repair_id": "fix_adobe_crash", "user_permission_required": False,
    },
    "nvidia_driver_crash": {
        "id": "nvidia_driver_crash", "name": "NVIDIA Display Driver Crash (TDR)",
        "severity": HIGH, "category": "Drivers",
        "description": "NVIDIA display driver stopped responding and recovered. Known as TDR event. Update or DDU clean install of driver.",
        "technical": "nvlddmkm.sys — Display driver stopped responding (Event ID 4101)",
        "detection": {"type": "event", "log": "System", "source": "Display", "event_ids": [4101], "keywords": ["nvlddmkm", "nvidia"]},
        "repair_id": "fix_nvidia_tdr", "user_permission_required": True,
    },
    "amd_driver_crash": {
        "id": "amd_driver_crash", "name": "AMD Display Driver Crash (TDR)",
        "severity": HIGH, "category": "Drivers",
        "description": "AMD display driver stopped responding (TDR). Clean reinstall of AMD drivers with DDU is the fix.",
        "technical": "atikmpag.sys — AMD TDR failure",
        "detection": {"type": "event", "log": "System", "source": "Display", "event_ids": [4101], "keywords": ["atikmpag", "amd"]},
        "repair_id": "fix_amd_tdr", "user_permission_required": True,
    },
    "xbox_game_bar_crash": {
        "id": "xbox_game_bar_crash", "name": "Xbox Game Bar Crash",
        "severity": LOW, "category": "Gaming",
        "description": "Xbox Game Bar crashed or won't open. Repairing the Xbox Gaming Overlay app fixes this.",
        "technical": "GameBar.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["GameBar.exe"]},
        "repair_id": "fix_xbox_game_bar", "user_permission_required": False,
    },
    "windows_photos_crash": {
        "id": "windows_photos_crash", "name": "Windows Photos App Crash",
        "severity": LOW, "category": "Applications",
        "description": "Windows Photos app crashed. Re-registering the app in PowerShell fixes this.",
        "technical": "Microsoft.Photos.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Microsoft.Photos"]},
        "repair_id": "fix_windows_photos", "user_permission_required": False,
    },

    # ── Security & Firewall ────────────────────────────────────────
    "windows_firewall_not_running": {
        "id": "windows_firewall_not_running", "name": "Windows Firewall Service Stopped",
        "severity": CRITICAL, "category": "Security",
        "description": "The Windows Firewall (MpsSvc) service has stopped. Your system is exposed to network threats.",
        "technical": "Service: MpsSvc — Status: STOPPED",
        "detection": {"type": "service", "service_name": "MpsSvc", "expected_status": "running"},
        "repair_id": "restart_windows_firewall", "user_permission_required": True,
    },
    "windows_defender_disabled": {
        "id": "windows_defender_disabled", "name": "Windows Defender Antivirus Disabled",
        "severity": CRITICAL, "category": "Security",
        "description": "Windows Defender real-time protection has been disabled. Your PC is vulnerable to malware.",
        "technical": "Service: WinDefend — Status: STOPPED",
        "detection": {"type": "service", "service_name": "WinDefend", "expected_status": "running"},
        "repair_id": "enable_windows_defender", "user_permission_required": True,
    },
    "wsl_backend_crash": {
        "id": "wsl_backend_crash", "name": "WSL2 Backend Crash",
        "severity": HIGH, "category": "Virtualization",
        "description": "The Windows Subsystem for Linux 2 backend has crashed. Restarting the LxssManager service will fix it.",
        "technical": "Service: LxssManager — Status: STOPPED",
        "detection": {"type": "service", "service_name": "LxssManager", "expected_status": "running"},
        "repair_id": "restart_lxss_manager", "user_permission_required": True,
    },
    "windows_event_log_stopped": {
        "id": "windows_event_log_stopped", "name": "Windows Event Log Service Stopped",
        "severity": CRITICAL, "category": "Security",
        "description": "The Windows Event Log service (EventLog) is not running. System events are not being recorded.",
        "technical": "Service: EventLog — Status: STOPPED",
        "detection": {"type": "service", "service_name": "EventLog", "expected_status": "running"},
        "repair_id": "restart_event_log", "user_permission_required": True,
    },
    "shadow_copy_service_not_running": {
        "id": "shadow_copy_service_not_running", "name": "Volume Shadow Copy Service Stopped",
        "severity": HIGH, "category": "Backup & Recovery",
        "description": "The Volume Shadow Copy service (VSS) has stopped. System Restore and backups will not work.",
        "technical": "Service: VSS — Status: STOPPED",
        "detection": {"type": "service", "service_name": "VSS", "expected_status": "running"},
        "repair_id": "restart_vss", "user_permission_required": True,
    },
    "smart_disk_warning": {
        "id": "smart_disk_warning", "name": "Disk SMART Failure Warning",
        "severity": CRITICAL, "category": "Storage",
        "description": "Your hard drive reports a SMART failure warning. Back up your data immediately and consider replacing the drive.",
        "technical": "Event ID 7 — disk — SMART status: BAD",
        "detection": {"type": "event", "log": "System", "source": "disk", "event_ids": [7], "keywords": ["smart", "failure"]},
        "repair_id": "run_disk_diagnostics", "user_permission_required": True,
    },
    "ntfs_file_system_error": {
        "id": "ntfs_file_system_error", "name": "NTFS File System Error",
        "severity": CRITICAL, "category": "Storage",
        "description": "A critical NTFS file system error has been detected. Running CHKDSK will repair the filesystem corruption.",
        "technical": "Event ID 55 — NTFS — File system structure corruption",
        "detection": {"type": "event", "log": "System", "source": "Ntfs", "event_ids": [55], "keywords": ["corruption", "file system"]},
        "repair_id": "run_chkdsk", "user_permission_required": True,
    },
    "sfc_integrity_violation": {
        "id": "sfc_integrity_violation", "name": "System File Integrity Violation",
        "severity": CRITICAL, "category": "System Integrity",
        "description": "Windows Resource Protection detected corrupt system files. Running SFC /scannow will restore the corrupted files.",
        "technical": "Event ID 4098 — SFC — File integrity violation detected",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-WER-SystemErrorReporting", "event_ids": [1001], "keywords": ["SystemFile", "corrupt"]},
        "repair_id": "run_sfc_scannow", "user_permission_required": True,
    },
    "wmi_service_not_running": {
        "id": "wmi_service_not_running", "name": "WMI Service (Winmgmt) Stopped",
        "severity": HIGH, "category": "System",
        "description": "Windows Management Instrumentation service has stopped. Many administrative tools rely on WMI.",
        "technical": "Service: Winmgmt — Status: STOPPED",
        "detection": {"type": "service", "service_name": "Winmgmt", "expected_status": "running"},
        "repair_id": "restart_wmi", "user_permission_required": True,
    },
    "remote_desktop_service_stopped": {
        "id": "remote_desktop_service_stopped", "name": "Remote Desktop Service Stopped",
        "severity": HIGH, "category": "Remote Access",
        "description": "The Remote Desktop Services (TermService) has stopped. RDP connections will fail.",
        "technical": "Service: TermService — Status: STOPPED",
        "detection": {"type": "service", "service_name": "TermService", "expected_status": "running"},
        "repair_id": "restart_rdp", "user_permission_required": True,
    },
    "superfetch_not_running": {
        "id": "superfetch_not_running", "name": "SysMain (Superfetch) Service Stopped",
        "severity": MEDIUM, "category": "Performance",
        "description": "The SysMain service responsible for pre-loading apps into memory has stopped, causing slow app launch times.",
        "technical": "Service: SysMain — Status: STOPPED",
        "detection": {"type": "service", "service_name": "SysMain", "expected_status": "running"},
        "repair_id": "restart_sysmain", "user_permission_required": True,
    },
    "office_update_failure": {
        "id": "office_update_failure", "name": "Microsoft Office Update Failure",
        "severity": MEDIUM, "category": "Applications",
        "description": "Microsoft Office failed to update. Running the Office repair tool will restore the update pipeline.",
        "technical": "ClickToRun.exe — Update error",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft Office", "event_ids": [2000, 2001], "keywords": ["update", "failed"]},
        "repair_id": "repair_office_click_to_run", "user_permission_required": False,
    },
    "teams_crash": {
        "id": "teams_crash", "name": "Microsoft Teams Application Crash",
        "severity": MEDIUM, "category": "Applications",
        "description": "Microsoft Teams has crashed or is unresponsive. Clearing the Teams cache will resolve this.",
        "technical": "Teams.exe — Application Error (Event 1000)",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["Teams.exe"]},
        "repair_id": "fix_teams_crash", "user_permission_required": False,
    },
    "nvidia_driver_crash": {
        "id": "nvidia_driver_crash", "name": "NVIDIA Display Driver Crash (TDR)",
        "severity": HIGH, "category": "Graphics",
        "description": "The NVIDIA display driver crashed and recovered. A driver reinstall is recommended to prevent BSODs.",
        "technical": "nvlddmkm.sys — Display driver stopped responding (TDR)",
        "detection": {"type": "event", "log": "System", "source": "Display", "event_ids": [4101], "keywords": ["nvlddmkm", "display driver stopped"]},
        "repair_id": "reinstall_gpu_driver", "user_permission_required": True,
    },
    "hyper_v_not_running": {
        "id": "hyper_v_not_running", "name": "Hyper-V Virtual Machine Management Stopped",
        "severity": HIGH, "category": "Virtualization",
        "description": "The Hyper-V Virtual Machine Management service has stopped. Virtual machines cannot start.",
        "technical": "Service: vmms — Status: STOPPED",
        "detection": {"type": "service", "service_name": "vmms", "expected_status": "running"},
        "repair_id": "restart_hyperv", "user_permission_required": True,
    },
    "task_scheduler_error": {
        "id": "task_scheduler_error", "name": "Task Scheduler Service Error",
        "severity": HIGH, "category": "System",
        "description": "The Windows Task Scheduler service has encountered an error. Scheduled tasks cannot run.",
        "technical": "Service: Schedule — Error in task execution",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-TaskScheduler", "event_ids": [101, 202], "keywords": ["Task Scheduler", "failed"]},
        "repair_id": "restart_task_scheduler", "user_permission_required": True,
    },
    "dhcp_client_stopped": {
        "id": "dhcp_client_stopped", "name": "DHCP Client Service Stopped",
        "severity": CRITICAL, "category": "Network",
        "description": "The DHCP Client service (Dhcp) has stopped. Your PC cannot obtain a network address automatically.",
        "technical": "Service: Dhcp — Status: STOPPED",
        "detection": {"type": "service", "service_name": "Dhcp", "expected_status": "running"},
        "repair_id": "restart_dhcp_client", "user_permission_required": True,
    },
    "network_location_awareness_stopped": {
        "id": "network_location_awareness_stopped", "name": "Network Location Awareness Service Stopped",
        "severity": HIGH, "category": "Network",
        "description": "The NlaSvc service has stopped. Windows cannot detect connected networks correctly.",
        "technical": "Service: NlaSvc — Status: STOPPED",
        "detection": {"type": "service", "service_name": "NlaSvc", "expected_status": "running"},
        "repair_id": "restart_nla", "user_permission_required": True,
    },
    "windows_search_indexer_crash": {
        "id": "windows_search_indexer_crash", "name": "Windows Search Indexer Crash",
        "severity": MEDIUM, "category": "System",
        "description": "The Windows Search indexer (SearchIndexer.exe) has crashed. File and app searches will be slow.",
        "technical": "SearchIndexer.exe — Application Error (Event 1000)",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["SearchIndexer.exe"]},
        "repair_id": "rebuild_search_index", "user_permission_required": False,
    },
    "explorer_crash_loop": {
        "id": "explorer_crash_loop", "name": "Windows Explorer Crash Loop",
        "severity": CRITICAL, "category": "System",
        "description": "Windows Explorer (explorer.exe) is crashing repeatedly. Restarting it and clearing shell extensions will fix this.",
        "technical": "explorer.exe — Application Error (repeated Event 1000)",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["explorer.exe"]},
        "repair_id": "restart_explorer", "user_permission_required": False,
    },
    "net_runtime_crash": {
        "id": "net_runtime_crash", "name": ".NET Runtime Crash",
        "severity": HIGH, "category": "Applications",
        "description": "A .NET application has crashed with a runtime exception. Repairing the .NET Framework will fix this.",
        "technical": ".NET Runtime — Event 1026 — Application crash",
        "detection": {"type": "event", "log": "Application", "source": ".NET Runtime", "event_ids": [1026], "keywords": ["crash", "exception"]},
        "repair_id": "repair_dotnet_framework", "user_permission_required": True,
    },
}

# ── PC Lab / Shared Workstation Errors ────────────────────────
PC_LAB_ERRORS = {
    "lab_usb_storage_blocked": {
        "id": "lab_usb_storage_blocked", "name": "USB Flash Drive Blocked / Write-Protected",
        "severity": HIGH, "category": "PC Lab",
        "description": "USB storage drive is not recognized, write-protected, or blocked by Windows policy.",
        "technical": "USBSTOR service disabled (Start=4) or StorageDevicePolicies WriteProtect=1",
        "detection": {"type": "service", "service_name": "USBSTOR", "expected_status": "running"},
        "repair_id": "lab_fix_usb_storage", "user_permission_required": True,
    },
    "lab_taskmgr_cmd_regedit_disabled": {
        "id": "lab_taskmgr_cmd_regedit_disabled", "name": "Task Manager & CMD Locked by Policy",
        "severity": CRITICAL, "category": "PC Lab",
        "description": "Task Manager, Command Prompt, or Registry Editor has been disabled by a Group Policy or registry restriction.",
        "technical": "Policies\\System DisableTaskMgr=1 or DisableCMD=1",
        "detection": {"type": "manual"},
        "repair_id": "lab_unlock_taskmgr_cmd", "user_permission_required": True,
    },
    "lab_proxy_stuck_offline": {
        "id": "lab_proxy_stuck_offline", "name": "Proxy Server Blocking Network Access",
        "severity": HIGH, "category": "PC Lab",
        "description": "Internet is blocked because a stale proxy server or PAC script is still configured in Windows network settings.",
        "technical": "WinINET ProxyEnable=1 or WinHTTP proxy server unreachable",
        "detection": {"type": "manual"},
        "repair_id": "lab_reset_proxy_settings", "user_permission_required": True,
    },
    "lab_xampp_port80_conflict": {
        "id": "lab_xampp_port80_conflict", "name": "XAMPP / Apache Port 80 Conflict",
        "severity": HIGH, "category": "PC Lab",
        "description": "Apache web server cannot start because Windows IIS (W3SVC) or BranchCache is locking Port 80.",
        "technical": "Port 80/443 bound by PID 4 (System) / W3SVC — Apache start failure",
        "detection": {"type": "manual"},
        "repair_id": "lab_fix_apache_port_conflict", "user_permission_required": True,
    },
    "lab_mysql_port3306_locked": {
        "id": "lab_mysql_port3306_locked", "name": "MySQL / MariaDB Port 3306 Locked",
        "severity": HIGH, "category": "PC Lab",
        "description": "Database server cannot start because a crashed or ghost mysqld instance is locking port 3306.",
        "technical": "Port 3306 in use by orphan mysqld.exe process",
        "detection": {"type": "manual"},
        "repair_id": "lab_fix_mysql_port_locked", "user_permission_required": True,
    },
    "lab_compiler_path_missing": {
        "id": "lab_compiler_path_missing", "name": "Compiler / Dev PATH Missing (Python/GCC/Java/Node)",
        "severity": HIGH, "category": "PC Lab",
        "description": "Compilers or programming runtimes (python, gcc, javac, node) are missing from the system PATH — commands fail in terminal.",
        "technical": "Command not recognized: System PATH missing compiler binary directories",
        "detection": {"type": "manual"},
        "repair_id": "lab_restore_compiler_paths", "user_permission_required": True,
    },
    "lab_ssl_clock_drift": {
        "id": "lab_ssl_clock_drift", "name": "HTTPS SSL Certificate Error — Clock Desync",
        "severity": HIGH, "category": "PC Lab",
        "description": "Browsers show NET::ERR_CERT_DATE_INVALID because the system CMOS clock has drifted out of sync with NTP servers.",
        "technical": "System time drift > 300s causing TLS/SSL handshake & Kerberos failures",
        "detection": {"type": "manual"},
        "repair_id": "lab_resync_clock_ntp", "user_permission_required": True,
    },
    "temp_files_overflow": {
        "id": "temp_files_overflow", "name": "Excessive Temporary Files & System Cache Clutter",
        "severity": HIGH, "category": "Storage & Performance",
        "description": "Temporary folders and application caches have accumulated gigabytes of stale files, slowing down disk I/O and consuming drive space.",
        "technical": "Excessive file count and size detected in %TEMP% and C:\\Windows\\Temp",
        "detection": {"type": "manual"},
        "repair_id": "purge_temp_cache_files", "user_permission_required": True,
    },
    "lab_disk_full_student_temps": {
        "id": "lab_disk_full_student_temps", "name": "Disk Full — Accumulated Temp & Cache Files",
        "severity": HIGH, "category": "PC Lab",
        "description": "C: drive is critically low on space due to accumulated build artifacts, temp files, and download caches.",
        "technical": "Temp and cache directories consuming critical drive space",
        "detection": {"type": "manual"},
        "repair_id": "purge_temp_cache_files", "user_permission_required": True,
    },
    "lab_display_projector_blackscreen": {
        "id": "lab_display_projector_blackscreen", "name": "External Display / Projector Black Screen",
        "severity": HIGH, "category": "PC Lab",
        "description": "Monitor shows black screen or distorted resolution after connecting or disconnecting a projector or external display.",
        "technical": "Windows Display topology stuck in external/extended projector mode",
        "detection": {"type": "manual"},
        "repair_id": "lab_reset_display_mode", "user_permission_required": True,
    },
    "lab_vs_code_lock_frozen": {
        "id": "lab_vs_code_lock_frozen", "name": "VS Code / IDE Frozen — Lockfile Conflict",
        "severity": MEDIUM, "category": "PC Lab",
        "description": "VS Code or IDE fails to launch because orphan background worker processes are holding file locks from a previous crash.",
        "technical": "Orphan Code.exe instances and stale workspaceStorage lockfiles",
        "detection": {"type": "manual"},
        "repair_id": "lab_fix_vscode_frozen", "user_permission_required": True,
    },
}

ERROR_CATALOG.update(PC_LAB_ERRORS)
ERROR_CATALOG.update(DIFFICULT_ERRORS)


learned = load_learned_errors()
for lr_id, lr_data in learned.items():
    ERROR_CATALOG[lr_id] = lr_data["error_info"]

CATALOG_LIST = list(ERROR_CATALOG.values())

def get_error(error_id: str) -> dict:
    return ERROR_CATALOG.get(error_id, {})

def get_all_errors() -> list:
    return CATALOG_LIST


DEMO_ERRORS = [
    "print_spooler_not_running",
    "windows_search_not_running",
    "windows_audio_not_running",
    "dns_resolution_failure",
    "high_cpu_usage",
]
