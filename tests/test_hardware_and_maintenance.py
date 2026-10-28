"""
Tests for Hardware Diagnostics & Preventive Maintenance Modules.
"""
import unittest
from monitor.hardware_diag import check_disk_smart_health, check_driver_health, check_battery_health, run_full_hardware_diagnostics
from monitor.maintenance import get_maintenance_status, ROUTINE_TASKS, DEEP_TASKS


class TestHardwareAndMaintenance(unittest.TestCase):

    def test_hardware_diagnostics_structure(self):
        hw = run_full_hardware_diagnostics()
        self.assertIn("healthy", hw)
        self.assertIn("status", hw)
        self.assertIn("disk", hw)
        self.assertIn("driver", hw)
        self.assertIn("battery", hw)

        self.assertIn("summary", hw["disk"])
        self.assertIn("summary", hw["driver"])
        self.assertIn("summary", hw["battery"])

    def test_maintenance_tasks_defined(self):
        self.assertTrue(len(ROUTINE_TASKS) >= 2)
        self.assertTrue(len(DEEP_TASKS) >= 2)
        status = get_maintenance_status()
        self.assertIn("last_status", status)
        self.assertIn("next_scheduled", status)


if __name__ == "__main__":
    unittest.main()
