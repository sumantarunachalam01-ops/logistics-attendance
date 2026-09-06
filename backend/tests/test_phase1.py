import os
import sys
import unittest
import json

# Set path to include backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import get_connection, query_one
from app.services.auth_service import hash_password, verify_password, generate_token, decode_token

class TestPhase1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_db_connection(self):
        """Test MySQL database connection and presence of key tables."""
        conn = get_connection()
        self.assertIsNotNone(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM users")
            row = cur.fetchone()
            self.assertGreater(row['cnt'], 0, "Users table must have seed data")
        conn.close()

    def test_02_bcrypt_hashing(self):
        """Test password hashing and verification logic."""
        plain = "secureLogisticPass2026"
        hashed = hash_password(plain)
        self.assertTrue(verify_password(plain, hashed))
        self.assertFalse(verify_password("wrongPass", hashed))

    def test_03_jwt_token_generation_and_decoding(self):
        """Test JWT token encoding and decoding."""
        token = generate_token(user_id=99, role='STAFF', email='test@logistics.com', employee_id=88)
        decoded = decode_token(token)
        self.assertEqual(decoded['user_id'], 99)
        self.assertEqual(decoded['role'], 'STAFF')
        self.assertEqual(decoded['email'], 'test@logistics.com')
        self.assertEqual(decoded['employee_id'], 88)

    def test_04_health_endpoint(self):
        """Test public health check endpoint."""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'UP')

    def test_05_admin_login(self):
        """Test authentication for Admin account."""
        payload = {'identifier': 'admin@logistics.com', 'password': 'admin123'}
        res = self.client.post('/api/auth/login', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data['data'])
        self.assertEqual(data['data']['user']['role'], 'ADMIN')

    def test_06_staff_login(self):
        """Test authentication for Staff account (Arun Kumar)."""
        payload = {'identifier': 'arun@logistics.com', 'password': 'staff123'}
        res = self.client.post('/api/auth/login', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['role'], 'STAFF')
        self.assertEqual(data['data']['user']['employee_code'], 'EMP-1001')
        self.assertEqual(data['data']['user']['full_name'], 'Arun Kumar')

    def test_07_invalid_login(self):
        """Test login with incorrect password returns 401."""
        payload = {'identifier': 'admin@logistics.com', 'password': 'wrongPassword!'}
        res = self.client.post('/api/auth/login', json=payload)
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertFalse(data['success'])

    def test_08_admin_dashboard_stats(self):
        """Test Admin role access to KPI stats."""
        # 1. Login as admin
        login_res = self.client.post('/api/auth/login', json={'identifier': 'admin@logistics.com', 'password': 'admin123'})
        token = json.loads(login_res.data)['data']['token']

        # 2. Query stats with Bearer token
        res = self.client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        stats = data['data']
        self.assertIn('total_staff', stats)
        self.assertIn('present_today', stats)
        self.assertIn('tasks_today', stats)
        self.assertGreaterEqual(stats['total_staff'], 1)

    def test_09_staff_access_to_admin_endpoint_forbidden(self):
        """Test that Staff role cannot access Admin-only stats endpoint (403 Forbidden)."""
        login_res = self.client.post('/api/auth/login', json={'identifier': 'arun@logistics.com', 'password': 'staff123'})
        token = json.loads(login_res.data)['data']['token']

        res = self.client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 403)
        data = json.loads(res.data)
        self.assertFalse(data['success'])

    def test_10_staff_today_tasks(self):
        """Test Staff user can fetch their assigned tasks for today."""
        login_res = self.client.post('/api/auth/login', json={'identifier': 'arun@logistics.com', 'password': 'staff123'})
        token = json.loads(login_res.data)['data']['token']

        res = self.client.get('/api/tasks/today', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        tasks = data['data']['tasks']
        self.assertIsInstance(tasks, list)
        titles = [t['title'] for t in tasks]
        self.assertIn('Customs Documentation & Bill of Entry', titles)

if __name__ == '__main__':
    unittest.main()
