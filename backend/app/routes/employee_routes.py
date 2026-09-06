from flask import Blueprint, request, g
from app.db import get_db_cursor, query_one, query_all, execute
from app.services.auth_service import hash_password
from app.utils.response import success_response, error_response
from app.middleware.auth import role_required
from app.middleware.audit import log_audit

employee_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

@employee_bp.route('', methods=['GET'])
@role_required(['ADMIN'])
def list_employees():
    """List all employees with search and status filters."""
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()

    sql = """
        SELECT
            e.id, e.employee_code, e.full_name, e.phone, e.email,
            e.department, e.designation, e.joining_date, e.employment_type,
            e.status, e.user_id,
            u.role, u.is_active AS user_active,
            COALESCE(a.status, 'NOT_STARTED') AS today_status,
            TIME_FORMAT(a.check_in_time, '%%h:%%i %%p') AS today_check_in,
            TIME_FORMAT(a.check_out_time, '%%h:%%i %%p') AS today_check_out
        FROM employees e
        JOIN users u ON e.user_id = u.id
        LEFT JOIN attendance a ON e.id = a.employee_id AND a.attendance_date = CURDATE()
        WHERE 1=1
    """
    params = []

    if search:
        sql += " AND (e.full_name LIKE %s OR e.employee_code LIKE %s OR e.email LIKE %s OR e.department LIKE %s)"
        like_search = f"%{search}%"
        params.extend([like_search, like_search, like_search, like_search])

    if status:
        sql += " AND e.status = %s"
        params.append(status)

    sql += " ORDER BY e.id ASC"

    employees = query_all(sql, params) or []
    return success_response(data={'employees': employees, 'total': len(employees)}, message="Employees list retrieved.")


@employee_bp.route('', methods=['POST'])
@role_required(['ADMIN'])
def create_employee():
    """Create a new employee and associated user account in a transaction."""
    data = request.get_json() or {}

    full_name = (data.get('full_name') or '').strip()
    employee_code = (data.get('employee_code') or '').strip().upper()
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()
    phone = (data.get('phone') or '').strip()
    department = (data.get('department') or 'Operations').strip()
    designation = (data.get('designation') or 'Field Executive').strip()
    joining_date = data.get('joining_date')
    employment_type = data.get('employment_type') or 'FULL_TIME'
    role = (data.get('role') or 'STAFF').strip().upper()

    if not full_name or not employee_code or not email or not password:
        return error_response("Full name, employee code, email, and password are required.", 400)

    if len(password) < 6:
        return error_response("Password must be at least 6 characters long.", 400)

    # Enforce strict policy: exactly 2 Admins in system, all others are Staff
    if role == 'ADMIN':
        admin_count = query_one("SELECT COUNT(*) AS cnt FROM users WHERE role = 'ADMIN'")['cnt']
        if admin_count >= 2:
            return error_response("Maximum 2 Administrators allowed in the system. All other accounts must be Employees (STAFF).", 400)

    # Check for existing email in users table
    if query_one("SELECT id FROM users WHERE email = %s", (email,)):
        return error_response(f"An account with email '{email}' already exists.", 400)

    # Check for existing employee code
    if query_one("SELECT id FROM employees WHERE employee_code = %s", (employee_code,)):
        return error_response(f"Employee code '{employee_code}' is already assigned.", 400)

    password_hashed = hash_password(password)

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, %s, TRUE)",
            (email, password_hashed, role)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO employees
              (user_id, employee_code, full_name, phone, email, department, designation, joining_date, employment_type, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURDATE()), %s, 'ACTIVE')
            """,
            (user_id, employee_code, full_name, phone, email, department, designation, joining_date, employment_type)
        )
        employee_id = cursor.lastrowid

    log_audit(
        user_id=g.user['id'],
        action='EMPLOYEE_CREATED',
        entity_type='EMPLOYEE',
        entity_id=employee_id,
        description=f"Created employee {full_name} ({employee_code})"
    )

    return success_response(
        data={'employee_id': employee_id, 'user_id': user_id, 'employee_code': employee_code},
        message=f"Employee '{full_name}' created successfully.",
        status_code=201
    )


@employee_bp.route('/<int:emp_id>', methods=['GET'])
@role_required(['ADMIN'])
def get_employee(emp_id):
    """Retrieve single employee profile details."""
    sql = """
        SELECT
            e.id, e.employee_code, e.full_name, e.phone, e.email,
            e.department, e.designation, e.joining_date, e.employment_type,
            e.status, e.user_id,
            u.role, u.is_active AS user_active
        FROM employees e
        JOIN users u ON e.user_id = u.id
        WHERE e.id = %s
    """
    employee = query_one(sql, (emp_id,))
    if not employee:
        return error_response("Employee not found.", 404)

    return success_response(data={'employee': employee}, message="Employee details retrieved.")


@employee_bp.route('/<int:emp_id>', methods=['PUT'])
@role_required(['ADMIN'])
def update_employee(emp_id):
    """Update employee details."""
    emp = query_one("SELECT id, user_id, email FROM employees WHERE id = %s", (emp_id,))
    if not emp:
        return error_response("Employee not found.", 404)

    data = request.get_json() or {}
    full_name = (data.get('full_name') or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip().lower()
    department = (data.get('department') or '').strip()
    designation = (data.get('designation') or '').strip()
    employment_type = data.get('employment_type') or 'FULL_TIME'
    status = data.get('status')

    if email and email != emp['email']:
        if query_one("SELECT id FROM users WHERE email = %s AND id != %s", (email, emp['user_id'])):
            return error_response(f"The email '{email}' is already in use by another user.", 400)

    with get_db_cursor(commit=True) as cursor:
        if email:
            cursor.execute("UPDATE users SET email = %s WHERE id = %s", (email, emp['user_id']))

        cursor.execute("UPDATE users SET is_active = 1 WHERE id = %s", (emp['user_id'],))

        cursor.execute(
            """
            UPDATE employees
            SET full_name = COALESCE(NULLIF(%s, ''), full_name),
                phone = %s,
                email = COALESCE(NULLIF(%s, ''), email),
                department = COALESCE(NULLIF(%s, ''), department),
                designation = COALESCE(NULLIF(%s, ''), designation),
                employment_type = %s,
                status = 'ACTIVE',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (full_name, phone, email, department, designation, employment_type, emp_id)
        )

    log_audit(
        user_id=g.user['id'],
        action='EMPLOYEE_UPDATED',
        entity_type='EMPLOYEE',
        entity_id=emp_id,
        description=f"Updated employee ID {emp_id}"
    )

    return success_response(message="Employee details updated successfully.")


@employee_bp.route('/<int:emp_id>/toggle-status', methods=['PUT'])
@role_required(['ADMIN'])
def toggle_employee_status(emp_id):
    """Deactivation option is disabled. Return friendly guidance."""
    return error_response("The deactivation option has been disabled. To remove an employee, use the Delete option.", 400)


@employee_bp.route('/<int:emp_id>/reset-password', methods=['POST'])
@role_required(['ADMIN'])
def reset_employee_password(emp_id):
    """Admin reset employee password."""
    data = request.get_json() or {}
    new_password = (data.get('new_password') or '').strip()

    if not new_password or len(new_password) < 6:
        return error_response("New password must be at least 6 characters long.", 400)

    emp = query_one("SELECT id, user_id, full_name FROM employees WHERE id = %s", (emp_id,))
    if not emp:
        return error_response("Employee not found.", 404)

    new_hash = hash_password(new_password)
    execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, emp['user_id']))

    log_audit(
        user_id=g.user['id'],
        action='PASSWORD_RESET_BY_ADMIN',
        entity_type='EMPLOYEE',
        entity_id=emp_id,
        description=f"Admin reset password for {emp['full_name']}"
    )

    return success_response(message=f"Password for {emp['full_name']} reset successfully.")


@employee_bp.route('/<int:emp_id>', methods=['DELETE'])
@role_required(['ADMIN'])
def delete_employee(emp_id):
    """Permanently delete an employee, their attendance records, and user account."""
    emp = query_one("SELECT id, user_id, full_name, employee_code FROM employees WHERE id = %s", (emp_id,))
    if not emp:
        return error_response("Employee not found.", 404)

    # Prevent deleting own logged in administrator account
    if emp['id'] == g.user.get('employee_id') or emp['user_id'] == g.user.get('id'):
        return error_response("You cannot delete your own active administrator account.", 400)

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM attendance WHERE employee_id = %s", (emp_id,))
        cursor.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
        if emp.get('user_id'):
            cursor.execute("DELETE FROM users WHERE id = %s", (emp['user_id'],))

    log_audit(
        user_id=g.user['id'],
        action='EMPLOYEE_DELETED',
        entity_type='EMPLOYEE',
        entity_id=emp_id,
        description=f"Deleted employee {emp['full_name']} ({emp['employee_code']})"
    )

    return success_response(message=f"Employee '{emp['full_name']}' has been permanently deleted.")
