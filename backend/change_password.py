"""
CLI Utility to change user email (username) and password for LogiTrack PRO.
Usage:
    python change_password.py --email admin@logistics.com --password myNewPassword123
    python change_password.py --email admin@logistics.com --new-email newadmin@logistics.com --password myNewPassword123
    python change_password.py  (Interactive mode)
"""

import sys
import os
import argparse

# Add parent directory to sys.path so app modules can be loaded
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import query_one, execute
from app.services.auth_service import hash_password

def change_credentials(current_email, new_password=None, new_email=None):
    current_email = (current_email or '').strip()
    if not current_email:
        print("[ERROR] Current email is required.")
        return False

    user = query_one("SELECT id, email, role FROM users WHERE email = %s", (current_email,))
    if not user:
        print(f"[ERROR] User with email '{current_email}' not found.")
        return False

    user_id = user['id']

    # Update email / username if requested
    if new_email and new_email.strip() and new_email.strip() != current_email:
        new_email = new_email.strip()
        existing = query_one("SELECT id FROM users WHERE email = %s AND id != %s", (new_email, user_id))
        if existing:
            print(f"[ERROR] New email '{new_email}' is already taken by another account.")
            return False

        execute("UPDATE users SET email = %s WHERE id = %s", (new_email, user_id))
        execute("UPDATE employees SET email = %s WHERE user_id = %s", (new_email, user_id))
        print(f"[SUCCESS] Username/Email updated from '{current_email}' to '{new_email}'.")
        current_email = new_email

    # Update password if requested
    if new_password and new_password.strip():
        new_password = new_password.strip()
        if len(new_password) < 6:
            print("[ERROR] Password must be at least 6 characters long.")
            return False

        new_hash = hash_password(new_password)
        execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        print(f"[SUCCESS] Password updated successfully for '{current_email}'.")

    print(f"\n[DONE] Account (Role: {user['role']}) updated:")
    print(f"       Username (Email): {current_email}")
    if new_password:
        print(f"       Password:        [Updated Successfully]")
    return True

def main():
    parser = argparse.ArgumentParser(description="Change LogiTrack user credentials")
    parser.add_argument("--email", "-e", help="Current email of the user (e.g. admin@logistics.com)")
    parser.add_argument("--new-email", "-n", help="New email / username to assign")
    parser.add_argument("--password", "-p", help="New plaintext password to set")

    args = parser.parse_args()

    if args.email:
        change_credentials(args.email, args.password, args.new_email)
    else:
        # Interactive mode
        print("=" * 60)
        print("  LOGITRACK PRO - CREDENTIAL MANAGER")
        print("=" * 60)
        email = input("Enter current user email (default: admin@logistics.com): ").strip() or "admin@logistics.com"
        new_email = input(f"Enter new email [leave blank to keep '{email}']: ").strip() or None
        password = input("Enter new password [min 6 chars]: ").strip()
        if not password:
            print("[CANCELLED] No new password provided.")
            return
        change_credentials(email, password, new_email)

if __name__ == "__main__":
    main()
