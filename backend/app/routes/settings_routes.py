from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.middleware.auth import role_required
from app.services.cleanup_service import (
    get_storage_stats, 
    perform_manual_storage_cleanup, 
    cleanup_oldest_batch_until_headroom
)

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

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
