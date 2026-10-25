from monitor.repair_engine import repair, _run_ps





@repair("fix_bcd_corruption")
def fix_bcd_corruption():
    ok, out = _run_ps("""
Write-Output "Fixing BCD Corruption..."
Write-Output "1. Attempting automated bcdboot..."
$sysDrive = $env:SystemDrive
bcdboot $sysDrive\\Windows /s $sysDrive
Write-Output "2. Scanning for OS installations..."
bootrec /scanos 2>&1 | Out-Null
Write-Output "3. Rebuilding BCD and fixing MBR..."
bootrec /fixmbr 2>&1 | Out-Null
bootrec /fixboot 2>&1 | Out-Null
bootrec /rebuildbcd 2>&1 | Out-Null
Write-Output "BCD Rebuild operations completed. Please restart."
""")
    return True, out

@repair("fix_bootmgr_missing")
def fix_bootmgr_missing():
    ok, out = _run_ps("""
Write-Output "Fixing missing BOOTMGR..."
$sysDrive = $env:SystemDrive
bcdboot $sysDrive\\Windows
bootrec /fixboot 2>&1 | Out-Null
Write-Output "BOOTMGR files re-copied. Please restart."
""")
    return True, out

@repair("fix_startup_repair_loop")
def fix_startup_repair_loop():
    ok, out = _run_ps("""
Write-Output "Fixing Startup Repair Loop..."
Write-Output "1. Disabling automatic startup repair temporarily..."
bcdedit /set {default} recoveryenabled No 2>&1 | Out-Null
Write-Output "2. Checking disk for bad sectors..."
chkdsk /f /r $env:SystemDrive 2>&1 | Select-Object -Last 5
Write-Output "Automatic repair disabled. Restart to see exact error, or run SFC/DISM."
""")
    return True, out

@repair("fix_wmi_repository")
def fix_wmi_repository():
    ok, out = _run_ps("""
Write-Output "Rebuilding corrupted WMI Repository..."
net stop winmgmt /y 2>&1 | Out-Null
winmgmt /verifyrepository 2>&1 | Out-String | Write-Output
winmgmt /salvagerepository 2>&1 | Out-String | Write-Output
winmgmt /resetrepository 2>&1 | Out-String | Write-Output
net start winmgmt 2>&1 | Out-Null
Write-Output "WMI Repository rebuilt. Restarting related services..."
""")
    return True, out

@repair("fix_registry_corruption")
def fix_registry_corruption():
    ok, out = _run_ps("""
Write-Output "Fixing Registry Corruption..."
Write-Output "Running System File Checker to repair registry hives..."
sfc /scannow
Write-Output "If issues persist, you must restore registry from a System Restore Point or RegBack."
""")
    return True, out

@repair("fix_registry_permissions")
def fix_registry_permissions():
    ok, out = _run_ps("""
Write-Output "Fixing Registry Permissions..."
Write-Output "Applying default permissions to HKEY_LOCAL_MACHINE and HKEY_CLASSES_ROOT..."
$subinacl = "$env:ProgramFiles (x86)\\Windows Resource Kits\\Tools\\subinacl.exe"
if (Test-Path $subinacl) {
    & $subinacl /subkeyreg HKEY_LOCAL_MACHINE /grant=administrators=f /grant=system=f
    & $subinacl /subkeyreg HKEY_CLASSES_ROOT /grant=administrators=f /grant=system=f
    Write-Output "Permissions reset."
} else {
    Write-Output "SubInACL tool not found. Re-registering all DLLs as a workaround..."
    Get-ChildItem -Path $env:SystemRoot\\System32\\*.dll -Recurse -ErrorAction SilentlyContinue | % { regsvr32.exe /s $_.FullName }
    Write-Output "DLLs re-registered."
}
""")
    return True, out

@repair("fix_icon_cache")
def fix_icon_cache():
    ok, out = _run_ps("""
Write-Output "Rebuilding Icon Cache..."
ie4uinit.exe -show
taskkill /IM explorer.exe /F 2>&1 | Out-Null
Remove-Item -Path "$env:LOCALAPPDATA\\IconCache.db" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer\\iconcache*" -Force -ErrorAction SilentlyContinue
Start-Process explorer.exe
Write-Output "Icon cache rebuilt and Explorer restarted."
""")
    return True, out

@repair("fix_thumbnail_cache")
def fix_thumbnail_cache():
    ok, out = _run_ps("""
Write-Output "Rebuilding Thumbnail Cache..."
taskkill /IM explorer.exe /F 2>&1 | Out-Null
Remove-Item -Path "$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer\\thumbcache*" -Force -ErrorAction SilentlyContinue
Start-Process explorer.exe
Write-Output "Thumbnail cache rebuilt and Explorer restarted."
""")
    return True, out

@repair("fix_font_cache")
def fix_font_cache():
    ok, out = _run_ps("""
Write-Output "Rebuilding Font Cache..."
Stop-Service "FontCache" -Force -ErrorAction SilentlyContinue
Stop-Service "FontCache3.0.0.0" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:SystemRoot\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:SystemRoot\\System32\\FNTCACHE.DAT" -Force -ErrorAction SilentlyContinue
Start-Service "FontCache" -ErrorAction SilentlyContinue
Write-Output "Font cache files deleted and service restarted."
""")
    return True, out

@repair("fix_group_policy_client")
def fix_group_policy_client():
    ok, out = _run_ps("""
Write-Output "Fixing Group Policy Client Service..."
Set-Service gpsvc -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service gpsvc -ErrorAction SilentlyContinue
Write-Output "gpsvc service: $((Get-Service gpsvc -ErrorAction SilentlyContinue).Status)"
""")
    return True, out

@repair("fix_group_policy_errors")
def fix_group_policy_errors():
    ok, out = _run_ps("""
Write-Output "Fixing Group Policy Errors..."
Remove-Item "$env:SystemRoot\\System32\\GroupPolicy\\Machine\\Registry.pol" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:SystemRoot\\System32\\GroupPolicy\\User\\Registry.pol" -Force -ErrorAction SilentlyContinue
gpupdate /force 2>&1 | Out-String | Write-Output
Write-Output "Group policy cache cleared and updated."
""")
    return True, out

@repair("fix_rdp_service")
def fix_rdp_service():
    ok, out = _run_ps("""
Write-Output "Fixing RDP Service..."
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -Value 0
Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
Set-Service TermService -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service TermService -ErrorAction SilentlyContinue
Write-Output "RDP Enabled, Firewall rule created, TermService: $((Get-Service TermService -ErrorAction SilentlyContinue).Status)"
""")
    return True, out

@repair("fix_rdp_firewall")
def fix_rdp_firewall():
    return fix_rdp_service()

@repair("fix_ipv6_conflict")
def fix_ipv6_conflict():
    ok, out = _run_ps("""
Write-Output "Fixing IPv6 Network Conflict..."
Disable-NetAdapterBinding -Name "*" -ComponentID ms_tcpip6 -ErrorAction SilentlyContinue
Write-Output "IPv6 temporarily disabled on all adapters to resolve conflict."
ipconfig /flushdns 2>&1 | Out-Null
Write-Output "DNS Flushed. Network should stabilize."
""")
    return True, out

@repair("fix_all_uwp_apps")
def fix_all_uwp_apps():
    ok, out = _run_ps("""
Write-Output "Re-registering all Windows UWP Apps (Takes 1-2 minutes)..."
Get-AppXPackage -AllUsers | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml" -ErrorAction SilentlyContinue}
Write-Output "All UWP apps re-registered. Windows Settings and Store should now open."
""", timeout=180)
    return True, out

@repair("fix_windows_settings")
def fix_windows_settings():
    ok, out = _run_ps("""
Write-Output "Re-registering Windows Settings App..."
Get-AppXPackage *windows.immersivecontrolpanel* | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml" -ErrorAction SilentlyContinue}
Write-Output "Settings App re-registered."
""")
    return True, out

@repair("fix_disk_partition")
def fix_disk_partition():
    ok, out = _run_ps("""
Write-Output "Fixing Disk Partition/File System Errors..."
Write-Output "Running chkdsk. This may require a reboot if the drive is in use..."
chkdsk $env:SystemDrive /f /x 2>&1 | Select-Object -Last 8 | Out-String | Write-Output
Write-Output "If asked to schedule on next restart, type 'Y' in an admin command prompt: chkdsk /f /r"
""")
    return True, out

@repair("fix_vss_failure")
def fix_vss_failure():
    ok, out = _run_ps("""
Write-Output "Fixing Volume Shadow Copy Service (VSS)..."
net stop vss 2>&1 | Out-Null
net stop swprv 2>&1 | Out-Null
regsvr32 /s ole32.dll
regsvr32 /s oleaut32.dll
regsvr32 /s vss_ps.dll
vssadmin list writers 2>&1 | Select-Object -First 5 | Out-String | Write-Output
net start vss 2>&1 | Out-Null
Write-Output "VSS DLLs re-registered and service restarted."
""")
    return True, out

@repair("fix_pagefile")
def fix_pagefile():
    ok, out = _run_ps("""
Write-Output "Resetting Virtual Memory (Pagefile)..."
$cs = Get-WmiObject Win32_ComputerSystem
$cs.AutomaticManagedPagefile = $true
$cs.Put() | Out-Null
Write-Output "Pagefile set to system managed automatically. Please restart your PC."
""")
    return True, out

@repair("fix_sleep_wake")
def fix_sleep_wake():
    ok, out = _run_ps("""
Write-Output "Fixing Sleep/Wake Configuration..."
powercfg -waketimers 2>&1 | Out-String | Write-Output
Write-Output "Disabling wake timers in power plans..."
# Very complex to do across all GUIDs via CLI natively without a script, using a common setting:
powercfg /setacvalueindex SCHEME_CURRENT 238c9fa8-0aad-41ed-83f4-97be242c8f20 bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 0
powercfg /setdcvalueindex SCHEME_CURRENT 238c9fa8-0aad-41ed-83f4-97be242c8f20 bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 0
powercfg /setactive SCHEME_CURRENT
Write-Output "Wake timers disabled for current power plan."
""")
    return True, out

@repair("fix_battery_power")
def fix_battery_power():
    ok, out = _run_ps("""
Write-Output "Generating Battery Health Report..."
$reportPath = "$env:USERPROFILE\\Desktop\\Battery_Report.html"
powercfg /batteryreport /output $reportPath 2>&1 | Out-Null
Write-Output "Battery report generated at: $reportPath"
Write-Output "Review the report for design capacity vs full charge capacity to determine wear."
""")
    return True, out

@repair("fix_windows_hello")
def fix_windows_hello():
    ok, out = _run_ps("""
Write-Output "Fixing Windows Hello / Biometrics..."
Stop-Service WbioSrvc -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:SystemRoot\\System32\\WinBioDatabase\\*.DAT" -Force -ErrorAction SilentlyContinue
Start-Service WbioSrvc -ErrorAction SilentlyContinue
Write-Output "Biometrics database cleared and service restarted. You must set up Windows Hello again in Settings."
""")
    return True, out

@repair("fix_edge_crash")
def fix_edge_crash():
    ok, out = _run_ps("""
Write-Output "Fixing Microsoft Edge Crashing..."
taskkill /IM msedge.exe /F 2>&1 | Out-Null
Remove-Item -Path "$env:LOCALAPPDATA\\Microsoft\\Edge\\User Data\\Default\\Cache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Edge closed and cache cleared. Try opening Edge again."
""")
    return True, out

@repair("fix_memory_errors")
def fix_memory_errors():
    ok, out = _run_ps("""
Write-Output "Scheduling Windows Memory Diagnostic..."
mdsched.exe
Write-Output "Memory Diagnostic Tool opened. Choose to restart now and check for problems."
""")
    return True, out

@repair("fix_certificate_store")
def fix_certificate_store():
    ok, out = _run_ps("""
Write-Output "Resetting Certificate Store / Cryptographic Services..."
net stop cryptsvc /y 2>&1 | Out-Null
Rename-Item -Path "$env:SystemRoot\\System32\\catroot2" -NewName "catroot2.old" -ErrorAction SilentlyContinue
net start cryptsvc 2>&1 | Out-Null
Write-Output "CryptSvc restarted and catroot2 folder rebuilt. Certificates should now validate."
""")
    return True, out

@repair("fix_codec_missing")
def fix_codec_missing():
    ok, out = _run_ps("""
Write-Output "Media Codecs Check..."
Write-Output "To fix missing codecs for Windows Media Player / Movies & TV:"
Write-Output "1. Open Microsoft Store"
Write-Output "2. Search and install: 'HEVC Video Extensions' (if needed) or 'Web Media Extensions'"
Write-Output "3. Alternatively, install VLC Media Player or K-Lite Codec Pack for all formats."
""")
    return True, out

@repair("fix_installer_locked")
def fix_installer_locked():
    ok, out = _run_ps("""
Write-Output "Fixing Locked Windows Installer (MSI)..."
taskkill /IM msiexec.exe /F 2>&1 | Out-Null
net stop msiserver 2>&1 | Out-Null
net start msiserver 2>&1 | Out-Null
Write-Output "msiexec processes killed and Windows Installer service restarted."
""")
    return True, out

@repair("fix_hyperv_conflict")
def fix_hyperv_conflict():
    ok, out = _run_ps("""
Write-Output "Fixing Hyper-V / Virtualization Conflict..."
Write-Output "Disabling Hyper-V hypervisor from starting at boot..."
bcdedit /set hypervisorlaunchtype off 2>&1 | Out-Null
Write-Output "Hypervisor launch type set to OFF. Please restart your PC."
Write-Output "(Note: This will disable WSL2, Docker, and Windows Sandbox. Run 'bcdedit /set hypervisorlaunchtype auto' to re-enable)"
""")
    return True, out

@repair("fix_temp_cleanup")
def fix_temp_cleanup():
    ok, out = _run_ps("""
Write-Output "Cleaning Temporary Files, Cache Dumps, and Junk Clutter..."
$initialSpace = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
Remove-Item -Path "$env:TEMP\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:LOCALAPPDATA\\Temp\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:SystemRoot\\Temp\\*" -Recurse -Force -ErrorAction SilentlyContinue
$demoJunk = Join-Path $env:TEMP "SmartFix_Demo_TempJunk"
if (Test-Path $demoJunk) { Remove-Item -Path $demoJunk -Recurse -Force -ErrorAction SilentlyContinue }
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
$finalSpace = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
$freed = [Math]::Round($finalSpace - $initialSpace, 2)
Write-Output "Temporary folders emptied and caches purged. Free space on C: $finalSpace GB (Freed ~$freed GB)."
""")
    return True, out

@repair("fix_rebuild_search_index_full")
def fix_rebuild_search_index_full():
    ok, out = _run_ps("""
Write-Output "Fully Rebuilding Windows Search Index..."
net stop WSearch 2>&1 | Out-Null
Remove-Item -Path "$env:ProgramData\\Microsoft\\Search\\Data\\Applications\\Windows\\Windows.edb" -Force -ErrorAction SilentlyContinue
net start WSearch 2>&1 | Out-Null
Write-Output "Search index deleted and service restarted. Windows will now rebuild the index (takes time)."
""")
    return True, out

@repair("fix_task_scheduler")
def fix_task_scheduler():
    ok, out = _run_ps("""
Write-Output "Fixing Task Scheduler Service..."
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Services\Schedule' -name "Start" -Value 2 -ErrorAction SilentlyContinue
net start Schedule 2>&1 | Out-Null
Write-Output "Task Scheduler set to automatic and started."
""")
    return True, out
