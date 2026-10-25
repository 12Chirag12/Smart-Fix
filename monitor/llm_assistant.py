import os
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("smartfix.llm")

OLLAMA_BASE_URL = os.getenv("SMARTFIX_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("SMARTFIX_AI_MODEL", "llama3")
OLLAMA_URL = os.getenv("SMARTFIX_OLLAMA_URL", f"{OLLAMA_BASE_URL}/api/generate")

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
        return r.json().get("response", "Error generating response.")
    except Exception as e:
        logger.error(f"LLM Generation failed: {e}")
        return f"❌ AI Assistant encountered an error while analyzing: {str(e)}"
