from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.middleware.auth import role_required
from app.services.cleanup_service import (
    get_storage_stats, 
    perform_manual_storage_cleanup, 
    cleanup_oldest_batch_until_headroom
)
from app.db import query_all, execute

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('/general', methods=['GET'])
@role_required(['ADMIN', 'STAFF'])
def get_general_settings():
    """Retrieve system settings like company_name, work_hours, timezone."""
    try:
        rows = query_all("SELECT setting_key, setting_value FROM system_settings")
        settings = {r['setting_key']: r['setting_value'] for r in rows}
    except Exception:
        settings = {}
    settings.setdefault('company_name', 'Seven Stars Logistics Private Limited')
    settings.setdefault('work_hours', '8')
    settings.setdefault('timezone', 'Asia/Kolkata')
    return success_response(data=settings, message="General settings retrieved.")

@settings_bp.route('/general', methods=['PUT'])
@role_required(['ADMIN'])
def update_general_settings():
    """Update general system settings."""
    data = request.get_json() or {}
    company_name = (data.get('company_name') or '').strip()
    work_hours = data.get('work_hours')

    if company_name:
        execute("""
            INSERT INTO system_settings (setting_key, setting_value)
            VALUES ('company_name', %s)
            ON DUPLICATE KEY UPDATE setting_value = %s
        """, (company_name, company_name))

    if work_hours is not None:
        try:
            wh_val = str(max(1, min(24, int(work_hours))))
            execute("""
                INSERT INTO system_settings (setting_key, setting_value)
                VALUES ('work_hours', %s)
                ON DUPLICATE KEY UPDATE setting_value = %s
            """, (wh_val, wh_val))
        except (ValueError, TypeError):
            pass

    try:
        rows = query_all("SELECT setting_key, setting_value FROM system_settings")
        settings = {r['setting_key']: r['setting_value'] for r in rows}
    except Exception:
        settings = {'company_name': company_name or 'Seven Stars Logistics Private Limited', 'work_hours': str(work_hours or 8)}

    return success_response(data=settings, message="System settings updated successfully.")


@settings_bp.route('/storage', methods=['GET'])
@role_required(['ADMIN'])
def get_storage():
    """Retrieve 5GB storage usage, full-capacity trigger threshold, and status."""
    stats = get_storage_stats()
    return success_response(data=stats, message="Storage statistics retrieved.")

@settings_bp.route('/cleanup', methods=['POST'])
@role_required(['ADMIN'])
def trigger_cleanup():
    """Admin triggers manual storage cleanup with specified retention days."""
    data = request.get_json() or {}
    retention_days = int(data.get('retention_days') or 90)

    result = perform_manual_storage_cleanup(
        retention_days=retention_days,
        admin_user_id=g.user.get('id')
    )
    return success_response(data=result, message=result['message'])

@settings_bp.route('/cleanup-on-full-test', methods=['POST'])
@role_required(['ADMIN'])
def trigger_on_full_cleanup():
    """Admin manually tests the 'clean up oldest batch across all staff' engine."""
    data = request.get_json() or {}
    target_free_mb = float(data.get('target_free_mb') or 50.0)

    result = cleanup_oldest_batch_until_headroom(
        target_free_mb=target_free_mb,
        admin_user_id=g.user.get('id')
    )
    return success_response(data=result, message=result['message'])
