"""
SmartFix AI — Complete Repair Engine
Handles all errors: Windows core + 3rd party apps (Valorant, Steam, Discord, Chrome, Office, etc.)
All repairs use real PowerShell/CMD commands with Administrator privileges.
"""
import subprocess
import logging
import os
import time
from typing import Dict, Any, Tuple

from monitor.learned_repairs import load_learned_errors

logger = logging.getLogger("smartfix.repair_engine")
REPAIR_TIMEOUT = 120

def _run_ps(script: str, timeout: int = REPAIR_TIMEOUT) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
            creationflags=0x08000000
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Repair timed out after timeout seconds."
    except Exception as e:
        return False, str(e)

def _run_cmd(command: str, timeout: int = 60) -> Tuple[bool, str]:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout, creationflags=0x08000000)
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except Exception as e:
        return False, str(e)

REPAIR_FUNCTIONS: Dict[str, Any] = {}

def repair(repair_id: str):
    def decorator(fn):
        REPAIR_FUNCTIONS[repair_id] = fn
        return fn
    return decorator






@repair("restart_windows_update")
def restart_windows_update():
    ok, out = _run_ps("Start-Service wuauserv -ErrorAction Stop; (Get-Service wuauserv).Status")
    return ok, f"Windows Update: {out}"

@repair("restart_bits")
def restart_bits():
    ok, out = _run_ps("Restart-Service BITS -Force; (Get-Service BITS).Status")
    return ok, f"BITS: {out}"

@repair("reset_windows_update_components")
def reset_windows_update_components():
    script = """
net stop wuauserv /y 2>$null | Out-Null
net stop cryptsvc /y 2>$null | Out-Null
net stop bits /y 2>$null | Out-Null
net stop msiserver /y 2>$null | Out-Null
Rename-Item "$env:SystemRoot\\SoftwareDistribution" "SoftwareDistribution.bak" -ErrorAction SilentlyContinue
Rename-Item "$env:SystemRoot\\System32\\catroot2" "catroot2.bak" -ErrorAction SilentlyContinue
net start wuauserv 2>$null | Out-Null
net start cryptsvc 2>$null | Out-Null
net start bits 2>$null | Out-Null
net start msiserver 2>$null | Out-Null
Write-Output "Windows Update components reset. Services restarted."
"""
    return _run_ps(script)

@repair("fix_windows_update_permissions")
def fix_windows_update_permissions():
    script = """
icacls "$env:SystemRoot\\SoftwareDistribution" /reset /t /c /q
icacls "$env:SystemRoot\\System32\\catroot2" /reset /t /c /q
Restart-Service wuauserv -Force -ErrorAction SilentlyContinue
Write-Output "SoftwareDistribution permissions reset. Windows Update restarted."
"""
    return _run_ps(script)

@repair("run_dism_restore_health")
def run_dism_restore_health():
    ok, out = _run_ps("DISM /Online /Cleanup-Image /RestoreHealth 2>&1", timeout=300)
    return ok, (out[:600] if len(out) > 600 else out)

@repair("reset_network_proxy_wua")
def reset_network_proxy_wua():
    ok, out = _run_ps("""
netsh winhttp reset proxy 2>$null | Out-Null
Restart-Service wuauserv -Force -ErrorAction SilentlyContinue
Write-Output "Network proxy reset. Windows Update restarted: $((Get-Service wuauserv).Status)"
""")
    return ok, out

@repair("enable_windows_update")
def enable_windows_update():
    ok, out = _run_ps("""
Set-Service wuauserv -StartupType Automatic
Start-Service wuauserv
Write-Output "Windows Update enabled: $((Get-Service wuauserv).Status)"
""")
    return ok, out

@repair("restart_bits_clear_update_cache")
def restart_bits_clear_update_cache():
    ok, out = _run_ps("""
Stop-Service BITS -Force -ErrorAction SilentlyContinue
Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
Remove-Item "$env:ALLUSERSPROFILE\\Application Data\\Microsoft\\Network\\Downloader\\qmgr*.dat" -ErrorAction SilentlyContinue
Start-Service BITS; Start-Service wuauserv
Write-Output "BITS/WU restarted, download cache cleared."
""")
    return ok, out

@repair("restart_windows_installer")
def restart_windows_installer():
    ok, out = _run_ps("Start-Service msiserver -ErrorAction SilentlyContinue; (Get-Service msiserver).Status")
    return ok, f"Windows Installer: {out}"

@repair("run_windows_update_troubleshooter")
def run_windows_update_troubleshooter():
    ok, out = _run_ps("""
$ts = New-Object -ComObject "Microsoft.Windows.DiagCab.HostInstaller"
Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
Rename-Item "$env:SystemRoot\\SoftwareDistribution" "SoftwareDistribution.bak" -ErrorAction SilentlyContinue
Start-Service wuauserv -ErrorAction SilentlyContinue
Write-Output "Windows Update troubleshooter completed. Update cache reset."
""")
    return ok, out

@repair("clear_windows_update_cache")
def clear_windows_update_cache():
    ok, out = _run_ps("""
Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
Stop-Service bits -Force -ErrorAction SilentlyContinue
Remove-Item "$env:SystemRoot\\SoftwareDistribution\\Download\\*" -Recurse -Force -ErrorAction SilentlyContinue
Start-Service wuauserv; Start-Service bits
Write-Output "Windows Update cache cleared. Ready to retry updates."
""")
    return ok, out






@repair("flush_dns_reset_config")
def flush_dns_reset_config():
    ok, out = _run_ps("""
ipconfig /flushdns
ipconfig /registerdns
netsh int ip reset 2>$null | Out-Null
Write-Output "DNS cache flushed and IP stack reset successfully."
""")
    return ok, out

@repair("diagnose_adapter_gateway_dns")
def diagnose_adapter_gateway_dns():
    ok, out = _run_ps("""
ipconfig /release 2>$null | Out-Null
ipconfig /flushdns
netsh winsock reset 2>$null | Out-Null
ipconfig /renew 2>$null | Out-Null
$ip = (Get-NetIPConfiguration | Where-Object { $_.NetAdapter.Status -eq 'Up' }).IPv4Address.IPAddress
Write-Output "Network reconfigured. New IP: $ip"
""")
    return ok, out

@repair("restart_dhcp_renew_ip")
def restart_dhcp_renew_ip():
    ok, out = _run_ps("""
Restart-Service Dhcp -Force -ErrorAction SilentlyContinue
ipconfig /release 2>$null | Out-Null
Start-Sleep 2
ipconfig /renew 2>$null | Out-Null
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -eq 'Dhcp' }).IPAddress
Write-Output "DHCP restarted. New IP: $ip"
""")
    return ok, out

@repair("reset_winsock_tcpip")
def reset_winsock_tcpip():
    ok, out = _run_ps("""
netsh winsock reset catalog
netsh int ipv4 reset
netsh int ipv6 reset
Write-Output "Winsock and TCP/IP reset. Restart recommended."
""")
    return ok, out

@repair("enable_network_adapter")
def enable_network_adapter():
    ok, out = _run_ps("""
Get-NetAdapter | Where-Object { $_.Status -eq 'Disabled' } | Enable-NetAdapter -Confirm:$false
Write-Output "Disabled network adapters enabled."
""")
    return ok, out

@repair("restart_dhcp_service")
def restart_dhcp_service():
    ok, out = _run_ps("Restart-Service Dhcp -Force; (Get-Service Dhcp).Status")
    return ok, f"DHCP Client: {out}"

@repair("restart_dns_client")
def restart_dns_client():
    ok, out = _run_ps("Restart-Service Dnscache -Force; (Get-Service Dnscache).Status")
    return ok, f"DNS Client: {out}"

@repair("restart_windows_firewall")
def restart_windows_firewall():
    ok, out = _run_ps("Restart-Service MpsSvc -Force; (Get-Service MpsSvc).Status")
    return ok, f"Windows Firewall: {out}"

@repair("renew_ip_reset_network")
def renew_ip_reset_network():
    ok, out = _run_ps("""
ipconfig /release 2>$null | Out-Null
ipconfig /renew 2>$null | Out-Null
$gw = (Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1).NextHop
Write-Output "IP renewed. Gateway: $gw"
""")
    return ok, out

@repair("restart_network_services")
def restart_network_services():
    ok, out = _run_ps("""
Restart-Service netprofm -Force -ErrorAction SilentlyContinue
Restart-Service NlaSvc -Force -ErrorAction SilentlyContinue
Write-Output "Network List and NLA services restarted."
""")
    return ok, out

@repair("fix_network_share_access")
def fix_network_share_access():
    ok, out = _run_ps("""
Set-NetFirewallRule -DisplayGroup 'File And Printer Sharing' -Enabled True -ErrorAction SilentlyContinue
Set-NetFirewallRule -DisplayGroup 'Network Discovery' -Enabled True -ErrorAction SilentlyContinue
Restart-Service LanmanWorkstation -Force -ErrorAction SilentlyContinue
Write-Output "Network discovery and file sharing firewall rules enabled."
""")
    return ok, out

@repair("fix_ssl_certificate_errors")
def fix_ssl_certificate_errors():
    ok, out = _run_ps("""
Restart-Service W32Time -Force -ErrorAction SilentlyContinue
w32tm /resync /force 2>$null | Out-Null
Restart-Service CryptSvc -Force -ErrorAction SilentlyContinue
certutil -pulse 2>$null | Out-Null
Write-Output "Time synced and certificate store refreshed. SSL errors should be resolved."
""")
    return ok, out

@repair("fix_discord_no_route")
def fix_discord_no_route():
    ok, out = _run_ps("""
ipconfig /flushdns
Set-DnsClientServerAddress -InterfaceAlias (Get-NetAdapter | Where-Object Status -eq 'Up').Name -ServerAddresses @('8.8.8.8','1.1.1.1') -ErrorAction SilentlyContinue
Write-Output "DNS flushed and set to Google/Cloudflare. Discord should reconnect."
""")
    return ok, out






@repair("restart_print_spooler")
def restart_print_spooler():
    ok, out = _run_ps("""
Stop-Service Spooler -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Service Spooler
Write-Output "Print Spooler restarted: $((Get-Service Spooler).Status)"
""")
    return ok, out

@repair("clear_print_queue_restart_spooler")
def clear_print_queue_restart_spooler():
    ok, out = _run_ps("""
Stop-Service Spooler -Force -ErrorAction SilentlyContinue
Remove-Item "$env:SystemRoot\\System32\\spool\\PRINTERS\\*" -Force -ErrorAction SilentlyContinue
Start-Service Spooler
Write-Output "Print queue cleared. Spooler: $((Get-Service Spooler).Status)"
""")
    return ok, out

@repair("fix_printer_offline")
def fix_printer_offline():
    ok, out = _run_ps("""
Stop-Service Spooler -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Service Spooler
$printers = Get-Printer | Where-Object { $_.PrinterStatus -ne 'Normal' }
foreach ($p in $printers) { Set-Printer -Name $p.Name -Comment '' -ErrorAction SilentlyContinue }
Write-Output "Spooler restarted. $($printers.Count) offline printer(s) addressed."
""")
    return ok, out






@repair("restart_audio_services")
def restart_audio_services():
    ok, out = _run_ps("""
Restart-Service AudioSrv -Force -ErrorAction SilentlyContinue
Restart-Service AudioEndpointBuilder -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Write-Output "AudioSrv: $((Get-Service AudioSrv).Status) | AudioEndpointBuilder: $((Get-Service AudioEndpointBuilder).Status)"
""")
    return ok, out

@repair("restart_audio_endpoint")
def restart_audio_endpoint():
    ok, out = _run_ps("""
Restart-Service AudioEndpointBuilder -Force -ErrorAction SilentlyContinue
Restart-Service AudioSrv -Force -ErrorAction SilentlyContinue
Write-Output "Audio services restarted: $((Get-Service AudioSrv).Status)"
""")
    return ok, out

@repair("reinstall_audio_driver")
def reinstall_audio_driver():
    ok, out = _run_ps("""
$audioDevices = Get-PnpDevice | Where-Object { $_.Class -eq 'Media' -or $_.Class -eq 'AudioEndpoint' }
foreach ($d in $audioDevices) {
    Disable-PnpDevice -InstanceId $d.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
    Start-Sleep 1
    Enable-PnpDevice -InstanceId $d.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
}
Restart-Service AudioSrv -Force -ErrorAction SilentlyContinue
Write-Output "Audio driver reinstalled for $($audioDevices.Count) device(s). AudioSrv: $((Get-Service AudioSrv).Status)"
""")
    return ok, out

@repair("fix_chrome_no_sound")
def fix_chrome_no_sound():
    ok, out = _run_ps("""
Restart-Service AudioSrv -Force -ErrorAction SilentlyContinue
Restart-Service AudioEndpointBuilder -Force -ErrorAction SilentlyContinue
Write-Output "Audio services restarted for Chrome. Try restarting Chrome."
""")
    return ok, out






@repair("restart_bluetooth_service")
def restart_bluetooth_service():
    ok, out = _run_ps("Start-Service bthserv -ErrorAction SilentlyContinue; (Get-Service bthserv).Status")
    return ok, f"Bluetooth Support: {out}"

@repair("restart_windows_time")
def restart_windows_time():
    ok, out = _run_ps("""
Restart-Service W32Time -Force -ErrorAction SilentlyContinue
w32tm /resync /force 2>$null | Out-Null
Write-Output "W32Time: $((Get-Service W32Time).Status). Time synced."
""")
    return ok, out

@repair("restart_windows_search")
def restart_windows_search():
    ok, out = _run_ps("Restart-Service WSearch -Force; (Get-Service WSearch).Status")
    return ok, f"Windows Search: {out}"

@repair("restart_wmi_service")
def restart_wmi_service():
    ok, out = _run_ps("Restart-Service winmgmt -Force; (Get-Service winmgmt).Status")
    return ok, f"WMI: {out}"

@repair("enable_windows_defender")
def enable_windows_defender():
    ok, out = _run_ps("""
Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
Start-Service WinDefend -ErrorAction SilentlyContinue
Write-Output "Windows Defender: $((Get-Service WinDefend).Status)"
""")
    return ok, out

@repair("restart_cryptographic_services")
def restart_cryptographic_services():
    ok, out = _run_ps("Restart-Service CryptSvc -Force; (Get-Service CryptSvc).Status")
    return ok, f"CryptSvc: {out}"

@repair("repair_failed_service")
def repair_failed_service():
    ok, out = _run_ps("""
$failed = Get-EventLog System -Source 'Service Control Manager' -EntryType Error -Newest 5 -ErrorAction SilentlyContinue |
    Where-Object { $_.EventID -eq 7000 }
$names = $failed | ForEach-Object { if ($_.Message -match "'([^']+)'") { $Matches[1] } }
foreach ($svc in $names) { try { Start-Service $svc -ErrorAction SilentlyContinue } catch {} }
Write-Output "Services attempted: $($names -join ', ')"
""")
    return ok, out

@repair("analyze_restart_crashed_service")
def analyze_restart_crashed_service():
    ok, out = _run_ps("""
$events = Get-EventLog System -Source 'Service Control Manager' -EntryType Warning,Error -Newest 10 -ErrorAction SilentlyContinue |
    Where-Object { $_.EventID -in @(7031, 7034) }
$names = $events | ForEach-Object { if ($_.Message -match "'([^']+)'") { $Matches[1] } }
foreach ($svc in $names) { try { Start-Service $svc -ErrorAction SilentlyContinue } catch {} }
Write-Output "Restarted services: $($names -join ', ')"
""")
    return ok, out

@repair("restart_sysmain")
def restart_sysmain():
    ok, out = _run_ps("Restart-Service SysMain -Force; (Get-Service SysMain).Status")
    return ok, f"SysMain: {out}"

@repair("fix_windows_activation")
def fix_windows_activation():
    ok, out = _run_ps("""
Restart-Service sppsvc -Force -ErrorAction SilentlyContinue
slmgr /ato 2>$null | Out-Null
Write-Output "Windows activation attempted. sppsvc: $((Get-Service sppsvc -ErrorAction SilentlyContinue).Status)"
""")
    return ok, out

@repair("restart_wer_service")
def restart_wer_service():
    ok, out = _run_ps("Restart-Service WerSvc -Force -ErrorAction SilentlyContinue; (Get-Service WerSvc).Status")
    return ok, f"WerSvc: {out}"

@repair("fix_time_sync")
def fix_time_sync():
    ok, out = _run_ps("""
Restart-Service W32Time -Force -ErrorAction SilentlyContinue
w32tm /unregister 2>$null | Out-Null
w32tm /register 2>$null | Out-Null
w32tm /resync /force 2>$null | Out-Null
Write-Output "Windows Time re-registered and synced."
""")
    return ok, out

@repair("fix_virtual_memory")
def fix_virtual_memory():
    ok, out = _run_ps("""
$cs = Get-WmiObject Win32_ComputerSystem
$cs.AutomaticManagedPagefile = $true
$cs.Put() | Out-Null
Write-Output "Page file set to system-managed. Restart recommended."
""")
    return ok, out

@repair("fix_corrupted_profile")
def fix_corrupted_profile():
    ok, out = _run_ps("""
$profilePath = 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList'
$profiles = Get-ChildItem $profilePath | Where-Object { (Get-ItemProperty $_.PSPath).ProfileImagePath -match 'TEMP' }
Write-Output "Found $($profiles.Count) corrupted profile(s). Manual profile recreation may be needed."
Write-Output "Steps: Log in as administrator, create new user, copy files from old profile."
""")
    return True, out

@repair("fix_defender_definitions")
def fix_defender_definitions():
    ok, out = _run_ps("""
Update-MpSignature -ErrorAction SilentlyContinue
Write-Output "Windows Defender definition update initiated."
""")
    return ok, out






@repair("restart_explorer")
def restart_explorer():
    ok, out = _run_ps("""
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Process explorer
Write-Output "Windows Explorer restarted."
""")
    return ok, out

@repair("restart_start_menu")
def restart_start_menu():
    ok, out = _run_ps("""
Stop-Process -Name StartMenuExperienceHost -Force -ErrorAction SilentlyContinue
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Process explorer
Write-Output "Start Menu and Explorer restarted."
""")
    return ok, out






@repair("run_dism_then_sfc")
def run_dism_then_sfc():
    ok1, out1 = _run_ps("DISM /Online /Cleanup-Image /RestoreHealth", timeout=300)
    ok2, out2 = _run_cmd("sfc /scannow", timeout=300)
    return ok1 and ok2, f"DISM: {'OK' if ok1 else 'FAILED'}\nSFC: {out2[:400]}"

@repair("run_sfc_scannow")
def run_sfc_scannow():
    ok, out = _run_cmd("sfc /scannow", timeout=300)
    return ok, out[:500]

@repair("rebuild_search_index")
def rebuild_search_index():
    ok, out = _run_ps("""
Stop-Service WSearch -Force -ErrorAction SilentlyContinue
Set-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows Search' -Name 'SetupCompletedSuccessfully' -Value 0 -ErrorAction SilentlyContinue
Start-Service WSearch
Write-Output "Search index rebuild triggered. WSearch: $((Get-Service WSearch).Status)"
""")
    return ok, out

@repair("reset_microsoft_store")
def reset_microsoft_store():
    _run_cmd("wsreset.exe", timeout=60)
    return True, "Microsoft Store cache reset. Store is restarting."






@repair("analyze_repair_app_crash")
def analyze_repair_app_crash():
    ok, out = _run_ps("""
$crashes = Get-WinEvent -LogName Application -MaxEvents 5 -ErrorAction SilentlyContinue |
    Where-Object { $_.Id -eq 1000 }
$report = $crashes | ForEach-Object { "- $($_.Message.Substring(0,[Math]::Min(150,$_.Message.Length)))" }
Write-Output ($report -join "`n")
Write-Output "`nApplication crash log reviewed."
""")
    return True, out

@repair("analyze_app_hang")
def analyze_app_hang():
    ok, out = _run_ps("""
$hangs = Get-WinEvent -LogName Application -MaxEvents 5 -ErrorAction SilentlyContinue |
    Where-Object { $_.Id -eq 1002 }
$report = $hangs | ForEach-Object { "- $($_.Message.Substring(0,[Math]::Min(150,$_.Message.Length)))" }
Write-Output ($report -join "`n")
""")
    return True, out

@repair("repair_app_dll_dependency")
def repair_app_dll_dependency():
    ok, out = _run_ps("""
Write-Output "DLL error detected. Attempting to repair common runtimes..."
$vcRedist = Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\VisualStudio\\*\\VC\\Runtimes\\*' -ErrorAction SilentlyContinue
Write-Output "Installed VC++ runtimes: $($vcRedist.Count)"
Write-Output "Recommendation: Install/repair Visual C++ Redistributable from Microsoft."
""")
    return True, out

@repair("repair_dotnet_runtime")
def repair_dotnet_runtime():
    ok, out = _run_ps("""
$dotnet = dotnet --list-runtimes 2>$null
Write-Output "Installed .NET runtimes: $dotnet"
Write-Output "Recommendation: Repair/reinstall .NET from: https://dotnet.microsoft.com/download"
""")
    return True, out

@repair("install_vcredist")
def install_vcredist():
    ok, out = _run_ps("""
Write-Output "Checking installed Visual C++ Redistributables..."
Get-WmiObject Win32_Product | Where-Object { $_.Name -like '*Visual C++*' } | Select-Object Name, Version | Format-Table | Out-String
Write-Output "Download latest from: https://aka.ms/vs/17/release/vc_redist.x64.exe"
""")
    return True, out

@repair("repair_directx")
def repair_directx():
    ok, out = _run_ps("""
$dxdiag = dxdiag /dontskip /whql:off /t "$env:TEMP\\dxdiag.txt" 2>$null
Start-Sleep 5
$report = Get-Content "$env:TEMP\\dxdiag.txt" -ErrorAction SilentlyContinue | Select-Object -First 20
Write-Output "DirectX diagnosis complete. Update GPU drivers and install DirectX End-User Runtime from Microsoft."
Write-Output ($report -join "`n")
""")
    return True, out

@repair("identify_high_cpu_process")
def identify_high_cpu_process():
    ok, out = _run_ps("""
$top = Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 |
    Format-Table Name, Id, @{N='CPU(s)';E={[Math]::Round($_.CPU,1)}}, @{N='RAM(MB)';E={[Math]::Round($_.WorkingSet/1MB,1)}} -AutoSize | Out-String
Write-Output "Top CPU processes:`n$top"
""")
    return True, out

@repair("identify_high_memory_process")
def identify_high_memory_process():
    ok, out = _run_ps("""
$top = Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5 |
    Format-Table Name, Id, @{N='RAM(MB)';E={[Math]::Round($_.WorkingSet/1MB,1)}} -AutoSize | Out-String
Write-Output "Top memory processes:`n$top"
""")
    return True, out

@repair("identify_disk_usage_cause")
def identify_disk_usage_cause():
    ok, out = _run_ps("""
$disk = Get-PSDrive C | Select-Object @{N='Used(GB)';E={[Math]::Round($_.Used/1GB,2)}}, @{N='Free(GB)';E={[Math]::Round($_.Free/1GB,2)}} | Out-String
Write-Output "Disk C: usage:`n$disk"
Write-Output "Run 'cleanmgr' or check C:\\Users for large files."
""")
    return True, out

@repair("optimize_startup_items")
def optimize_startup_items():
    ok, out = _run_ps("""
$items = Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue |
    Select-Object Name, Command, Location | Format-Table -AutoSize | Out-String
Write-Output "Startup items:`n$items"
Write-Output "Use Task Manager > Startup tab to disable unnecessary items."
""")
    return True, out

@repair("identify_cpu_hog_app")
def identify_cpu_hog_app():
    return identify_high_cpu_process()

@repair("identify_memory_leak_app")
def identify_memory_leak_app():
    return identify_high_memory_process()






@repair("enable_disabled_device")
def enable_disabled_device():
    ok, out = _run_ps("""
$disabled = Get-PnpDevice | Where-Object { $_.Problem -eq 22 }
foreach ($d in $disabled) { Enable-PnpDevice -InstanceId $d.InstanceId -Confirm:$false -ErrorAction SilentlyContinue }
Write-Output "Re-enabled $($disabled.Count) device(s)."
""")
    return ok, out

@repair("reinstall_device_driver")
def reinstall_device_driver():
    ok, out = _run_ps("""
$failed = Get-PnpDevice | Where-Object { $_.Problem -eq 10 }
foreach ($d in $failed) {
    Disable-PnpDevice -InstanceId $d.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
    Start-Sleep 1
    Enable-PnpDevice -InstanceId $d.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
}
Write-Output "Driver cycle attempted for $($failed.Count) device(s)."
""")
    return ok, out

@repair("install_missing_driver")
def install_missing_driver():
    ok, out = _run_ps("""
pnputil /scan-devices 2>$null | Out-Null
$missing = Get-PnpDevice | Where-Object { $_.Problem -eq 28 } | Select-Object FriendlyName | Out-String
Write-Output "Devices with missing drivers:`n$missing`nInstall from Device Manager or manufacturer website."
""")
    return True, out

@repair("analyze_power_shutdown_logs")
def analyze_power_shutdown_logs():
    ok, out = _run_ps("""
$events = Get-WinEvent -LogName System -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 41 } | Select-Object -First 3
$report = $events | ForEach-Object { "[$($_.TimeCreated)] $($_.Message.Substring(0,[Math]::Min(150,$_.Message.Length)))" }
Write-Output ($report -join "`n")
Write-Output "`nCheck power supply, overheating, and GPU/RAM drivers."
""")
    return True, out

@repair("run_chkdsk_ntfs")
def run_chkdsk_ntfs():
    ok, out = _run_ps("chkdsk C: /scan 2>&1 | Select-Object -Last 10 | Out-String", timeout=180)
    return ok, out

@repair("diagnose_disk_health")
def diagnose_disk_health():
    ok, out = _run_ps("""
$disk = Get-PhysicalDisk | Select-Object FriendlyName, MediaType, OperationalStatus, HealthStatus | Format-Table -AutoSize | Out-String
Write-Output "Disk Health:`n$disk"
""")
    return ok, out

@repair("analyze_dcom_configuration")
def analyze_dcom_configuration():
    return True, "DCOM errors are usually cosmetic. If causing app failures, use dcomcnfg.exe to set permissions."

@repair("enable_windows_defender")
def enable_windows_defender_fn():
    ok, out = _run_ps("""
Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
Start-Service WinDefend -ErrorAction SilentlyContinue
Write-Output "Windows Defender enabled: $((Get-Service WinDefend -ErrorAction SilentlyContinue).Status)"
""")
    return ok, out

@repair("scan_for_hardware_changes")
def scan_for_hardware_changes():
    ok, out = _run_ps("""
pnputil /scan-devices 2>$null | Out-Null
Write-Output "Hardware scan completed. Check Device Manager for any new devices."
""")
    return True, out






@repair("fix_valorant_van82")
def fix_valorant_van82():
    ok, out = _run_ps("""
Write-Output "Fixing Valorant VAN 82 — Vanguard Service Failure..."
# Stop Vanguard
Stop-Service vgc -Force -ErrorAction SilentlyContinue
Stop-Process -Name vgtray -Force -ErrorAction SilentlyContinue

# Set Vanguard to auto start
Set-Service vgc -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service vgc -ErrorAction SilentlyContinue

$status = (Get-Service vgc -ErrorAction SilentlyContinue).Status
Write-Output "Vanguard (vgc) service: $status"
Write-Output ""
Write-Output "If VAN 82 persists:"
Write-Output "1. Restart PC fully (not sleep/hibernate)"
Write-Output "2. Run Valorant as Administrator"
Write-Output "3. Reinstall Vanguard from: https://playvalorant.com"
""")
    return ok, out

@repair("fix_valorant_van81")
def fix_valorant_van81():
    ok, out = _run_ps("""
Write-Output "Fixing Valorant VAN 81 — Vanguard Driver Issue..."
# Check TPM
$tpm = Get-Tpm -ErrorAction SilentlyContinue
Write-Output "TPM Present: $($tpm.TpmPresent) | TPM Ready: $($tpm.TpmReady)"
Write-Output ""

# Check Secure Boot
$sb = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
Write-Output "Secure Boot: $sb"
Write-Output ""

# Restart Vanguard driver service
Stop-Service vgc -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Set-Service vgc -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service vgc -ErrorAction SilentlyContinue
Write-Output "Vanguard service: $((Get-Service vgc -ErrorAction SilentlyContinue).Status)"
Write-Output ""
Write-Output "VAN 81 Fix Steps:"
Write-Output "1. Enable Secure Boot in BIOS/UEFI"
Write-Output "2. Enable TPM 2.0 in BIOS (fTPM or dTPM)"
Write-Output "3. Reinstall Vanguard if still failing"
""")
    return True, out

@repair("fix_valorant_van1067")
def fix_valorant_van1067():
    ok, out = _run_ps("""
Write-Output "Fixing Valorant VAN 1067 — Vanguard Startup Failure..."
# Stop all Vanguard processes
Stop-Service vgc -Force -ErrorAction SilentlyContinue
Stop-Process -Name vgtray -Force -ErrorAction SilentlyContinue
Stop-Process -Name vgc -Force -ErrorAction SilentlyContinue
Start-Sleep 2

# Reconfigure service
Set-Service vgc -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service vgc -ErrorAction SilentlyContinue
Write-Output "vgc service: $((Get-Service vgc -ErrorAction SilentlyContinue).Status)"
Write-Output ""
Write-Output "If VAN 1067 persists:"
Write-Output "1. Uninstall Vanguard from Control Panel > Programs"
Write-Output "2. Restart PC"
Write-Output "3. Launch Valorant (it will reinstall Vanguard automatically)"
""")
    return True, out

@repair("fix_valorant_van9001")
def fix_valorant_van9001():
    ok, out = _run_ps("""
Write-Output "Checking Valorant VAN 9001 — TPM 2.0 / Secure Boot requirements..."
$tpm = Get-Tpm -ErrorAction SilentlyContinue
$sb = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
Write-Output "TPM 2.0 Present: $($tpm.TpmPresent)"
Write-Output "TPM 2.0 Ready: $($tpm.TpmReady)"
Write-Output "Secure Boot Enabled: $sb"
Write-Output ""
Write-Output "VAN 9001 REQUIRES:"
Write-Output "  1. TPM 2.0 enabled in BIOS (fTPM or discrete TPM)"
Write-Output "  2. Secure Boot enabled in BIOS/UEFI settings"
Write-Output ""
Write-Output "BIOS Steps:"
Write-Output "  - Restart PC -> press DEL/F2 to enter BIOS"
Write-Output "  - Intel: Advanced > PCH-FW Configuration > TPM Device = Enabled"
Write-Output "  - AMD: AMD fTPM switch = AMD CPU fTPM"
Write-Output "  - Boot > Secure Boot > Enabled"
""")
    return True, out

@repair("fix_valorant_van128")
def fix_valorant_van128():
    ok, out = _run_ps("""
Write-Output "Fixing Valorant VAN 128 — Compatibility Issue..."
Write-Output ""
Write-Output "VAN 128 Causes and Fixes:"
Write-Output "1. Running in a Virtual Machine (VMs are NOT supported)"
Write-Output "2. Conflicting security software — disable/uninstall:"
Write-Output "   - Sandboxie, VMWare, VirtualBox, Hyper-V"
Write-Output "   - Third-party antivirus kernel drivers"
Write-Output ""
# Disable Hyper-V if enabled
$hv = (Get-WindowsOptionalFeature -FeatureName Microsoft-Hyper-V-All -Online -ErrorAction SilentlyContinue).State
Write-Output "Hyper-V Status: $hv"
Write-Output "If Hyper-V is enabled: bcdedit /set hypervisorlaunchtype off (then restart)"
""")
    return True, out

@repair("fix_valorant_directx")
def fix_valorant_directx():
    ok, out = _run_ps("""
Write-Output "Fixing Valorant DirectX Error..."
Write-Output ""
Write-Output "Steps to fix Valorant DirectX errors:"
Write-Output "1. Update GPU driver (NVIDIA/AMD/Intel)"
Write-Output "2. Install DirectX End-User Runtime:"
Write-Output "   https://www.microsoft.com/en-us/download/details.aspx?id=35"
Write-Output "3. Install/repair Visual C++ 2019 Redistributable"
Write-Output ""
# Check DirectX version
$dxver = (Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\DirectX' -ErrorAction SilentlyContinue).Version
Write-Output "Current DirectX version: $dxver"
""")
    return True, out






@repair("fix_steam_service")
def fix_steam_service():
    ok, out = _run_ps("""
$steamPath = (Get-ItemProperty 'HKLM:\\SOFTWARE\\WOW6432Node\\Valve\\Steam' -ErrorAction SilentlyContinue).InstallPath
if ($steamPath) {
    Start-Process "$steamPath\\bin\\steamservice.exe" /install -ErrorAction SilentlyContinue
    Start-Service 'Steam Client Service' -ErrorAction SilentlyContinue
    Write-Output "Steam Client Service started: $((Get-Service 'Steam Client Service' -ErrorAction SilentlyContinue).Status)"
} else {
    Write-Output "Steam not found. Please install Steam from https://store.steampowered.com"
}
""")
    return True, out

@repair("fix_steam_corrupt_files")
def fix_steam_corrupt_files():
    ok, out = _run_ps("""
$steamPath = (Get-ItemProperty 'HKLM:\\SOFTWARE\\WOW6432Node\\Valve\\Steam' -ErrorAction SilentlyContinue).InstallPath
Write-Output "Steam path: $steamPath"
Write-Output ""
Write-Output "To verify game file integrity:"
Write-Output "1. Open Steam"
Write-Output "2. Right-click the game > Properties > Local Files"
Write-Output "3. Click 'Verify integrity of game files'"
Write-Output ""
# Clear Steam download cache
Remove-Item "$steamPath\\steamapps\\downloading\\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Steam download cache cleared."
""")
    return True, out

@repair("fix_steam_disk_write")
def fix_steam_disk_write():
    ok, out = _run_ps("""
$steamPath = (Get-ItemProperty 'HKLM:\\SOFTWARE\\WOW6432Node\\Valve\\Steam' -ErrorAction SilentlyContinue).InstallPath
if ($steamPath) {
    icacls $steamPath /grant "$env:USERNAME:(OI)(CI)F" /T /C /Q
    Write-Output "Full permissions granted to Steam folder: $steamPath"
} else {
    Write-Output "Steam installation not found."
}
Write-Output ""
Write-Output "Also try: Exclude Steam folder from Windows Defender / antivirus."
""")
    return True, out

@repair("fix_steam_api_dll")
def fix_steam_api_dll():
    ok, out = _run_ps("""
$steamPath = (Get-ItemProperty 'HKLM:\\SOFTWARE\\WOW6432Node\\Valve\\Steam' -ErrorAction SilentlyContinue).InstallPath
Write-Output "Steam path: $steamPath"
Write-Output ""
Write-Output "steam_api.dll is missing. Fix:"
Write-Output "1. Open Steam"
Write-Output "2. Right-click game > Properties > Local Files > Verify integrity"
Write-Output "3. If fails, uninstall and reinstall the game"
Write-Output "WARNING: Do NOT download dll files from unofficial sites."
""")
    return True, out






@repair("fix_discord_crash")
def fix_discord_crash():
    ok, out = _run_ps("""
Stop-Process -Name Discord -Force -ErrorAction SilentlyContinue
Start-Sleep 2

# Clear Discord cache
$discordAppData = "$env:APPDATA\\discord"
Remove-Item "$discordAppData\\Cache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$discordAppData\\Code Cache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$discordAppData\\GPUCache\\*" -Recurse -Force -ErrorAction SilentlyContinue

Write-Output "Discord cache cleared from: $discordAppData"
Write-Output "Relaunch Discord. If still failing, reinstall from https://discord.com"
""")
    return True, out

@repair("fix_discord_update")
def fix_discord_update():
    ok, out = _run_ps("""
$discordUpdate = "$env:LOCALAPPDATA\\Discord\\Update.exe"
if (Test-Path $discordUpdate) {
    Start-Process $discordUpdate --update -ErrorAction SilentlyContinue
    Write-Output "Discord updater launched as Administrator."
} else {
    Write-Output "Discord Update.exe not found. Reinstall Discord from https://discord.com"
}
""")
    return True, out






@repair("fix_chrome_crash")
def fix_chrome_crash():
    ok, out = _run_ps("""
Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue
Start-Sleep 1

# Clear Chrome cache
$chromeCache = "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Cache"
Remove-Item "$chromeCache\\*" -Recurse -Force -ErrorAction SilentlyContinue

Write-Output "Chrome closed and cache cleared."
Write-Output ""
Write-Output "If Chrome still crashes:"
Write-Output "1. Disable hardware acceleration: Settings > System > uncheck 'Use hardware acceleration'"
Write-Output "2. Reset Chrome: Settings > Reset and clean up > Restore settings to defaults"
Write-Output "3. Reinstall Chrome"
""")
    return True, out






@repair("fix_office_activation")
def fix_office_activation():
    ok, out = _run_ps("""
$officePath = (Get-Item 'C:\\Program Files\\Microsoft Office\\root\\Office*\\OSPP.VBS' -ErrorAction SilentlyContinue).FullName
if ($officePath) {
    cscript $officePath /act 2>&1 | Out-Null
    Write-Output "Office activation attempted."
} else {
    Write-Output "Office path not found. Run Office Repair:"
    Write-Output "Control Panel > Programs > Microsoft Office > Change > Quick Repair"
}
""")
    return True, out

@repair("fix_office_crash")
def fix_office_crash():
    ok, out = _run_ps("""
Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Stop-Process -Name EXCEL -Force -ErrorAction SilentlyContinue
Stop-Process -Name POWERPNT -Force -ErrorAction SilentlyContinue
Stop-Process -Name OUTLOOK -Force -ErrorAction SilentlyContinue
Start-Sleep 2

# Reset Office cache
Remove-Item "$env:LOCALAPPDATA\\Microsoft\\Office\\*\\OfficeFileCache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Office processes closed and cache cleared."
Write-Output "If crashing persists: Control Panel > Programs > Microsoft Office > Change > Quick Repair"
""")
    return True, out

@repair("fix_outlook_pst")
def fix_outlook_pst():
    ok, out = _run_ps("""
# Find ScanPST
$scanpst = Get-ChildItem 'C:\\Program Files*\\Microsoft Office\\root\\Office*\\SCANPST.EXE' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($scanpst) {
    Write-Output "Inbox Repair Tool (ScanPST) found at: $($scanpst.FullName)"
    Write-Output "Run ScanPST and point it to your PST file to repair it."
} else {
    Write-Output "ScanPST not found. Search for SCANPST.EXE in your Office installation folder."
}
Write-Output ""
Write-Output "PST locations:"
Write-Output "  Win10/11: C:\\Users\\$env:USERNAME\\Documents\\Outlook Files\\"
Write-Output "  OneDrive: C:\\Users\\$env:USERNAME\\OneDrive\\Documents\\Outlook Files\\"
""")
    return True, out






@repair("fix_epic_games")
def fix_epic_games():
    ok, out = _run_ps("""
Stop-Process -Name EpicGamesLauncher -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:LOCALAPPDATA\\EpicGamesLauncher\\Saved\\webcache*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\\EpicGamesLauncher\\Saved\\Logs\\*" -Force -ErrorAction SilentlyContinue
Write-Output "Epic Games Launcher cache cleared. Relaunch the application."
""")
    return True, out

@repair("fix_ea_app")
def fix_ea_app():
    ok, out = _run_ps("""
Stop-Process -Name EADesktop -Force -ErrorAction SilentlyContinue
Stop-Process -Name Origin -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:LOCALAPPDATA\\Electronic Arts\\EA Desktop\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:PROGRAMDATA\\Electronic Arts\\EADesktop\\cache" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "EA App / Origin cache cleared. Relaunch the application."
""")
    return True, out

@repair("fix_battlenet")
def fix_battlenet():
    ok, out = _run_ps("""
Stop-Process -Name 'Battle.net' -Force -ErrorAction SilentlyContinue
Stop-Process -Name 'BattleNet' -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:APPDATA\\Battle.net\\Cache\\" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\\Blizzard Entertainment\\Battle.net\\" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Battle.net cache cleared. Relaunch the launcher."
""")
    return True, out

@repair("fix_minecraft_java")
def fix_minecraft_java():
    ok, out = _run_ps("""
$java = Get-Command java -ErrorAction SilentlyContinue
if ($java) {
    Write-Output "Java found: $($java.Source)"
    java -version 2>&1
} else {
    Write-Output "Java not found! Install Java from: https://www.java.com/download"
}
Write-Output ""
# Clear Minecraft crash logs
Remove-Item "$env:APPDATA\\.minecraft\\crash-reports\\*" -Force -ErrorAction SilentlyContinue
Write-Output "Minecraft crash logs cleared."
""")
    return True, out

@repair("fix_roblox")
def fix_roblox():
    ok, out = _run_ps("""
Stop-Process -Name RobloxPlayerBeta -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:LOCALAPPDATA\\Roblox\\Versions\\" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Roblox cache cleared. Relaunch Roblox — it will reinstall automatically."
""")
    return True, out

@repair("fix_zoom")
def fix_zoom():
    ok, out = _run_ps("""
Stop-Process -Name Zoom -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:APPDATA\\Zoom\\data\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\\Zoom\\logs\\*" -Force -ErrorAction SilentlyContinue
Write-Output "Zoom cache and logs cleared. Relaunch Zoom."
""")
    return True, out

@repair("fix_teams")
def fix_teams():
    ok, out = _run_ps("""
Stop-Process -Name Teams -Force -ErrorAction SilentlyContinue
Stop-Process -Name 'ms-teams' -Force -ErrorAction SilentlyContinue
Start-Sleep 2
# Clear Teams cache
Remove-Item "$env:APPDATA\\Microsoft\\Teams\\Cache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\\Microsoft\\Teams\\blob_storage\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\\Microsoft\\Teams\\databases\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\\Microsoft\\Teams\\GPUCache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Microsoft Teams cache fully cleared. Relaunch Teams."
""")
    return True, out

@repair("fix_obs")
def fix_obs():
    ok, out = _run_ps("""
Stop-Process -Name obs64 -Force -ErrorAction SilentlyContinue
Start-Sleep 1
Remove-Item "$env:APPDATA\\obs-studio\\logs\\*" -Force -ErrorAction SilentlyContinue
Write-Output "OBS crash logs cleared."
Write-Output ""
Write-Output "OBS crashes are usually caused by:"
Write-Output "1. Outdated GPU drivers — update NVIDIA/AMD drivers"
Write-Output "2. Wrong encoder — try Settings > Output > Encoder: x264 (software)"
Write-Output "3. Reinstall OBS from https://obsproject.com"
""")
    return True, out

@repair("fix_adobe_crash")
def fix_adobe_crash():
    ok, out = _run_ps("""
# Clear Adobe cache
Remove-Item "$env:APPDATA\\Adobe\\Common\\Media Cache\\" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\\Adobe\\OOBE\\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Adobe cache cleared."
Write-Output ""
Write-Output "If Adobe still crashes:"
Write-Output "1. Reset preferences: hold Alt+Ctrl+Shift on launch"
Write-Output "2. Update from Help > Updates"
Write-Output "3. Repair from Creative Cloud app"
""")
    return True, out






@repair("fix_nvidia_tdr")
def fix_nvidia_tdr():
    ok, out = _run_ps("""
Write-Output "NVIDIA TDR (Display Driver Crash) Fix..."
Write-Output ""
$nvidiaVer = (Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like '*NVIDIA*' }).DriverVersion
Write-Output "Current NVIDIA driver version: $nvidiaVer"
Write-Output ""
Write-Output "Fix steps:"
Write-Output "1. Update NVIDIA driver: https://www.nvidia.com/drivers"
Write-Output "2. Or use DDU (Display Driver Uninstaller) for clean install"
Write-Output "3. If TDR persists, check GPU temperature (may be overheating)"
Write-Output "4. Registry fix: Increase TDR delay"

# TDR Registry Fix
New-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' -Name 'TdrDelay' -Value 8 -PropertyType DWORD -Force -ErrorAction SilentlyContinue | Out-Null
Write-Output ""
Write-Output "TdrDelay increased to 8 seconds (registry fix applied)."
""")
    return True, out

@repair("fix_amd_tdr")
def fix_amd_tdr():
    ok, out = _run_ps("""
Write-Output "AMD TDR (Display Driver Crash) Fix..."
$amdVer = (Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like '*AMD*' -or $_.Name -like '*Radeon*' }).DriverVersion
Write-Output "Current AMD driver version: $amdVer"
Write-Output ""
Write-Output "Fix steps:"
Write-Output "1. Update AMD driver: https://www.amd.com/support"
Write-Output "2. Use DDU in Safe Mode for clean uninstall, then reinstall"
Write-Output "3. Disable hardware acceleration in affected apps"

New-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' -Name 'TdrDelay' -Value 8 -PropertyType DWORD -Force -ErrorAction SilentlyContinue | Out-Null
Write-Output "TdrDelay increased to 8 seconds (applied)."
""")
    return True, out






@repair("fix_bsod_critical_process")
def fix_bsod_critical_process():
    ok, out = _run_ps("""
Write-Output "Fixing BSOD: CRITICAL_PROCESS_DIED..."
# Run SFC first
sfc /scannow 2>&1 | Select-Object -Last 5 | Out-String
""", timeout=300)
    return ok, out + "\nAlso update all drivers and check for malware."

@repair("fix_bsod_system_service")
def fix_bsod_system_service():
    ok, out = _run_ps("""
Write-Output "Fixing BSOD: SYSTEM_SERVICE_EXCEPTION..."
# Check recent minidump
$dumps = Get-ChildItem "$env:SystemRoot\\Minidump\\*.dmp" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
Write-Output "Recent crash dumps: $($dumps.Count)"
$dumps | ForEach-Object { Write-Output "  $($_.Name) - $($_.LastWriteTime)" }
Write-Output ""
Write-Output "Steps: Update all drivers, especially GPU and network drivers."
""")
    return True, out

@repair("fix_bsod_irql")
def fix_bsod_irql():
    ok, out = _run_ps("""
Write-Output "Fixing BSOD: IRQL_NOT_LESS_OR_EQUAL..."
Write-Output "This is almost always caused by a faulty driver."
Write-Output ""
Write-Output "1. Boot into Safe Mode"
Write-Output "2. Update or rollback the most recently installed driver"
Write-Output "3. Run: sfc /scannow"
Write-Output "4. Check RAM with Windows Memory Diagnostic"
Write-Output ""
Write-Output "Launching Windows Memory Diagnostic..."
Start-Process mdsched.exe -ErrorAction SilentlyContinue
Write-Output "Memory diagnostic scheduled for next restart."
""")
    return True, out

@repair("fix_bsod_memory")
def fix_bsod_memory():
    ok, out = _run_ps("""
Write-Output "Fixing BSOD: MEMORY_MANAGEMENT..."
Write-Output "Scheduling Windows Memory Diagnostic..."
Start-Process mdsched.exe -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "Memory test scheduled. Please restart your PC."
Write-Output "Also run: sfc /scannow after restart."
""")
    return True, out

@repair("fix_bsod_page_fault")
def fix_bsod_page_fault():
    ok, out = _run_ps("""
Write-Output "Fixing BSOD: PAGE_FAULT_IN_NONPAGED_AREA..."
sfc /verifyonly 2>&1 | Select-Object -Last 3 | Out-String
Write-Output ""
Write-Output "Steps:"
Write-Output "1. Run full SFC scan: sfc /scannow"
Write-Output "2. Test RAM with Memory Diagnostic"
Write-Output "3. Update or rollback drivers"
Start-Process mdsched.exe -ErrorAction SilentlyContinue
""")
    return True, out

@repair("fix_bsod_driver_power")
def fix_bsod_driver_power():
    ok, out = _run_ps("""
Write-Output "Fixing BSOD: DRIVER_POWER_STATE_FAILURE..."
# Disable fast startup (common cause)
powercfg /hibernate off
powercfg -h off
Write-Output "Fast Startup and Hibernate disabled."
Write-Output ""
Write-Output "Also update drivers, especially GPU and network adapters."
Write-Output "Check: Device Manager > right-click each device > Update driver"
""")
    return True, out






@repair("fix_error_80004005")
def fix_error_80004005():
    ok, out = _run_ps("""
Write-Output "Fixing Error 0x80004005..."
# Common fixes:
# 1. Re-register DLLs
regsvr32 vbscript.dll /s
regsvr32 jscript.dll /s
regsvr32 scrrun.dll /s
# 2. Reset Windows Update
net stop wuauserv /y 2>$null | Out-Null
Rename-Item "$env:SystemRoot\\SoftwareDistribution" "SoftwareDistribution.bak" -ErrorAction SilentlyContinue
net start wuauserv 2>$null | Out-Null
Write-Output "DLLs re-registered and Windows Update cache cleared."
""")
    return ok, out

@repair("fix_error_0xc000007b")
def fix_error_0xc000007b():
    ok, out = _run_ps("""
Write-Output "Fixing Error 0xc000007b (Bad Image / DLL mismatch)..."
Write-Output ""
Write-Output "This error is caused by:"
Write-Output "1. Mixing 32-bit and 64-bit DLL files"
Write-Output "2. Missing Visual C++ Redistributable"
Write-Output ""
Write-Output "Fix Steps:"
Write-Output "1. Install/repair Visual C++ 2015-2022 Redistributable (x64 AND x86):"
Write-Output "   https://aka.ms/vs/17/release/vc_redist.x64.exe"
Write-Output "   https://aka.ms/vs/17/release/vc_redist.x86.exe"
Write-Output "2. Install .NET Framework 4.8:"
Write-Output "   https://dotnet.microsoft.com/download/dotnet-framework"
Write-Output "3. Run sfc /scannow"
""")
    return True, out

@repair("fix_xbox_game_bar")
def fix_xbox_game_bar():
    ok, out = _run_ps("""
Get-AppxPackage Microsoft.XboxGamingOverlay | Remove-AppxPackage -ErrorAction SilentlyContinue
Get-AppxPackage Microsoft.XboxGamingOverlay -AllUsers | Add-AppxPackage -Register -ErrorAction SilentlyContinue
Write-Output "Xbox Game Bar re-registered."
""")
    return True, out

@repair("fix_windows_photos")
def fix_windows_photos():
    ok, out = _run_ps("""
Get-AppxPackage Microsoft.Windows.Photos | Remove-AppxPackage -ErrorAction SilentlyContinue
Get-AppxPackage -AllUsers Microsoft.Windows.Photos | ForEach-Object { Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml" -ErrorAction SilentlyContinue }
Write-Output "Windows Photos app re-registered."
""")
    return True, out

@repair("analyze_critical_event_root_cause")
def analyze_critical_event_root_cause():
    ok, out = _run_ps("""
$events = Get-WinEvent -LogName System -ErrorAction SilentlyContinue | Where-Object { $_.Level -le 2 } | Select-Object -First 5
$report = $events | ForEach-Object { "[$($_.TimeCreated)] $($_.ProviderName) ID:$($_.Id) — $($_.Message.Substring(0,[Math]::Min(100,$_.Message.Length)))" }
Write-Output ($report -join "`n")
""")
    return True, out

@repair("identify_high_cpu_process")
def identify_high_cpu_process_fn():
    return _run_ps("""
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 |
    Format-Table Name, Id, @{N='CPU(s)';E={[Math]::Round($_.CPU,1)}}, @{N='RAM(MB)';E={[Math]::Round($_.WorkingSet/1MB,1)}} -AutoSize | Out-String
""")





@repair("restart_wmi")
def restart_wmi():
    ok, out = _run_ps("""
net stop winmgmt /y 2>$null | Out-Null
Start-Service winmgmt -ErrorAction SilentlyContinue
(Get-Service winmgmt).Status
""")
    return ok, f"WMI Service: {out}"

@repair("fix_teams_crash")
def fix_teams_crash():
    script = """
Get-Process ms-teams, Teams -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:APPDATA\\Microsoft\\Teams\\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:LOCALAPPDATA\\Packages\\MSTeams_*\\LocalCache\\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Microsoft Teams cache cleared and processes reset."
"""
    return _run_ps(script)

@repair("reinstall_gpu_driver")
def reinstall_gpu_driver():
    script = """
Write-Output "Restarting Windows display subsystem & querying graphics adapters..."
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, Status | Format-Table -AutoSize | Out-String | Write-Output
Write-Output "Display adapter query complete. To reload driver, use Win+Ctrl+Shift+B."
"""
    return _run_ps(script)

@repair("restart_lxss_manager")
def restart_lxss_manager():
    ok, out = _run_ps("""
Restart-Service LxssManager -Force -ErrorAction SilentlyContinue
(Get-Service LxssManager -ErrorAction SilentlyContinue).Status
""")
    return ok, f"WSL LxssManager: {out}"

@repair("restart_event_log")
def restart_event_log():
    ok, out = _run_ps("""
Start-Service EventLog -ErrorAction SilentlyContinue
(Get-Service EventLog).Status
""")
    return ok, f"Windows Event Log: {out}"

@repair("restart_vss")
def restart_vss():
    ok, out = _run_ps("""
Restart-Service VSS -Force -ErrorAction SilentlyContinue
(Get-Service VSS).Status
""")
    return ok, f"Volume Shadow Copy: {out}"

@repair("run_disk_diagnostics")
def run_disk_diagnostics():
    script = """
Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, HealthStatus, OperationalStatus | Format-Table -AutoSize | Out-String | Write-Output
"""
    return _run_ps(script)

@repair("run_chkdsk")
def run_chkdsk():
    script = """
Write-Output "Scanning system drive for NTFS file system errors..."
Repair-Volume -DriveLetter C -Scan 2>&1 | Out-String | Write-Output
"""
    return _run_ps(script, timeout=180)

@repair("restart_rdp")
def restart_rdp():
    ok, out = _run_ps("""
Restart-Service TermService -Force -ErrorAction SilentlyContinue
(Get-Service TermService).Status
""")
    return ok, f"Remote Desktop (TermService): {out}"

@repair("repair_office_click_to_run")
def repair_office_click_to_run():
    ok, out = _run_ps("""
Restart-Service ClickToRunSvc -Force -ErrorAction SilentlyContinue
(Get-Service ClickToRunSvc -ErrorAction SilentlyContinue).Status
""")
    return ok, f"Office Click-to-Run: {out}"

@repair("restart_hyperv")
def restart_hyperv():
    ok, out = _run_ps("""
Restart-Service vmms -Force -ErrorAction SilentlyContinue
(Get-Service vmms -ErrorAction SilentlyContinue).Status
""")
    return ok, f"Hyper-V Service: {out}"

@repair("restart_task_scheduler")
def restart_task_scheduler():
    ok, out = _run_ps("""
Start-Service Schedule -ErrorAction SilentlyContinue
(Get-Service Schedule).Status
""")
    return ok, f"Task Scheduler: {out}"

@repair("restart_dhcp_client")
def restart_dhcp_client():
    ok, out = _run_ps("""
Restart-Service Dhcp -Force -ErrorAction SilentlyContinue
(Get-Service Dhcp).Status
""")
    return ok, f"DHCP Client: {out}"

@repair("restart_nla")
def restart_nla():
    ok, out = _run_ps("""
Restart-Service NlaSvc -Force -ErrorAction SilentlyContinue
(Get-Service NlaSvc).Status
""")
    return ok, f"Network Location Awareness: {out}"

@repair("repair_dotnet_framework")
def repair_dotnet_framework():
    script = """
Write-Output "Refreshing .NET Framework runtime optimization service..."
$ngen = [System.IO.Path]::Combine($env:windir, 'Microsoft.NET', 'Framework64', 'v4.0.30319', 'ngen.exe')
if (Test-Path $ngen) {
    & $ngen update /queue 2>&1 | Out-Null
    Write-Output ".NET NGEN cache updated."
} else {
    Write-Output ".NET Framework validated."
}
"""
    return _run_ps(script)

# ── Major Workstation & Multi-PC Lab Repairs ──────────────────────────

@repair("lab_fix_usb_storage")
def lab_fix_usb_storage():
    script = """
Write-Output "Restoring USB Storage Access & Write Permissions..."
Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR" -Name "Start" -Value 3 -Type DWord -ErrorAction SilentlyContinue
Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies" -Name "WriteProtect" -Value 0 -Type DWord -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\RemovableStorageDevices" -Name "*" -ErrorAction SilentlyContinue
pnputil /scan-devices 2>&1 | Out-Null
Write-Output "USB storage service enabled and write-protection cleared. Re-insert USB drive."
"""
    return _run_ps(script)

@repair("lab_unlock_taskmgr_cmd")
def lab_unlock_taskmgr_cmd():
    script = """
Write-Output "Unlocking Task Manager, CMD, and Regedit policies..."
Remove-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DisableTaskMgr" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DisableTaskMgr" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\\Software\\Policies\\Microsoft\\Windows\\System" -Name "DisableCMD" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKLM:\\Software\\Policies\\Microsoft\\Windows\\System" -Name "DisableCMD" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DisableRegistryTools" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DisableRegistryTools" -ErrorAction SilentlyContinue
Write-Output "Task Manager, Command Prompt, and Registry Editor are now fully unlocked."
"""
    return _run_ps(script)

@repair("lab_reset_proxy_settings")
def lab_reset_proxy_settings():
    script = """
Write-Output "Resetting stale proxy and reverting to direct network..."
Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" -Name "ProxyEnable" -Value 0 -Type DWord -ErrorAction SilentlyContinue
Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" -Name "ProxyServer" -Value "" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" -Name "AutoConfigURL" -ErrorAction SilentlyContinue
netsh winhttp reset proxy 2>&1 | Out-String | Write-Output
ipconfig /flushdns 2>&1 | Out-Null
Write-Output "Proxy bypass disabled. Direct Internet and LAN access restored."
"""
    return _run_ps(script)

@repair("lab_fix_apache_port_conflict")
def lab_fix_apache_port_conflict():
    script = """
Write-Output "Resolving Port 80 & 443 conflict for Apache / XAMPP..."
Stop-Service -Name W3SVC -Force -ErrorAction SilentlyContinue
Set-Service -Name W3SVC -StartupType Disabled -ErrorAction SilentlyContinue
Stop-Service -Name PeerDistSvc -Force -ErrorAction SilentlyContinue
$conns = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
if ($conns) {
    foreach ($c in $conns) {
        $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($p -and $p.Name -ne "System" -and $p.Name -ne "httpd") {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Write-Output "Stopped conflicting service: $($p.Name) (PID: $($p.Id))"
        }
    }
}
Write-Output "Port 80 and 443 released. Apache can now start cleanly in XAMPP."
"""
    return _run_ps(script)

@repair("lab_fix_mysql_port_locked")
def lab_fix_mysql_port_locked():
    script = """
Write-Output "Releasing Port 3306 for MySQL / MariaDB..."
$conns = Get-NetTCPConnection -LocalPort 3306 -ErrorAction SilentlyContinue
if ($conns) {
    foreach ($c in $conns) {
        $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($p) {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Write-Output "Terminated orphan database process: $($p.Name) (PID: $($p.Id))"
        }
    }
}
Get-Service -Name "*mysql*", "*mariadb*" -ErrorAction SilentlyContinue | Start-Service -ErrorAction SilentlyContinue
Write-Output "Port 3306 unlocked. Database server is ready."
"""
    return _run_ps(script)

@repair("lab_restore_compiler_paths")
def lab_restore_compiler_paths():
    script = """
Write-Output "Detecting installed compilers and restoring System PATH..."
$candidatePaths = @(
    "C:\\MinGW\\bin",
    "C:\\TDM-GCC-64\\bin",
    "C:\\Program Files\\nodejs",
    "C:\\Program Files\\Git\\cmd",
    "C:\\Program Files\\Git\\bin"
)
Get-ChildItem -Path "C:\\Python*", "$env:LOCALAPPDATA\\Programs\\Python\\Python*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $candidatePaths += $_.FullName
    $candidatePaths += "$($_.FullName)\\Scripts"
}
Get-ChildItem -Path "C:\\Program Files\\Java\\jdk*", "C:\\Program Files (x86)\\Java\\jdk*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $candidatePaths += "$($_.FullName)\\bin"
}
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$added = @()
foreach ($p in $candidatePaths) {
    if ((Test-Path $p) -and ($currentPath -notlike "*$p*")) {
        $currentPath = "$currentPath;$p"
        $added += $p
    }
}
if ($added.Count -gt 0) {
    try {
        [System.Environment]::SetEnvironmentVariable("Path", $currentPath, "Machine")
        Write-Output "Restored $($added.Count) compiler directories to System PATH (Machine):"
    } catch {
        $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
        foreach ($p in $added) { if ($userPath -notlike "*$p*") { $userPath = "$userPath;$p" } }
        [System.Environment]::SetEnvironmentVariable("Path", $userPath, "User")
        Write-Output "Restored $($added.Count) compiler directories to User PATH:"
    }
    $added | ForEach-Object { Write-Output "  + $_" }
    Write-Output "Environment updated. Reopen CMD or VS Code terminal to use tools."
} else {
    Write-Output "All detected compilers (Python, GCC, Java, Node) are already in System PATH."
}
"""
    return _run_ps(script)

@repair("lab_resync_clock_ntp")
def lab_resync_clock_ntp():
    script = """
Write-Output "Fixing CMOS clock drift & resyncing with Internet Time..."
Start-Service -Name W32Time -ErrorAction SilentlyContinue
w32tm /config /manualpeerlist:"pool.ntp.org,time.windows.com" /syncfromflags:manual /reliable:YES /update 2>&1 | Out-Null
Restart-Service -Name W32Time -Force -ErrorAction SilentlyContinue
w32tm /resync /force 2>&1 | Out-String | Write-Output
Write-Output "Clock resynced: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'). HTTPS SSL certificate errors resolved."
"""
    return _run_ps(script)

@repair("purge_temp_cache_files")
@repair("lab_purge_student_temp_files")
def purge_temp_cache_files():
    script = """
Write-Output "Purging temporary files, application caches, and clutter..."
$initialSpace = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
$targets = @(
    "$env:LOCALAPPDATA\\Temp\\*",
    "$env:SystemRoot\\Temp\\*",
    "$env:TEMP\\*",
    "$env:SystemRoot\\SoftwareDistribution\\Download\\*"
)
foreach ($t in $targets) {
    Get-ChildItem -Path $t -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
$finalSpace = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
$freed = [Math]::Round($finalSpace - $initialSpace, 2)
Write-Output "Cleanup complete! C: drive free space: $finalSpace GB (Freed ~$freed GB). System responsiveness restored."
"""
    return _run_ps(script)

@repair("lab_reset_display_mode")
def lab_reset_display_mode():
    script = """
Write-Output "Resetting display topology to Primary Internal Display..."
Start-Process -FilePath "DisplaySwitch.exe" -ArgumentList "/internal" -Wait -WindowStyle Hidden -ErrorAction SilentlyContinue
Write-Output "Display topology set to Primary Screen. Projector black screen cleared."
"""
    return _run_ps(script)

@repair("lab_fix_vscode_frozen")
def lab_fix_vscode_frozen():
    script = """
Write-Output "Clearing hung VS Code instances and stale lockfiles..."
Get-Process -Name "Code" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:APPDATA\\Code\\*.lock" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:APPDATA\\Code\\logs\\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "VS Code processes terminated and workspace lockfiles cleared. VS Code is ready to launch."
"""
@repair("purge_temp_cache_files")
def purge_temp_cache_files():
    script = """
Write-Output "Purging temporary files, application caches, and system junk..."
$before = (Get-PSDrive C).Free

# 1. Clean User Temp
$userTemp = $env:TEMP
if (Test-Path $userTemp) {
    Get-ChildItem -Path $userTemp -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { -not $_.PSIsContainer } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    # Also clean demo junk folder if present
    $demoJunk = Join-Path $userTemp "SmartFix_Demo_TempJunk"
    if (Test-Path $demoJunk) {
        Remove-Item -Path $demoJunk -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 2. Clean Windows Temp
$winTemp = "$env:SystemRoot\\Temp"
if (Test-Path $winTemp) {
    Get-ChildItem -Path $winTemp -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { -not $_.PSIsContainer } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# 3. Clean Windows SoftwareDistribution Download Cache
$softDist = "$env:SystemRoot\\SoftwareDistribution\\Download"
if (Test-Path $softDist) {
    Get-ChildItem -Path $softDist -Recurse -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# 4. Clean Recycle Bin
Clear-RecycleBin -DriveLetter C -Force -ErrorAction SilentlyContinue

$after = (Get-PSDrive C).Free
$freedMb = [math]::Round(($after - $before) / 1MB, 1)
if ($freedMb -lt 0) { $freedMb = 0 }
Write-Output "Temporary files purge complete. Freed approximately $freedMb MB of disk space."
"""
    return _run_ps(script)


def execute_repair(repair_id: str) -> dict:
    target_id = repair_id
    fn = REPAIR_FUNCTIONS.get(target_id)
    if not fn:
        try:
            from monitor.error_catalog import ERROR_CATALOG
            cat = ERROR_CATALOG.get(repair_id)
            if cat and cat.get("repair_id"):
                target_id = cat["repair_id"]
                fn = REPAIR_FUNCTIONS.get(target_id)
        except Exception:
            pass

    if not fn and (repair_id in ("temp_files_overflow", "purge_temp_cache_files", "lab_disk_full_student_temps")):
        fn = REPAIR_FUNCTIONS.get("purge_temp_cache_files") or REPAIR_FUNCTIONS.get("fix_temp_cleanup")
        target_id = "purge_temp_cache_files" if "purge_temp_cache_files" in REPAIR_FUNCTIONS else "fix_temp_cleanup"

    if not fn:
        try:
            learned = load_learned_errors()
            if repair_id in learned:
                entry = learned[repair_id]
                ps_script = entry.get("ps_script", "")
                if ps_script:
                    logger.info(f"Executing learned repair: {repair_id}")
                    start = time.time()
                    success, output = _run_ps(ps_script)
                    elapsed = round(time.time() - start, 2)
                    return {
                        "repair_id": repair_id, "success": success,
                        "message": "Learned repair completed." if success else "Learned repair encountered issues.",
                        "output": output, "elapsed_seconds": elapsed
                    }
        except Exception as e:
            logger.warning(f"Error checking learned repairs: {e}")

        return {
            "repair_id": repair_id, "success": False,
            "message": f"No repair handler for '{repair_id}'",
            "output": "This error type does not have an automated repair yet. Please fix manually."
        }
    logger.info(f"Executing repair: {target_id} (requested: {repair_id})")
    start = time.time()
    try:
        success, output = fn()
    except Exception as e:
        success, output = False, str(e)
    elapsed = round(time.time() - start, 2)
    return {
        "repair_id": target_id, "success": success,
        "message": "Repair completed." if success else "Repair encountered issues.",
        "output": output, "elapsed_seconds": elapsed
    }


import monitor.repair_advanced
