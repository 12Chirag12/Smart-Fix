# SmartFix AI: Intelligent Windows Troubleshooting System

SmartFix AI is a final-year B.Tech project that aims to make Windows troubleshooting easier through system-data collection, explainable rule-based analysis, AI-assisted diagnosis, and controlled repair workflows.

This repository currently contains a **small, read-only demonstration prototype**. It implements only this part of the planned architecture:

> System Collection → Rule-Based Diagnosis → Recommendation

It does not modify Windows, run repairs, edit the registry, or execute PowerShell commands.

## Current prototype features

- Modern dark desktop interface built with CustomTkinter
- CPU, RAM, and Windows-drive health cards
- Windows version, computer name, CPU/core, memory, and disk information
- Local network-adapter and IPv4 status
- List of the top running processes by memory use
- Read-only status checks for selected Windows services when available
- Explainable rules for high CPU, high RAM, low available memory, a nearly full disk, and unavailable networking
- Severity, possible cause, and recommended action for every detected issue
- Temporary simulated AI explanation with no API key required
- Error isolation so one unavailable data source does not stop the whole scan

## Project files

```text
SmartFix-AI/
├── main.py               # CustomTkinter desktop interface
├── system_collector.py   # Read-only Windows data collection
├── diagnosis_engine.py   # Rules and temporary AI explanations
├── requirements.txt      # Python packages
└── README.md              # Setup and project notes
```

## Installation

Requirements:

- Windows 10 or Windows 11
- Python 3.10 or newer
- VS Code with the Python extension (recommended)

Open the project folder in VS Code. In **Terminal → New Terminal**, create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the two dependencies:

```powershell
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, the prototype can still be run by selecting `.venv\Scripts\python.exe` as the VS Code Python interpreter and using the Run button.

## Run the prototype

From the project directory:

```powershell
python main.py
```

Then:

1. Select **Scan My PC** to collect a fresh system snapshot and run the rules.
2. Review the CPU, RAM, and disk health cards.
3. Review detected problems, possible causes, severity, simulated AI insight, and recommended fixes.
4. Select **View System Info** to show detailed system, network, service, and process information.
5. Select **Diagnose Problems** to rerun the rules on the latest snapshot.

## Rule thresholds

| Condition | Detected problem |
|---|---|
| CPU usage above 85% | High CPU Usage |
| RAM usage above 85% | High Memory Usage |
| Available RAM below 1 GB | Very Low Available Memory |
| Windows disk usage above 90% | Disk Almost Full |
| No active adapter with a normal local IPv4 address | Network Unavailable |
| DHCP Client or DNS Client is reported stopped | Essential Network Service Stopped |

## Current limitations

- The rules use one point-in-time snapshot and are intentionally simple.
- Network availability is inferred from local adapter state; the prototype does not contact the internet.
- Service details may be unavailable because of Windows permissions or platform support.
- The AI explanation is predefined text, not a real language model response.
- The application recommends actions but never executes repairs.
- There is no event-log analysis, history database, authentication, installer, or background monitoring yet.

## Planned next phases

The complete project architecture is planned as:

> User Reports Problem → System Data Collection → Rule-Based Analysis → AI/LLM Diagnosis → Recommended Repair → User Approval → Repair Execution → Post-Repair Verification

Future modules will include:

- Windows Event Log analysis
- WMI integration for deeper hardware, driver, and operating-system details
- AI diagnosis using a local Ollama/Qwen model
- Correlation between user-reported symptoms, system data, and event logs
- Controlled repair engine with allow-listed actions
- Clear user approval before every system change
- Logging, rollback planning, and safety controls
- Post-repair verification and before/after health comparison

## Suggested progress-demo talking points

**Completed:** modular system collection, explainable rule engine, professional prototype GUI, diagnosis severity, safe recommendations, simulated AI text, and basic error handling.

**Under development:** broader diagnostic rules, more accurate process analysis, Windows service coverage, user problem input, and scan-history storage.

**Next phase:** Event Log and WMI collectors, real local LLM integration through Ollama/Qwen, then a permission-controlled repair-and-verification workflow.

> Safety note: This prototype is diagnostic and read-only. Recommendations should still be reviewed before a user performs them manually.
