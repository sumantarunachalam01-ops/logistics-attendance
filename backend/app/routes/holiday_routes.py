from flask import Blueprint, request, g
from datetime import datetime
from app.db import query_all, query_one, execute
from app.middleware.auth import jwt_required, role_required
from app.middleware.audit import log_audit
from app.utils.response import success_response, error_response

holiday_bp = Blueprint('holidays', __name__, url_prefix='/api/holidays')

@holiday_bp.route('', methods=['GET'])
def get_holidays():
    """
    Get company holiday calendar. Available to all users.
    Ordered chronologically with 'is_upcoming' boolean flag.
    """
    year = request.args.get('year')
    sql = "SELECT id, holiday_date, name, description, is_active FROM holidays WHERE is_active = TRUE"
    params = []

    if year:
        sql += " AND YEAR(holiday_date) = %s"
        params.append(year)

    sql += " ORDER BY holiday_date ASC"
    holidays = query_all(sql, params)

    now_date = datetime.now().date()
    for h in holidays:
        h['is_upcoming'] = h['holiday_date'] >= now_date

    return success_response(data={'holidays': holidays}, message="Holidays retrieved.")

@holiday_bp.route('', methods=['POST'])
@role_required(['ADMIN', 'HR'])
def create_holiday():
    """Admin adds a holiday."""
    data = request.get_json() or {}
    holiday_date = (data.get('holiday_date') or '').strip()
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()

    if not holiday_date or not name:
        return error_response("Holiday date and name are required.", 400)

    try:
        datetime.strptime(holiday_date, '%Y-%m-%d')
    except ValueError:
        return error_response("Date must be in YYYY-MM-DD format.", 400)

    existing = query_one("SELECT id FROM holidays WHERE holiday_date = %s", (holiday_date,))
    if existing:
        return error_response(f"A holiday is already scheduled on {holiday_date}.", 400)

    exec_res = execute(
        "INSERT INTO holidays (holiday_date, name, description) VALUES (%s, %s, %s)",
        (holiday_date, name, description)
    )
    holiday_id = exec_res['lastrowid']

    log_audit(
        user_id=g.user['id'],
        action='HOLIDAY_CREATED',
        entity_type='HOLIDAY',
        entity_id=holiday_id,
        description=f"Added holiday: {name} on {holiday_date}"
    )

    return success_response(
        data={'id': holiday_id, 'name': name, 'holiday_date': holiday_date},
        message="Holiday added successfully.",
        status_code=201
    )

@holiday_bp.route('/<int:holiday_id>', methods=['DELETE'])
@role_required(['ADMIN', 'HR'])
def delete_holiday(holiday_id):
    """Admin removes a holiday."""
    h = query_one("SELECT id, name, holiday_date FROM holidays WHERE id = %s", (holiday_id,))
    if not h:
        return error_response("Holiday not found.", 404)

    execute("DELETE FROM holidays WHERE id = %s", (holiday_id,))

    log_audit(
        user_id=g.user['id'],
        action='HOLIDAY_DELETED',
        entity_type='HOLIDAY',
        entity_id=holiday_id,
        description=f"Deleted holiday: {h['name']} ({h['holiday_date']})"
    )

    return success_response(message=f"Holiday '{h['name']}' deleted.")
