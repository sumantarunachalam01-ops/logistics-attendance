import os
import sys
import unittest
import json

# Set path to include backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import query_one

class TestPhase2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Login as Admin to get auth token
        login_res = cls.client.post('/api/auth/login', json={'identifier': 'admin@logistics.com', 'password': 'admin123'})
        cls.admin_token = json.loads(login_res.data)['data']['token']
        cls.headers = {'Authorization': f'Bearer {cls.admin_token}'}

        from app.db import execute
        execute("DELETE FROM employees WHERE employee_code = 'EMP-TEST-01'")
        execute("DELETE FROM users WHERE email = 'anand.test@logistics.com'")

    @classmethod
    def tearDownClass(cls):
        from app.db import execute
        execute("DELETE FROM employees WHERE employee_code = 'EMP-TEST-01'")
        execute("DELETE FROM users WHERE email = 'anand.test@logistics.com'")

    def test_01_list_employees(self):
        """Test GET /api/employees with and without search filters."""
        res = self.client.get('/api/employees', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('employees', data)
        self.assertGreaterEqual(len(data['employees']), 5)

        # Test search filter
        search_res = self.client.get('/api/employees?search=Arun', headers=self.headers)
        self.assertEqual(search_res.status_code, 200)
        search_data = json.loads(search_res.data)['data']['employees']
        self.assertEqual(len(search_data), 1)
        self.assertEqual(search_data[0]['employee_code'], 'EMP-1001')

    def test_02_create_employee_transaction(self):
        """Test POST /api/employees creates user and employee in transaction."""
        new_emp = {
            'full_name': 'Anand Ramesh',
            'employee_code': 'EMP-TEST-01',
            'email': 'anand.test@logistics.com',
            'password': 'testPassword123',
            'phone': '+91 98409 99888',
            'department': 'Port Operations',
            'designation': 'Berthing Specialist',
            'shift_id': 1,
            'role': 'STAFF'
        }
        res = self.client.post('/api/employees', json=new_emp, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)['data']
        emp_id = data['employee_id']
        self.assertIsNotNone(emp_id)

        # Verify DB records
        emp_row = query_one("SELECT * FROM employees WHERE id = %s", (emp_id,))
        self.assertEqual(emp_row['full_name'], 'Anand Ramesh')
        self.assertEqual(emp_row['employee_code'], 'EMP-TEST-01')

        user_row = query_one("SELECT * FROM users WHERE id = %s", (emp_row['user_id'],))
        self.assertEqual(user_row['email'], 'anand.test@logistics.com')
        self.assertEqual(user_row['role'], 'STAFF')
        self.assertTrue(user_row['is_active'])

    def test_03_create_duplicate_rejection(self):
        """Test duplicate email or employee code returns 400 Bad Request."""
        dup = {
            'full_name': 'Duplicate Person',
            'employee_code': 'EMP-1001',  # Already belongs to Arun Kumar
            'email': 'unique@logistics.com',
            'password': 'password123'
        }
        res = self.client.post('/api/employees', json=dup, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_04_get_employee_360_profile(self):
        """Test GET /api/employees/<id> returns all 5 tabs data."""
        # Arun Kumar has id 3
        res = self.client.get('/api/employees/3', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']

        # 1. Profile Base
        self.assertEqual(data['profile']['employee_code'], 'EMP-1001')
        self.assertEqual(data['profile']['full_name'], 'Arun Kumar')

        # 2. Overview Tab
        self.assertIn('overview', data)
        self.assertIn('today_attendance', data['overview'])
        self.assertIn('today_task', data['overview'])

        # 3. Attendance Tab
        self.assertIn('attendance', data)
        self.assertIsInstance(data['attendance'], list)

        # 4. Tasks Tab
        self.assertIn('tasks', data)
        self.assertIsInstance(data['tasks'], list)

        # 5. Leaves Tab
        self.assertIn('leaves', data)
        self.assertIsInstance(data['leaves'], list)

        # 6. Reports Summary
        self.assertIn('summary', data)
        self.assertIn('present_days', data['summary'])
        self.assertIn('total_work_hours', data['summary'])

    def test_05_update_employee(self):
        """Test PUT /api/employees/<id> modifies demographic info."""
        emp = query_one("SELECT id FROM employees WHERE employee_code = 'EMP-TEST-01'")
        emp_id = emp['id']

        update_payload = {
            'full_name': 'Anand R. Menon',
            'phone': '+91 99999 88888',
            'department': 'Air Cargo',
            'designation': 'Senior Cargo Officer',
            'shift_id': 2
        }
        res = self.client.put(f'/api/employees/{emp_id}', json=update_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)

        updated_row = query_one("SELECT full_name, phone, designation FROM employees WHERE id = %s", (emp_id,))
        self.assertEqual(updated_row['full_name'], 'Anand R. Menon')
        self.assertEqual(updated_row['phone'], '+91 99999 88888')
        self.assertEqual(updated_row['designation'], 'Senior Cargo Officer')

    def test_06_disable_and_enable_employee_login(self):
        """Test toggling employee status and verifying login blocking."""
        emp = query_one("SELECT id FROM employees WHERE employee_code = 'EMP-TEST-01'")
        emp_id = emp['id']

        # 1. Disable employee
        res = self.client.patch(f'/api/employees/{emp_id}/status', json={'status': 'INACTIVE'}, headers=self.headers)
        self.assertEqual(res.status_code, 200)

        # 2. Attempt login as disabled employee -> must fail with 403
        login_res = self.client.post('/api/auth/login', json={'identifier': 'anand.test@logistics.com', 'password': 'testPassword123'})
        self.assertEqual(login_res.status_code, 403)
        self.assertIn('deactivated', json.loads(login_res.data)['message'].lower())

        # 3. Re-enable employee
        enable_res = self.client.patch(f'/api/employees/{emp_id}/status', json={'status': 'ACTIVE'}, headers=self.headers)
        self.assertEqual(enable_res.status_code, 200)

        # 4. Attempt login now -> must succeed with 200 OK
        login_success = self.client.post('/api/auth/login', json={'identifier': 'anand.test@logistics.com', 'password': 'testPassword123'})
        self.assertEqual(login_success.status_code, 200)

    def test_07_shifts_dropdown(self):
        """Test GET /api/shifts returns list of shifts."""
        res = self.client.get('/api/shifts')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('shifts', data)
        self.assertGreaterEqual(len(data['shifts']), 1)

if __name__ == '__main__':
    unittest.main()
