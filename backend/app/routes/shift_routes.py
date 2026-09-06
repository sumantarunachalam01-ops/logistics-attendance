from flask import Blueprint, request, g
from app.db import query_all, query_one, execute
from app.middleware.auth import role_required, jwt_required
from app.middleware.audit import log_audit
from app.utils.response import success_response, error_response

shift_bp = Blueprint('shifts', __name__, url_prefix='/api/shifts')

@shift_bp.route('', methods=['GET'])
def get_shifts():
    """List all work shifts with assigned employee counts."""
    sql = """
        SELECT
            s.id, s.name, s.start_time, s.end_time,
            TIME_FORMAT(s.start_time, '%%h:%%i %%p') AS start_time_formatted,
            TIME_FORMAT(s.end_time, '%%h:%%i %%p') AS end_time_formatted,
            s.required_work_minutes, s.late_after_minutes, s.absent_after_minutes,
            s.is_active,
            COUNT(e.id) AS assigned_staff_count
        FROM shifts s
        LEFT JOIN employees e ON s.id = e.shift_id AND e.status = 'ACTIVE'
        GROUP BY s.id, s.name, s.start_time, s.end_time, s.required_work_minutes, s.late_after_minutes, s.absent_after_minutes, s.is_active
        ORDER BY s.id ASC
    """
    shifts = query_all(sql)
    return success_response(data={'shifts': shifts}, message="Shifts retrieved.")

@shift_bp.route('', methods=['POST'])
@role_required(['ADMIN', 'HR'])
def create_shift():
    """Create a new work shift schedule."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    start_time = data.get('start_time') or '09:00'
    end_time = data.get('end_time') or '18:00'
    required_work_minutes = int(data.get('required_work_minutes') or 480)
    late_after_minutes = int(data.get('late_after_minutes') or 15)

    if not name:
        return error_response("Shift name is required.", 400)

    res = execute(
        """INSERT INTO shifts (name, start_time, end_time, required_work_minutes, late_after_minutes, is_active)
           VALUES (%s, %s, %s, %s, %s, TRUE)""",
        (name, start_time, end_time, required_work_minutes, late_after_minutes)
    )

    log_audit(
        user_id=g.user['id'],
        action='SHIFT_CREATED',
        entity_type='SHIFT',
        entity_id=res['lastrowid'],
        description=f"Created shift '{name}' ({start_time} - {end_time})"
    )

    return success_response(
        data={'shift_id': res['lastrowid'], 'name': name},
        message=f"Shift '{name}' created successfully.",
        status_code=201
    )

@shift_bp.route('/<int:shift_id>', methods=['PUT'])
@role_required(['ADMIN', 'HR'])
def update_shift(shift_id):
    """Update shift details and timings."""
    shift = query_one("SELECT * FROM shifts WHERE id = %s", (shift_id,))
    if not shift:
        return error_response("Shift not found.", 404)

    data = request.get_json() or {}
    name = (data.get('name') or shift['name']).strip()
    start_time = data.get('start_time', str(shift['start_time']))
    end_time = data.get('end_time', str(shift['end_time']))
    required_work_minutes = int(data.get('required_work_minutes', shift['required_work_minutes']))
    late_after_minutes = int(data.get('late_after_minutes', shift['late_after_minutes']))

    execute(
        """UPDATE shifts
           SET name = %s, start_time = %s, end_time = %s,
               required_work_minutes = %s, late_after_minutes = %s
           WHERE id = %s""",
        (name, start_time, end_time, required_work_minutes, late_after_minutes, shift_id)
    )

    log_audit(
        user_id=g.user['id'],
        action='SHIFT_UPDATED',
        entity_type='SHIFT',
        entity_id=shift_id,
        description=f"Updated shift #{shift_id} ('{name}')"
    )

    return success_response(message=f"Shift '{name}' updated successfully.")

@shift_bp.route('/<int:shift_id>/status', methods=['PATCH'])
@role_required(['ADMIN', 'HR'])
def toggle_shift_status(shift_id):
    """Toggle shift active status."""
    shift = query_one("SELECT id, name, is_active FROM shifts WHERE id = %s", (shift_id,))
    if not shift:
        return error_response("Shift not found.", 404)

    new_status = not bool(shift['is_active'])
    execute("UPDATE shifts SET is_active = %s WHERE id = %s", (new_status, shift_id))

    action_label = "activated" if new_status else "deactivated"
    log_audit(
        user_id=g.user['id'],
        action='SHIFT_STATUS_TOGGLED',
        entity_type='SHIFT',
        entity_id=shift_id,
        description=f"Admin {action_label} shift '{shift['name']}'"
    )

    return success_response(
        data={'id': shift_id, 'is_active': new_status},
        message=f"Shift '{shift['name']}' {action_label}."
    )
