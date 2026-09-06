import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import query_one, execute

class TestPhase6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Admin Token
        admin_res = cls.client.post('/api/auth/login', json={'identifier': 'admin@logistics.com', 'password': 'admin123'})
        cls.admin_token = json.loads(admin_res.data)['data']['token']
        cls.headers = {'Authorization': f'Bearer {cls.admin_token}'}

        # Cleanup any previous test location
        execute("DELETE FROM locations WHERE name = 'Kattupalli Port Terminal'")

    @classmethod
    def tearDownClass(cls):
        execute("DELETE FROM locations WHERE name = 'Kattupalli Port Terminal'")

    def test_01_dashboard_analytics(self):
        """Test GET /api/dashboard/analytics returns department and shift distributions."""
        res = self.client.get('/api/dashboard/analytics', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('departments', data)
        self.assertIn('shifts', data)
        self.assertIn('task_priorities', data)
        self.assertGreaterEqual(len(data['departments']), 1)
        self.assertGreaterEqual(len(data['shifts']), 1)

    def test_02_map_data_endpoint(self):
        """Test GET /api/locations/map-data returns hubs and staff with GPS."""
        res = self.client.get('/api/locations/map-data', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertIn('hubs', data)
        self.assertIn('staff', data)
        self.assertGreaterEqual(data['total_hubs'], 4)
        # Check first hub has geofence radius
        hub = data['hubs'][0]
        self.assertIn('allowed_radius_meters', hub)
        self.assertIn('latitude', hub)
        self.assertIn('longitude', hub)

    def test_03_create_update_toggle_location(self):
        """Test Admin creates, updates, and toggles status of a logistics hub."""
        # 1. Create
        payload = {
            'name': 'Kattupalli Port Terminal',
            'type': 'HARBOUR',
            'address': 'Kattupalli Village, Ponneri Taluk, Tiruvallur',
            'latitude': 13.3105,
            'longitude': 80.3450,
            'allowed_radius_meters': 600
        }
        res = self.client.post('/api/locations', json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        loc_id = json.loads(res.data)['data']['location_id']

        # 2. Update
        update_payload = {
            'name': 'Kattupalli Port Terminal',
            'type': 'PORT',
            'address': 'Updated Gate 2 Address',
            'latitude': 13.3110,
            'longitude': 80.3455,
            'allowed_radius_meters': 750
        }
        update_res = self.client.put(f'/api/locations/{loc_id}', json=update_payload, headers=self.headers)
        self.assertEqual(update_res.status_code, 200)

        # Verify in DB
        row = query_one("SELECT * FROM locations WHERE id = %s", (loc_id,))
        self.assertEqual(row['allowed_radius_meters'], 750)
        self.assertEqual(row['address'], 'Updated Gate 2 Address')

        # 3. Toggle Status (Deactivate)
        status_res = self.client.patch(f'/api/locations/{loc_id}/status', headers=self.headers)
        self.assertEqual(status_res.status_code, 200)
        self.assertFalse(json.loads(status_res.data)['data']['is_active'])

        # 4. Toggle Status (Re-activate)
        reactivate_res = self.client.patch(f'/api/locations/{loc_id}/status', headers=self.headers)
        self.assertEqual(reactivate_res.status_code, 200)
        self.assertTrue(json.loads(reactivate_res.data)['data']['is_active'])

if __name__ == '__main__':
    unittest.main()
