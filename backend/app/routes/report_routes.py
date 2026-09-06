import io
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, request, Response, g
from app.config import Config
from app.db import query_all
from app.utils.response import success_response, error_response
from app.middleware.auth import role_required

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

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
    return f"{h}h {m:02d}m"

@report_bp.route('/monthly', methods=['GET'])
@role_required(['ADMIN'])
def monthly_company_report():
    """
    Generate Section 13 Monthly Company Report:
    Employee | Present | Absent | Leave | Total Hours | Overtime
    Supports ?month=YYYY-MM and ?format=csv
    """
    month_str = request.args.get('month') or get_kolkata_now().strftime('%Y-%m')
    export_format = (request.args.get('format') or 'json').lower()

    sql = """
        SELECT
            e.id AS employee_id,
            e.employee_code,
            e.full_name,
            e.department,
            e.designation,
            COALESCE(SUM(CASE WHEN a.status = 'PRESENT' THEN 1 ELSE 0 END), 0) AS present_days,
            COALESCE(SUM(CASE WHEN a.status = 'ABSENT' THEN 1 ELSE 0 END), 0) AS absent_days,
            COALESCE(SUM(CASE WHEN a.status = 'LEAVE' THEN 1 ELSE 0 END), 0) AS leave_days,
            COALESCE(SUM(CASE WHEN a.status = 'HALF_DAY' THEN 1 ELSE 0 END), 0) AS half_days,
            COALESCE(SUM(a.total_work_minutes), 0) AS total_work_minutes,
            COALESCE(SUM(a.overtime_minutes), 0) AS total_ot_minutes
        FROM employees e
        JOIN users u ON e.user_id = u.id
        LEFT JOIN attendance a ON e.id = a.employee_id AND DATE_FORMAT(a.attendance_date, '%%Y-%%m') = %s
        WHERE u.role = 'STAFF' AND e.status = 'ACTIVE'
        GROUP BY e.id, e.employee_code, e.full_name, e.department, e.designation
        ORDER BY e.id ASC
    """
    records = query_all(sql, (month_str,)) or []

    for r in records:
        r['present_days'] = int(r['present_days'])
        r['absent_days'] = int(r['absent_days'])
        r['leave_days'] = int(r['leave_days'])
        r['half_days'] = int(r['half_days'])
        r['total_work_minutes'] = int(r['total_work_minutes'])
        r['total_ot_minutes'] = int(r['total_ot_minutes'])
        r['total_hours_formatted'] = format_minutes_to_hm(r['total_work_minutes'])
        r['overtime_formatted'] = format_minutes_to_hm(r['total_ot_minutes'])

    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Month', 'Employee Code', 'Full Name', 'Department', 'Designation',
            'Present Days', 'Absent Days', 'Leave Days', 'Total Hours', 'Overtime'
        ])
        for r in records:
            writer.writerow([
                month_str,
                r['employee_code'],
                r['full_name'],
                r['department'],
                r['designation'],
                r['present_days'],
                r['absent_days'],
                r['leave_days'],
                r['total_hours_formatted'],
                r['overtime_formatted']
            ])

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=monthly_attendance_report_{month_str}.csv"}
        )

    return success_response(
        data={'month': month_str, 'records': records, 'total_employees': len(records)},
        message="Monthly company report generated successfully."
    )
