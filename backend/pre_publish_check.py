import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:5000/api'

def req(endpoint, method='GET', data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    encoded_data = json.dumps(data).encode('utf-8') if data is not None else None
    request = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode('utf-8')), response.status
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode('utf-8')) if e.fp else {}
        return body, e.code

def run_checks():
    print("=" * 70)
    print("       LOGITRACK PRO - PRE-PUBLISH COMPREHENSIVE SYSTEM AUDIT")
    print("=" * 70)

    # 1. Health Check
    res, status = req('/health')
    assert status == 200 and res['data']['status'] == 'UP', 'Health check failed'
    print("[PASS] 01. API Health Check verified (HTTP 200)")

    # 2. Authentication: Admin, HR, and Staff Logins
    res, status = req('/auth/login', 'POST', {'email': 'admin@sevenstarslogistics.com', 'password': 'admin123'})
    assert status == 200 and res['data']['user']['role'] == 'ADMIN', 'Admin login failed'
    admin_token = res['data']['token']
    print("[PASS] 02. Admin Authentication verified (Role: ADMIN - admin@sevenstarslogistics.com)")

    res, status = req('/auth/login', 'POST', {'email': 'hr@logistics.com', 'password': 'staff123'})
    assert status == 200 and res['data']['user']['role'] == 'STAFF', 'HR-002 staff login failed'
    hr_token = res['data']['token']
    print("[PASS] 03. HR-002 Employee Authentication verified (Role: STAFF)")

    res, status = req('/auth/login', 'POST', {'email': 'arun@logistics.com', 'password': 'staff123'})
    assert status == 200 and res['data']['user']['role'] == 'STAFF', 'Staff login failed'
    staff_token = res['data']['token']
    print("[PASS] 04. Staff Authentication verified (Role: STAFF, EMP-1001)")

    # 3. RBAC Enforcement
    res, status = req('/audit-logs', 'GET', token=staff_token)
    assert status == 403, 'Staff should be forbidden from audit-logs'
    print("[PASS] 05. RBAC Staff Security Boundary verified (Audit Logs = 403)")

    res, status = req('/employees/3/credentials', 'PUT', {'password': 'bad'}, token=hr_token)
    assert status == 403, 'HR should be forbidden from changing staff credentials'
    print("[PASS] 06. RBAC Staff Credentials Admin-Only Boundary verified (HR = 403)")

    # 4. Admin Dashboard
    res, status = req('/dashboard/stats', 'GET', token=admin_token)
    assert status == 200 and 'total_staff' in res['data'], 'Dashboard stats failed'
    print(f"[PASS] 07. Dashboard KPI Stats verified (Staff: {res['data']['total_staff']}, Tasks: {res['data']['tasks_today']})")

    res, status = req('/dashboard/live-staff', 'GET', token=admin_token)
    assert status == 200 and 'staff' in res['data'], 'Live staff list failed'
    print(f"[PASS] 08. Live Staff Operations Map Data verified ({len(res['data']['staff'])} active tracked)")

    # 5. Employees Management & 360 Profiles
    res, status = req('/employees', 'GET', token=admin_token)
    assert status == 200 and len(res['data']['employees']) > 0, 'Employees listing failed'
    print(f"[PASS] 09. Personnel Roster retrieved ({len(res['data']['employees'])} employees)")

    res, status = req('/employees/3', 'GET', token=admin_token)
    assert status == 200 and res['data']['profile']['full_name'] == 'Arun Kumar', 'Employee 360 failed'
    print("[PASS] 10. Employee 360 Profile verified (EMP-1001 Arun Kumar)")

    # 6. Employee Profile Update
    res, status = req('/employees/3', 'PUT', {
        'full_name': 'Arun Kumar',
        'email': 'arun@logistics.com',
        'phone': '+91 98765 43210',
        'department': 'Customs Clearing',
        'designation': 'Customs Field Officer',
        'shift_id': 1,
        'employment_type': 'FULL_TIME'
    }, token=admin_token)
    assert status == 200, 'Employee edit profile failed'
    print("[PASS] 11. Employee Profile Update verified")

    # 7. Admin-only Staff Credentials Update
    res, status = req('/employees/3/credentials', 'PUT', {'password': 'staff123'}, token=admin_token)
    assert status == 200, 'Staff credentials update failed'
    print("[PASS] 12. Staff Credentials Update verified (Admin-Exclusive)")

    # 8. Locations & Geofence Map Data
    res, status = req('/locations/map-data', 'GET', token=admin_token)
    assert status == 200 and 'hubs' in res['data'], 'Map data failed'
    print(f"[PASS] 13. Logistics Hubs & Geofences verified ({len(res['data']['hubs'])} hubs)")

    # 9. Shifts Module
    res, status = req('/shifts', 'GET', token=admin_token)
    assert status == 200 and len(res['data']['shifts']) > 0, 'Shifts failed'
    print(f"[PASS] 14. Work Shifts retrieved ({len(res['data']['shifts'])} shifts)")

    # 10. Holidays Module
    res, status = req('/holidays', 'GET', token=admin_token)
    assert status == 200 and len(res['data']['holidays']) > 0, 'Holidays failed'
    print(f"[PASS] 15. Holiday Calendar retrieved ({len(res['data']['holidays'])} holidays)")

    # 11. Staff Attendance & Field Tasks
    res, status = req('/attendance/today', 'GET', token=staff_token)
    assert status == 200 and 'attendance' in res['data'], 'Staff today attendance failed'
    att_record = res['data']['attendance'] or {}
    att_status = att_record.get('status') or 'NOT_STARTED'
    print(f"[PASS] 16. Staff Daily Attendance verified (Status: {att_status})")

    res, status = req('/tasks/today', 'GET', token=staff_token)
    assert status == 200 and 'tasks' in res['data'], 'Staff today tasks failed'
    print(f"[PASS] 17. Staff Field Tasks retrieved ({len(res['data']['tasks'])} assigned)")

    # 12. Leave Management
    res, status = req('/leaves/my-leaves', 'GET', token=staff_token)
    assert status == 200 and 'leaves' in res['data'] and 'balances' in res['data'], 'My leaves failed'
    print(f"[PASS] 18. Staff Leave History & Balances verified ({len(res['data']['leaves'])} applications, {len(res['data']['balances'])} balance categories)")

    res, status = req('/leaves', 'GET', token=admin_token)
    assert status == 200 and 'leaves' in res['data'] and 'summary' in res['data'], 'Admin leaves failed'
    print(f"[PASS] 19. Admin Leave Applications & Summary KPIs verified (Total: {res['data']['summary']['total_requests']}, Pending: {res['data']['summary']['pending_count']})")

    # 13. Reports & Analytics
    res, status = req('/reports/daily-attendance', 'GET', token=admin_token)
    assert status == 200 and 'records' in res['data'], 'Reports daily-attendance failed'
    print(f"[PASS] 20. Daily Attendance Report verified ({len(res['data']['records'])} records)")

    res, status = req('/reports/monthly-summary', 'GET', token=admin_token)
    assert status == 200 and 'records' in res['data'], 'Reports monthly-summary failed'
    print(f"[PASS] 21. Monthly Attendance Summary Report verified ({len(res['data']['records'])} employee records)")

    # 14. Notifications
    res, status = req('/notifications', 'GET', token=admin_token)
    assert status == 200 and 'notifications' in res['data'], 'Notifications failed'
    print(f"[PASS] 22. In-App Notifications verified ({len(res['data']['notifications'])} alerts)")

    # 15. Audit Logs
    res, status = req('/audit-logs', 'GET', token=admin_token)
    assert status == 200 and 'logs' in res['data'], 'Audit logs failed'
    print(f"[PASS] 23. Security Audit Ledger verified ({len(res['data']['logs'])} entries)")

    print("=" * 70)
    print("  SUCCESS: ALL 23 PRE-PUBLISH ENDPOINTS AND RBAC GATES PASSED 100%!")
    print("=" * 70)

if __name__ == '__main__':
    run_checks()
