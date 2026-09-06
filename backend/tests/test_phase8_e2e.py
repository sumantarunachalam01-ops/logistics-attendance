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
    print("RUNNING PHASE 8 NOTIFICATIONS & AUDIT LOGS E2E")
    print("==================================================")

    # 1. Admin Login
    print("\n1. Admin Login...")
    res, status = api_call("/auth/login", method="POST", payload={"identifier": "admin@logistics.com", "password": "admin123"})
    assert status == 200, f"Admin login failed: {res}"
    admin_token = res["data"]["token"]
    print(f"   [+] Admin authenticated: {res['data']['user']['full_name']}")

    # 2. Staff Login (Arun Kumar)
    print("\n2. Staff Login (Arun Kumar)...")
    res, status = api_call("/auth/login", method="POST", payload={"identifier": "arun@logistics.com", "password": "staff123"})
    assert status == 200, f"Staff login failed: {res}"
    staff_token = res["data"]["token"]
    print(f"   [+] Staff authenticated: {res['data']['user']['full_name']}")

    # 3. Staff Fetches In-App Notifications
    print("\n3. Staff retrieves notifications list...")
    res, status = api_call("/notifications", method="GET", token=staff_token)
    assert status == 200, f"Get notifications failed: {res}"
    notifs = res["data"]["notifications"]
    print(f"   [+] Notifications in inbox: {len(notifs)}, Unread: {res['data']['unread_count']}")
    if notifs:
        sample = notifs[0]
        print(f"       - [{sample['type']}] {sample['title']}: '{sample['message']}' (Read: {sample['is_read']})")

    # 4. Mark All Read
    print("\n4. Staff marks all notifications as read...")
    res, status = api_call("/notifications/read-all", method="POST", token=staff_token)
    assert status == 200
    res, status = api_call("/notifications", method="GET", token=staff_token)
    assert res["data"]["unread_count"] == 0
    print("   [+] All notifications marked as read! Unread count = 0")

    # 5. Admin Inspects Audit Trail
    print("\n5. Admin inspects security audit trail...")
    res, status = api_call("/audit-logs", method="GET", token=admin_token)
    assert status == 200, f"Get audit logs failed: {res}"
    logs = res["data"]["logs"]
    print(f"   [+] Total recorded security events: {res['data']['total']}")
    for l in logs[:4]:
        print(f"       [{l['created_at_formatted']}] {l['action']} | Operator: {l['user_name'] or l['user_email']} | Desc: {l['description']}")

    # 6. Staff Blocked from Audit Trail
    print("\n6. Security Boundary: Staff tries to access audit trail...")
    res, status = api_call("/audit-logs", method="GET", token=staff_token)
    assert status == 403, f"Security violation! Expected 403, got {status}"
    print(f"   [+] Access strictly blocked: '{res['message']}'")

    print("\n==================================================")
    print("PHASE 8 NOTIFICATIONS & AUDIT LOGS E2E VERIFIED 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e()
