from flask import jsonify
import datetime
from decimal import Decimal

def serialize_item(obj):
    """Recursively convert datetime, date, timedelta, and Decimal to JSON serializable types."""
    if obj is None:
        return None
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        total_seconds = int(obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: serialize_item(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [serialize_item(x) for x in obj]
    return obj

def success_response(data=None, message="Success", status_code=200):
    payload = {
        "success": True,
        "message": message,
        "data": serialize_item(data)
    }
    return jsonify(payload), status_code

def error_response(message="An error occurred", status_code=400, errors=None):
    payload = {
        "success": False,
        "message": message,
        "errors": serialize_item(errors)
    }
    return jsonify(payload), status_code
