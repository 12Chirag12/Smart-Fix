"""
SmartFix AI — Network Diagnostics Module
Runs real network tests: ping, DNS lookup, traceroute, speed estimate, port check.
"""
import subprocess
import socket
import time
import platform
from typing import Dict, Any, List, Tuple
from datetime import datetime

def _run(cmd: str, timeout: int = 15) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "Timed out."
    except Exception as e:
        return str(e)

def _run_ps(script: str, timeout: int = 20) -> str:
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=timeout
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return str(e)

def ping_test(host: str = "8.8.8.8", count: int = 4) -> dict:
    start = time.time()
    out = _run(f"ping -n {count} {host}")
    elapsed = round(time.time() - start, 2)
    success = "TTL=" in out or "Reply from" in out
    
    latency = "—"
    for line in out.splitlines():
        if "Average" in line or "average" in line:
            parts = line.split("=")
            if parts:
                latency = parts[-1].strip()
    return {"host": host, "success": success, "latency": latency, "output": out, "elapsed": elapsed}

def dns_test(hostnames: List[str] = None) -> dict:
    if hostnames is None:
        hostnames = ["google.com", "microsoft.com", "cloudflare.com"]
    results = {}
    for h in hostnames:
        try:
            ip = socket.gethostbyname(h)
            results[h] = {"success": True, "ip": ip}
        except Exception as e:
            results[h] = {"success": False, "error": str(e)}
    all_ok = all(v["success"] for v in results.values())
    return {"success": all_ok, "results": results}

def gateway_test() -> dict:
    out = _run_ps("""
$gw = (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Sort-Object RouteMetric | Select-Object -First 1).NextHop
if ($gw) {
    $ping = Test-Connection -ComputerName $gw -Count 2 -ErrorAction SilentlyContinue
    $latency = ($ping | Measure-Object ResponseTime -Average).Average
    Write-Output "$gw|$latency"
} else {
    Write-Output "NO_GATEWAY"
}
""")
    if out == "NO_GATEWAY" or not out:
        return {"success": False, "gateway": "Not found", "latency": "—"}
    parts = out.split("|")
    gw = parts[0] if parts else "Unknown"
    lat = (parts[1] + "ms") if len(parts) > 1 and parts[1] != "" else "—"
    return {"success": True, "gateway": gw, "latency": lat}

def adapter_info() -> dict:
    out = _run_ps("""
Get-NetAdapter | Where-Object Status -eq 'Up' | ForEach-Object {
    $ip = (Get-NetIPAddress -InterfaceIndex $_.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress
    "$($_.Name)|$($_.LinkSpeed)|$ip|$($_.MacAddress)"
}
""")
    adapters = []
    for line in out.strip().splitlines():
        parts = line.split("|")
        if len(parts) >= 3:
            adapters.append({
                "name": parts[0], "speed": parts[1],
                "ip": parts[2], "mac": parts[3] if len(parts) > 3 else "—"
            })
    return {"adapters": adapters}

def dns_servers() -> dict:
    out = _run_ps("""
Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object { $_.ServerAddresses } |
    Select-Object InterfaceAlias, @{N='DNS';E={$_.ServerAddresses -join ', '}} |
    ForEach-Object { "$($_.InterfaceAlias)|$($_.DNS)" }
""")
    servers = []
    for line in out.strip().splitlines():
        parts = line.split("|")
        if len(parts) >= 2 and parts[1]:
            servers.append({"adapter": parts[0], "dns": parts[1]})
    return {"servers": servers}

def internet_connectivity() -> dict:
    test_hosts = [("8.8.8.8", "Google DNS"), ("1.1.1.1", "Cloudflare DNS"), ("208.67.222.222", "OpenDNS")]
    results = []
    for host, name in test_hosts:
        r = ping_test(host, count=2)
        results.append({"host": host, "name": name, "success": r["success"], "latency": r["latency"]})
    all_ok = all(r["success"] for r in results)
    return {"success": all_ok, "results": results}

def open_ports_check() -> dict:
    """Check if common essential ports are accessible."""
    tests = [
        ("8.8.8.8", 53, "DNS"),
        ("time.windows.com", 123, "NTP"),
    ]
    results = []
    for host, port, name in tests:
        try:
            s = socket.create_connection((host, port), timeout=3)
            s.close()
            results.append({"service": name, "host": host, "port": port, "open": True})
        except Exception:
            results.append({"service": name, "host": host, "port": port, "open": False})
    return {"results": results}

def run_full_diagnostics() -> dict:
    """Run all diagnostics and return a combined report."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "timestamp": ts,
        "adapter": adapter_info(),
        "gateway": gateway_test(),
        "dns_servers": dns_servers(),
        "dns_resolution": dns_test(),
        "internet": internet_connectivity(),
        "ping_google": ping_test("8.8.8.8"),
        "ping_cf": ping_test("1.1.1.1"),
        "ports": open_ports_check(),
    }
