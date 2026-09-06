from flask import Blueprint, g
from datetime import datetime
from zoneinfo import ZoneInfo
from app.config import Config
from app.db import query_one, query_all
from app.utils.response import success_response
from app.middleware.auth import role_required
from app.services.cleanup_service import maybe_run_daily_auto_cleanup

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

def get_kolkata_now():
    return datetime.now(ZoneInfo(Config.TIMEZONE))

def format_minutes_to_hm(minutes):
    if not minutes:
        return "0h 00m"
    try:
        total_m = int(minutes)
    except (ValueError, TypeError):
        return "0h 00m"
    if total_m <= 0:
        return "0h 00m"
    h = total_m // 60
    m = total_m % 60
    return f"{h:02d}h {m:02d}m"

@dashboard_bp.route('/today', methods=['GET'])
@role_required(['ADMIN'])
def get_today_dashboard():
    """
    Retrieve Section 9 Admin Today's Attendance Overview:
    Cards: Total Staff, Present, Absent, Currently Working, Completed Attendance.
    Table: All staff members with today's status, times, live/completed hours, location & selfie info.
    """
    # Background check: auto-prune data older than retention window once daily
    try:
        maybe_run_daily_auto_cleanup()
    except Exception as e:
        pass

    now_ist = get_kolkata_now()
    today_str = now_ist.strftime('%Y-%m-%d')

    # Fetch all active staff employees with today's attendance record (if any)
    sql = """
        SELECT
            e.id AS employee_id,
            e.employee_code,
            e.full_name,
            e.phone,
            e.department,
            e.designation,
            a.id AS attendance_id,
            a.check_in_time,
            TIME_FORMAT(a.check_in_time, '%%h:%%i %%p') AS check_in_formatted,
            TIME_FORMAT(a.check_in_time, '%%h:%%i:%%s %%p') AS check_in_exact,
            a.check_out_time,
            TIME_FORMAT(a.check_out_time, '%%h:%%i %%p') AS check_out_formatted,
            TIME_FORMAT(a.check_out_time, '%%h:%%i:%%s %%p') AS check_out_exact,
            a.check_in_latitude,
            a.check_in_longitude,
            a.check_in_accuracy,
            a.check_out_latitude,
            a.check_out_longitude,
            a.check_out_accuracy,
            a.check_in_selfie,
            a.check_out_selfie,
            a.status AS raw_status,
            a.total_work_minutes,
            a.overtime_minutes,
            a.remarks
        FROM employees e
        JOIN users u ON e.user_id = u.id
        LEFT JOIN attendance a ON e.id = a.employee_id AND a.attendance_date = %s
        WHERE u.role = 'STAFF' AND e.status = 'ACTIVE'
        ORDER BY e.id ASC
    """
    staff_rows = query_all(sql, (today_str,)) or []

    total_staff = len(staff_rows)
    present_count = 0
    currently_working_count = 0
    completed_count = 0
    absent_count = 0

    roster = []
    for r in staff_rows:
        check_in = r.get('check_in_time')
        check_out = r.get('check_out_time')
        raw_status = r.get('raw_status')

        # Determine user-friendly display status
        if check_in and check_out:
            display_status = 'COMPLETED'
            completed_count += 1
            present_count += 1
            minutes = r.get('total_work_minutes') or 0
            hours_formatted = format_minutes_to_hm(minutes)
        elif check_in and not check_out:
            display_status = 'WORKING'
            currently_working_count += 1
            present_count += 1
            # Calculate elapsed live hours
            in_dt = check_in
            if in_dt.tzinfo is None:
                in_dt = in_dt.replace(tzinfo=ZoneInfo(Config.TIMEZONE))
            elapsed = max(0, int((now_ist - in_dt).total_seconds() // 60))
            hours_formatted = format_minutes_to_hm(elapsed)
        elif raw_status == 'LEAVE':
            display_status = 'LEAVE'
            hours_formatted = '—'
        else:
            display_status = 'NOT_STARTED'
            absent_count += 1
            hours_formatted = '—'

        roster.append({
            'employee_id': r['employee_id'],
            'employee_code': r['employee_code'],
            'full_name': r['full_name'],
            'department': r['department'],
            'designation': r['designation'],
            'attendance_id': r['attendance_id'],
            'status': display_status,
            'check_in_formatted': r['check_in_formatted'] or '—',
            'check_in_exact': r['check_in_exact'],
            'check_out_formatted': r['check_out_formatted'] or '—',
            'check_out_exact': r['check_out_exact'],
            'hours_formatted': hours_formatted,
            'total_work_minutes': r['total_work_minutes'] or 0,
            'overtime_formatted': format_minutes_to_hm(r['overtime_minutes']) if r['overtime_minutes'] else '—',
            'check_in_latitude': r['check_in_latitude'],
            'check_in_longitude': r['check_in_longitude'],
            'check_in_accuracy': r['check_in_accuracy'],
            'check_out_latitude': r['check_out_latitude'],
            'check_out_longitude': r['check_out_longitude'],
            'check_out_accuracy': r['check_out_accuracy'],
            'check_in_selfie': r['check_in_selfie'],
            'check_out_selfie': r['check_out_selfie'],
            'remarks': r['remarks']
        })

    stats = {
        'total_staff': total_staff,
        'present': present_count,
        'absent': absent_count,
        'currently_working': currently_working_count,
        'completed': completed_count,
        'today_date': today_str,
        'today_formatted': now_ist.strftime('%A, %B %d, %Y'),
        'current_time_formatted': now_ist.strftime('%I:%M %p')
    }

    return success_response(data={'stats': stats, 'roster': roster}, message="Today's attendance retrieved.")
