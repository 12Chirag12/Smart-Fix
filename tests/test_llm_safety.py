"""
Tests for LLM AI Script Safety Sandbox.
Ensures destructive commands are strictly blocked while benign repair scripts pass.
"""
import unittest
from monitor.llm_assistant import validate_ai_script


class TestLLMSafetySandbox(unittest.TestCase):

    def test_safe_script_passes(self):
        script = "Start-Service -Name wuauserv; (Get-Service wuauserv).Status"
        is_safe, msg, warnings = validate_ai_script(script)
        self.assertTrue(is_safe, f"Safe script was incorrectly blocked: {msg}")

    def test_format_volume_blocked(self):
        script = "Format-Volume -DriveLetter C -Full"
        is_safe, msg, warnings = validate_ai_script(script)
        self.assertFalse(is_safe, "Destructive Format-Volume was not blocked!")

    def test_recursive_root_deletion_blocked(self):
        scripts = [
            "Remove-Item C:\\ -Recurse -Force",
            "del /s /q C:\\",
            "rd /s /q C:\\Windows",
        ]
        for s in scripts:
            is_safe, msg, warnings = validate_ai_script(s)
            self.assertFalse(is_safe, f"Dangerous command '{s}' was not blocked!")

    def test_destructive_system_controls_blocked(self):
        scripts = [
            "Stop-Computer -Force",
            "Restart-Computer -Force",
            "net user Administrator /delete",
        ]
        for s in scripts:
            is_safe, msg, warnings = validate_ai_script(s)
            self.assertFalse(is_safe, f"System altering command '{s}' was not blocked!")


if __name__ == "__main__":
    unittest.main()
