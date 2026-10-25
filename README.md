# 🛡️ SmartFix AI — Autonomous Windows Error Monitor & Lab Auto-Repair

> **Autonomous Windows error detection, diagnosis, and automated repair — powered by Local AI (Qwen / Llama 3) and multi-PC Lab Management.**

SmartFix AI runs silently in the background, monitors your Windows systems for **170+ known errors**, and offers one-click automated PowerShell repairs. For unknown application crashes, it uses a local AI model (**Qwen 3 / Llama 3 via Ollama**) to generate and execute custom PowerShell fixes — which are automatically saved into a self-learning database for future automated reuse.

SmartFix AI is built to operate both as an **individual workstation guardian** and as a **centralized College Computer Lab Monitor (1 Admin PC + N Client PCs)** over local area networks (LAN).

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Real-time Monitoring** | Multi-threaded polling for Windows services, Event Log crashes, CPU/RAM/Disk metrics |
| ⚡ **170+ Deterministic Repairs** | 100% verified PowerShell scripts covering Windows Update, Network, Security, and Storage |
| 🎓 **College Lab Monitor** | 1 Admin PC monitors all student PCs on the LAN with live telemetry and 1-click remote fix |
| 🛠️ **10 Major College Lab Fixes** | USB drive unlock, Task Manager/CMD policy unlock, Proxy reset, XAMPP port 80, MySQL port 3306, compiler PATHs |
| 🤖 **Local AI Diagnosis** | Uses Ollama (`qwen3:4b-instruct` / `llama3.2`) running 100% offline and private |
| 🧠 **Autonomous Self-Learning** | AI-generated fixes are saved into `data/learned_errors.json` and reused automatically |
| 🔔 **Windows 11 Toast Alerts** | Clean slide-in notifications in the bottom-right corner with 30s countdown |
| 🛠 **One-Click Real Repair** | Direct administrative PowerShell execution (`-ExecutionPolicy Bypass`) |
| 📊 **Modern Dark Dashboard** | Real-time hardware gauges, service status, and active error management |
| 🌐 **Network Diagnostics** | Full gateway ping, DNS resolution, and latency diagnostics |
| 📄 **System Health Reports** | Generates exportable, styled HTML diagnostic reports |
| 🎭 **Judge Demo Mode** | Safely simulates real Windows errors to demonstrate detection → alert → repair flow |

---

## 🚀 Quick Install (End Users & Lab Setup)

1. Run **`SmartFix_Setup.exe`** from `dist\installer\` 
2. The installer automatically downloads and silently provisions:
   - Visual C++ 2015–2022 Redistributable (x64)
   - Python 3.11.9 (with PATH configured)
   - All libraries (`PyQt6`, `psutil`, `httpx`, `pywin32`, `WMI`, `Pillow`, `pystray`, `plyer`)
   - Ollama AI engine & local LLM model
   - Windows Defender Firewall rules for Lab Monitor (TCP 7771, UDP 7772)
   - Windows auto-start on boot
3. SmartFix AI launches automatically and runs in the Windows System Tray.

---

## 🖥️ Computer Lab Monitor (Dynamic Admin & Workstation Setup)

SmartFix AI uses the **exact same installer** across all computers in the local network:

1. **Any PC can be Admin (Central Controller)**:
   - Go to **🖥 Lab Monitor** in the sidebar.
   - Click **`🛡 Set as Admin (Central Controller)`** or use **`⇄ Switch Role`**.
   - Authenticate with the Admin Passkey.
   - The dashboard opens the Lab Central Controller, listening for workstations and displaying live telemetry.

2. **Any PC can be a Client (Workstation)**:
   - Go to **🖥 Lab Monitor** in the sidebar.
   - Click **`💻 Set as Client (Workstation)`**.
   - Enter a unique seat name (defaults to `PC-<HOSTNAME>`).
   - The workstation automatically broadcasts its presence and telemetry on the LAN (UDP 7772).

3. **Dynamic Role Switching & Demotion**:
   - An Admin PC can switch back to Client mode at any time using **`💻 Switch this PC to Client`** or **`⇄ Switch Role`** (requires admin passkey).
   - A Client PC can be promoted to Admin anytime by clicking **`🛡 Promote this PC to Admin`** and entering the Admin Passkey.

4. **Passkey Management & Authentication**:
   - Remote repairs and admin elevation are secured with SHA-256 passkey verification.
   - Change the passkey at any time via the **`🔑 Passkey`** button on the Lab Monitor header.

5. **Remote Diagnostic & One-Click Repair**:
   - If any workstation PC encounters an issue, its card flags the error on the Admin's screen.
   - The administrator clicks **`🔧 Fix Remotely`** or uses the on-demand maintenance toolbox to execute authenticated repairs over TCP 7771.

---

## 🏗 Project Architecture

```
SmartFix-AI/
├── smartfix_app.py          ← Main application (PyQt6 UI + system tray + lab page)
├── SmartFix AI.exe          ← C# .NET launcher stub with UAC administrator manifest
├── BUILD_INSTALLER.bat      ← 1-Click Inno Setup builder script
├── SmartFix_Installer.iss   ← Inno Setup configuration script
├── install_helper.ps1       ← Silent dependency installer (Python, Ollama, model, firewall)
├── requirements.txt         ← Python dependencies
├── monitor/
│   ├── monitor.py           ← Multi-threaded background monitoring engine
│   ├── error_catalog.py     ← 170 Windows error definitions
│   ├── repair_engine.py     ← 100% verified PowerShell repair functions
│   ├── repair_advanced.py   ← BCD, bootmgr, WMI salvage, and registry repairs
│   ├── difficult_errors.py  ← BSOD bugcheck analyzers & crash dump definitions
│   ├── lab_config.py        ← LAN protocol (JSON framing), ports (7771, 7772), config
│   ├── lab_agent.py         ← Client Agent: UDP 7772 broadcaster & TCP 7771 listener
│   ├── lab_admin.py         ← Admin Manager: discovery listener, polling & remote fix
│   ├── llm_assistant.py     ← Ollama local AI client (dynamic model detection + fallback)
│   ├── learned_repairs.py   ← Self-learning database manager (learned_errors.json)
│   ├── ai_dialog.py         ← Interactive AI technical assistant dialog
│   ├── demo_mode.py         ← Safe error simulation engine for judge presentations
│   ├── history.py           ← SQLite database logger (smartfix_history.db)
│   └── network_diag.py      ← Network ping, DNS, and latency tests
└── data/
    ├── smartfix_history.db  ← SQLite database of repair history
    ├── learned_errors.json  ← Persisted AI-learned repairs
    └── lab_config.json      ← Persistent lab seat name and role
```

---

## 📦 Building the Installer

```bat
# Requires Inno Setup 6 (auto-detected in AppData or Program Files)
BUILD_INSTALLER.bat
# Output: dist\installer\SmartFix_Setup.exe
```

---

## 🎓 Academic Project

Developed as a **B.E. Final Year Major Project** — *Autonomous Windows System Administration and Multi-PC Lab Monitor with Local LLM Self-Learning*.

---

## 📄 License

Copyright (c) 2026 Chirag Patil. Released under the [MIT License](LICENSE).
