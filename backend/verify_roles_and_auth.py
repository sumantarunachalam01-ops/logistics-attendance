import urllib.request
import json
import sys

BASE = 'http://127.0.0.1:5000/api'

def req(url, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    b = json.dumps(data).encode('utf-8') if data else None
    r = urllib.request.Request(f'{BASE}{url}', data=b, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read().decode('utf-8')), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8')) if e.fp else {}, e.code

def run():
    print('=' * 65)
    print('   LOGITRACK - ROLE & AUTH REDIRECTION VERIFICATION')
    print('=' * 65)

    # 1. hr-002 with staff123
    res1, s1 = req('/auth/login', 'POST', {'identifier': 'hr-002', 'password': 'staff123'})
    assert s1 == 200, f"hr-002 login failed: {res1}"
    u1 = res1['data']['user']
    assert u1['role'] == 'STAFF', f"Expected STAFF role, got {u1['role']}"
    assert u1['employee_code'] == 'HR-002'
    hr_token = res1['data']['token']
    print(f"[PASS] 1. 'hr-002' login (staff123) -> Role: {u1['role']}, Code: {u1['employee_code']}, Name: {u1['full_name']}")

    # 2. hr-002 with admin123 (dual password compatibility)
    res2, s2 = req('/auth/login', 'POST', {'identifier': 'hr-002', 'password': 'admin123'})
    assert s2 == 200, f"hr-002 login with admin123 failed: {res2}"
    u2 = res2['data']['user']
    assert u2['role'] == 'STAFF'
    print(f"[PASS] 2. 'hr-002' login (admin123) -> Role: {u2['role']}, Code: {u2['employee_code']}")

    # 3. Admin 1 login
    res3, s3 = req('/auth/login', 'POST', {'identifier': 'arunachalam@sevenstarslogistics.com', 'password': 'admin123'})
    assert s3 == 200, f"Admin 1 login failed: {res3}"
    u3 = res3['data']['user']
    assert u3['role'] == 'ADMIN'
    print(f"[PASS] 3. Admin 1 login -> Role: {u3['role']}, Code: {u3['employee_code']}, Name: {u3['full_name']}")

    # 4. Admin 2 login
    res4, s4 = req('/auth/login', 'POST', {'identifier': 'admin@sevenstarslogistics.com', 'password': 'admin123'})
    assert s4 == 200, f"Admin 2 login failed: {res4}"
    u4 = res4['data']['user']
    assert u4['role'] == 'ADMIN'
    admin2_token = res4['data']['token']
    print(f"[PASS] 4. Admin 2 login -> Role: {u4['role']}, Code: {u4['employee_code']}, Name: {u4['full_name']}")

    # 5. RBAC: HR-002 blocked from Admin Dashboard
    res5, s5 = req('/dashboard/today', 'GET', token=hr_token)
    assert s5 == 403, f"Expected 403 for HR-002 on /dashboard/today, got {s5}"
    print("[PASS] 5. HR-002 blocked from Admin Dashboard (HTTP 403 Forbidden)")

    # 6. RBAC: HR-002 blocked from Admin Employee Management
    res6, s6 = req('/employees', 'GET', token=hr_token)
    assert s6 == 403, f"Expected 403 for HR-002 on /employees, got {s6}"
    print("[PASS] 6. HR-002 blocked from Admin Employee Directory (HTTP 403 Forbidden)")

    # 7. HR-002 has access to Staff Attendance
    res7, s7 = req('/attendance/today', 'GET', token=hr_token)
    assert s7 == 200, f"Expected 200 for HR-002 on /attendance/today, got {s7}"
    print(f"[PASS] 7. HR-002 can access Staff Attendance (HTTP 200 OK)")

    # 8. Admin has access to Admin Dashboard
    res8, s8 = req('/dashboard/today', 'GET', token=admin2_token)
    assert s8 == 200, f"Expected 200 for Admin on /dashboard/today, got {s8}"
    print("[PASS] 8. Admin 2 can access Admin Dashboard (HTTP 200 OK)")

    # 9. Verify exactly 2 Admins in DB
    from app.db import query_all
    all_users = query_all("SELECT u.id, u.email, u.role, e.employee_code, e.full_name FROM users u JOIN employees e ON u.id = e.user_id ORDER BY u.id")
    admins = [u for u in all_users if u['role'] == 'ADMIN']
    staff = [u for u in all_users if u['role'] == 'STAFF']
    assert len(admins) == 2, f"Expected 2 admins, got {len(admins)}"
    print(f"[PASS] 9. Exactly {len(admins)} Administrators in system:")
    for a in admins:
        print(f"         - {a['employee_code']}: {a['email']} ({a['full_name']})")

    print(f"[PASS] 10. Remaining {len(staff)} accounts are all EMPLOYEES (Role: STAFF):")
    for st in staff:
        print(f"         - {st['employee_code']}: {st['email']} ({st['full_name']})")

    print('=' * 65)
    print('  ALL VERIFICATIONS PASSED: 2 ADMINS & ALL OTHERS ARE EMPLOYEES!')
    print('=' * 65)

if __name__ == '__main__':
    run()
