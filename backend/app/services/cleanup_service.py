import os
import datetime
from app.db import query_all, query_one, execute, get_db_cursor
from app.config import Config
from app.middleware.audit import log_audit

# 5 GB free cloud storage plan = 5,120 MB
STORAGE_LIMIT_MB = 5120.0
# Auto-clean triggers only when storage reaches 90% full (4,608 MB)
DEFAULT_TRIGGER_PERCENT = 90.0
# Target headroom freed when cleaning up full storage (500 MB freed gives space for ~15,000 selfies)
DEFAULT_HEADROOM_MB = 500.0

_last_full_check = None


def get_selfie_storage_info():
    """Returns (total_bytes, file_count, size_mb) for the selfie storage directory."""
    upload_folder = Config.UPLOAD_FOLDER
    total_bytes = 0
    file_count = 0

    if os.path.exists(upload_folder):
        for entry in os.scandir(upload_folder):
            if entry.is_file():
                file_count += 1
                total_bytes += entry.stat().st_size

    size_mb = round(total_bytes / (1024 * 1024), 2)
    return total_bytes, file_count, size_mb


def get_storage_stats():
    """
    Calculate current storage usage, record counts, and date ranges.
    Returns status indicating whether cleanup is needed or if storage is healthy.
    """
    record_stats = query_one("""
        SELECT 
            COUNT(*) AS total_records,
            MIN(attendance_date) AS oldest_date,
            MAX(attendance_date) AS newest_date
        FROM attendance
    """) or {}

    total_records = record_stats.get('total_records') or 0
    oldest_date = record_stats.get('oldest_date')
    newest_date = record_stats.get('newest_date')

    total_bytes, file_count, size_mb = get_selfie_storage_info()

    trigger_percent = float(os.getenv('CLEANUP_TRIGGER_PERCENT', DEFAULT_TRIGGER_PERCENT))
    trigger_mb = round((trigger_percent / 100.0) * STORAGE_LIMIT_MB, 2)
    used_percentage = round((size_mb / STORAGE_LIMIT_MB) * 100, 2)
    free_mb = round(max(0.0, STORAGE_LIMIT_MB - size_mb), 2)

    is_near_full = used_percentage >= trigger_percent

    return {
        'policy': 'CLEANUP_ON_STORAGE_FULL_ONLY',
        'policy_description': 'Old records are permanently kept and only pruned when 5 GB cloud storage fills up',
        'total_records': total_records,
        'oldest_record_date': oldest_date.strftime('%Y-%m-%d') if oldest_date else None,
        'newest_record_date': newest_date.strftime('%Y-%m-%d') if newest_date else None,
        'selfie_files_count': file_count,
        'selfies_storage_mb': size_mb,
        'storage_limit_mb': STORAGE_LIMIT_MB,
        'storage_free_mb': free_mb,
        'storage_used_percentage': used_percentage,
        'cleanup_trigger_percent': trigger_percent,
        'cleanup_trigger_mb': trigger_mb,
        'is_near_full': is_near_full,
        'status': 'FULL_CLEANUP_NEEDED' if is_near_full else 'HEALTHY'
    }


def cleanup_oldest_batch_until_headroom(target_free_mb=DEFAULT_HEADROOM_MB, admin_user_id=None):
    """
    Automatically prunes the oldest historical dates across ALL staff simultaneously
    until the requested headroom (e.g. 500 MB) is freed up.
    
    Ensures that whenever data is deleted, it deletes the entire day across ALL staff
    at the exact same time, so no staff member has mismatched records.
    """
    upload_folder = Config.UPLOAD_FOLDER
    target_bytes = int(target_free_mb * 1024 * 1024)
    total_freed_bytes = 0
    records_deleted_total = 0
    files_deleted_total = 0
    dates_pruned = []

    # Get distinct attendance dates sorted from oldest to newest
    date_rows = query_all("""
        SELECT DISTINCT attendance_date 
        FROM attendance 
        ORDER BY attendance_date ASC
    """)

    if not date_rows:
        return {
            'success': True,
            'freed_mb': 0.0,
            'records_deleted': 0,
            'files_deleted': 0,
            'dates_pruned_count': 0,
            'message': 'No attendance records found to clean up.'
        }

    # Safety: do not delete records from the last 7 days under any circumstance
    safe_cutoff = datetime.date.today() - datetime.timedelta(days=7)

    for row in date_rows:
        dt = row.get('attendance_date')
        if not dt or dt >= safe_cutoff:
            # Reached safe recent days; stop pruning
            break

        # 1. Fetch all attendance records and selfie filenames for this day across ALL staff
        records = query_all("""
            SELECT id, check_in_selfie, check_out_selfie 
            FROM attendance 
            WHERE attendance_date = %s
        """, (dt,))

        day_files_deleted = 0
        day_bytes_freed = 0

        for rec in records:
            for selfie in (rec.get('check_in_selfie'), rec.get('check_out_selfie')):
                if selfie:
                    file_path = os.path.join(upload_folder, selfie)
                    if os.path.exists(file_path):
                        try:
                            fsize = os.path.getsize(file_path)
                            os.remove(file_path)
                            day_files_deleted += 1
                            day_bytes_freed += fsize
                        except OSError:
                            pass
                    try:
                        execute("DELETE FROM selfie_storage WHERE filename = %s", (selfie,))
                    except Exception:
                        pass

        # 2. Delete database records for this date across ALL staff simultaneously
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM attendance WHERE attendance_date = %s", (dt,))
            day_records_deleted = cursor.rowcount

        total_freed_bytes += day_bytes_freed
        records_deleted_total += day_records_deleted
        files_deleted_total += day_files_deleted
        dates_pruned.append(dt.strftime('%Y-%m-%d'))

        # If we have freed enough headroom, stop pruning
        if total_freed_bytes >= target_bytes:
            break

    freed_mb = round(total_freed_bytes / (1024 * 1024), 2)

    # Log audit trail
    log_desc = (
        f"Storage auto-clean freed {freed_mb} MB ({records_deleted_total} records, "
        f"{files_deleted_total} photos) across {len(dates_pruned)} oldest dates for all staff."
    )
    if admin_user_id or records_deleted_total > 0:
        log_audit(
            user_id=admin_user_id,
            action='STORAGE_FULL_AUTO_CLEANUP',
            entity_type='ATTENDANCE',
            description=log_desc
        )

    return {
        'success': True,
        'freed_mb': freed_mb,
        'records_deleted': records_deleted_total,
        'files_deleted': files_deleted_total,
        'dates_pruned_count': len(dates_pruned),
        'dates_pruned': dates_pruned,
        'message': log_desc
    }


def ensure_storage_headroom(headroom_mb=DEFAULT_HEADROOM_MB):
    """
    Called before saving a new selfie or attendance record.
    Checks if storage has reached the full threshold (90% / 4,608 MB).
    If full: automatically cleans up the oldest batch across all staff to restore headroom.
    If not full: does nothing and returns immediately with zero overhead.
    """
    stats = get_storage_stats()
    if stats['is_near_full']:
        return cleanup_oldest_batch_until_headroom(target_free_mb=headroom_mb)
    return None


def maybe_run_auto_cleanup_if_full():
    """
    Checks storage usage periodically.
    Only triggers cleanup if storage is genuinely full (>= 90% of 5 GB).
    Otherwise, preserves 100% of historical data indefinitely.
    """
    global _last_full_check
    today = datetime.date.today()

    # Run check at most once an hour
    if _last_full_check == datetime.datetime.now().strftime('%Y-%m-%d %H'):
        return None

    _last_full_check = datetime.datetime.now().strftime('%Y-%m-%d %H')

    stats = get_storage_stats()
    if stats['is_near_full']:
        return cleanup_oldest_batch_until_headroom(target_free_mb=DEFAULT_HEADROOM_MB)

    return {
        'cleaned': False,
        'reason': f"Storage healthy ({stats['storage_used_percentage']}% used). No cleanup required."
    }


def perform_manual_storage_cleanup(retention_days=90, admin_user_id=None):
    """
    Manual override: Allows an admin to force-prune records older than retention_days
    simultaneously across all staff if desired.
    """
    if retention_days < 7:
        retention_days = 7

    cutoff_date = datetime.date.today() - datetime.timedelta(days=retention_days)
    upload_folder = Config.UPLOAD_FOLDER

    # 1. Fetch old selfies
    old_records = query_all("""
        SELECT id, check_in_selfie, check_out_selfie 
        FROM attendance 
        WHERE attendance_date < %s
    """, (cutoff_date,))

    files_deleted = 0
    for rec in old_records:
        for selfie in (rec.get('check_in_selfie'), rec.get('check_out_selfie')):
            if selfie:
                file_path = os.path.join(upload_folder, selfie)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        files_deleted += 1
                    except OSError:
                        pass
                try:
                    execute("DELETE FROM selfie_storage WHERE filename = %s", (selfie,))
                except Exception:
                    pass

    # 2. Delete database records across ALL staff simultaneously
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM attendance WHERE attendance_date < %s", (cutoff_date,))
        records_deleted = cursor.rowcount

    if admin_user_id:
        log_audit(
            user_id=admin_user_id,
            action='MANUAL_STORAGE_CLEANUP',
            entity_type='ATTENDANCE',
            description=f"Manual cleanup: {records_deleted} records and {files_deleted} selfies older than {cutoff_date} ({retention_days} days retention)"
        )

    return {
        'success': True,
        'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
        'records_deleted': records_deleted,
        'files_deleted': files_deleted,
        'message': f"Manual cleanup completed: {records_deleted} attendance records and {files_deleted} photos pruned."
    }


# Compatibility Aliases
perform_storage_cleanup = perform_manual_storage_cleanup
maybe_run_daily_auto_cleanup = maybe_run_auto_cleanup_if_full
