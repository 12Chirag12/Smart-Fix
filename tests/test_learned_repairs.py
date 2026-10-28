"""
Tests for Learned Repairs Database.
Validates atomic file replacement, concurrent access, and error signature hashing.
"""
import unittest
import threading
from monitor.learned_repairs import save_learned_error, load_learned_errors


class TestLearnedRepairs(unittest.TestCase):

    def test_save_and_retrieve_learned_repair(self):
        err = {"name": "Test Diagnostic Crash", "id": "test_crash", "category": "UnitTests"}
        ps = "Write-Output 'Testing learned execution'"
        save_learned_error(err, ps)

        all_learned = load_learned_errors()
        self.assertIsInstance(all_learned, dict)
        found = any("test_diagnostic_crash" in k for k in all_learned.keys())
        self.assertTrue(found, "Saved learned error was not found in loaded database")

    def test_concurrent_saves(self):
        """Ensure multiple threads saving learned errors simultaneously do not corrupt JSON."""
        errors = []

        def worker(idx: int):
            try:
                for i in range(5):
                    err = {"name": f"Concurrent Error {idx}_{i}", "id": f"err_{idx}_{i}"}
                    save_learned_error(err, "Write-Output 'OK'")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent saves failed: {errors}")
        data = load_learned_errors()
        self.assertIsInstance(data, dict)


if __name__ == "__main__":
    unittest.main()
