import urllib.request
import json

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
    print("RUNNING PHASE 4 FIELD TASK MANAGEMENT E2E VERIFICATION")
    print("==================================================")

    # 1. Admin Login
    print("\n1. Admin Login...")
    res, status = api_call("/auth/login", method="POST", payload={"identifier": "admin@logistics.com", "password": "admin123"})
    assert status == 200, f"Admin login failed: {res}"
    admin_token = res["data"]["token"]
    print(f"   [+] Admin authenticated: {res['data']['user']['full_name']}")

    # 2. Staff Login (Karthik Raja - EMP-1003)
    print("\n2. Staff Login (Karthik Raja)...")
    res, status = api_call("/auth/login", method="POST", payload={"identifier": "karthik@logistics.com", "password": "staff123"})
    assert status == 200, f"Staff login failed: {res}"
    staff_token = res["data"]["token"]
    karthik_emp_id = res["data"]["user"]["employee_id"]
    print(f"   [+] Staff authenticated: {res['data']['user']['full_name']} (ID: {karthik_emp_id})")

    # 3. Staff Clock In Attendance (prerequisite for field task)
    print("\n3. Staff Clock-In at CFS...")
    res, status = api_call("/attendance/start", method="POST", payload={
        "latitude": 13.1415,
        "longitude": 80.2985,
        "accuracy": 10.0,
        "device_info": "Mobile Chrome / Android 14"
    }, token=staff_token)
    print(f"   Clock in response code: {status}")

    # 4. Admin Dispatches Urgent Field Task to Karthik
    print("\n4. Admin Dispatches Field Task to Karthik at Ennore Port...")
    res, status = api_call("/tasks", method="POST", payload={
        "employee_id": karthik_emp_id,
        "title": "Ennore Container Berth Vessel Loading Supervision",
        "description": "Supervise unloading of 40ft refrigerated containers from MV Maersk Singapore.",
        "location_id": 4, # Ennore Port (lat: 13.2625, lng: 80.3312, radius: 800m)
        "priority": "URGENT",
        "assigned_date": "2026-09-06",
        "scheduled_start": "13:30",
        "scheduled_end": "17:00"
    }, token=admin_token)
    assert status == 201, f"Task dispatch failed: {res}"
    task_id = res["data"]["task_id"]
    print(f"   [+] Task #{task_id} dispatched: {res['data']['title']} -> {res['data']['assigned_to']}")

    # 5. Karthik views his task list
    print("\n5. Staff fetches assigned tasks...")
    res, status = api_call("/tasks", method="GET", token=staff_token)
    assert status == 200, f"Fetch tasks failed: {res}"
    staff_tasks = res["data"]["tasks"]
    matched = [t for t in staff_tasks if t["id"] == task_id]
    assert len(matched) == 1, "Dispatched task not found in staff task list!"
    print(f"   [+] Staff successfully sees assigned task #{task_id} (Status: {matched[0]['status']})")

    # 6. Karthik Accepts Task
    print("\n6. Staff accepts task...")
    res, status = api_call(f"/tasks/{task_id}/accept", method="POST", token=staff_token)
    assert status == 200, f"Accept failed: {res}"
    print(f"   [+] Task #{task_id} marked as {res['data']['status']}")

    # 7. Karthik tries to start task from wrong location (Airport ~35km away)
    print("\n7. Geofence test: Staff attempts start from Airport (outside Ennore Port radius)...")
    res, status = api_call(f"/tasks/{task_id}/start", method="POST", payload={
        "latitude": 12.9815,
        "longitude": 80.1636,
        "accuracy": 15.0
    }, token=staff_token)
    assert status == 403, f"Geofence bypass bug! Expected 403, got {status}: {res}"
    print(f"   [+] Geofence violation correctly blocked: '{res['message']}'")

    # 8. Karthik arrives on site at CFS Manali and starts task
    print("\n8. Staff starts task within CFS Manali geofence...")
    res, status = api_call(f"/tasks/{task_id}/start", method="POST", payload={
        "latitude": 13.1671,
        "longitude": 80.2601,
        "accuracy": 8.0
    }, token=staff_token)
    assert status == 200, f"Start task failed: {res}"
    print(f"   [+] Task started! Status: {res['data']['status']} at {res['data']['actual_start']}")

    # 9. Karthik completes task with cargo remarks
    print("\n9. Staff completes task with remarks...")
    res, status = api_call(f"/tasks/{task_id}/end", method="POST", payload={
        "latitude": 13.1671,
        "longitude": 80.2601,
        "accuracy": 10.0,
        "remarks": "All 28 reefer containers unloaded with temperature logs verified at -20 deg C."
    }, token=staff_token)
    assert status == 200, f"End task failed: {res}"
    print(f"   [+] Task completed! Status: {res['data']['status']}, Duration: {res['data']['formatted_duration']}")
    print(f"   Remarks recorded: '{res['data']['remarks']}'")

    # 10. Admin verifies updated task ledger & stats
    print("\n10. Admin checks task dashboard metrics...")
    res, status = api_call(f"/tasks?date=2026-09-06", method="GET", token=admin_token)
    assert status == 200, f"Admin get tasks failed: {res}"
    summary = res["data"]["summary"]
    print(f"   [+] Daily Task Summary: Total: {summary['total']}, Completed: {summary['completed']}, In-Progress: {summary['in_progress']}")

    print("\n==================================================")
    print("PHASE 4 E2E VERIFICATION COMPLETED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e()
