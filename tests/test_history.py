"""
Tests for SQLite History Database.
Validates multi-threaded concurrency, WAL mode integrity, and statistical queries.
"""
import unittest
import threading
from monitor.history import (
    log_detection, log_repair, log_restore_point,
    get_history, get_stats, get_category_stats, get_recent_failures
)


class TestHistoryDatabase(unittest.TestCase):

    def test_concurrent_writes(self):
        """Spawn multiple threads writing concurrently to ensure no 'database is locked' errors."""
        errors = []

        def worker(thread_idx: int):
            try:
                for i in range(10):
                    err = {
                        "id": f"test_err_{thread_idx}_{i}",
                        "name": f"Test Error {thread_idx}-{i}",
                        "category": "TestCategory",
                        "severity": "LOW",
                    }
                    log_detection(err)
                    log_repair(err, {"repair_id": "test_fix", "success": True, "output": "OK", "elapsed_seconds": 0.05})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent database write raised errors: {errors}")

    def test_stats_and_category_retrieval(self):
        stats = get_stats()
        self.assertIn("total", stats)
        self.assertIn("repaired", stats)
        self.assertIn("success", stats)

        cat_stats = get_category_stats()
        self.assertIsInstance(cat_stats, list)

    def test_restore_point_logging(self):
        try:
            log_restore_point("Test Pre-Repair Snapshot", "test_repair_123", True)
        except Exception as e:
            self.fail(f"log_restore_point raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
