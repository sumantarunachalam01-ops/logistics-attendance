import os
import json
import base64
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from app import create_app
from app.db import execute

class AttendancePortalTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Clean Karthik's attendance for today so start/end test can run cleanly
        execute("DELETE FROM attendance WHERE employee_id = 6 AND attendance_date = CURDATE()")

        cls.sample_selfie = (
            "data:image/jpeg;base64,"
            "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
            "wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        )

    def login(self, identifier, password):
        res = self.client.post('/api/auth/login', json={
            'identifier': identifier,
            'password': password
        })
        data = res.get_json()
        self.assertTrue(data.get('success'), f"Login failed for {identifier}: {data}")
        return data['data']['token'], data['data']['user']

    def get_admin_email(self):
        from app.db import query_one
        admin = query_one("SELECT email FROM users WHERE role = 'ADMIN' LIMIT 1")
        return admin['email'] if admin else 'admin@sevenstarslogistics.com'

    def test_01_health_check(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'UP')
        print("[PASS] TEST 1: Health check passed")

    def test_02_authentication(self):
        # Admin login
        admin_token, admin_user = self.login(self.get_admin_email(), 'admin123')
        self.assertEqual(admin_user['role'], 'ADMIN')

        # Staff login
        staff_token, staff_user = self.login('arun@logistics.com', 'staff123')
        self.assertEqual(staff_user['role'], 'STAFF')
        self.assertEqual(staff_user['employee_code'], 'EMP-1001')

        # Invalid password
        bad_res = self.client.post('/api/auth/login', json={
            'identifier': 'arun@logistics.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(bad_res.status_code, 401)
        print("[PASS] TEST 2: Authentication & RBAC verified")

    def test_03_staff_start_and_end_attendance(self):
        staff_token, staff_user = self.login('karthik@logistics.com', 'staff123')
        headers = {'Authorization': f'Bearer {staff_token}'}

        # 1. Start Attendance
        start_payload = {
            'latitude': 12.9815,
            'longitude': 80.1636,
            'accuracy': 16.5,
            'selfie': self.sample_selfie
        }
        start_res = self.client.post('/api/attendance/start', json=start_payload, headers=headers)
        self.assertEqual(start_res.status_code, 200)
        start_data = start_res.get_json()
        self.assertTrue(start_data['success'])
        self.assertEqual(start_data['data']['status'], 'PRESENT')
        self.assertIsNotNone(start_data['data']['selfie_filename'])
        print("[PASS] TEST 3: Staff start attendance recorded with GPS & selfie")

        # 2. Cannot start attendance twice on same day
        duplicate_start = self.client.post('/api/attendance/start', json=start_payload, headers=headers)
        self.assertEqual(duplicate_start.status_code, 400)
        print("[PASS] TEST 4: Duplicate attendance prevention verified")

        # 3. End Attendance
        end_payload = {
            'latitude': 12.9816,
            'longitude': 80.1638,
            'accuracy': 14.0,
            'selfie': self.sample_selfie
        }
        end_res = self.client.post('/api/attendance/end', json=end_payload, headers=headers)
        self.assertEqual(end_res.status_code, 200)
        end_data = end_res.get_json()
        self.assertTrue(end_data['success'])
        self.assertIn('duration_formatted', end_data['data'])
        self.assertIn('overtime_formatted', end_data['data'])
        print("[PASS] TEST 5: Staff end attendance recorded with duration & overtime calculation")

        # 4. Cannot end attendance twice
        duplicate_end = self.client.post('/api/attendance/end', json=end_payload, headers=headers)
        self.assertEqual(duplicate_end.status_code, 400)
        print("[PASS] TEST 6: Duplicate checkout prevention verified")

    def test_04_security_selfie_access_control(self):
        admin_token, _ = self.login(self.get_admin_email(), 'admin123')
        arun_token, _ = self.login('arun@logistics.com', 'staff123')
        priya_token, _ = self.login('priya@logistics.com', 'staff123')

        arun_selfie = 'emp_arun_in.jpg'

        # 1. Arun can view his own selfie
        res1 = self.client.get(f'/api/attendance/selfie/{arun_selfie}', headers={'Authorization': f'Bearer {arun_token}'})
        self.assertEqual(res1.status_code, 200)

        # 2. Admin can view Arun's selfie
        res2 = self.client.get(f'/api/attendance/selfie/{arun_selfie}', headers={'Authorization': f'Bearer {admin_token}'})
        self.assertEqual(res2.status_code, 200)

        # 3. Priya CANNOT view Arun's selfie (Strict 403 Forbidden!)
        res3 = self.client.get(f'/api/attendance/selfie/{arun_selfie}', headers={'Authorization': f'Bearer {priya_token}'})
        self.assertEqual(res3.status_code, 403)

        # 4. Unauthenticated request is rejected (401 Unauthorized)
        res4 = self.client.get(f'/api/attendance/selfie/{arun_selfie}')
        self.assertEqual(res4.status_code, 401)
        print("[PASS] TEST 7: Selfie privacy and cross-employee access blocking verified")

    def test_05_security_role_based_access(self):
        arun_token, _ = self.login('arun@logistics.com', 'staff123')
        headers = {'Authorization': f'Bearer {arun_token}'}

        # Staff cannot access /api/employees
        res_emp = self.client.get('/api/employees', headers=headers)
        self.assertEqual(res_emp.status_code, 403)

        # Staff cannot access another employee's monthly attendance
        res_other = self.client.get('/api/attendance/employee/4/monthly', headers=headers)
        self.assertEqual(res_other.status_code, 403)

        # Staff CAN access their own monthly attendance
        res_own = self.client.get('/api/attendance/employee/3/monthly', headers=headers)
        self.assertEqual(res_own.status_code, 200)
        print("[PASS] TEST 8: Role-based authorization & personal privacy verified")

    def test_06_admin_dashboard_and_reports(self):
        admin_token, _ = self.login(self.get_admin_email(), 'admin123')
        headers = {'Authorization': f'Bearer {admin_token}'}

        # Today's Dashboard
        dash_res = self.client.get('/api/dashboard/today', headers=headers)
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.get_json()['data']
        self.assertIn('stats', dash_data)
        self.assertIn('roster', dash_data)
        self.assertGreater(dash_data['stats']['total_staff'], 0)

        # Monthly Attendance for Arun (EMP-1001 / ID: 3)
        month_res = self.client.get('/api/attendance/employee/3/monthly?month=2026-09', headers=headers)
        self.assertEqual(month_res.status_code, 200)
        month_data = month_res.get_json()['data']
        self.assertIn('summary', month_data)
        self.assertIn('days', month_data)
        self.assertEqual(len(month_data['days']), 30) # September has 30 days
        self.assertGreater(month_data['summary']['present_days'], 0)

        # Monthly Company Report
        rep_res = self.client.get('/api/reports/monthly?month=2026-09', headers=headers)
        self.assertEqual(rep_res.status_code, 200)
        rep_data = rep_res.get_json()['data']
        self.assertIn('records', rep_data)
        self.assertGreater(len(rep_data['records']), 0)
        print("[PASS] TEST 9: Admin Today Roster, Monthly Attendance & Company Report verified")

if __name__ == '__main__':
    unittest.main()
