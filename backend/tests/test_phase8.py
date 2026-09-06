import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import execute, query_one

class TestPhase8(unittest.TestCase):
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

        # Seed test notification for Arun
        res = execute(
            """INSERT INTO notifications (employee_id, title, message, type, is_read)
               VALUES (3, 'Urgent Container Gate Inspection', 'Please proceed to Harbour Gate 1 immediately.', 'TASK', FALSE)"""
        )
        cls.test_notif_id = res['lastrowid']

    @classmethod
    def tearDownClass(cls):
        execute("DELETE FROM notifications WHERE id = %s", (cls.test_notif_id,))

    def test_01_get_notifications(self):
        """Test Staff fetches their in-app notifications."""
        res = self.client.get('/api/notifications', headers=self.arun_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('notifications', data)
        self.assertGreaterEqual(data['unread_count'], 1)
        found = any(n['id'] == self.test_notif_id for n in data['notifications'])
        self.assertTrue(found)

    def test_02_mark_notification_read(self):
        """Test Staff marks an individual notification as read."""
        res = self.client.patch(f'/api/notifications/{self.test_notif_id}/read', headers=self.arun_headers)
        self.assertEqual(res.status_code, 200)

        # Verify in DB
        row = query_one("SELECT is_read FROM notifications WHERE id = %s", (self.test_notif_id,))
        self.assertTrue(row['is_read'])

    def test_03_mark_all_read(self):
        """Test Staff marks all notifications as read."""
        res = self.client.post('/api/notifications/read-all', headers=self.arun_headers)
        self.assertEqual(res.status_code, 200)

        # Verify unread count is 0
        get_res = self.client.get('/api/notifications', headers=self.arun_headers)
        self.assertEqual(json.loads(get_res.data)['data']['unread_count'], 0)

    def test_04_get_audit_logs(self):
        """Test Admin retrieves system security audit logs with action and search filtering."""
        res = self.client.get('/api/audit-logs', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('logs', data)
        self.assertGreaterEqual(data['total'], 1)
        log = data['logs'][0]
        self.assertIn('action', log)
        self.assertIn('user_email', log)
        self.assertIn('ip_address', log)

    def test_05_staff_cannot_access_audit_logs(self):
        """Test Staff role is forbidden from viewing audit trail."""
        res = self.client.get('/api/audit-logs', headers=self.arun_headers)
        self.assertEqual(res.status_code, 403)

if __name__ == '__main__':
    unittest.main()
