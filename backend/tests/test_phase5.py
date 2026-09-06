import os
import sys
import unittest
import json

# Set path to include backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import query_one, query_all

class TestPhase5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Admin Token
        admin_res = cls.client.post('/api/auth/login', json={'identifier': 'admin@logistics.com', 'password': 'admin123'})
        cls.admin_token = json.loads(admin_res.data)['data']['token']
        cls.admin_headers = {'Authorization': f'Bearer {cls.admin_token}'}

        # Staff Token (Arun Kumar - EMP-1001, Employee ID: 3)
        arun_res = cls.client.post('/api/auth/login', json={'identifier': 'arun@logistics.com', 'password': 'staff123'})
        cls.arun_token = json.loads(arun_res.data)['data']['token']
        cls.arun_headers = {'Authorization': f'Bearer {cls.arun_token}'}

        # Staff Token (Rahul Verma - EMP-1002, Employee ID: 4)
        rahul_res = cls.client.post('/api/auth/login', json={'identifier': 'rahul@logistics.com', 'password': 'staff123'})
        cls.rahul_token = json.loads(rahul_res.data)['data']['token']
        cls.rahul_headers = {'Authorization': f'Bearer {cls.rahul_token}'}

        # Clean test records
        from app.db import execute
        execute("DELETE FROM leaves WHERE id > 2")
        execute("DELETE FROM notifications WHERE type = 'LEAVE'")

    @classmethod
    def tearDownClass(cls):
        from app.db import execute
        execute("DELETE FROM leaves WHERE id > 2")

    def test_01_get_holidays(self):
        """Test GET /api/holidays returns upcoming and historical company holidays."""
        res = self.client.get('/api/holidays')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']['holidays']
        self.assertGreaterEqual(len(data), 5)
        names = [h['name'] for h in data]
        self.assertIn('Pongal / Harvest Festival', names)
        self.assertIn('Independence Day', names)

    def test_02_staff_apply_leave(self):
        """Test Staff (Arun Kumar) submits a 2-day Casual Leave application."""
        payload = {
            'leave_type': 'CASUAL',
            'start_date': '2026-11-10',
            'end_date': '2026-11-11',
            'reason': 'Attending family wedding in Coimbatore'
        }
        res = self.client.post('/api/leaves', json=payload, headers=self.arun_headers)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)['data']
        self.assertEqual(data['status'], 'PENDING')
        self.assertEqual(data['days_count'], 2)
        TestPhase5.created_leave_id = data['leave_id']

        # Verify notification created for Admin
        notif = query_one(
            "SELECT * FROM notifications WHERE type = 'LEAVE' ORDER BY id DESC LIMIT 1"
        )
        self.assertIsNotNone(notif)
        self.assertIn('Arun Kumar', notif['message'])

    def test_03_prevent_overlapping_leave(self):
        """Test server rejects overlapping leave requests for the same employee."""
        payload = {
            'leave_type': 'SICK',
            'start_date': '2026-11-11', # overlaps with 2026-11-10 to 2026-11-11
            'end_date': '2026-11-12',
            'reason': 'Overlapping leave attempt'
        }
        res = self.client.post('/api/leaves', json=payload, headers=self.arun_headers)
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn('overlapping', data['message'].lower())

    def test_04_admin_views_leaves_and_kpis(self):
        """Test Admin retrieves all leave requests and summary metrics."""
        res = self.client.get('/api/leaves', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('leaves', data)
        self.assertIn('summary', data)
        self.assertGreaterEqual(data['summary']['pending_count'], 1)

    def test_05_admin_approves_leave_and_syncs_attendance(self):
        """Test Admin approves leave and verifies attendance ledger gets LEAVE records."""
        leave_id = TestPhase5.created_leave_id
        res = self.client.put(
            f'/api/leaves/{leave_id}/approve',
            json={'remarks': 'Approved, please ensure handover of customs files.'},
            headers=self.admin_headers
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertEqual(data['status'], 'APPROVED')

        # Verify Attendance Ledger has LEAVE status for both 2026-11-10 and 2026-11-11
        att_rows = query_all(
            "SELECT attendance_date, status, remarks FROM attendance WHERE employee_id = 3 AND attendance_date IN ('2026-11-10', '2026-11-11')"
        )
        self.assertEqual(len(att_rows), 2)
        for row in att_rows:
            self.assertEqual(row['status'], 'LEAVE')
            self.assertIn('Approved CASUAL Leave', row['remarks'])

        # Verify Notification generated for Arun (Employee ID 3)
        notif = query_one(
            "SELECT * FROM notifications WHERE employee_id = 3 AND title = 'Leave Request Approved' ORDER BY id DESC LIMIT 1"
        )
        self.assertIsNotNone(notif)
        self.assertIn('approved', notif['message'].lower())

    def test_06_admin_rejects_leave(self):
        """Test Staff applies for leave and Admin rejects it with justification."""
        # Rahul applies for leave
        apply_res = self.client.post(
            '/api/leaves',
            json={
                'leave_type': 'ANNUAL',
                'start_date': '2026-12-01',
                'end_date': '2026-12-03',
                'reason': 'Vacation trip to Goa'
            },
            headers=self.rahul_headers
        )
        self.assertEqual(apply_res.status_code, 201)
        leave_id = json.loads(apply_res.data)['data']['leave_id']

        # Admin rejects
        reject_res = self.client.put(
            f'/api/leaves/{leave_id}/reject',
            json={'remarks': 'Peak annual audit and container volume scheduled that week.'},
            headers=self.admin_headers
        )
        self.assertEqual(reject_res.status_code, 200)
        data = json.loads(reject_res.data)['data']
        self.assertEqual(data['status'], 'REJECTED')
        self.assertIn('Peak annual audit', data['review_remarks'])

    def test_07_staff_my_leaves_and_balances(self):
        """Test Staff retrieves their leave balances and application history."""
        res = self.client.get('/api/leaves/my-leaves', headers=self.arun_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('balances', data)
        self.assertIn('leaves', data)
        casual_bal = next(b for b in data['balances'] if b['leave_type'] == 'CASUAL')
        self.assertEqual(casual_bal['allotted'], 12)
        self.assertGreaterEqual(casual_bal['used'], 2)

    def test_08_staff_cancels_pending_leave(self):
        """Test staff can cancel their own pending leave request."""
        # Create a pending leave
        apply_res = self.client.post(
            '/api/leaves',
            json={
                'leave_type': 'EMERGENCY',
                'start_date': '2026-12-24',
                'end_date': '2026-12-24',
                'reason': 'Personal errand'
            },
            headers=self.rahul_headers
        )
        leave_id = json.loads(apply_res.data)['data']['leave_id']

        # Rahul cancels it
        cancel_res = self.client.post(f'/api/leaves/{leave_id}/cancel', headers=self.rahul_headers)
        self.assertEqual(cancel_res.status_code, 200)

        # Verify status in database
        leave_row = query_one("SELECT status FROM leaves WHERE id = %s", (leave_id,))
        self.assertEqual(leave_row['status'], 'CANCELLED')

if __name__ == '__main__':
    unittest.main()
