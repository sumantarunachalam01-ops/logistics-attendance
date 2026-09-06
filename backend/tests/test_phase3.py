import os
import sys
import unittest
import json

# Set path to include backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import query_one
from app.services.geofence import calculate_haversine_distance, is_within_geofence

class TestPhase3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Login as Admin
        admin_res = cls.client.post('/api/auth/login', json={'identifier': 'admin@logistics.com', 'password': 'admin123'})
        cls.admin_token = json.loads(admin_res.data)['data']['token']
        cls.admin_headers = {'Authorization': f'Bearer {cls.admin_token}'}

        # Login as Staff (Arun Kumar - EMP-1001)
        staff_res = cls.client.post('/api/auth/login', json={'identifier': 'arun@logistics.com', 'password': 'staff123'})
        cls.staff_token = json.loads(staff_res.data)['data']['token']
        cls.staff_headers = {'Authorization': f'Bearer {cls.staff_token}'}

    def test_01_haversine_geofence_calculation(self):
        """Test Haversine distance formula between known Chennai landmarks."""
        # Chennai Customs (13.0883, 80.2925) to Chennai Port Gate 1 (13.0970, 80.2980)
        customs_lat, customs_lon = 13.0883, 80.2925
        port_lat, port_lon = 13.0970, 80.2980

        distance = calculate_haversine_distance(customs_lat, customs_lon, port_lat, port_lon)
        # Expected distance ~ 1130 meters (+- 50 meters)
        self.assertGreaterEqual(distance, 1050)
        self.assertLessEqual(distance, 1200)

        # Geofence checks
        is_inside_1200, dist1 = is_within_geofence(customs_lat, customs_lon, port_lat, port_lon, 1200)
        self.assertTrue(is_inside_1200)

        is_inside_300, dist2 = is_within_geofence(customs_lat, customs_lon, port_lat, port_lon, 300)
        self.assertFalse(is_inside_300)

    def test_02_duplicate_attendance_prevention(self):
        """Test employee who already checked in today cannot start attendance again."""
        # Arun Kumar already checked in at 09:04 AM in seed data
        payload = {
            'latitude': 13.0883,
            'longitude': 80.2925,
            'accuracy': 15.0
        }
        res = self.client.post('/api/attendance/start', json=payload, headers=self.staff_headers)
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data['success'])
        self.assertIn('already', data['message'].lower())

    def test_03_staff_monthly_attendance_history(self):
        """Test staff can fetch their monthly attendance calendar ledger and summary."""
        res = self.client.get('/api/attendance/history', headers=self.staff_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']

        self.assertIn('records', data)
        self.assertIn('summary', data)
        self.assertIsInstance(data['records'], list)
        self.assertIn('present_days', data['summary'])
        self.assertIn('total_work_formatted', data['summary'])

    def test_04_admin_attendance_ledger(self):
        """Test Admin can retrieve company-wide daily attendance roster with summary counters."""
        res = self.client.get('/api/attendance/admin-ledger', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']

        self.assertIn('ledger', data)
        self.assertIn('summary', data)
        self.assertGreaterEqual(data['summary']['total_staff'], 1)
        self.assertGreaterEqual(data['summary']['present'], 1)

    def test_05_admin_attendance_override_and_audit_log(self):
        """Test Admin can override/correct attendance record and verify audit trail."""
        # Get Arun's attendance record id
        att = query_one("SELECT id FROM attendance WHERE employee_id = 3 AND attendance_date = CURDATE()")
        att_id = att['id']

        override_payload = {
            'status': 'PRESENT',
            'check_in_time': '2026-09-06 09:00:00',
            'check_out_time': '2026-09-06 18:30:00',
            'reason': 'GPS drifted during initial check-in; supervisor manual verification'
        }
        res = self.client.put(f'/api/attendance/{att_id}/override', json=override_payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertEqual(data['total_work_minutes'], 570)  # 9h 30m = 570 mins
        self.assertEqual(data['overtime_minutes'], 90)     # 570 - 480 = 90 mins

        # Verify audit log was recorded
        audit = query_one(
            "SELECT * FROM audit_logs WHERE action = 'ATTENDANCE_OVERRIDE' AND entity_id = %s ORDER BY id DESC LIMIT 1",
            (att_id,)
        )
        self.assertIsNotNone(audit)
        self.assertIn('supervisor manual verification', audit['description'])

if __name__ == '__main__':
    unittest.main()
