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
            return response.read(), response.status, response.headers
    except urllib.error.HTTPError as e:
        return e.read(), e.code, e.headers

def run_e2e():
    print("==================================================")
    print("RUNNING PHASE 7 REPORTS & EXPORT ENGINE E2E")
    print("==================================================")

    # 1. Admin Login
    print("\n1. Admin Login...")
    body, status, _ = api_call("/auth/login", method="POST", payload={"identifier": "admin@logistics.com", "password": "admin123"})
    res = json.loads(body.decode())
    assert status == 200, f"Admin login failed: {res}"
    admin_token = res["data"]["token"]
    print(f"   [+] Admin authenticated: {res['data']['user']['full_name']}")

    # 2. Daily Attendance JSON Report
    print("\n2. Fetching Daily Attendance JSON Report...")
    body, status, _ = api_call("/reports/daily-attendance", method="GET", token=admin_token)
    assert status == 200
    res = json.loads(body.decode())
    print(f"   [+] Records retrieved: {res['data']['total_records']} on {res['data']['target_date']}")
    for r in res['data']['records'][:3]:
        print(f"       - {r['full_name']} ({r['department']}) | Shift: {r['shift_name']} | Check-in: {r['check_in_time']} | Status: {r['status']}")

    # 3. Daily Attendance CSV Export Download
    print("\n3. Testing Daily Attendance CSV Stream Export...")
    body, status, headers = api_call("/reports/daily-attendance?format=csv", method="GET", token=admin_token)
    assert status == 200
    assert "text/csv" in headers.get("Content-Type")
    csv_content = body.decode()
    assert "Employee Code,Full Name,Department" in csv_content
    assert "Arun Kumar" in csv_content
    print(f"   [+] CSV stream received successfully ({len(csv_content)} bytes)")
    print("       CSV Header:", csv_content.splitlines()[0])

    # 4. Monthly Summary JSON Report
    print("\n4. Fetching Monthly Attendance Summary JSON Report...")
    body, status, _ = api_call("/reports/monthly-summary", method="GET", token=admin_token)
    assert status == 200
    res = json.loads(body.decode())
    print(f"   [+] Employees summarized: {res['data']['total_employees']} for month {res['data']['month']}")
    for r in res['data']['records'][:3]:
        print(f"       - {r['full_name']}: Present: {r['present_days']}, Late: {r['late_days']}, Leaves: {r['leave_days']}, Hours: {r['total_work_hours']}h")

    # 5. Monthly Summary CSV Export
    print("\n5. Testing Monthly Summary CSV Export...")
    body, status, headers = api_call("/reports/monthly-summary?format=csv", method="GET", token=admin_token)
    assert status == 200
    assert "text/csv" in headers.get("Content-Type")
    csv_content = body.decode()
    assert "Present Days,Late Days,Half Days" in csv_content
    print(f"   [+] Monthly summary CSV generated ({len(csv_content)} bytes)")

    # 6. Task Performance Report
    print("\n6. Fetching Task Performance CSV Report...")
    body, status, headers = api_call("/reports/tasks?format=csv", method="GET", token=admin_token)
    assert status == 200
    assert "text/csv" in headers.get("Content-Type")
    csv_content = body.decode()
    assert "Task ID,Title,Priority" in csv_content
    print(f"   [+] Task performance CSV generated ({len(csv_content)} bytes)")

    print("\n==================================================")
    print("PHASE 7 REPORTS & EXPORT ENGINE E2E VERIFIED 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e()
