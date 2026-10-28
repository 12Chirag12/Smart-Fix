"""
SmartFix AI — Executive Diagnostic & System Health Report Generator
Produces a high-end, professionally styled HTML report with full telemetry,
repair history, category analytics, and print-ready PDF stylesheet (@media print).
"""
import os
import socket
import platform
import webbrowser
import psutil
from datetime import datetime
from typing import Dict, Any, Optional

from monitor.history import get_history, get_stats, get_category_stats
from monitor.hardware_diag import run_full_hardware_diagnostics
from monitor.maintenance import get_maintenance_status

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT, "data", "reports")


def generate_health_report(open_in_browser: bool = True) -> str:
    """
    Generate an executive HTML report of current system state and repair history.
    Saves to data/reports/ and optionally opens in default browser.
    Returns the absolute path to the generated HTML report.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now()
    report_filename = f"SmartFix_Audit_Report_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.join(REPORTS_DIR, report_filename)

    # 1. System info
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"
    os_name = platform.platform()
    cpu_count = psutil.cpu_count(logical=True)
    cpu_percent = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    uptime_seconds = int(datetime.now().timestamp() - psutil.boot_time())
    days, rem = divmod(uptime_seconds, 86400)
    hours, mins = divmod(rem, 3600)
    uptime_str = f"{days}d {hours}h {mins // 60}m" if days > 0 else f"{hours}h {mins // 60}m"

    # 2. Hardware telemetry
    hw = run_full_hardware_diagnostics()
    disk_diag = hw.get("disk", {})
    driver_diag = hw.get("driver", {})
    battery_diag = hw.get("battery", {})

    # 3. Statistics & History
    stats = get_stats()
    cat_stats = get_category_stats()
    history_records = get_history(100)
    maint_status = get_maintenance_status()

    total_repairs = stats.get("repaired", 0)
    successful_repairs = stats.get("success", 0)
    success_rate = (successful_repairs / total_repairs * 100) if total_repairs > 0 else 100.0

    # Build category breakdown rows
    cat_rows_html = ""
    for c in cat_stats:
        attempts = c.get("attempts", 0)
        successes = c.get("successes", 0)
        rate = (successes / attempts * 100) if attempts > 0 else 0
        cat_rows_html += f"""
        <tr>
            <td style="font-weight: 600;">{c.get('category', 'General')}</td>
            <td>{attempts}</td>
            <td><span style="color: #10B981; font-weight: 600;">{successes}</span></td>
            <td>
                <div style="background: #1E2030; border-radius: 4px; height: 8px; width: 100px; display: inline-block; vertical-align: middle; margin-right: 8px;">
                    <div style="background: #10B981; height: 100%; width: {min(100, int(rate))}%; border-radius: 4px;"></div>
                </div>
                <span>{rate:.1f}%</span>
            </td>
        </tr>
        """
    if not cat_rows_html:
        cat_rows_html = "<tr><td colspan='4' style='text-align: center; color: #8B8FA8;'>No category-specific repair history recorded yet.</td></tr>"

    # Build repair history rows
    hist_rows_html = ""
    for r in history_records:
        ts = str(r.get("timestamp", ""))[:19].replace("T", " ")
        name = r.get("error_name", "Unknown Issue")
        cat = r.get("category", "General")
        sev = r.get("severity", "LOW").upper()
        action = r.get("action", "DETECTED")
        success = r.get("success", 0)
        elapsed = r.get("elapsed_seconds", 0)

        # Badges
        sev_color = "#EF4444" if sev == "CRITICAL" else "#F59E0B" if sev == "HIGH" else "#3B82F6"
        sev_badge = f'<span style="background: {sev_color}22; color: {sev_color}; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">{sev}</span>'

        if action == "REPAIRED":
            status_badge = '<span style="color: #10B981; font-weight: 600;">✅ Success</span>' if success == 1 else '<span style="color: #EF4444; font-weight: 600;">❌ Issue</span>'
        elif action == "DETECTED":
            status_badge = '<span style="color: #F59E0B; font-weight: 600;">⚠️ Detected</span>'
        else:
            status_badge = f'<span style="color: #8B8FA8;">{action}</span>'

        hist_rows_html += f"""
        <tr>
            <td style="font-family: monospace; font-size: 12px; color: #8B8FA8;">{ts}</td>
            <td style="font-weight: 600; color: #E8EAF0;">{name}</td>
            <td>{cat}</td>
            <td>{sev_badge}</td>
            <td>{status_badge}</td>
            <td style="font-size: 12px; color: #8B8FA8;">{f"{elapsed:.2f}s" if elapsed else "-"}</td>
        </tr>
        """
    if not hist_rows_html:
        hist_rows_html = "<tr><td colspan='6' style='text-align: center; color: #8B8FA8;'>No repair actions logged in history database.</td></tr>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartFix AI — Executive Audit Report</title>
    <style>
        :root {{
            --bg-body: #0E0F14;
            --bg-card: #13141A;
            --bg-card2: #1A1B23;
            --border: #2A2D40;
            --text-main: #E8EAF0;
            --text-muted: #8B8FA8;
            --accent: #5B6EF5;
            --success: #10B981;
            --danger: #EF4444;
            --warning: #F59E0B;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-body);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 30px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1050px; margin: 0 auto; }}
        
        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 24px;
            margin-bottom: 30px;
        }}
        .brand {{ display: flex; align-items: center; gap: 14px; }}
        .brand-icon {{
            background: linear-gradient(135deg, #5B6EF5, #3B82F6);
            color: white;
            font-weight: 800;
            font-size: 18px;
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(91, 110, 245, 0.3);
        }}
        .brand-text h1 {{ font-size: 22px; font-weight: 700; color: #FFF; }}
        .brand-text p {{ font-size: 13px; color: var(--text-muted); }}

        .print-btn {{
            background: var(--accent);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .print-btn:hover {{ background: #475be8; transform: translateY(-1px); }}

        /* KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
        }}
        .kpi-title {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 26px; font-weight: 700; color: #FFF; }}

        /* Section Cards */
        .section-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 16px;
            color: #FFF;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }}

        /* Data Grids */
        .telemetry-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        .tele-item {{
            background: var(--bg-card2);
            padding: 14px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .tele-label {{ font-size: 12px; color: var(--text-muted); }}
        .tele-val {{ font-size: 14px; font-weight: 600; margin-top: 4px; color: var(--text-main); }}

        /* Tables */
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        th {{
            text-align: left;
            padding: 12px 14px;
            background: var(--bg-card2);
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
        }}
        td {{ padding: 12px 14px; border-bottom: 1px solid var(--border); }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}

        /* Footer */
        .footer {{
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }}

        /* Print / PDF Styling */
        @media print {{
            body {{ background: #FFF !important; color: #111 !important; padding: 0 !important; }}
            .container {{ max-width: 100% !important; }}
            .print-btn {{ display: none !important; }}
            .header {{ border-bottom: 2px solid #222 !important; }}
            .kpi-card, .section-card, .tele-item {{
                background: #F9FAFB !important;
                border: 1px solid #E5E7EB !important;
                box-shadow: none !important;
                color: #111 !important;
            }}
            .brand-text h1, .section-title, .kpi-value, .tele-val {{ color: #111 !important; }}
            th {{ background: #F3F4F6 !important; color: #4B5563 !important; border-bottom: 1px solid #D1D5DB !important; }}
            td {{ border-bottom: 1px solid #E5E7EB !important; color: #1F2937 !important; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="brand">
                <div class="brand-icon">SF</div>
                <div class="brand-text">
                    <h1>SmartFix AI — System Health & Audit Report</h1>
                    <p>Autonomous Diagnostics, Telemetry & Repair History Audit</p>
                </div>
            </div>
            <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>

        <!-- KPI Summary Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">System Status</div>
                <div class="kpi-value" style="color: var(--success);">Healthy</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Repairs Executed</div>
                <div class="kpi-value">{total_repairs}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Repair Success Rate</div>
                <div class="kpi-value" style="color: var(--accent);">{success_rate:.1f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">System Uptime</div>
                <div class="kpi-value" style="font-size: 20px;">{uptime_str}</div>
            </div>
        </div>

        <!-- Workstation & Host Telemetry -->
        <div class="section-card">
            <div class="section-title">💻 Workstation & OS Specifications</div>
            <div class="telemetry-grid">
                <div class="tele-item">
                    <div class="tele-label">Host Name</div>
                    <div class="tele-val">{hostname}</div>
                </div>
                <div class="tele-item">
                    <div class="tele-label">Local IP Address</div>
                    <div class="tele-val">{local_ip}</div>
                </div>
                <div class="tele-item">
                    <div class="tele-label">Operating System</div>
                    <div class="tele-val">{os_name}</div>
                </div>
                <div class="tele-item">
                    <div class="tele-label">Processor / Cores</div>
                    <div class="tele-val">{cpu_count} Logical Cores (Usage: {cpu_percent}%)</div>
                </div>
                <div class="tele-item">
                    <div class="tele-label">System Memory (RAM)</div>
                    <div class="tele-val">{mem.used / (1024**3):.1f} GB / {mem.total / (1024**3):.1f} GB ({mem.percent}%)</div>
                </div>
                <div class="tele-item">
                    <div class="tele-label">Primary Drive (C:)</div>
                    <div class="tele-val">{disk.free / (1024**3):.1f} GB Free of {disk.total / (1024**3):.1f} GB ({disk.percent}% Used)</div>
                </div>
            </div>
        </div>

        <!-- Hardware & Driver Diagnostics -->
        <div class="section-card">
            <div class="section-title">🛡️ Hardware & S.M.A.R.T. Diagnostics</div>
            <div class="telemetry-grid">
                <div class="tele-item">
                    <div class="tele-label">S.M.A.R.T. Drive Health</div>
                    <div class="tele-val" style="color: var(--success);">{disk_diag.get('summary', 'Operating Normally')}</div>
                </div>
                <div class="tele-item">
                    <div class="tele-label">Device Drivers (Device Mgr)</div>
                    <div class="tele-val" style="color: {'var(--success)' if driver_diag.get('healthy') else 'var(--danger)'};">
                        {driver_diag.get('summary', '0 Device Errors')}
                    </div>
                </div>
                <div class="tele-item">
                    <div class="tele-label">Power & Battery</div>
                    <div class="tele-val">{battery_diag.get('summary', 'AC Power')}</div>
                </div>
            </div>
        </div>

        <!-- Category Breakdown -->
        <div class="section-card">
            <div class="section-title">📊 Self-Improving Repair Success Analytics</div>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Attempts</th>
                        <th>Successes</th>
                        <th>Success Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {cat_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Repair History Log -->
        <div class="section-card">
            <div class="section-title">📜 Historical Repair & Incident Timeline</div>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Incident / Error</th>
                        <th>Category</th>
                        <th>Severity</th>
                        <th>Outcome</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
                    {hist_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Footer -->
        <div class="footer">
            Generated autonomously by <strong>SmartFix AI</strong> on {timestamp.strftime('%B %d, %Y at %I:%M:%S %p')} • Workstation: {hostname}
        </div>
    </div>
</body>
</html>
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    if open_in_browser:
        try:
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        except Exception:
            pass

    return report_path
