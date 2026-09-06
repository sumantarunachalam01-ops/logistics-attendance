import os
import sys
import unittest
import json

# Set path to include backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import query_one

class TestPhase4(unittest.TestCase):
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

    def test_01_locations_endpoint(self):
        """Test GET /api/locations returns active logistics hubs."""
        res = self.client.get('/api/locations', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']['locations']
        self.assertGreaterEqual(len(data), 4)
        customs = next(loc for loc in data if loc['name'] == 'Chennai Customs House')
        self.assertEqual(customs['type'], 'CUSTOMS')
        self.assertEqual(customs['allowed_radius_meters'], 300)

    def test_02_admin_creates_task_and_notifies_employee(self):
        """Test Admin assigns field task to Arun Kumar and generates in-app notification."""
        payload = {
            'employee_id': 3,  # Arun Kumar
            'title': 'Emergency Pharma Cargo Customs Clearance',
            'description': 'Expedite customs clearance for temperature-sensitive insulin consignment CA-8891.',
            'location_id': 2,  # Chennai Customs House (lat: 13.0883, lng: 80.2925, radius: 300m)
            'priority': 'URGENT',
            'assigned_date': '2026-09-06',
            'scheduled_start': '14:00:00',
            'scheduled_end': '16:30:00'
        }
        res = self.client.post('/api/tasks', json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)['data']
        self.task_id = data['task_id']

        # Verify notification was generated for Arun (employee_id 3)
        notif = query_one(
            "SELECT * FROM notifications WHERE employee_id = 3 AND title = 'New Task Assigned' ORDER BY id DESC LIMIT 1"
        )
        self.assertIsNotNone(notif)
        self.assertIn('Emergency Pharma', notif['message'])

    def test_03_staff_task_creation_blocked(self):
        """Test field staff cannot create tasks (Section 3 & 9)."""
        payload = {
            'employee_id': 3,
            'title': 'Unauthorized Task Attempt',
            'location_id': 2
        }
        res = self.client.post('/api/tasks', json=payload, headers=self.arun_headers)
        self.assertEqual(res.status_code, 403)

    def test_04_staff_accept_task(self):
        """Test Staff accepts assigned task (ASSIGNED -> ACCEPTED)."""
        # Create a task to accept
        payload = {
            'employee_id': 3,
            'title': 'Acceptance Test Task',
            'location_id': 2,
            'priority': 'MEDIUM'
        }
        create_res = self.client.post('/api/tasks', json=payload, headers=self.admin_headers)
        task_id = json.loads(create_res.data)['data']['task_id']

        accept_res = self.client.post(f'/api/tasks/{task_id}/accept', headers=self.arun_headers)
        self.assertEqual(accept_res.status_code, 200)
        data = json.loads(accept_res.data)['data']
        self.assertEqual(data['status'], 'ACCEPTED')

    def test_05_geofence_rejection_outside_radius(self):
        """Test task start rejected when staff is outside allowed hub radius (Section 12)."""
        # Task assigned at Chennai Customs House (13.0883, 80.2925, radius 300m)
        # Staff reports coordinates from Chennai Airport (~18km away: 12.9815, 80.1636)
        payload = {
            'employee_id': 3,
            'title': 'Geofence Test Task',
            'location_id': 2,
            'priority': 'HIGH'
        }
        create_res = self.client.post('/api/tasks', json=payload, headers=self.admin_headers)
        task_id = json.loads(create_res.data)['data']['task_id']

        airport_gps = {
            'latitude': 12.9815,
            'longitude': 80.1636,
            'accuracy': 15.0
        }
        start_res = self.client.post(f'/api/tasks/{task_id}/start', json=airport_gps, headers=self.arun_headers)
        self.assertEqual(start_res.status_code, 403)
        data = json.loads(start_res.data)
        self.assertFalse(data['success'])
        self.assertIn('geofence validation failed', data['message'].lower())
        self.assertIn('away from the assigned location', data['message'].lower())

    def test_06_geofence_success_and_completion(self):
        """Test task start succeeds within hub radius, followed by completion with remarks."""
        payload = {
            'employee_id': 3,
            'title': 'On-Site Clearance Execution',
            'location_id': 2,
            'priority': 'URGENT'
        }
        create_res = self.client.post('/api/tasks', json=payload, headers=self.admin_headers)
        task_id = json.loads(create_res.data)['data']['task_id']

        # Coordinates 40 meters from Customs House
        on_site_gps = {
            'latitude': 13.0884,
            'longitude': 80.2926,
            'accuracy': 10.0
        }
        start_res = self.client.post(f'/api/tasks/{task_id}/start', json=on_site_gps, headers=self.arun_headers)
        self.assertEqual(start_res.status_code, 200)
        start_data = json.loads(start_res.data)['data']
        self.assertEqual(start_data['status'], 'IN_PROGRESS')

        # End task
        end_gps = {
            'latitude': 13.0885,
            'longitude': 80.2925,
            'accuracy': 12.0,
            'remarks': 'Customs out-of-charge order issued by deputy commissioner.'
        }
        end_res = self.client.post(f'/api/tasks/{task_id}/end', json=end_gps, headers=self.arun_headers)
        self.assertEqual(end_res.status_code, 200)
        end_data = json.loads(end_res.data)['data']
        self.assertEqual(end_data['status'], 'COMPLETED')
        self.assertGreaterEqual(end_data['duration_minutes'], 1)
        self.assertEqual(end_data['remarks'], 'Customs out-of-charge order issued by deputy commissioner.')

    def test_07_unauthorized_employee_access_blocked(self):
        """Test employee cannot start or end another employee's task."""
        # Create task for Arun (ID 3)
        payload = {'employee_id': 3, 'title': 'Arun Task Sole Ownership', 'location_id': 2}
        create_res = self.client.post('/api/tasks', json=payload, headers=self.admin_headers)
        task_id = json.loads(create_res.data)['data']['task_id']

        # Rahul (ID 4) attempts to start Arun's task
        res = self.client.post(f'/api/tasks/{task_id}/start', json={'latitude': 13.0883, 'longitude': 80.2925}, headers=self.rahul_headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn('unauthorized', json.loads(res.data)['message'].lower())

if __name__ == '__main__':
    unittest.main()
