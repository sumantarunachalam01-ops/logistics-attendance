import urllib.request
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BASE_URL = "http://127.0.0.1:5000/api"

def api_call(path, method="GET", payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode()), response.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()), e.code

def run_e2e():
    print("==================================================")
    print("RUNNING PHASE 6 LIVE MAP & ANALYTICS E2E")
    print("==================================================")

    # 1. Admin Login
    print("\n1. Admin Login...")
    res, status = api_call("/auth/login", method="POST", payload={"identifier": "admin@logistics.com", "password": "admin123"})
    assert status == 200, f"Admin login failed: {res}"
    admin_token = res["data"]["token"]
    print(f"   [+] Admin authenticated: {res['data']['user']['full_name']}")

    # 2. Fetch Multi-Dimensional Analytics
    print("\n2. Fetching Operations Analytics (/dashboard/analytics)...")
    res, status = api_call("/dashboard/analytics", method="GET", token=admin_token)
    assert status == 200, f"Get analytics failed: {res}"
    data = res["data"]
    print(f"   [+] Departments reported: {len(data['departments'])}")
    for d in data['departments']:
        print(f"       - {d['department']}: {d['present_count']}/{d['total_staff']} Present, {d['late_count']} Late, {d['on_leave_count']} On Leave")
    print(f"   [+] Shifts active: {len(data['shifts'])}")
    for s in data['shifts']:
        print(f"       - {s['shift_name']} ({s['start_time']}-{s['end_time']}): {s['assigned_staff']} Staff")

    # 3. Fetch Unified Map Geospatial Data
    print("\n3. Fetching Geospatial Corridor Map Data (/locations/map-data)...")
    res, status = api_call("/locations/map-data", method="GET", token=admin_token)
    assert status == 200, f"Get map-data failed: {res}"
    map_data = res["data"]
    print(f"   [+] Total Logistics Hubs with Geofences: {map_data['total_hubs']}")
    for h in map_data['hubs']:
        print(f"       * [{h['type']}] {h['name']} @ ({h['latitude']}, {h['longitude']}) - Radius: {h['allowed_radius_meters']}m")
    print(f"   [+] Active Field Staff with live GPS: {map_data['active_field_staff']}")
    for st in map_data['staff']:
        print(f"       * {st['full_name']} ({st['employee_code']}) - Status: {st['attendance_status']} - GPS: ({st['latitude']}, {st['longitude']}) - Task: {st['task_title'] or 'None'}")

    # 4. Admin Creates a New Strategic Hub
    print("\n4. Admin creates new container logistics hub...")
    hub_payload = {
        "name": "Vallarpadam Transshipment Terminal",
        "type": "HARBOUR",
        "address": "Vallarpadam Island, ICTT Gateway",
        "latitude": 9.9912,
        "longitude": 76.2415,
        "allowed_radius_meters": 750
    }
    res, status = api_call("/locations", method="POST", payload=hub_payload, token=admin_token)
    assert status == 201, f"Create location failed: {res}"
    loc_id = res["data"]["location_id"]
    print(f"   [+] Location #{loc_id} ('{res['data']['name']}') created.")

    # 5. Admin Updates Geofence Radius
    print("\n5. Admin modifies geofence perimeter...")
    res, status = api_call(f"/locations/{loc_id}", method="PUT", payload={
        "name": "Vallarpadam Transshipment Terminal - Phase 2",
        "type": "HARBOUR",
        "address": "Vallarpadam Island, ICTT Gateway",
        "latitude": 9.9915,
        "longitude": 76.2418,
        "allowed_radius_meters": 1000
    }, token=admin_token)
    assert status == 200, f"Update location failed: {res}"
    print(f"   [+] Geofence perimeter updated to 1000m: '{res['message']}'")

    # 6. Admin Deactivates and Re-activates Location
    print("\n6. Admin toggles location operational status...")
    res, status = api_call(f"/locations/{loc_id}/status", method="PATCH", token=admin_token)
    assert status == 200
    print(f"   [+] Deactivated: is_active = {res['data']['is_active']}")
    res, status = api_call(f"/locations/{loc_id}/status", method="PATCH", token=admin_token)
    assert status == 200
    print(f"   [+] Re-activated: is_active = {res['data']['is_active']}")

    # Clean up test location
    from app.db import execute
    execute("DELETE FROM locations WHERE id = %s", (loc_id,))
    print(f"   [+] Cleaned up temporary test location #{loc_id}")

    print("\n==================================================")
    print("PHASE 6 LIVE MAP & ANALYTICS E2E VERIFIED 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e()
