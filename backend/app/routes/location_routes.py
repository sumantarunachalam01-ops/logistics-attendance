from flask import Blueprint, request, g
from app.db import query_all, query_one, execute
from app.utils.response import success_response, error_response
from app.middleware.auth import jwt_required, role_required
from app.middleware.audit import log_audit

location_bp = Blueprint('locations', __name__, url_prefix='/api/locations')

@location_bp.route('', methods=['GET'])
@jwt_required
def list_locations():
    """List all authorized logistics hubs, ports, and office locations."""
    type_filter = request.args.get('type', '').strip()
    sql = "SELECT id, name, type, address, latitude, longitude, allowed_radius_meters, is_active FROM locations WHERE is_active = TRUE"
    params = []

    if type_filter:
        sql += " AND type = %s"
        params.append(type_filter)

    sql += " ORDER BY name ASC"
    locations = query_all(sql, params)
    return success_response(data={'locations': locations}, message="Locations retrieved.")

@location_bp.route('', methods=['POST'])
@role_required(['ADMIN', 'HR'])
def create_location():
    """Create a new reusable logistics hub or office location with geofencing radius."""
    data = request.get_json() or {}

    name = (data.get('name') or '').strip()
    valid_types = ['OFFICE', 'AIRPORT', 'HARBOUR', 'CUSTOMS', 'CFS', 'WAREHOUSE', 'CLIENT', 'OTHER']
    raw_type = (data.get('type') or 'OTHER').strip().upper()
    loc_type = raw_type if raw_type in valid_types else 'OTHER'
    address = (data.get('address') or '').strip()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    radius = data.get('allowed_radius_meters') or 300

    if not name or latitude is None or longitude is None:
        return error_response("Name, latitude, and longitude are required.", 400)

    try:
        lat = float(latitude)
        lng = float(longitude)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return error_response("Coordinates out of valid geographical bounds.", 400)
    except (ValueError, TypeError):
        return error_response("Coordinates must be valid numeric values.", 400)

    res = execute(
        """INSERT INTO locations (name, type, address, latitude, longitude, allowed_radius_meters, is_active)
           VALUES (%s, %s, %s, %s, %s, %s, TRUE)""",
        (name, loc_type, address, lat, lng, radius)
    )

    log_audit(
        user_id=g.user['id'],
        action='LOCATION_CREATED',
        entity_type='LOCATION',
        entity_id=res['lastrowid'],
        description=f"Admin created location '{name}' ({loc_type}) with geofence radius {radius}m"
    )

    return success_response(
        data={'location_id': res['lastrowid'], 'name': name},
        message=f"Location '{name}' created successfully.",
        status_code=201
    )

@location_bp.route('/map-data', methods=['GET'])
@role_required(['ADMIN', 'HR'])
def get_map_data():
    """
    Returns unified geospatial dataset for Leaflet map:
    1. Active logistics hubs with coordinates and circular geofence radiuses.
    2. Active staff members who have clocked in today with their latest GPS fix and active field task.
    """
    # 1. Fetch active hubs
    hubs = query_all("""
        SELECT id, name, type, address, latitude, longitude, allowed_radius_meters
        FROM locations
        WHERE is_active = TRUE
        ORDER BY id ASC
    """)

    # 2. Fetch staff with valid GPS coordinates recorded today
    staff_markers = query_all("""
        SELECT
            e.id AS employee_id,
            e.employee_code,
            e.full_name,
            e.department,
            e.designation,
            COALESCE(a.status, 'NOT_STARTED') AS attendance_status,
            TIME_FORMAT(a.check_in_time, '%%h:%%i %%p') AS check_in_formatted,
            COALESCE(a.check_out_latitude, a.check_in_latitude) AS latitude,
            COALESCE(a.check_out_longitude, a.check_in_longitude) AS longitude,
            COALESCE(a.check_in_accuracy, 10.0) AS accuracy,
            t.id AS task_id,
            t.title AS task_title,
            t.status AS task_status,
            t.priority AS task_priority,
            l.name AS task_hub
        FROM employees e
        JOIN users u ON e.user_id = u.id
        JOIN attendance a ON e.id = a.employee_id AND a.attendance_date = CURDATE()
        LEFT JOIN tasks t ON e.id = t.employee_id AND t.assigned_date = CURDATE() AND t.status = 'IN_PROGRESS'
        LEFT JOIN locations l ON t.location_id = l.id
        WHERE u.role = 'STAFF'
          AND e.status = 'ACTIVE'
          AND (a.check_in_latitude IS NOT NULL OR a.check_out_latitude IS NOT NULL)
    """)

    return success_response(
        data={
            'hubs': hubs,
            'staff': staff_markers,
            'total_hubs': len(hubs),
            'active_field_staff': len(staff_markers)
        },
        message="Geospatial map data retrieved."
    )

@location_bp.route('/<int:location_id>', methods=['PUT'])
@role_required(['ADMIN', 'HR'])
def update_location(location_id):
    """Admin updates logistics hub details or geofence perimeter."""
    loc = query_one("SELECT * FROM locations WHERE id = %s", (location_id,))
    if not loc:
        return error_response("Location not found.", 404)

    data = request.get_json() or {}
    name = (data.get('name') or loc['name']).strip()
    valid_types = ['OFFICE', 'AIRPORT', 'HARBOUR', 'CUSTOMS', 'CFS', 'WAREHOUSE', 'CLIENT', 'OTHER']
    raw_type = (data.get('type') or loc['type']).strip().upper()
    loc_type = raw_type if raw_type in valid_types else loc['type']
    address = data.get('address', loc['address'])
    latitude = data.get('latitude', loc['latitude'])
    longitude = data.get('longitude', loc['longitude'])
    radius = data.get('allowed_radius_meters', loc['allowed_radius_meters'])

    try:
        lat = float(latitude)
        lng = float(longitude)
        radius = int(radius)
    except (ValueError, TypeError):
        return error_response("Coordinates and radius must be valid numbers.", 400)

    execute(
        """UPDATE locations
           SET name = %s, type = %s, address = %s, latitude = %s, longitude = %s, allowed_radius_meters = %s
           WHERE id = %s""",
        (name, loc_type, address, lat, lng, radius, location_id)
    )

    log_audit(
        user_id=g.user['id'],
        action='LOCATION_UPDATED',
        entity_type='LOCATION',
        entity_id=location_id,
        description=f"Admin updated location #{location_id} ('{name}', radius: {radius}m)"
    )

    return success_response(message=f"Location '{name}' updated successfully.")

@location_bp.route('/<int:location_id>/status', methods=['PATCH'])
@role_required(['ADMIN', 'HR'])
def toggle_location_status(location_id):
    """Admin toggles location active state."""
    loc = query_one("SELECT id, name, is_active FROM locations WHERE id = %s", (location_id,))
    if not loc:
        return error_response("Location not found.", 404)

    new_status = not bool(loc['is_active'])
    execute("UPDATE locations SET is_active = %s WHERE id = %s", (new_status, location_id))

    action_label = "activated" if new_status else "deactivated"
    log_audit(
        user_id=g.user['id'],
        action='LOCATION_STATUS_TOGGLED',
        entity_type='LOCATION',
        entity_id=location_id,
        description=f"Admin {action_label} location '{loc['name']}'"
    )

    return success_response(
        data={'id': location_id, 'is_active': new_status},
        message=f"Location '{loc['name']}' has been {action_label}."
    )

