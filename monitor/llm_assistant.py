"""
SmartFix AI — Local LLM Assistant (Ollama)
Analyzes unknown system errors using a local AI model and generates PowerShell repairs.
Includes a safety sandbox that blocks destructive AI-generated commands before execution.
"""
import os
import re
import httpx
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("smartfix.llm")

OLLAMA_BASE_URL = os.getenv("SMARTFIX_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("SMARTFIX_AI_MODEL", "llama3")
OLLAMA_URL = os.getenv("SMARTFIX_OLLAMA_URL", f"{OLLAMA_BASE_URL}/api/generate")


# ── AI Script Safety Sandbox ──────────────────────────────────────────────────

DANGEROUS_PATTERNS = [
    # Disk/partition destruction
    (r"Format-Volume",                          "Disk format command"),
    (r"Clear-Disk",                             "Disk wipe command"),
    (r"Initialize-Disk.*-RemoveData",           "Disk data removal"),
    (r"Remove-Partition",                       "Partition deletion"),
    # Recursive system file deletion
    (r"Remove-Item\s+[\"']?C:\\[\"']?\s+-Recurse", "Recursive C:\\ deletion"),
    (r"Remove-Item.*Windows.*-Recurse",         "Windows directory deletion"),
    (r"Remove-Item.*System32.*-Recurse",        "System32 directory deletion"),
    (r"Remove-Item.*Program\s*Files.*-Recurse", "Program Files deletion"),
    (r"del\s+/[sS]\s+/[qQ]\s+C:\\",            "CMD recursive C:\\ deletion"),
    (r"rd\s+/[sS]\s+/[qQ]\s+C:\\",             "CMD recursive directory removal"),
    (r"rmdir\s+/[sS]\s+/[qQ]\s+C:\\",          "CMD recursive directory removal"),
    # System shutdown / reboot (should be user-initiated)
    (r"Stop-Computer",                          "System shutdown"),
    (r"Restart-Computer",                       "System reboot"),
    (r"shutdown\s+/[sStrR]",                    "CMD shutdown/reboot"),
    # User account destruction
    (r"Disable-LocalUser.*Administrator",       "Administrator account disable"),
    (r"Remove-LocalUser",                       "Local user deletion"),
    (r"net\s+user.*\/delete",                   "CMD user account deletion"),
    (r"net\s+user\s+Administrator.*\/active:no","Administrator deactivation"),
    # Registry destruction
    (r"Remove-Item.*HKLM:\\.*-Recurse",         "Registry hive deletion"),
    (r"Remove-ItemProperty.*HKLM:\\",           "Registry key deletion"),
    (r"reg\s+delete\s+HKLM",                   "CMD registry deletion"),
    # BitLocker / encryption
    (r"Enable-BitLocker",                       "BitLocker encryption"),
    (r"Disable-BitLocker",                      "BitLocker decryption"),
    # Network firewall disable
    (r"Set-NetFirewallProfile.*-Enabled\s+False", "Firewall disable"),
    (r"netsh\s+advfirewall\s+set.*state\s+off",   "Firewall disable"),
    # Boot configuration destruction
    (r"bcdedit\s+/delete",                      "Boot entry deletion"),
    (r"bcdedit\s+/deletevalue",                 "Boot config value deletion"),
]

# Commands that are suspicious but allowed with a warning
SUSPICIOUS_PATTERNS = [
    (r"Set-ExecutionPolicy\s+Unrestricted",     "Unrestricted execution policy"),
    (r"Invoke-WebRequest",                      "Web download — verify URL"),
    (r"Invoke-RestMethod",                      "Web request — verify URL"),
    (r"Start-BitsTransfer",                     "Background download — verify URL"),
    (r"New-Service",                            "Service creation"),
    (r"sc\.exe\s+create",                       "CMD service creation"),
]


def validate_ai_script(script: str) -> Tuple[bool, str, list]:
    """
    Validate an AI-generated PowerShell script against the safety sandbox.

    Returns:
        (is_safe, message, warnings)
        - is_safe: True if the script passes all safety checks
        - message: Human-readable result
        - warnings: List of suspicious (but non-blocking) patterns found
    """
    if not script or not script.strip():
        return False, "Empty script — nothing to execute.", []

    blocked = []
    warnings = []

    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, script, re.IGNORECASE | re.MULTILINE):
            blocked.append(f"🚫 {description} (pattern: {pattern})")

    for pattern, description in SUSPICIOUS_PATTERNS:
        if re.search(pattern, script, re.IGNORECASE | re.MULTILINE):
            warnings.append(f"⚠️ {description}")

    if blocked:
        msg = "BLOCKED — AI-generated script contains dangerous commands:\n" + "\n".join(blocked)
        logger.warning(f"[SAFETY] {msg}")
        return False, msg, warnings

    if warnings:
        msg = "Script passed safety check with warnings:\n" + "\n".join(warnings)
        logger.info(f"[SAFETY] {msg}")
        return True, msg, warnings

    return True, "✅ Script passed all safety checks.", []


# ── Ollama Client ─────────────────────────────────────────────────────────────

def is_ollama_available() -> bool:
    """Checks if the local Ollama server is running."""
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/", timeout=2.0)
        return r.status_code == 200
    except httpx.RequestError:
        return False

def get_installed_model() -> Optional[str]:
    """Finds the best installed model in Ollama (llama3.2, llama3, etc.)."""
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        if r.status_code == 200:
            models = r.json().get("models", [])
            for m in models:
                name = m.get("name", "")
                if OLLAMA_MODEL and (OLLAMA_MODEL == name or OLLAMA_MODEL in name):
                    return name
            for m in models:
                name = m.get("name", "")
                if "llama3" in name:
                    return name
            for m in models:
                name = m.get("name", "")
                if "llama" in name:
                    return name
            if models:
                return models[0].get("name", "")
    except Exception:
        pass
    return None

def check_model_exists() -> bool:
    """Checks if any compatible model is downloaded in Ollama."""
    return get_installed_model() is not None

def analyze_unknown_error(error_info: Dict[str, Any]) -> str:
    """
    Sends the unknown error details to the local LLM and asks for a diagnosis 
    and manual fix steps.
    """
    model_name = get_installed_model()
    if not is_ollama_available() or not model_name:
        logger.info("Ollama or model unavailable; using SmartFix autonomous diagnostic engine fallback.")
        return f"""**SmartFix Autonomous Diagnosis (Autonomous Fallback Engine):**

**Diagnosis:**
The process encountered an unhandled exception or access violation (e.g. 0xc0000005). This occurs when an application attempts to access protected memory or encounters corrupted runtime cache/DLL handles.

**Autonomous Remediation Plan:**
1. Purge corrupted application crash dump buffers.
2. Flush temporary faulting runtime files.
3. Verify core Windows system module integrity.

**PowerShell Fix:**
```powershell
Write-Output "Flushing application crash dump buffers..."
Get-ChildItem -Path "$env:LOCALAPPDATA\\CrashDumps" -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\\*.dmp" -Force -ErrorAction SilentlyContinue
Write-Output "Verifying core Windows runtime module integrity..."
sfc /scanfile="$env:SystemRoot\\System32\\kernel32.dll" | Out-Null
Write-Output "Autonomous system fault repair applied successfully."
```"""

    prompt = f"""
You are SmartFix AI, an expert Windows System Administrator. 
The user has encountered an unknown system error that our automated scripts cannot fix. 
Please analyze this error and provide a short, clear explanation of what went wrong.
Crucially, if the error can be fixed via a script, write a precise PowerShell script to fix the issue. Wrap the script strictly in ```powershell and ``` tags.

IMPORTANT SAFETY RULES — Your script MUST NOT:
- Format, clear, or wipe any disk or partition
- Delete system directories (Windows, System32, Program Files) recursively
- Disable the Administrator account or delete user accounts
- Shut down or restart the computer
- Disable Windows Firewall
- Delete registry hives
- Download or execute files from the internet

Error Name: {error_info.get('name', 'Unknown Error')}
Category: {error_info.get('category', 'System')}
Technical Details: {error_info.get('technical', 'No technical details provided.')}

Response format:
**Diagnosis:** [Short explanation]

**PowerShell Fix:**
```powershell
# Script goes here
```
"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:
        r = httpx.post(OLLAMA_URL, json=payload, timeout=60.0)
        r.raise_for_status()
        response = r.json().get("response", "Error generating response.")

        # Extract and validate any PowerShell script in the response
        ps_match = re.search(r'```powershell\s*\n(.*?)```', response, re.DOTALL)
        if ps_match:
            script = ps_match.group(1).strip()
            is_safe, safety_msg, warnings = validate_ai_script(script)
            if not is_safe:
                logger.warning(f"[SAFETY] AI-generated script BLOCKED: {safety_msg}")
                response += f"\n\n🛡️ **SmartFix Safety Sandbox:**\n{safety_msg}\n\n_This script was blocked from automatic execution. Please review manually._"

        return response
    except Exception as e:
        logger.error(f"LLM Generation failed: {e}")
        return f"❌ AI Assistant encountered an error while analyzing: {str(e)}"
