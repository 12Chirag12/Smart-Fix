@echo off
title SmartFix AI
echo.
echo  =====================================================
echo    SmartFix AI -- AI-Powered Windows Error Monitor
echo  =====================================================
echo.

:: Auto-elevate to Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo  [OK] Running as Administrator
cd /d "%~dp0"

:: Start Ollama in background if not already running
echo  [*] Checking Ollama AI engine...
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if errorlevel 1 (
    echo  [*] Starting Ollama service...
    where ollama >nul 2>&1
    if not errorlevel 1 (
        start /b "" ollama serve >nul 2>&1
    ) else (
        set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
        if exist "%OLLAMA_EXE%" (
            start /b "" "%OLLAMA_EXE%" serve >nul 2>&1
        )
    )
    echo  [*] Waiting for Ollama to start...
    timeout /t 5 /nobreak >nul
) else (
    echo  [OK] Ollama already running.
)

echo  [*] Launching SmartFix AI...
echo.

:: Check local virtual environment first (.venv)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" smartfix_app.py
    goto :check_error
)

:: Try finding python
where python >nul 2>&1
if not errorlevel 1 (
    python smartfix_app.py
    goto :check_error
)

:: Try common Python locations
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if exist "%PY%" ( "%PY%" smartfix_app.py & goto :check_error )
set "PY=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if exist "%PY%" ( "%PY%" smartfix_app.py & goto :check_error )
set "PY=C:\Python311\python.exe"
if exist "%PY%" ( "%PY%" smartfix_app.py & goto :check_error )

echo  [ERROR] Python not found. Please run SmartFix_Setup.exe to install dependencies.
pause
exit /b 1

:check_error
if %errorLevel% neq 0 (
    echo.
    echo  [ERROR] SmartFix AI exited with an error (code %errorLevel%).
    echo  Check install_log.txt in the SmartFix AI folder.
    echo  Or reinstall using SmartFix_Setup.exe
    pause
)
