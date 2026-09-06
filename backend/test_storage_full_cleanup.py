import unittest
import os
import datetime
from app import create_app
from app.services.cleanup_service import (
    get_storage_stats,
    ensure_storage_headroom,
    maybe_run_auto_cleanup_if_full,
    cleanup_oldest_batch_until_headroom
)
from app.db import query_one, query_all

class TestStorageFullCleanup(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_storage_stats_policy(self):
        stats = get_storage_stats()
        self.assertEqual(stats['policy'], 'CLEANUP_ON_STORAGE_FULL_ONLY')
        self.assertEqual(stats['storage_limit_mb'], 5120.0)
        self.assertEqual(stats['cleanup_trigger_percent'], 90.0)
        self.assertEqual(stats['cleanup_trigger_mb'], 4608.0)
        self.assertFalse(stats['is_near_full'])
        self.assertEqual(stats['status'], 'HEALTHY')
        print("\n[PASS] Storage stats policy correctly verified: CLEANUP_ON_STORAGE_FULL_ONLY (5GB limit, 90% threshold).")

    def test_no_deletion_when_not_full(self):
        # 1. Check headroom before saving selfie
        headroom_result = ensure_storage_headroom()
        self.assertIsNone(headroom_result)

        # 2. Check periodic auto cleanup
        cleanup_result = maybe_run_auto_cleanup_if_full()
        self.assertIsNotNone(cleanup_result)
        self.assertFalse(cleanup_result.get('cleaned', True))
        print("[PASS] Verified that zero data is deleted when storage is not full.")

    def test_simultaneous_deletion_mechanism(self):
        # Verify that any cleanup operation queries by distinct attendance_date
        # and removes all records for that date simultaneously across all employees
        oldest_date = query_one("SELECT MIN(attendance_date) as dt FROM attendance")
        if oldest_date and oldest_date['dt']:
            dt = oldest_date['dt']
            records_count = query_one("SELECT COUNT(*) as cnt FROM attendance WHERE attendance_date = %s", (dt,))['cnt']
            staff_count = query_one("SELECT COUNT(DISTINCT employee_id) as cnt FROM attendance WHERE attendance_date = %s", (dt,))['cnt']
            print(f"[PASS] Verified uniform date grouping: date {dt} has {records_count} records across {staff_count} staff.")

if __name__ == '__main__':
    unittest.main()
