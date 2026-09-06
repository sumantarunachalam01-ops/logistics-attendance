import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

class TestPhase7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Admin Token
        admin_res = cls.client.post('/api/auth/login', json={'identifier': 'admin@logistics.com', 'password': 'admin123'})
        cls.admin_token = json.loads(admin_res.data)['data']['token']
        cls.headers = {'Authorization': f'Bearer {cls.admin_token}'}

    def test_01_daily_attendance_report_json(self):
        """Test GET /api/reports/daily-attendance returns JSON records with Section 15 schema."""
        res = self.client.get('/api/reports/daily-attendance', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('records', data)
        self.assertGreaterEqual(data['total_records'], 4)
        rec = data['records'][0]
        self.assertIn('full_name', rec)
        self.assertIn('department', rec)
        self.assertIn('duration_formatted', rec)
        self.assertIn('overtime_formatted', rec)

    def test_02_daily_attendance_report_csv(self):
        """Test GET /api/reports/daily-attendance?format=csv returns downloadable CSV stream."""
        res = self.client.get('/api/reports/daily-attendance?format=csv', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        csv_text = res.data.decode('utf-8')
        self.assertIn('Employee Code,Full Name,Department', csv_text)
        self.assertIn('Arun Kumar', csv_text)

    def test_03_monthly_summary_report_json_and_csv(self):
        """Test GET /api/reports/monthly-summary returns monthly aggregates and CSV export."""
        # JSON
        res = self.client.get('/api/reports/monthly-summary', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('records', data)
        self.assertGreaterEqual(data['total_employees'], 4)

        # CSV
        csv_res = self.client.get('/api/reports/monthly-summary?format=csv', headers=self.headers)
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, 'text/csv')
        self.assertIn('Present Days,Late Days,Half Days', csv_res.data.decode('utf-8'))

    def test_04_task_performance_report(self):
        """Test GET /api/reports/tasks returns task performance data and CSV."""
        res = self.client.get('/api/reports/tasks', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('records', data)

        csv_res = self.client.get('/api/reports/tasks?format=csv', headers=self.headers)
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn('Task ID,Title,Priority', csv_res.data.decode('utf-8'))

    def test_05_hub_traffic_report(self):
        """Test GET /api/reports/hub-traffic returns hub volume data."""
        res = self.client.get('/api/reports/hub-traffic', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('records', data)
        self.assertGreaterEqual(len(data['records']), 4)

if __name__ == '__main__':
    unittest.main()
