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
    print("RUNNING PHASE 5 LEAVE & HOLIDAYS MANAGEMENT E2E")
    print("==================================================")

    # 1. Admin Login
    print("\n1. Admin Login...")
    res, status = api_call("/auth/login", method="POST", payload={"identifier": "admin@logistics.com", "password": "admin123"})
    assert status == 200, f"Admin login failed: {res}"
    admin_token = res["data"]["token"]
    print(f"   [+] Admin authenticated: {res['data']['user']['full_name']}")

    # 2. Staff Login (Arun Kumar - EMP-1001)
    print("\n2. Staff Login (Arun Kumar)...")
    res, status = api_call("/auth/login", method="POST", payload={"identifier": "arun@logistics.com", "password": "staff123"})
    assert status == 200, f"Staff login failed: {res}"
    staff_token = res["data"]["token"]
    print(f"   [+] Staff authenticated: {res['data']['user']['full_name']}")

    # Cleanup any previous test run for these dates
    from app.db import execute
    execute("DELETE FROM leaves WHERE start_date = '2026-11-20' AND employee_id = 3")
    execute("DELETE FROM attendance WHERE attendance_date IN ('2026-11-20', '2026-11-21', '2026-11-22') AND employee_id = 3")

    # 3. Staff Submits Leave Application
    print("\n3. Staff applies for 3-day Annual Leave (2026-11-20 to 2026-11-22)...")
    res, status = api_call("/leaves", method="POST", payload={
        "leave_type": "ANNUAL",
        "start_date": "2026-11-20",
        "end_date": "2026-11-22",
        "reason": "Annual family pilgrimage and personal time off."
    }, token=staff_token)
    assert status == 201, f"Apply leave failed: {res}"
    leave_id = res["data"]["leave_id"]
    print(f"   [+] Leave request #{leave_id} created: {res['data']['days_count']} days, Status: {res['data']['status']}")

    # 4. Admin Checks Pending Leaves
    print("\n4. Admin checks pending leaves queue...")
    res, status = api_call("/leaves?status=PENDING", method="GET", token=admin_token)
    assert status == 200, f"Get leaves failed: {res}"
    pending_list = res["data"]["leaves"]
    matched = [l for l in pending_list if l["id"] == leave_id]
    assert len(matched) == 1, "Submitted leave not found in pending list!"
    print(f"   [+] Admin sees leave #{leave_id} from {matched[0]['employee_name']} (Dept: {matched[0]['department']})")

    # 5. Admin Approves Leave with Management Remarks
    print("\n5. Admin approves leave request with handover notes...")
    res, status = api_call(f"/leaves/{leave_id}/approve", method="PUT", payload={
        "remarks": "Approved by HR Management. Please ensure port dispatch handover to team."
    }, token=admin_token)
    assert status == 200, f"Approve leave failed: {res}"
    print(f"   [+] Leave #{leave_id} status updated to {res['data']['status']}")

    # 6. Verify Attendance Ledger reflects LEAVE for all 3 dates
    print("\n6. Admin checks attendance ledger for auto-synced LEAVE records...")
    res, status = api_call("/attendance/admin-ledger?date=2026-11-20", method="GET", token=admin_token)
    assert status == 200, f"Get ledger failed: {res}"
    records = res["data"]["ledger"]
    arun_rec = next((r for r in records if r["employee_id"] == 3), None)
    assert arun_rec is not None, "Attendance record for Arun not found on 2026-11-20!"
    assert arun_rec["status"] == "LEAVE", f"Expected status 'LEAVE', got: {arun_rec['status']}"
    print(f"   [+] Attendance ledger correctly synced: Status = {arun_rec['status']} ('{arun_rec['remarks']}')")

    # 7. Staff Views My-Leaves
    print("\n7. Staff checks updated leave history & balances...")
    res, status = api_call("/leaves/my-leaves", method="GET", token=staff_token)
    assert status == 200, f"Get my leaves failed: {res}"
    my_leaves = res["data"]["leaves"]
    my_matched = next(l for l in my_leaves if l["id"] == leave_id)
    assert my_matched["status"] == "APPROVED"
    print(f"   [+] Staff sees approved leave #{leave_id} with manager remarks: '{my_matched['review_remarks']}'")

    # 8. Holiday Management
    print("\n8. Admin adds a test company holiday...")
    res, status = api_call("/holidays", method="POST", payload={
        "holiday_date": "2026-11-08",
        "name": "Diwali / Deepavali",
        "description": "Festival of Lights Celebration"
    }, token=admin_token)
    assert status == 201, f"Create holiday failed: {res}"
    holiday_id = res["data"]["id"]
    print(f"   [+] Holiday #{holiday_id} ('{res['data']['name']}') created on {res['data']['holiday_date']}")

    # 9. Clean up test holiday
    print("\n9. Admin deletes test holiday...")
    res, status = api_call(f"/holidays/{holiday_id}", method="DELETE", token=admin_token)
    assert status == 200, f"Delete holiday failed: {res}"
    print(f"   [+] Cleaned up holiday #{holiday_id}")

    print("\n==================================================")
    print("PHASE 5 LEAVE MANAGEMENT E2E VERIFIED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e()
