from flask import Blueprint, request, g
from app.db import query_all, query_one, execute
from app.middleware.auth import jwt_required
from app.utils.response import success_response, error_response

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notification_bp.route('', methods=['GET'])
@jwt_required
def get_notifications():
    """
    Fetch in-app notifications for the logged-in employee.
    Ordered with unread notifications first, then chronologically descending.
    """
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return success_response(data={'notifications': [], 'unread_count': 0}, message="No notifications.")

    sql = """
        SELECT
            id, title, message, type, is_read,
            DATE_FORMAT(created_at, '%%d %%b %%Y, %%h:%%i %%p') AS created_at_formatted,
            created_at
        FROM notifications
        WHERE employee_id = %s
        ORDER BY is_read ASC, created_at DESC
        LIMIT 50
    """
    notifications = query_all(sql, (employee_id,))
    unread_count = sum(1 for n in notifications if not n['is_read'])

    return success_response(
        data={'notifications': notifications, 'unread_count': unread_count},
        message="Notifications retrieved."
    )

@notification_bp.route('/<int:notif_id>/read', methods=['PATCH', 'POST'])
@jwt_required
def mark_notification_read(notif_id):
    """Mark an individual notification as read."""
    employee_id = g.user.get('employee_id')
    notif = query_one("SELECT * FROM notifications WHERE id = %s", (notif_id,))
    if not notif:
        return error_response("Notification not found.", 404)

    if notif['employee_id'] != employee_id and g.user.get('role') not in ['ADMIN', 'HR']:
        return error_response("Unauthorized access.", 403)

    execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notif_id,))
    return success_response(message="Notification marked as read.")

@notification_bp.route('/read-all', methods=['POST'])
@jwt_required
def mark_all_read():
    """Mark all notifications for the current employee as read."""
    employee_id = g.user.get('employee_id')
    if employee_id:
        execute("UPDATE notifications SET is_read = TRUE WHERE employee_id = %s", (employee_id,))

    return success_response(message="All notifications marked as read.")
