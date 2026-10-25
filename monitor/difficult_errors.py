"""
SmartFix AI — Additional Difficult Errors Catalog
Extends error_catalog.py with hard-to-fix errors that require expert knowledge.
Import and merge this into ERROR_CATALOG in error_catalog.py.
"""

DIFFICULT_ERRORS = {

    
    "bcd_boot_corruption": {
        "id": "bcd_boot_corruption", "name": "Boot Configuration Data (BCD) Corruption",
        "severity": "CRITICAL", "category": "Boot",
        "description": "Windows Boot Manager is corrupted. System may fail to boot. BCD rebuild and bootrec /fixmbr will repair this.",
        "technical": "BCD Store — corrupted or missing entries",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Diagnosis-Scripted", "event_ids": [1001], "keywords": ["BCD", "bootmgr"]},
        "repair_id": "fix_bcd_corruption", "user_permission_required": True,
    },
    "windows_boot_manager_missing": {
        "id": "windows_boot_manager_missing", "name": "Windows Boot Manager Missing",
        "severity": "CRITICAL", "category": "Boot",
        "description": "BOOTMGR is missing or damaged. This will prevent Windows from starting.",
        "technical": "BOOTMGR missing / MBR corrupted",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-WER-SystemErrorReporting", "event_ids": [1001], "keywords": ["bootmgr"]},
        "repair_id": "fix_bootmgr_missing", "user_permission_required": True,
    },
    "windows_startup_repair_loop": {
        "id": "windows_startup_repair_loop", "name": "Windows Automatic Startup Repair Loop",
        "severity": "CRITICAL", "category": "Boot",
        "description": "Windows is stuck in a startup repair loop. This is caused by corrupted BCD or boot files.",
        "technical": "Startup Repair — infinite loop",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Startup-Repair-Client", "event_ids": [1001], "keywords": []},
        "repair_id": "fix_startup_repair_loop", "user_permission_required": True,
    },

    
    "wmi_repository_corrupt": {
        "id": "wmi_repository_corrupt", "name": "WMI Repository Corrupted",
        "severity": "CRITICAL", "category": "System",
        "description": "The WMI repository is corrupted. System management tools, monitoring software, and many apps rely on WMI. Rebuilding the repository fixes this.",
        "technical": "WMI — repository consistency check failed",
        "detection": {"type": "event", "log": "Application", "source": "WMI", "event_ids": [10, 63], "keywords": ["corrupted", "repository"]},
        "repair_id": "fix_wmi_repository", "user_permission_required": True,
    },

    
    "registry_hive_corruption": {
        "id": "registry_hive_corruption", "name": "Registry Hive Corruption",
        "severity": "CRITICAL", "category": "Registry",
        "description": "A Windows registry hive is corrupted. This can cause system instability, app failures, and blue screens.",
        "technical": "Registry — hive load failure Event ID 6",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Kernel-General", "event_ids": [6], "keywords": ["registry", "hive"]},
        "repair_id": "fix_registry_corruption", "user_permission_required": True,
    },
    "registry_permissions_broken": {
        "id": "registry_permissions_broken", "name": "Registry Permissions Broken",
        "severity": "HIGH", "category": "Registry",
        "description": "Registry key permissions are incorrect. Applications cannot read/write required registry keys.",
        "technical": "Registry — access denied on key read/write",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["registry", "0x80070005"]},
        "repair_id": "fix_registry_permissions", "user_permission_required": True,
    },

    
    "icon_cache_corrupt": {
        "id": "icon_cache_corrupt", "name": "Icon Cache Corrupted (Blank/Wrong Icons)",
        "severity": "MEDIUM", "category": "Shell",
        "description": "Desktop and file icons appear blank, incorrect, or generic. The icon cache is corrupted. Rebuilding it fixes this instantly.",
        "technical": "IconCache.db — corrupted",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["icon", "shell32"]},
        "repair_id": "fix_icon_cache", "user_permission_required": False,
    },
    "thumbnail_cache_corrupt": {
        "id": "thumbnail_cache_corrupt", "name": "Thumbnail Cache Corrupted (Missing Previews)",
        "severity": "LOW", "category": "Shell",
        "description": "File thumbnails in File Explorer appear blank. Clearing the thumbnail cache forces Windows to regenerate them.",
        "technical": "Thumbcache — corrupted database files",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["thumbcache"]},
        "repair_id": "fix_thumbnail_cache", "user_permission_required": False,
    },
    "font_cache_corrupt": {
        "id": "font_cache_corrupt", "name": "Font Cache Corrupted (Fonts Not Rendering)",
        "severity": "MEDIUM", "category": "Shell",
        "description": "Windows fonts are not rendering correctly. Applications show wrong or missing fonts. Rebuilding the font cache fixes this.",
        "technical": "FontCache3.0.0.0.dat — corrupted",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["FontCache", "font"]},
        "repair_id": "fix_font_cache", "user_permission_required": True,
    },

    
    "group_policy_client_not_running": {
        "id": "group_policy_client_not_running", "name": "Group Policy Client Not Running",
        "severity": "HIGH", "category": "System",
        "description": "The Group Policy Client service stopped. Some settings may not apply and logon can fail.",
        "technical": "Service: gpsvc — Status: STOPPED",
        "detection": {"type": "service", "service_name": "gpsvc", "expected_status": "running"},
        "repair_id": "fix_group_policy_client", "user_permission_required": True,
    },
    "group_policy_errors": {
        "id": "group_policy_errors", "name": "Group Policy Application Errors",
        "severity": "MEDIUM", "category": "System",
        "description": "Group Policy failed to apply. This causes logon delays and policy settings not taking effect.",
        "technical": "UserEnv Event ID 1085, 1058",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft-Windows-GroupPolicy", "event_ids": [1085, 1058], "keywords": []},
        "repair_id": "fix_group_policy_errors", "user_permission_required": True,
    },

    
    "rdp_service_not_running": {
        "id": "rdp_service_not_running", "name": "Remote Desktop Service Not Running",
        "severity": "HIGH", "category": "Remote",
        "description": "The Remote Desktop Services (TermService) stopped. RDP connections will be refused.",
        "technical": "Service: TermService — Status: STOPPED",
        "detection": {"type": "service", "service_name": "TermService", "expected_status": "running"},
        "repair_id": "fix_rdp_service", "user_permission_required": True,
    },
    "rdp_firewall_blocked": {
        "id": "rdp_firewall_blocked", "name": "RDP Blocked by Firewall",
        "severity": "MEDIUM", "category": "Remote",
        "description": "Windows Firewall is blocking Remote Desktop connections. Enabling the RDP firewall rule fixes this.",
        "technical": "Firewall blocking port 3389",
        "detection": {"type": "event", "log": "Security", "source": "Microsoft-Windows-Security-Auditing", "event_ids": [5157], "keywords": ["3389"]},
        "repair_id": "fix_rdp_firewall", "user_permission_required": True,
    },

    
    "ipv6_conflict": {
        "id": "ipv6_conflict", "name": "IPv6 Conflict Causing Network Issues",
        "severity": "MEDIUM", "category": "Network",
        "description": "IPv6 misconfiguration is causing network connectivity issues. Disabling IPv6 on the adapter or resetting it resolves the conflict.",
        "technical": "IPv6 — DAD conflict / Router Advertisement failure",
        "detection": {"type": "event", "log": "System", "source": "Tcpip", "event_ids": [4199, 4198], "keywords": ["IPv6", "conflict"]},
        "repair_id": "fix_ipv6_conflict", "user_permission_required": True,
    },

    
    "all_uwp_apps_broken": {
        "id": "all_uwp_apps_broken", "name": "All Windows Apps / UWP Broken",
        "severity": "CRITICAL", "category": "Applications",
        "description": "Windows built-in apps (Photos, Calculator, Store, Settings) all fail to open. Re-registering all UWP apps fixes this.",
        "technical": "AppX deployment — all UWP packages failed",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft-Windows-AppModel-Runtime", "event_ids": [65, 69], "keywords": []},
        "repair_id": "fix_all_uwp_apps", "user_permission_required": True,
    },
    "windows_settings_not_opening": {
        "id": "windows_settings_not_opening", "name": "Windows Settings Won't Open",
        "severity": "HIGH", "category": "Applications",
        "description": "The Windows Settings app will not open. Re-registering the SystemSettings app fixes this.",
        "technical": "SystemSettings.exe — AppX deployment failure",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["SystemSettings"]},
        "repair_id": "fix_windows_settings", "user_permission_required": False,
    },

    
    "disk_partition_error": {
        "id": "disk_partition_error", "name": "Disk Partition Table Error",
        "severity": "CRITICAL", "category": "Disk",
        "description": "The disk partition table has errors. CHKDSK with repair flag will fix file system errors.",
        "technical": "NTFS/GPT partition — integrity error",
        "detection": {"type": "event", "log": "System", "source": "Ntfs", "event_ids": [55, 137], "keywords": ["partition", "corrupt"]},
        "repair_id": "fix_disk_partition", "user_permission_required": True,
    },
    "shadow_copy_failure": {
        "id": "shadow_copy_failure", "name": "Volume Shadow Copy (VSS) Failure",
        "severity": "HIGH", "category": "Disk",
        "description": "Volume Shadow Copy Service failed. Windows Backup, System Restore, and some antivirus will not work.",
        "technical": "Service: VSS / vssadmin — failure",
        "detection": {"type": "event", "log": "Application", "source": "VSS", "event_ids": [8193, 8194, 13], "keywords": []},
        "repair_id": "fix_vss_failure", "user_permission_required": True,
    },
    "pagefile_corruption": {
        "id": "pagefile_corruption", "name": "Page File (Virtual Memory) Corruption",
        "severity": "HIGH", "category": "Performance",
        "description": "The Windows page file is corrupted or incorrectly configured, causing memory errors and crashes.",
        "technical": "pagefile.sys — corruption or misconfiguration",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Kernel-PnP", "event_ids": [219], "keywords": ["pagefile"]},
        "repair_id": "fix_pagefile", "user_permission_required": True,
    },

    
    "sleep_wake_failure": {
        "id": "sleep_wake_failure", "name": "Sleep/Wake Failure (PC Wakes Randomly or Won't Wake)",
        "severity": "MEDIUM", "category": "Power",
        "description": "PC randomly wakes from sleep or fails to wake. Driver or wake timer configuration is the cause.",
        "technical": "Power — sleep/wake failure",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Kernel-Power", "event_ids": [41, 6008], "keywords": ["sleep", "wake"]},
        "repair_id": "fix_sleep_wake", "user_permission_required": True,
    },
    "battery_report_warning": {
        "id": "battery_report_warning", "name": "Battery/Power Capacity Warning",
        "severity": "MEDIUM", "category": "Power",
        "description": "Battery capacity has degraded significantly. Power plan adjustment can help extend remaining battery life.",
        "technical": "Windows Battery Report — capacity degraded",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Kernel-Power", "event_ids": [80], "keywords": []},
        "repair_id": "fix_battery_power", "user_permission_required": False,
    },

    
    "windows_hello_failure": {
        "id": "windows_hello_failure", "name": "Windows Hello / Biometrics Not Working",
        "severity": "MEDIUM", "category": "Security",
        "description": "Windows Hello fingerprint or face recognition stopped working. Restarting the Biometric service and re-enrolling fixes this.",
        "technical": "Service: WbioSrvc — Windows Hello failure",
        "detection": {"type": "service", "service_name": "WbioSrvc", "expected_status": "running"},
        "repair_id": "fix_windows_hello", "user_permission_required": True,
    },

    
    "edge_crash": {
        "id": "edge_crash", "name": "Microsoft Edge Crash / Won't Open",
        "severity": "MEDIUM", "category": "Browser",
        "description": "Microsoft Edge has crashed or won't open. Clearing Edge cache and resetting profile data fixes most Edge crashes.",
        "technical": "msedge.exe — Application Error",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["msedge.exe"]},
        "repair_id": "fix_edge_crash", "user_permission_required": False,
    },

    
    "memory_diagnostic_warning": {
        "id": "memory_diagnostic_warning", "name": "RAM Error Detected (Memory Diagnostic)",
        "severity": "CRITICAL", "category": "Hardware",
        "description": "Windows Memory Diagnostic has detected RAM errors. This causes BSODs, crashes, and data corruption. RAM may need replacement.",
        "technical": "MemDiag — RAM test failure (hardware error)",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-MemoryDiagnostics-Results", "event_ids": [1201, 1101], "keywords": ["error", "hardware"]},
        "repair_id": "fix_memory_errors", "user_permission_required": True,
    },

    
    "certificate_store_corrupt": {
        "id": "certificate_store_corrupt", "name": "Windows Certificate Store Corrupted",
        "severity": "HIGH", "category": "Security",
        "description": "Windows Certificate Store is corrupted. HTTPS connections, Windows Update, and app installations will fail.",
        "technical": "CertUtil — certificate store inconsistency",
        "detection": {"type": "event", "log": "Application", "source": "Microsoft-Windows-CertificateServicesClient", "event_ids": [64, 82], "keywords": []},
        "repair_id": "fix_certificate_store", "user_permission_required": True,
    },

    
    "codec_missing": {
        "id": "codec_missing", "name": "Media Codec Missing (Video/Audio Won't Play)",
        "severity": "MEDIUM", "category": "Media",
        "description": "Required media codecs are missing. Videos or audio files won't play in Windows apps. Installing codec pack resolves this.",
        "technical": "DirectShow / MF codec — not found",
        "detection": {"type": "event", "log": "Application", "source": "Application Error", "event_ids": [1000], "keywords": ["wmplayer", "codec", "MF"]},
        "repair_id": "fix_codec_missing", "user_permission_required": False,
    },

    
    "windows_installer_locked": {
        "id": "windows_installer_locked", "name": "Windows Installer Database Locked",
        "severity": "HIGH", "category": "Applications",
        "description": "Windows Installer database is locked by another process. Software cannot be installed or uninstalled.",
        "technical": "MSI — database locked (Error 1618)",
        "detection": {"type": "event", "log": "Application", "source": "MsiInstaller", "event_ids": [1022, 11707], "keywords": ["1618", "locked"]},
        "repair_id": "fix_installer_locked", "user_permission_required": True,
    },

    
    "hyperv_conflict": {
        "id": "hyperv_conflict", "name": "Hyper-V / Virtualization Conflict",
        "severity": "MEDIUM", "category": "Virtualization",
        "description": "Hyper-V is conflicting with other virtualization software (VMware, VirtualBox, Valorant Vanguard). This prevents some software from running.",
        "technical": "Hyper-V hypervisor — conflicts with VT-x/AMD-V",
        "detection": {"type": "event", "log": "System", "source": "Microsoft-Windows-Hyper-V-Hypervisor", "event_ids": [41], "keywords": ["conflict"]},
        "repair_id": "fix_hyperv_conflict", "user_permission_required": True,
    },

    
    "temp_files_overflow": {
        "id": "temp_files_overflow", "name": "Excessive Temporary Files & Cache Clutter",
        "severity": "MEDIUM", "category": "Storage & Performance",
        "description": "Temporary folders and application caches have accumulated significant clutter, degrading disk performance and consuming drive space.",
        "technical": "%TEMP% and %LOCALAPPDATA%\\Temp — excessive accumulated files",
        "detection": {"type": "temp_files", "threshold_mb": 500, "threshold_files": 1200},
        "repair_id": "fix_temp_cleanup", "user_permission_required": False,
    },

    
    "search_index_missing": {
        "id": "search_index_missing", "name": "Windows Search Index Missing / Deleted",
        "severity": "MEDIUM", "category": "System",
        "description": "Windows Search index is missing or was deleted. Search will not return file results until the index is rebuilt (takes 1-2 hours).",
        "technical": "Windows.edb / WSearch index — missing",
        "detection": {"type": "event", "log": "Application", "source": "Search", "event_ids": [3079, 3036, 10023], "keywords": []},
        "repair_id": "fix_rebuild_search_index_full", "user_permission_required": True,
    },

    
    "task_scheduler_not_running": {
        "id": "task_scheduler_not_running", "name": "Task Scheduler Not Running",
        "severity": "HIGH", "category": "Services",
        "description": "The Task Scheduler service stopped. Scheduled tasks, Windows Update, and system maintenance won't run.",
        "technical": "Service: Schedule — Status: STOPPED",
        "detection": {"type": "service", "service_name": "Schedule", "expected_status": "running"},
        "repair_id": "fix_task_scheduler", "user_permission_required": True,
    },
}
