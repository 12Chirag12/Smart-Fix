# ============================================================================
# SmartFix AI — Full Dependency Installer
# Run by the Inno Setup installer post-copy, as Administrator.
# ============================================================================
param (
    [string]$InstallDir = "C:\Program Files\SmartFix AI"
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"

$LogFile = "$InstallDir\install_log.txt"

function Write-Log($msg) {
    $ts = (Get-Date -Format "HH:mm:ss")
    $line = "[$ts] $msg"
    try { Add-Content -Path $LogFile -Value $line -Encoding UTF8 } catch {}
    Write-Host $line
}

function Invoke-DownloadWithRetry($Url, $OutFile, $Description, $Retries = 3) {
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            Write-Log "  Downloading $Description (attempt $i)..."
            Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -TimeoutSec 120
            Write-Log "  Download complete: $Description"
            return
        } catch {
            Write-Log "  Attempt $i failed: $_"
            if ($i -lt $Retries) { Start-Sleep -Seconds 3 }
        }
    }
    throw "Failed to download $Description after $Retries attempts."
}

Write-Log "=== SmartFix AI Installation Started ==="
Write-Log "Install directory: $InstallDir"

@("$InstallDir\data", "$InstallDir\logs", "$InstallDir\monitor") | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

# STEP 1: Visual C++ Redistributable 2015-2022 (required by pywin32 + Qt6)
Write-Log "--- STEP 1: Visual C++ Redistributable ---"
$vcInstalled = $false
try {
    @(
        "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
    ) | ForEach-Object {
        if (Test-Path $_) {
            if ((Get-ItemProperty $_ -EA SilentlyContinue).Installed -eq 1) { $vcInstalled = $true }
        }
    }
} catch {}

if (-not $vcInstalled) {
    $vcExe = "$env:TEMP\vc_redist.x64.exe"
    Invoke-DownloadWithRetry "https://aka.ms/vs/17/release/vc_redist.x64.exe" $vcExe "Visual C++ Redistributable"
    Start-Process -FilePath $vcExe -ArgumentList "/quiet /norestart" -Wait -NoNewWindow
    Remove-Item $vcExe -Force -EA SilentlyContinue
    Write-Log "  Visual C++ Redistributable installed."
} else { Write-Log "  Visual C++ Redistributable already installed." }

# STEP 2: Python 3.11
Write-Log "--- STEP 2: Python 3.11 ---"
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" + $env:PATH

$pythonExe = $null
@("python",
  "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
  "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
  "C:\Python311\python.exe",
  "C:\Program Files\Python311\python.exe"
) | ForEach-Object {
    if (-not $pythonExe) {
        try {
            $v = & $_ --version 2>&1
            if ("$v" -match "Python 3\.(1[01])") { $pythonExe = $_; Write-Log "  Found: $v at $_" }
        } catch {}
    }
}

if (-not $pythonExe) {
    $pyExe = "$env:TEMP\python-3.11.9-amd64.exe"
    Invoke-DownloadWithRetry "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" $pyExe "Python 3.11.9"
    Write-Log "  Installing Python 3.11.9..."
    Start-Process -FilePath $pyExe `
        -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0 Include_launcher=0" `
        -Wait -NoNewWindow
    Remove-Item $pyExe -Force -EA SilentlyContinue
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" + $env:PATH
    $pythonExe = "python"
    Write-Log "  Python installed: $(& python --version 2>&1)"
}

# STEP 3: Upgrade pip
Write-Log "--- STEP 3: Upgrading pip ---"
& $pythonExe -m pip install --upgrade pip --quiet --no-warn-script-location 2>&1 | Out-Null
Write-Log "  pip upgraded."

# STEP 4: Python packages
Write-Log "--- STEP 4: Installing Python packages ---"
$packages = @(
    "PyQt6>=6.6.1",
    "PyQt6-Qt6>=6.6.1",
    "PyQt6-sip>=13.6.0",
    "psutil>=5.9.8",
    "httpx>=0.27.0",
    "pywin32>=306",
    "WMI>=1.5.1",
    "Pillow>=10.3.0",
    "pystray>=0.19.5",
    "plyer>=2.1.0"
)
foreach ($pkg in $packages) {
    Write-Log "  Installing $pkg..."
    $out = & $pythonExe -m pip install "$pkg" --quiet --no-warn-script-location 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "  WARNING: $pkg returned exit code $LASTEXITCODE. Output: $out"
    } else { Write-Log "  OK: $pkg" }
}

# Run pywin32 post-install (needed for Windows COM/registry integration)
Write-Log "  Running pywin32 post-install script..."
try {
    $scriptsDir = & $pythonExe -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>&1
    $postScript = "$scriptsDir\pywin32_postinstall.py"
    if (Test-Path $postScript) {
        & $pythonExe $postScript -install 2>&1 | Out-Null
        Write-Log "  pywin32 post-install done."
    }
} catch { Write-Log "  pywin32 post-install skipped." }
Write-Log "  All Python packages installed."

# STEP 5: Ollama
Write-Log "--- STEP 5: Ollama AI Engine ---"
$ollamaBin = $null
@(
    "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
    "$env:ProgramFiles\Ollama\ollama.exe",
    "ollama"
) | ForEach-Object {
    if (-not $ollamaBin) {
        try {
            $v = & $_ --version 2>&1
            if ("$v" -match "ollama") { $ollamaBin = $_; Write-Log "  Ollama found: $v at $_" }
        } catch {}
    }
}

if (-not $ollamaBin) {
    $ollamaExe = "$env:TEMP\OllamaSetup.exe"
    Invoke-DownloadWithRetry "https://ollama.com/download/OllamaSetup.exe" $ollamaExe "Ollama installer"
    Write-Log "  Installing Ollama..."
    Start-Process -FilePath $ollamaExe -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" -Wait -NoNewWindow
    Remove-Item $ollamaExe -Force -EA SilentlyContinue
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" + $env:PATH
    $ollamaBin = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (-not (Test-Path $ollamaBin)) { $ollamaBin = "ollama" }
    Write-Log "  Ollama installed."
}

# STEP 6: Start Ollama service
Write-Log "--- STEP 6: Starting Ollama service ---"
Get-Process -Name "ollama" -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
Start-Sleep -Seconds 2
Start-Process -FilePath $ollamaBin -ArgumentList "serve" -WindowStyle Hidden -EA SilentlyContinue

Write-Log "  Waiting for Ollama to start (up to 60s)..."
$ollamaReady = $false
for ($i = 1; $i -le 20; $i++) {
    Start-Sleep -Seconds 3
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:11434/" -UseBasicParsing -TimeoutSec 3 -EA SilentlyContinue
        if ($r.StatusCode -eq 200) { $ollamaReady = $true; Write-Log "  Ollama ready."; break }
    } catch {}
    Write-Log "  Waiting... ($($i*3)s)"
}
if (-not $ollamaReady) {
    Write-Log "  WARNING: Ollama did not respond. AI features may need manual start of Ollama."
}

# STEP 7: Pull llama AI model
Write-Log "--- STEP 7: Local AI Model (llama3.2:1b) ---"
$targetModel = "llama3.2:1b"
if ($ollamaReady) {
    $hasModel = $false
    try {
        $tags = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5
        $hasModel = (($tags.Content | ConvertFrom-Json).models | Where-Object { $_.name -like "llama*" }).Count -gt 0
    } catch {}

    if (-not $hasModel) {
        Write-Log "  Pulling $targetModel (high-performance 1.3 GB local LLM)..."
        $pullLog = "$InstallDir\logs\ollama_pull.log"
        $pullErrLog = "$InstallDir\logs\ollama_pull_err.log"
        $pullJob = Start-Process -FilePath $ollamaBin -ArgumentList "pull $targetModel" `
            -RedirectStandardOutput $pullLog -RedirectStandardError $pullErrLog `
            -PassThru -WindowStyle Hidden -EA SilentlyContinue
        
        # Wait up to 15 minutes
        $timeout = 900; $elapsed = 0
        while ($pullJob -and -not $pullJob.HasExited -and $elapsed -lt $timeout) {
            Start-Sleep -Seconds 10; $elapsed += 10
            Write-Log "  Pulling $targetModel... ($elapsed s / $timeout s)"
        }
        if ($pullJob -and $pullJob.HasExited -and $pullJob.ExitCode -eq 0) {
            Write-Log "  $targetModel downloaded successfully."
        } elseif ($pullJob -and -not $pullJob.HasExited) {
            $pullJob.Kill()
            Write-Log "  WARNING: Model pull timed out. Run 'ollama pull $targetModel' manually after install."
        } else {
            Write-Log "  WARNING: Model pull may have failed. Check $pullErrLog"
        }
    } else { Write-Log "  Local AI model already present in Ollama." }
} else { Write-Log "  Skipping model pull (Ollama not running). Run 'ollama pull $targetModel' manually." }

# STEP 8: Windows Firewall rules for Lab Monitor (ports 7771 TCP, 7772 UDP)
Write-Log "--- STEP 8: Firewall rules for Lab Monitor ---"
$fwRules = @(
    @{ Name="SmartFix-Lab-TCP-7771-In";  Dir="Inbound";  Proto="TCP"; Port=7771 },
    @{ Name="SmartFix-Lab-TCP-7771-Out"; Dir="Outbound"; Proto="TCP"; Port=7771 },
    @{ Name="SmartFix-Lab-UDP-7772-In";  Dir="Inbound";  Proto="UDP"; Port=7772 },
    @{ Name="SmartFix-Lab-UDP-7772-Out"; Dir="Outbound"; Proto="UDP"; Port=7772 }
)
foreach ($r in $fwRules) {
    try {
        if (-not (Get-NetFirewallRule -DisplayName $r.Name -EA SilentlyContinue)) {
            if ($r.Dir -eq "Inbound") {
                New-NetFirewallRule -DisplayName $r.Name -Direction Inbound  -Protocol $r.Proto -LocalPort  $r.Port -Action Allow -Profile Any | Out-Null
            } else {
                New-NetFirewallRule -DisplayName $r.Name -Direction Outbound -Protocol $r.Proto -RemotePort $r.Port -Action Allow -Profile Any | Out-Null
            }
            Write-Log "  Firewall rule added: $($r.Name)"
        } else { Write-Log "  Firewall rule exists: $($r.Name)" }
    } catch { Write-Log "  WARNING: Firewall rule failed: $($r.Name) — $_" }
}

# STEP 9: Register background auto-start on PC boot
Write-Log "--- STEP 9: Background Auto-start on Boot ---"
$appExe = "$InstallDir\SmartFix AI.exe"

# 9A: Elevated Windows Task Scheduler task (Runs silently with highest privileges at logon, no UAC prompts)
try {
    $schCmd = "schtasks.exe /Create /TN `"SmartFix AI Autostart`" /TR `"\`"$appExe\`" --background`" /SC ONLOGON /RL HIGHEST /F"
    Invoke-Expression $schCmd | Out-Null
    Write-Log "  Task Scheduler autostart registered (ONLOGON /RL HIGHEST)."
} catch {
    Write-Log "  WARNING: Task Scheduler registration failed: $_"
}

# 9B: Registry HKLM Run key (Fallback)
try {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" `
        -Name "SmartFix AI" -Value "`"$appExe`" --background" -Force
    Write-Log "  HKLM Run key registered."
} catch {
    Write-Log "  WARNING: HKLM registration failed: $_"
}

# 9C: Startup folder shortcut (User fallback)
try {
    $startupLnk = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\SmartFix AI.lnk"
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($startupLnk)
    $Shortcut.TargetPath = $appExe
    $Shortcut.Arguments = "--background"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "SmartFix AI Background Monitor"
    $Shortcut.Save()
    Write-Log "  Startup folder shortcut created."
} catch {
    Write-Log "  WARNING: Startup folder shortcut failed: $_"
}

Write-Log "=== SmartFix AI installation complete! Log: $LogFile ==="
exit 0
