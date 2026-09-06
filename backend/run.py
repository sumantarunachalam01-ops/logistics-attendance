import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[INFO] Logistics Attendance Backend API running on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
