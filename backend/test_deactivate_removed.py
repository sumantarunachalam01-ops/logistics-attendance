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

# 1. Admin login test
status, res = req('/auth/login', 'POST', {'identifier': 'arunachalam@sevenstarslogistics.com', 'password': 'admin123'})
print('Login status:', status, 'Success:', res.get('success'))
assert status == 200, f'Admin login failed: {res}'
token = res['data']['token']
print('[PASS] Admin login verified')

# 2. Test toggle status is disabled
status, res = req('/employees/3/toggle-status', 'PUT', token=token)
print('Toggle status response:', status, res.get('message'))
assert status == 400 and 'disabled' in res.get('message', '').lower(), f'Unexpected response: {res}'
print('[PASS] Deactivation endpoint verified safely disabled')

# 3. Fetch employee list
status, res = req('/employees', token=token)
assert status == 200, f'Fetch employees failed: {res}'
emp_count = len(res['data']['employees'])
print(f'[PASS] Fetched {emp_count} employees successfully')
print('=== ALL VERIFICATIONS PASSED ===')
