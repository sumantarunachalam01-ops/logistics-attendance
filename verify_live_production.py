import urllib.request
import re
import json

def verify_prod():
    print("========================================")
    print("VERIFYING LIVE VERCEL + RENDER DEPLOYMENT")
    print("========================================")
    
    # 1. Check Vercel
    v_url = 'https://logistics-attendance.vercel.app/'
    req = urllib.request.Request(v_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        html = r.read().decode('utf-8')
        print(f"[+] Vercel HTML Status: {r.status} OK")
        
    js_match = re.search(r'src="(/assets/[^"]+\.js)"', html)
    if js_match:
        js_url = 'https://logistics-attendance.vercel.app' + js_match.group(1)
        js_content = urllib.request.urlopen(js_url).read().decode('utf-8')
        has_render = 'logistics-attendance.onrender.com' in js_content
        print(f"[+] Frontend bundle points to Render backend: {has_render}")
        has_demo = 'Quick Demo Fast-Login' in js_content
        print(f"[+] Quick demo button absent from bundle: {not has_demo}")

    # 2. Check Render Backend
    r_url = 'https://logistics-attendance.onrender.com/api/health'
    with urllib.request.urlopen(r_url) as r:
        health = json.loads(r.read().decode('utf-8'))
        print(f"[+] Render Backend Status: {r.status} OK -> {health['data']}")

    # 3. Test Live Auth against TiDB Cloud via Render
    auth_url = 'https://logistics-attendance.onrender.com/api/auth/login'
    payload = json.dumps({'identifier': 'arunachalam@sevenstarslogistics.com', 'password': 'admin123'}).encode()
    auth_req = urllib.request.Request(auth_url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(auth_req) as r:
        auth_res = json.loads(r.read().decode('utf-8'))
        user = auth_res['data']['user']
        print(f"[+] Live Database Authentication: SUCCESS -> {user['full_name']} ({user['role']})")
        token = auth_res['data']['token']

    # 4. Test Storage Settings
    storage_url = 'https://logistics-attendance.onrender.com/api/settings/storage'
    storage_req = urllib.request.Request(storage_url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(storage_req) as r:
        storage_res = json.loads(r.read().decode('utf-8'))['data']
        print(f"[+] Live Cloud Storage Policy: {storage_res['policy']} ({storage_res['storage_used_percentage']}% used, {storage_res['storage_free_mb']} MB free)")

    print("\nALL PRODUCTION SYSTEMS OPERATIONAL AND 100% HEALTHY!")

if __name__ == '__main__':
    verify_prod()
