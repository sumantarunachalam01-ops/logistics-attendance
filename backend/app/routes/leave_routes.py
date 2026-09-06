from flask import Blueprint, request, g
from datetime import datetime, date, timedelta
from app.db import query_all, query_one, execute
from app.middleware.auth import jwt_required, role_required
from app.middleware.audit import log_audit
from app.utils.response import success_response, error_response

leave_bp = Blueprint('leaves', __name__, url_prefix='/api/leaves')

def daterange(start_date, end_date):
    """Yield all dates from start_date to end_date inclusive."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

@leave_bp.route('', methods=['GET'])
@role_required(['ADMIN', 'HR'])
def get_all_leaves():
    """
    Admin/HR fetches all leave applications with multi-criteria filtering and summary KPIs.
    """
    status_filter = request.args.get('status')
    dept_filter = request.args.get('department')
    emp_filter = request.args.get('employee_id')
    leave_type = request.args.get('leave_type')
    month = request.args.get('month') # YYYY-MM
    search = (request.args.get('search') or '').strip()

    sql = """
        SELECT
            l.id, l.employee_id, l.leave_type, l.start_date, l.end_date,
            l.reason, l.status, l.reviewed_by, l.review_remarks, l.reviewed_at, l.created_at,
            e.employee_code, e.full_name AS employee_name, e.department, e.designation,
            u_rev.email AS reviewer_email,
            DATEDIFF(l.end_date, l.start_date) + 1 AS days_count
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        LEFT JOIN users u_rev ON l.reviewed_by = u_rev.id
        WHERE 1=1
    """
    params = []

    if status_filter:
        sql += " AND l.status = %s"
        params.append(status_filter)

    if dept_filter:
        sql += " AND e.department = %s"
        params.append(dept_filter)

    if emp_filter:
        sql += " AND l.employee_id = %s"
        params.append(emp_filter)

    if leave_type:
        sql += " AND l.leave_type = %s"
        params.append(leave_type)

    if month:
        sql += " AND (DATE_FORMAT(l.start_date, '%%Y-%%m') = %s OR DATE_FORMAT(l.end_date, '%%Y-%%m') = %s)"
        params.extend([month, month])

    if search:
        sql += " AND (e.full_name LIKE %s OR e.employee_code LIKE %s OR l.reason LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    sql += " ORDER BY CASE l.status WHEN 'PENDING' THEN 1 ELSE 2 END, l.created_at DESC"

    leaves = query_all(sql, params)

    # Compute KPI summary metrics
    stats_sql = """
        SELECT
            COUNT(*) AS total_requests,
            SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) AS pending_count,
            SUM(CASE WHEN status = 'APPROVED' AND (start_date <= CURDATE() AND end_date >= CURDATE()) THEN 1 ELSE 0 END) AS on_leave_today,
            SUM(CASE WHEN status = 'APPROVED' AND MONTH(start_date) = MONTH(CURDATE()) AND YEAR(start_date) = YEAR(CURDATE()) THEN 1 ELSE 0 END) AS approved_this_month,
            SUM(CASE WHEN status = 'REJECTED' AND MONTH(start_date) = MONTH(CURDATE()) AND YEAR(start_date) = YEAR(CURDATE()) THEN 1 ELSE 0 END) AS rejected_this_month
        FROM leaves
    """
    stats = query_one(stats_sql) or {}

    return success_response(
        data={
            'leaves': leaves,
            'summary': {
                'total_requests': stats.get('total_requests') or 0,
                'pending_count': stats.get('pending_count') or 0,
                'on_leave_today': stats.get('on_leave_today') or 0,
                'approved_this_month': stats.get('approved_this_month') or 0,
                'rejected_this_month': stats.get('rejected_this_month') or 0,
            }
        },
        message="Leave records retrieved."
    )

@leave_bp.route('/my-leaves', methods=['GET'])
@jwt_required
def get_my_leaves():
    """
    Staff / logged-in user retrieves their personal leave applications and leave balance summary.
    """
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return error_response("Employee profile not associated with this account.", 403)

    # 1. Fetch employee's leaves
    sql = """
        SELECT
            l.id, l.leave_type, l.start_date, l.end_date, l.reason, l.status,
            l.review_remarks, l.reviewed_at, l.created_at,
            DATEDIFF(l.end_date, l.start_date) + 1 AS days_count
        FROM leaves l
        WHERE l.employee_id = %s
        ORDER BY l.created_at DESC
    """
    my_leaves = query_all(sql, (employee_id,))

    # 2. Compute Days Taken by Type this year
    balance_sql = """
        SELECT
            leave_type,
            SUM(DATEDIFF(end_date, start_date) + 1) AS days_taken
        FROM leaves
        WHERE employee_id = %s
          AND status = 'APPROVED'
          AND YEAR(start_date) = YEAR(CURDATE())
        GROUP BY leave_type
    """
    taken_records = query_all(balance_sql, (employee_id,))
    taken_dict = {row['leave_type']: int(row['days_taken']) for row in taken_records}

    # Standard annual allowances for logistics personnel
    allowance = {
        'CASUAL': 12,
        'SICK': 10,
        'ANNUAL': 15,
        'EMERGENCY': 5
    }

    balances = []
    for l_type, total_allotted in allowance.items():
        used = taken_dict.get(l_type, 0)
        balances.append({
            'leave_type': l_type,
            'allotted': total_allotted,
            'used': used,
            'available': max(0, total_allotted - used)
        })

    return success_response(
        data={
            'leaves': my_leaves,
            'balances': balances,
            'pending_count': sum(1 for l in my_leaves if l['status'] == 'PENDING'),
            'approved_count': sum(1 for l in my_leaves if l['status'] == 'APPROVED')
        },
        message="Personal leave applications retrieved."
    )

@leave_bp.route('', methods=['POST'])
@jwt_required
def apply_leave():
    """
    Employee applies for leave (CASUAL, SICK, ANNUAL, EMERGENCY, OTHER).
    Validates date format, date range, and avoids overlapping requests.
    """
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return error_response("Only registered employees can submit leave applications.", 403)

    data = request.get_json() or {}
    leave_type = (data.get('leave_type') or 'CASUAL').strip().upper()
    start_date_str = (data.get('start_date') or '').strip()
    end_date_str = (data.get('end_date') or '').strip()
    reason = (data.get('reason') or '').strip()

    valid_types = ['CASUAL', 'SICK', 'ANNUAL', 'EMERGENCY', 'OTHER']
    if leave_type not in valid_types:
        return error_response(f"Invalid leave type. Must be one of: {', '.join(valid_types)}", 400)

    if not start_date_str or not end_date_str:
        return error_response("Start date and end date are required.", 400)

    if not reason:
        return error_response("A reason for leave is required.", 400)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return error_response("Dates must be formatted as YYYY-MM-DD.", 400)

    if end_date < start_date:
        return error_response("End date cannot be earlier than start date.", 400)

    days_requested = (end_date - start_date).days + 1

    # Check for overlapping pending or approved leaves
    overlap_sql = """
        SELECT id, leave_type, start_date, end_date, status
        FROM leaves
        WHERE employee_id = %s
          AND status IN ('PENDING', 'APPROVED')
          AND start_date <= %s
          AND end_date >= %s
        LIMIT 1
    """
    overlap = query_one(overlap_sql, (employee_id, end_date_str, start_date_str))
    if overlap:
        return error_response(
            f"You already have a {overlap['status'].lower()} leave request ({overlap['leave_type']}) "
            f"overlapping this period ({overlap['start_date']} to {overlap['end_date']}).",
            400
        )

    # Insert leave application
    insert_sql = """
        INSERT INTO leaves (employee_id, leave_type, start_date, end_date, reason, status)
        VALUES (%s, %s, %s, %s, %s, 'PENDING')
    """
    exec_res = execute(insert_sql, (employee_id, leave_type, start_date_str, end_date_str, reason))
    leave_id = exec_res['lastrowid']

    # Fetch employee info for notification & audit
    emp = query_one("SELECT full_name, employee_code FROM employees WHERE id = %s", (employee_id,))
    emp_name = emp['full_name'] if emp else 'Employee'

    # Notify HR/Admin in notifications table
    admin_emps = query_all(
        "SELECT e.id FROM employees e JOIN users u ON e.user_id = u.id WHERE u.role IN ('ADMIN', 'HR')"
    )
    for a in admin_emps:
        execute(
            """INSERT INTO notifications (employee_id, title, message, type)
               VALUES (%s, 'New Leave Application', %s, 'LEAVE')""",
            (a['id'], f"{emp_name} requested {days_requested} day(s) of {leave_type} leave from {start_date_str} to {end_date_str}.")
        )

    log_audit(
        user_id=g.user['id'],
        action='LEAVE_APPLIED',
        entity_type='LEAVE',
        entity_id=leave_id,
        description=f"{emp_name} applied for {days_requested} days {leave_type} leave ({start_date_str} to {end_date_str})"
    )

    return success_response(
        data={
            'leave_id': leave_id,
            'leave_type': leave_type,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'days_count': days_requested,
            'status': 'PENDING'
        },
        message="Leave application submitted successfully. Awaiting HR approval.",
        status_code=201
    )

@leave_bp.route('/<int:leave_id>/approve', methods=['PUT', 'POST'])
@role_required(['ADMIN', 'HR'])
def approve_leave(leave_id):
    """
    HR/Admin approves leave application.
    Updates leave status to APPROVED, records audit, notifies employee,
    and automatically populates the attendance ledger with status 'LEAVE' for all dates in range.
    """
    data = request.get_json() or {}
    review_remarks = (data.get('review_remarks') or data.get('remarks') or 'Approved by Management').strip()

    leave = query_one(
        """SELECT l.*, e.full_name, e.employee_code, e.id AS emp_id
           FROM leaves l
           JOIN employees e ON l.employee_id = e.id
           WHERE l.id = %s""",
        (leave_id,)
    )
    if not leave:
        return error_response("Leave record not found.", 404)

    if leave['status'] == 'APPROVED':
        return error_response("This leave request is already approved.", 400)

    # 1. Update leave record
    update_sql = """
        UPDATE leaves
        SET status = 'APPROVED',
            reviewed_by = %s,
            review_remarks = %s,
            reviewed_at = NOW()
        WHERE id = %s
    """
    execute(update_sql, (g.user['id'], review_remarks, leave_id))

    # 2. Reflect on Attendance Ledger (populate each date with LEAVE status)
    start_d = leave['start_date']
    end_d = leave['end_date']

    for d in daterange(start_d, end_d):
        d_str = d.strftime('%Y-%m-%d')
        # Check if record exists
        existing_att = query_one(
            "SELECT id, status FROM attendance WHERE employee_id = %s AND attendance_date = %s",
            (leave['employee_id'], d_str)
        )
        if existing_att:
            # Overwrite status if not clocked in or override to LEAVE
            execute(
                """UPDATE attendance
                   SET status = 'LEAVE',
                       remarks = CONCAT(COALESCE(remarks, ''), ' | On Approved ', %s, ' Leave: ', %s)
                   WHERE id = %s""",
                (leave['leave_type'], review_remarks, existing_att['id'])
            )
        else:
            execute(
                """INSERT INTO attendance (employee_id, attendance_date, status, remarks)
                   VALUES (%s, %s, 'LEAVE', %s)""",
                (leave['employee_id'], d_str, f"On Approved {leave['leave_type']} Leave: {review_remarks}")
            )

    # 3. In-app notification to employee
    execute(
        """INSERT INTO notifications (employee_id, title, message, type)
           VALUES (%s, 'Leave Request Approved', %s, 'LEAVE')""",
        (
            leave['employee_id'],
            f"Your {leave['leave_type']} leave from {start_d} to {end_d} has been approved. Note: {review_remarks}"
        )
    )

    # 4. Audit Log
    log_audit(
        user_id=g.user['id'],
        action='LEAVE_APPROVED',
        entity_type='LEAVE',
        entity_id=leave_id,
        description=f"Admin {g.user['email']} approved leave #{leave_id} for {leave['full_name']} ({start_d} to {end_d})"
    )

    return success_response(
        data={
            'leave_id': leave_id,
            'status': 'APPROVED',
            'review_remarks': review_remarks,
            'start_date': str(start_d),
            'end_date': str(end_d)
        },
        message=f"Leave application for {leave['full_name']} approved and synced to attendance ledger."
    )

@leave_bp.route('/<int:leave_id>/reject', methods=['PUT', 'POST'])
@role_required(['ADMIN', 'HR'])
def reject_leave(leave_id):
    """
    HR/Admin rejects a leave application with mandatory remarks.
    """
    data = request.get_json() or {}
    review_remarks = (data.get('review_remarks') or data.get('remarks') or '').strip()

    if not review_remarks:
        return error_response("Review remarks explaining the reason for rejection are required.", 400)

    leave = query_one(
        """SELECT l.*, e.full_name
           FROM leaves l
           JOIN employees e ON l.employee_id = e.id
           WHERE l.id = %s""",
        (leave_id,)
    )
    if not leave:
        return error_response("Leave record not found.", 404)

    if leave['status'] == 'REJECTED':
        return error_response("This leave request is already marked as rejected.", 400)

    update_sql = """
        UPDATE leaves
        SET status = 'REJECTED',
            reviewed_by = %s,
            review_remarks = %s,
            reviewed_at = NOW()
        WHERE id = %s
    """
    execute(update_sql, (g.user['id'], review_remarks, leave_id))

    # Notify employee
    execute(
        """INSERT INTO notifications (employee_id, title, message, type)
           VALUES (%s, 'Leave Request Rejected', %s, 'LEAVE')""",
        (
            leave['employee_id'],
            f"Your leave application from {leave['start_date']} to {leave['end_date']} was declined. Reason: {review_remarks}"
        )
    )

    # Audit Log
    log_audit(
        user_id=g.user['id'],
        action='LEAVE_REJECTED',
        entity_type='LEAVE',
        entity_id=leave_id,
        description=f"Admin rejected leave #{leave_id} for {leave['full_name']}. Reason: {review_remarks}"
    )

    return success_response(
        data={'leave_id': leave_id, 'status': 'REJECTED', 'review_remarks': review_remarks},
        message="Leave application rejected."
    )

@leave_bp.route('/<int:leave_id>/cancel', methods=['POST'])
@jwt_required
def cancel_leave(leave_id):
    """
    Employee can cancel their own pending or future approved leave request.
    """
    employee_id = g.user.get('employee_id')
    leave = query_one("SELECT * FROM leaves WHERE id = %s", (leave_id,))
    if not leave:
        return error_response("Leave application not found.", 404)

    # Must be owner or Admin
    if leave['employee_id'] != employee_id and g.user.get('role') not in ['ADMIN', 'HR']:
        return error_response("Unauthorized: You cannot cancel another employee's leave.", 403)

    if leave['status'] in ['REJECTED', 'CANCELLED']:
        return error_response(f"Cannot cancel leave because it is already {leave['status']}.", 400)

    execute("UPDATE leaves SET status = 'CANCELLED' WHERE id = %s", (leave_id,))

    # If it was previously approved, remove LEAVE status from attendance for future/today dates
    if leave['status'] == 'APPROVED':
        start_d = leave['start_date']
        end_d = leave['end_date']
        for d in daterange(start_d, end_d):
            if d >= date.today():
                execute(
                    "DELETE FROM attendance WHERE employee_id = %s AND attendance_date = %s AND status = 'LEAVE' AND check_in_time IS NULL",
                    (leave['employee_id'], d.strftime('%Y-%m-%d'))
                )

    log_audit(
        user_id=g.user['id'],
        action='LEAVE_CANCELLED',
        entity_type='LEAVE',
        entity_id=leave_id,
        description=f"Leave application #{leave_id} cancelled."
    )

    return success_response(message="Leave application cancelled successfully.")
