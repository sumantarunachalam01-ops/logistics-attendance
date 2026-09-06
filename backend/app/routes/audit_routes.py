from flask import Blueprint, request
from app.db import query_all, query_one
from app.middleware.auth import role_required
from app.utils.response import success_response, error_response

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit-logs')

@audit_bp.route('', methods=['GET'])
@role_required(['ADMIN', 'HR'])
def get_audit_logs():
    """
    Retrieve system-wide audit logs with filters:
    action, entity_type, date, search query.
    """
    action_filter = request.args.get('action')
    entity_filter = request.args.get('entity_type')
    date_filter = request.args.get('date')
    search = (request.args.get('search') or '').strip()

    sql = """
        SELECT
            a.id, a.user_id, a.action, a.entity_type, a.entity_id,
            a.description, a.ip_address,
            DATE_FORMAT(a.created_at, '%%d %%b %%Y, %%h:%%i %%p') AS created_at_formatted,
            a.created_at,
            u.email AS user_email,
            u.role AS user_role,
            e.full_name AS user_name
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        LEFT JOIN employees e ON u.id = e.user_id
        WHERE 1=1
    """
    params = []

    if action_filter:
        sql += " AND a.action = %s"
        params.append(action_filter)

    if entity_filter:
        sql += " AND a.entity_type = %s"
        params.append(entity_filter)

    if date_filter:
        sql += " AND DATE(a.created_at) = %s"
        params.append(date_filter)

    if search:
        sql += " AND (a.description LIKE %s OR u.email LIKE %s OR e.full_name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    sql += " ORDER BY a.created_at DESC LIMIT 100"
    logs = query_all(sql, params)

    return success_response(
        data={'logs': logs, 'total': len(logs)},
        message="Audit logs retrieved."
    )
