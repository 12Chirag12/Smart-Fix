"""
Tests for Repair Engine.
Validates handler dispatch, escalation chains, verification definitions, and error handling.
"""
import unittest
from monitor.repair_engine import (
    REPAIR_FUNCTIONS, REPAIR_VERIFIERS, ESCALATION_CHAINS,
    execute_repair
)


class TestRepairEngine(unittest.TestCase):

    def test_verifiers_registered_for_core_services(self):
        core_repairs = [
            "restart_windows_update",
            "flush_dns_and_renew",
            "restart_audio_service",
            "restart_print_spooler",
        ]
        for r_id in core_repairs:
            self.assertIn(r_id, REPAIR_VERIFIERS, f"Core repair '{r_id}' missing post-repair verifier")
            v = REPAIR_VERIFIERS[r_id]
            self.assertIn("cmd", v)
            self.assertIn("expect", v)

    def test_escalation_chains_configured(self):
        self.assertIn("restart_windows_update", ESCALATION_CHAINS)
        self.assertIn("flush_dns_and_renew", ESCALATION_CHAINS)
        self.assertIn("run_sfc_scannow", ESCALATION_CHAINS)
        # Escalations must point to existing handlers
        for primary, chain in ESCALATION_CHAINS.items():
            self.assertIsInstance(chain, list)
            for esc_id in chain:
                self.assertIn(esc_id, REPAIR_FUNCTIONS, f"Escalation target '{esc_id}' not in REPAIR_FUNCTIONS")

    def test_unknown_repair_graceful_failure(self):
        result = execute_repair("completely_nonexistent_repair_xyz_999", enable_retry=False, enable_restore=False)
        self.assertFalse(result["success"])
        self.assertIn("No repair handler", result["message"])


if __name__ == "__main__":
    unittest.main()
