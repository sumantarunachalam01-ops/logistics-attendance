import os
import re
import base64
import uuid
import calendar
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, request, g, send_from_directory, current_app, Response
from werkzeug.utils import secure_filename
from app.config import Config
from app.db import query_one, query_all, execute, get_db_cursor
from app.utils.response import success_response, error_response
from app.middleware.auth import jwt_required, role_required
from app.middleware.audit import log_audit

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

def get_kolkata_now():
    """Returns current datetime in Asia/Kolkata timezone."""
    tz = ZoneInfo(Config.TIMEZONE)
    return datetime.now(tz)

def format_minutes_to_hm(minutes):
    """Formats minutes integer into 'Xh Ym' or '0h 00m'."""
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
    return f"{h}h {m:02d}m"

def ensure_selfie_table():
    """Ensure that the persistent selfie_storage table exists in the database."""
    try:
        execute("""
            CREATE TABLE IF NOT EXISTS selfie_storage (
                filename VARCHAR(255) PRIMARY KEY,
                image_data MEDIUMBLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
    except Exception:
        pass


def save_selfie_payload(selfie_str, prefix="selfie"):
    """
    Decodes a base64 selfie image string and writes it to Config.UPLOAD_FOLDER.
    Also persists to the MySQL selfie_storage table so ephemeral cloud container restarts never lose images.
    Returns the saved filename.
    """
    if not selfie_str:
        return None

    # Guarantee headroom: If storage reaches full threshold (90%), automatically
    # prune oldest batch across all staff simultaneously so new data can always be saved
    try:
        from app.services.cleanup_service import ensure_storage_headroom
        ensure_storage_headroom()
    except Exception as e:
        pass

    # Strip data URL header if present (e.g. data:image/jpeg;base64,...)
    if ',' in selfie_str:
        selfie_str = selfie_str.split(',', 1)[1]

    image_data = base64.b64decode(selfie_str)
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.jpg"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)

    # 1. Save to local disk cache (fast immediate serving)
    try:
        with open(filepath, 'wb') as f:
            f.write(image_data)
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not cache selfie to disk: {e}")

    # 2. Persist to MySQL database (survives Render / cloud container spin-downs & restarts)
    try:
        ensure_selfie_table()
        execute("""
            INSERT INTO selfie_storage (filename, image_data)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE image_data = VALUES(image_data)
        """, (filename, image_data))
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Could not persist selfie to database: {e}")

    return filename


@attendance_bp.route('/start', methods=['POST'])
@jwt_required
def start_attendance():
    """
    Start attendance for today:
    Requires live camera selfie, GPS coordinates, accuracy.
    Generates official server timestamp (Asia/Kolkata).
    """
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return error_response("Only registered employees can mark attendance.", 403)

    data = request.get_json() or {}
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    accuracy = data.get('accuracy', 0.0)
    selfie_data = data.get('selfie')

    if latitude is None or longitude is None:
        return error_response("GPS coordinates (latitude and longitude) are strictly required to start attendance.", 400)

    try:
        lat = float(latitude)
        lng = float(longitude)
        acc = float(accuracy) if accuracy is not None else 0.0
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
            return error_response("Invalid GPS coordinate values.", 400)
    except (ValueError, TypeError):
        return error_response("Coordinates must be valid numeric values.", 400)

    if not selfie_data:
        return error_response("Camera selfie capture is required to start attendance.", 400)

    now_ist = get_kolkata_now()
    today_str = now_ist.strftime('%Y-%m-%d')
    server_time_str = now_ist.strftime('%Y-%m-%d %H:%M:%S')

    # Check existing attendance record for today
    existing = query_one(
        "SELECT id, check_in_time, check_out_time, status FROM attendance WHERE employee_id = %s AND attendance_date = %s",
        (employee_id, today_str)
    )
    if existing and existing.get('check_in_time'):
        return error_response("Attendance has already been started for today.", 400)

    # Save selfie
    try:
        selfie_filename = save_selfie_payload(selfie_data, prefix=f"in_emp{employee_id}_{today_str}")
    except Exception as e:
        return error_response(f"Failed to process selfie image: {str(e)}", 400)

    if existing:
        execute(
            """
            UPDATE attendance
            SET check_in_time = %s,
                check_in_latitude = %s,
                check_in_longitude = %s,
                check_in_accuracy = %s,
                check_in_selfie = %s,
                status = 'PRESENT',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (server_time_str, lat, lng, acc, selfie_filename, existing['id'])
        )
        record_id = existing['id']
    else:
        record_id = execute(
            """
            INSERT INTO attendance
              (employee_id, attendance_date, check_in_time, check_in_latitude, check_in_longitude, check_in_accuracy, check_in_selfie, status, total_work_minutes, overtime_minutes)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s, 'PRESENT', 0, 0)
            """,
            (employee_id, today_str, server_time_str, lat, lng, acc, selfie_filename)
        )

    log_audit(
        user_id=g.user['id'],
        action='ATTENDANCE_STARTED',
        entity_type='ATTENDANCE',
        entity_id=record_id,
        description=f"Attendance started at {server_time_str} IST (Lat: {lat}, Lng: {lng}, Acc: ±{acc}m)"
    )

    formatted_time = now_ist.strftime('%I:%M %p')
    return success_response(
        data={
            'id': record_id,
            'attendance_date': today_str,
            'check_in_time': server_time_str,
            'check_in_formatted': formatted_time,
            'latitude': lat,
            'longitude': lng,
            'accuracy': acc,
            'selfie_filename': selfie_filename,
            'status': 'PRESENT',
            'message': 'Attendance Started Successfully'
        },
        message="Attendance Started Successfully"
    )


@attendance_bp.route('/end', methods=['POST'])
@jwt_required
def end_attendance():
    """
    End attendance for today:
    Captures checkout selfie, GPS coordinates, accuracy.
    Generates official server timestamp and calculates duration and overtime.
    """
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return error_response("Only registered employees can mark attendance.", 403)

    data = request.get_json() or {}
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    accuracy = data.get('accuracy', 0.0)
    selfie_data = data.get('selfie')

    if latitude is None or longitude is None:
        return error_response("GPS coordinates are strictly required to end attendance.", 400)

    try:
        lat = float(latitude)
        lng = float(longitude)
        acc = float(accuracy) if accuracy is not None else 0.0
    except (ValueError, TypeError):
        return error_response("Coordinates must be valid numeric values.", 400)

    if not selfie_data:
        return error_response("Camera selfie capture is required to end attendance.", 400)

    now_ist = get_kolkata_now()
    today_str = now_ist.strftime('%Y-%m-%d')
    server_time_str = now_ist.strftime('%Y-%m-%d %H:%M:%S')

    record = query_one(
        "SELECT id, check_in_time, check_out_time FROM attendance WHERE employee_id = %s AND attendance_date = %s",
        (employee_id, today_str)
    )

    if not record or not record.get('check_in_time'):
        return error_response("No active check-in found for today. Please start attendance first.", 400)

    if record.get('check_out_time'):
        return error_response("Attendance has already been ended for today.", 400)

    # Calculate duration
    check_in_dt = record['check_in_time']
    if isinstance(check_in_dt, str):
        check_in_dt = datetime.fromisoformat(check_in_dt)

    # If check_in_dt is naive, attach local IST timezone
    if check_in_dt.tzinfo is None:
        check_in_dt = check_in_dt.replace(tzinfo=ZoneInfo(Config.TIMEZONE))

    diff_seconds = (now_ist - check_in_dt).total_seconds()
    total_work_minutes = max(0, int(diff_seconds // 60))
    overtime_minutes = max(0, total_work_minutes - Config.STANDARD_WORK_MINUTES)

    # Save selfie
    try:
        selfie_filename = save_selfie_payload(selfie_data, prefix=f"out_emp{employee_id}_{today_str}")
    except Exception as e:
        return error_response(f"Failed to process selfie image: {str(e)}", 400)

    execute(
        """
        UPDATE attendance
        SET check_out_time = %s,
            check_out_latitude = %s,
            check_out_longitude = %s,
            check_out_accuracy = %s,
            check_out_selfie = %s,
            total_work_minutes = %s,
            overtime_minutes = %s,
            status = 'PRESENT',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (server_time_str, lat, lng, acc, selfie_filename, total_work_minutes, overtime_minutes, record['id'])
    )

    log_audit(
        user_id=g.user['id'],
        action='ATTENDANCE_COMPLETED',
        entity_type='ATTENDANCE',
        entity_id=record['id'],
        description=f"Attendance ended at {server_time_str} IST. Duration: {total_work_minutes}m, OT: {overtime_minutes}m"
    )

    check_in_formatted = check_in_dt.strftime('%I:%M %p')
    check_out_formatted = now_ist.strftime('%I:%M %p')
    duration_formatted = format_minutes_to_hm(total_work_minutes)
    overtime_formatted = format_minutes_to_hm(overtime_minutes)

    return success_response(
        data={
            'id': record['id'],
            'check_in_formatted': check_in_formatted,
            'check_out_formatted': check_out_formatted,
            'total_work_minutes': total_work_minutes,
            'duration_formatted': duration_formatted,
            'overtime_minutes': overtime_minutes,
            'overtime_formatted': overtime_formatted,
            'message': 'Attendance Completed Successfully'
        },
        message="Attendance Completed Successfully"
    )


@attendance_bp.route('/today', methods=['GET'])
@jwt_required
def get_today_attendance():
    """Retrieve today's attendance details for the requesting user or admin target."""
    employee_id = g.user.get('employee_id')
    if g.user.get('role') == 'ADMIN' and request.args.get('employee_id'):
        employee_id = int(request.args.get('employee_id'))

    if not employee_id:
        return error_response("No employee profile associated with this account.", 400)

    now_ist = get_kolkata_now()
    today_str = now_ist.strftime('%Y-%m-%d')

    sql = """
        SELECT
            a.id,
            a.employee_id,
            a.attendance_date,
            a.check_in_time,
            TIME_FORMAT(a.check_in_time, '%%h:%%i %%p') AS check_in_formatted,
            a.check_out_time,
            TIME_FORMAT(a.check_out_time, '%%h:%%i %%p') AS check_out_formatted,
            a.check_in_latitude,
            a.check_in_longitude,
            a.check_in_accuracy,
            a.check_out_latitude,
            a.check_out_longitude,
            a.check_out_accuracy,
            a.check_in_selfie,
            a.check_out_selfie,
            a.status,
            a.total_work_minutes,
            a.overtime_minutes,
            a.remarks
        FROM attendance a
        WHERE a.employee_id = %s AND a.attendance_date = %s
    """
    record = query_one(sql, (employee_id, today_str))

    # Calculate live elapsed minutes if currently working
    live_work_minutes = 0
    if record and record.get('check_in_time') and not record.get('check_out_time'):
        in_time = record['check_in_time']
        if in_time.tzinfo is None:
            in_time = in_time.replace(tzinfo=ZoneInfo(Config.TIMEZONE))
        live_work_minutes = max(0, int((now_ist - in_time).total_seconds() // 60))

    data = {
        'attendance': record,
        'today_date': today_str,
        'today_formatted': now_ist.strftime('%A, %B %d, %Y'),
        'current_time_formatted': now_ist.strftime('%I:%M %p'),
        'live_work_minutes': live_work_minutes,
        'live_duration_formatted': format_minutes_to_hm(live_work_minutes)
    }
    return success_response(data=data, message="Today's attendance status retrieved.")


@attendance_bp.route('/my', methods=['GET'])
@jwt_required
def get_my_attendance():
    """Staff retrieves their own monthly attendance breakdown."""
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return error_response("Employee profile not found.", 403)

    month_str = request.args.get('month') or get_kolkata_now().strftime('%Y-%m')

    sql = """
        SELECT
            a.id,
            a.attendance_date,
            DATE_FORMAT(a.attendance_date, '%%b %%e') AS date_short,
            DATE_FORMAT(a.attendance_date, '%%W') AS day_name,
            a.check_in_time,
            TIME_FORMAT(a.check_in_time, '%%h:%%i %%p') AS check_in_formatted,
            a.check_out_time,
            TIME_FORMAT(a.check_out_time, '%%h:%%i %%p') AS check_out_formatted,
            a.total_work_minutes,
            a.overtime_minutes,
            a.check_in_latitude,
            a.check_in_longitude,
            a.check_in_accuracy,
            a.check_out_latitude,
            a.check_out_longitude,
            a.check_out_accuracy,
            a.check_in_selfie,
            a.check_out_selfie,
            a.status,
            a.remarks
        FROM attendance a
        WHERE a.employee_id = %s AND DATE_FORMAT(a.attendance_date, '%%Y-%%m') = %s
        ORDER BY a.attendance_date DESC
    """
    records = query_all(sql, (employee_id, month_str)) or []

    # Calculate summary stats
    total_minutes = sum(r['total_work_minutes'] or 0 for r in records)
    total_ot_minutes = sum(r['overtime_minutes'] or 0 for r in records)
    present_days = sum(1 for r in records if r['status'] == 'PRESENT')
    absent_days = sum(1 for r in records if r['status'] == 'ABSENT')
    leave_days = sum(1 for r in records if r['status'] == 'LEAVE')

    for r in records:
        r['duration_formatted'] = format_minutes_to_hm(r['total_work_minutes'])
        r['overtime_formatted'] = format_minutes_to_hm(r['overtime_minutes'])

    summary = {
        'month': month_str,
        'total_work_minutes': total_minutes,
        'total_work_formatted': format_minutes_to_hm(total_minutes),
        'total_overtime_minutes': total_ot_minutes,
        'total_overtime_formatted': format_minutes_to_hm(total_ot_minutes),
        'present_days': present_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'total_records': len(records)
    }

    return success_response(data={'summary': summary, 'records': records}, message="My attendance retrieved.")


@attendance_bp.route('/employee/<int:emp_id>/monthly', methods=['GET'])
@jwt_required
def get_employee_monthly_attendance(emp_id):
    """
    Detailed Monthly Attendance view for an employee:
    Admin or owner of the profile.
    Returns summary cards and day-by-day calendar records for that month.
    """
    if g.user.get('role') != 'ADMIN' and g.user.get('employee_id') != emp_id:
        return error_response("Unauthorized to view this employee's attendance records.", 403)

    emp = query_one(
        "SELECT id, employee_code, full_name, email, phone, department, designation, status FROM employees WHERE id = %s",
        (emp_id,)
    )
    if not emp:
        return error_response("Employee not found.", 404)

    month_str = request.args.get('month') or get_kolkata_now().strftime('%Y-%m')
    try:
        year_int, month_int = map(int, month_str.split('-'))
        num_days = calendar.monthrange(year_int, month_int)[1]
    except Exception:
        return error_response("Invalid month format. Expected YYYY-MM", 400)

    # Fetch recorded attendance for the month
    sql = """
        SELECT
            id,
            attendance_date,
            check_in_time,
            TIME_FORMAT(check_in_time, '%%h:%%i:%%s %%p') AS check_in_exact,
            TIME_FORMAT(check_in_time, '%%h:%%i %%p') AS check_in_formatted,
            check_out_time,
            TIME_FORMAT(check_out_time, '%%h:%%i:%%s %%p') AS check_out_exact,
            TIME_FORMAT(check_out_time, '%%h:%%i %%p') AS check_out_formatted,
            check_in_latitude,
            check_in_longitude,
            check_in_accuracy,
            check_out_latitude,
            check_out_longitude,
            check_out_accuracy,
            check_in_selfie,
            check_out_selfie,
            status,
            total_work_minutes,
            overtime_minutes,
            remarks
        FROM attendance
        WHERE employee_id = %s AND DATE_FORMAT(attendance_date, '%%Y-%%m') = %s
    """
    existing_records = query_all(sql, (emp_id, month_str)) or []
    record_by_date = {str(r['attendance_date']): r for r in existing_records}

    today = get_kolkata_now().date()
    days_list = []
    total_minutes = 0
    total_ot_minutes = 0
    present_days = 0
    absent_days = 0
    leave_days = 0

    for day in range(1, num_days + 1):
        cur_date = date(year_int, month_int, day)
        cur_date_str = cur_date.strftime('%Y-%m-%d')
        weekday_name = cur_date.strftime('%A')
        date_display = cur_date.strftime('%B %e, %Y').replace('  ', ' ')
        date_short = cur_date.strftime('%B %e').replace('  ', ' ')

        if cur_date_str in record_by_date:
            rec = record_by_date[cur_date_str]
            rec_status = rec['status']
            minutes = rec['total_work_minutes'] or 0
            ot_minutes = rec['overtime_minutes'] or 0
            total_minutes += minutes
            total_ot_minutes += ot_minutes

            if rec_status == 'PRESENT':
                present_days += 1
            elif rec_status == 'ABSENT':
                absent_days += 1
            elif rec_status == 'LEAVE':
                leave_days += 1

            days_list.append({
                'id': rec['id'],
                'date': cur_date_str,
                'date_short': date_short,
                'date_display': date_display,
                'day_name': weekday_name,
                'status': rec_status,
                'check_in_time': rec['check_in_formatted'],
                'check_in_exact': rec['check_in_exact'],
                'check_out_time': rec['check_out_formatted'],
                'check_out_exact': rec['check_out_exact'],
                'total_work_minutes': minutes,
                'duration_formatted': format_minutes_to_hm(minutes) if minutes > 0 else ('Working' if rec['check_in_time'] and not rec['check_out_time'] else '—'),
                'overtime_minutes': ot_minutes,
                'overtime_formatted': format_minutes_to_hm(ot_minutes) if ot_minutes > 0 else '—',
                'check_in_latitude': rec['check_in_latitude'],
                'check_in_longitude': rec['check_in_longitude'],
                'check_in_accuracy': rec['check_in_accuracy'],
                'check_out_latitude': rec['check_out_latitude'],
                'check_out_longitude': rec['check_out_longitude'],
                'check_out_accuracy': rec['check_out_accuracy'],
                'check_in_selfie': rec['check_in_selfie'],
                'check_out_selfie': rec['check_out_selfie'],
                'remarks': rec['remarks']
            })
        else:
            # No record for this date
            if cur_date > today:
                status = 'UPCOMING'
            elif cur_date.weekday() == 6: # Sunday
                status = 'WEEK_OFF'
            else:
                status = 'ABSENT'
                absent_days += 1

            days_list.append({
                'id': None,
                'date': cur_date_str,
                'date_short': date_short,
                'date_display': date_display,
                'day_name': weekday_name,
                'status': status,
                'check_in_time': '—',
                'check_in_exact': None,
                'check_out_time': '—',
                'check_out_exact': None,
                'total_work_minutes': 0,
                'duration_formatted': '—',
                'overtime_minutes': 0,
                'overtime_formatted': '—',
                'check_in_latitude': None,
                'check_in_longitude': None,
                'check_in_accuracy': None,
                'check_out_latitude': None,
                'check_out_longitude': None,
                'check_out_accuracy': None,
                'check_in_selfie': None,
                'check_out_selfie': None,
                'remarks': None
            })

    # Average hours calculation
    avg_minutes = (total_minutes // present_days) if present_days > 0 else 0

    summary = {
        'employee': emp,
        'month': month_str,
        'month_formatted': datetime(year_int, month_int, 1).strftime('%B %Y'),
        'present_days': present_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'total_work_minutes': total_minutes,
        'total_hours_formatted': format_minutes_to_hm(total_minutes),
        'average_hours_formatted': format_minutes_to_hm(avg_minutes),
        'total_overtime_minutes': total_ot_minutes,
        'total_overtime_formatted': format_minutes_to_hm(total_ot_minutes)
    }

    return success_response(data={'summary': summary, 'days': days_list}, message="Employee monthly attendance retrieved.")


@attendance_bp.route('/selfie/<filename>', methods=['GET'])
@jwt_required
def get_attendance_selfie(filename):
    """
    Secure authenticated endpoint to retrieve attendance selfie images.
    Admins can view any selfie; Staff can ONLY view selfies belonging to their records.
    """
    safe_name = secure_filename(filename)
    if not safe_name:
        return error_response("Invalid filename.", 400)

    # Authorization Check
    user_role = g.user.get('role')
    user_emp_id = g.user.get('employee_id')

    if user_role != 'ADMIN':
        # Check ownership of this selfie
        owner_check = query_one(
            "SELECT id FROM attendance WHERE employee_id = %s AND (check_in_selfie = %s OR check_out_selfie = %s)",
            (user_emp_id, safe_name, safe_name)
        )
        if not owner_check:
            return error_response("Access forbidden: You do not have permission to view this selfie.", 403)

    filepath = os.path.join(Config.UPLOAD_FOLDER, safe_name)

    # 1. Check local disk cache or pre-bundled repo images
    if os.path.exists(filepath):
        return send_from_directory(Config.UPLOAD_FOLDER, safe_name, mimetype='image/jpeg')

    # 2. Check persistent database storage (for cloud hosting like Render where disk is ephemeral)
    try:
        ensure_selfie_table()
        row = query_one("SELECT image_data FROM selfie_storage WHERE filename = %s", (safe_name,))
        if row and row.get('image_data'):
            image_data = row['image_data']
            # Re-populate local disk cache
            try:
                with open(filepath, 'wb') as f:
                    f.write(image_data)
            except Exception:
                pass
            return Response(image_data, mimetype='image/jpeg')
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Error retrieving selfie from persistent database: {e}")

    return error_response("Selfie image not found.", 404)
