import urllib.request
import json

base_url = 'http://127.0.0.1:5000/api'

def req(path, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req_obj = urllib.request.Request(
        f'{base_url}{path}',
        data=json.dumps(data).encode('utf-8') if data else None,
        headers=headers,
        method=method
    )
    try:
        with urllib.request.urlopen(req_obj) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

# 1. Admin login
from app.db import query_one
admin = query_one("SELECT email FROM users WHERE role = 'ADMIN' LIMIT 1")
admin_email = admin['email'] if admin else 'arunachalam@sevenstarslogistics.com'
status, res = req('/auth/login', 'POST', {'identifier': admin_email, 'password': 'admin123'})
assert status == 200, f'Admin login failed: {res}'
token = res['data']['token']
admin_emp_id = res['data']['user']['employee_id']
print('[PASS] Admin login successful')

# 2. Test self-deletion prevention
status, res = req(f'/employees/{admin_emp_id}', 'DELETE', token=token)
assert status == 400 and 'cannot delete your own' in res.get('message', '').lower(), f'Self-delete check failed: {res}'
print('[PASS] Self-deletion guard confirmed blocked')

# 3. Create a temporary employee
new_emp = {
    'full_name': 'Delete Test Staff',
    'employee_code': 'DEL999',
    'email': 'del_test@example.com',
    'password': 'password123',
    'phone': '9876500000',
    'department': 'Fleet',
    'designation': 'Driver',
    'employment_type': 'FULL_TIME'
}
status, res = req('/employees', 'POST', new_emp, token=token)
assert status == 201, f'Create employee failed: {res}'
emp_id = res['data']['employee_id']
print(f'[PASS] Created temporary employee ID: {emp_id}')

# 4. Verify employee exists in list
status, res = req(f'/employees?search=DEL999', token=token)
assert any(e['id'] == emp_id for e in res['data']['employees']), 'Created employee not in list'
print('[PASS] Employee appears in list')

# 5. Delete employee
status, res = req(f'/employees/{emp_id}', 'DELETE', token=token)
assert status == 200, f'Delete employee failed: {res}'
msg = res.get('message')
print(f'[PASS] Successfully deleted employee: {msg}')

# 6. Verify employee is gone
status, res = req(f'/employees?search=DEL999', token=token)
assert not any(e['id'] == emp_id for e in res['data']['employees']), 'Employee still found after deletion'
print('[PASS] Verified employee permanently removed from database')
print('=== ALL DELETE TESTS PASSED ===')
