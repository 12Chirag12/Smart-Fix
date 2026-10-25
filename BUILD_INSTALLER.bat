@echo off
title SmartFix AI - Build Installer
color 0A

echo.
echo  ==========================================
echo   SmartFix AI v1.1.0 -- Installer Builder
echo  ==========================================
echo.

:: Check if Inno Setup is installed -- auto download if missing
set "ISCC="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo  [INFO] Inno Setup 6 not found. Attempting winget or direct download...
    winget install JRsoftware.InnoSetup --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo  [INFO] Downloading installer from official source...
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri 'https://jrsoftware.org/download.php/is.exe' -OutFile '%TEMP%\innosetup.exe' -UseBasicParsing"
    echo  [INFO] Installing Inno Setup 6...
    "%TEMP%\innosetup.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
    del /f /q "%TEMP%\innosetup.exe" 2>nul

    if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

    if "%ISCC%"=="" (
        echo  [ERROR] Inno Setup install failed. Please download manually from:
        echo  https://jrsoftware.org/isdl.php
        pause
        exit /b 1
    )
    echo  [OK] Inno Setup installed.
)

echo  [OK] Inno Setup found: %ISCC%
echo.

:: Create output directories
if not exist "dist\installer" mkdir "dist\installer"
if not exist "data"           mkdir "data"
if not exist "logs"           mkdir "logs"

echo  [*] Building installer...
echo.
"%ISCC%" "SmartFix_Installer.iss"

if %ERRORLEVEL%==0 (
    echo.
    echo  ==========================================
    echo   SUCCESS! Installer created at:
    echo   dist\installer\SmartFix_Setup.exe
    echo  ==========================================
    echo.
    echo  The installer will automatically install:
    echo    1. Visual C++ Redistributable 2022
    echo    2. Python 3.11.9 - auto-installed if missing
    echo    3. PyQt6, psutil, httpx, pywin32, WMI
    echo    4. Ollama AI engine
    echo    5. llama3 AI model - auto-downloaded
    echo    6. Windows Firewall rules for Lab Monitor
    echo    7. Auto-start with Windows [optional]
    echo.
    echo  Estimated install time: 10-30 min depending on internet speed
    echo.
    start "" "dist\installer"
) else (
    echo.
    echo  [ERROR] Build FAILED. Check the output above.
    echo.
)
pause
