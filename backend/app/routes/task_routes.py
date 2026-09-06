from flask import Blueprint, request, g
from datetime import datetime
from app.db import query_one, query_all, execute
from app.utils.response import success_response, error_response
from app.middleware.auth import jwt_required, role_required
from app.middleware.audit import log_audit
from app.services.geofence import calculate_haversine_distance

task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@task_bp.route('', methods=['GET'])
@jwt_required
def list_tasks():
    """List tasks. Admin/HR sees all tasks with filters; Staff sees assigned tasks."""
    user_role = g.user.get('role')
    employee_id = g.user.get('employee_id')

    # Query filters
    date_filter = request.args.get('date', '').strip()
    emp_filter = request.args.get('employee_id', '').strip()
    loc_filter = request.args.get('location_id', '').strip()
    priority_filter = request.args.get('priority', '').strip()
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    sql = """
        SELECT
            t.id, t.title, t.description, t.priority, t.status,
            t.assigned_date,
            DATE_FORMAT(t.assigned_date, '%%d %%b %%Y') AS formatted_assigned_date,
            TIME_FORMAT(t.scheduled_start, '%%h:%%i %%p') AS scheduled_start,
            TIME_FORMAT(t.scheduled_end, '%%h:%%i %%p') AS scheduled_end,
            TIME_FORMAT(t.actual_start, '%%h:%%i %%p') AS actual_start,
            TIME_FORMAT(t.actual_end, '%%h:%%i %%p') AS actual_end,
            t.start_latitude, t.start_longitude, t.start_accuracy,
            t.end_latitude, t.end_longitude, t.end_accuracy,
            t.duration_minutes,
            CONCAT(FLOOR(t.duration_minutes / 60), 'h ', MOD(t.duration_minutes, 60), 'm') AS formatted_duration,
            t.remarks,
            e.id AS employee_id, e.employee_code, e.full_name AS employee_name, e.department,
            l.id AS location_id, l.name AS location_name, l.type AS location_type,
            l.address AS location_address, l.latitude AS location_lat, l.longitude AS location_lng,
            l.allowed_radius_meters,
            u_by.email AS assigned_by_email
        FROM tasks t
        JOIN employees e ON t.employee_id = e.id
        LEFT JOIN locations l ON t.location_id = l.id
        LEFT JOIN users u_by ON t.assigned_by = u_by.id
        WHERE 1=1
    """
    params = []

    # If Staff, restrict strictly to their own tasks
    if user_role == 'STAFF':
        sql += " AND t.employee_id = %s"
        params.append(employee_id)
    elif emp_filter:
        sql += " AND t.employee_id = %s"
        params.append(emp_filter)

    if date_filter:
        sql += " AND t.assigned_date = %s"
        params.append(date_filter)

    if loc_filter:
        sql += " AND t.location_id = %s"
        params.append(loc_filter)

    if priority_filter:
        sql += " AND t.priority = %s"
        params.append(priority_filter)

    if status_filter:
        sql += " AND t.status = %s"
        params.append(status_filter)

    if search:
        sql += " AND (t.title LIKE %s OR t.description LIKE %s OR e.full_name LIKE %s OR e.employee_code LIKE %s)"
        like_str = f"%{search}%"
        params.extend([like_str, like_str, like_str, like_str])

    sql += """ ORDER BY
        CASE t.priority
            WHEN 'URGENT' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            ELSE 4
        END,
        t.assigned_date DESC, t.scheduled_start ASC"""

    tasks = query_all(sql, params)

    # Compute KPI summary
    total = len(tasks)
    in_prog = sum(1 for t in tasks if t['status'] == 'IN_PROGRESS')
    completed = sum(1 for t in tasks if t['status'] == 'COMPLETED')
    pending = sum(1 for t in tasks if t['status'] in ['ASSIGNED', 'ACCEPTED'])
    urgent_or_high = sum(1 for t in tasks if t['priority'] in ['URGENT', 'HIGH'])

    summary = {
        'total': total,
        'in_progress': in_prog,
        'completed': completed,
        'pending': pending,
        'high_priority': urgent_or_high,
    }

    return success_response(data={'tasks': tasks, 'summary': summary}, message="Tasks retrieved.")

@task_bp.route('/today', methods=['GET'])
@jwt_required
def get_today_tasks():
    """Retrieve today's tasks for requesting employee or all for admin."""
    user_role = g.user.get('role')
    employee_id = g.user.get('employee_id')

    if user_role in ['ADMIN', 'HR'] and request.args.get('all') == 'true':
        emp_filter = None
    else:
        emp_filter = employee_id

    sql = """
        SELECT
            t.id, t.title, t.description, t.priority, t.status,
            t.assigned_date,
            TIME_FORMAT(t.scheduled_start, '%%h:%%i %%p') AS scheduled_start,
            TIME_FORMAT(t.scheduled_end, '%%h:%%i %%p') AS scheduled_end,
            TIME_FORMAT(t.actual_start, '%%h:%%i %%p') AS actual_start,
            TIME_FORMAT(t.actual_end, '%%h:%%i %%p') AS actual_end,
            t.duration_minutes, t.remarks,
            e.id AS employee_id, e.employee_code, e.full_name AS employee_name,
            l.id AS location_id, l.name AS location_name, l.type AS location_type,
            l.address AS location_address, l.latitude AS location_lat, l.longitude AS location_lng,
            l.allowed_radius_meters
        FROM tasks t
        JOIN employees e ON t.employee_id = e.id
        LEFT JOIN locations l ON t.location_id = l.id
        WHERE t.assigned_date = CURDATE()
    """
    params = []
    if emp_filter:
        sql += " AND t.employee_id = %s"
        params.append(emp_filter)

    sql += """ ORDER BY
        CASE t.priority
            WHEN 'URGENT' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            ELSE 4
        END,
        t.scheduled_start ASC"""

    tasks = query_all(sql, params)
    return success_response(data={'tasks': tasks}, message="Today's tasks retrieved.")

@task_bp.route('', methods=['POST'])
@role_required(['ADMIN', 'HR'])
def create_task():
    """Admin/HR assigns a field task to one or multiple employees individually."""
    data = request.get_json() or {}

    raw_emp_ids = data.get('employee_ids') or []
    if not raw_emp_ids and data.get('employee_id'):
        raw_emp_ids = [data.get('employee_id')]

    employee_ids = []
    for eid in raw_emp_ids:
        try:
            val = int(eid)
            if val not in employee_ids:
                employee_ids.append(val)
        except (ValueError, TypeError):
            pass

    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    location_id = data.get('location_id')
    priority = (data.get('priority') or 'MEDIUM').strip().upper()
    assigned_date = data.get('assigned_date') or datetime.now().strftime('%Y-%m-%d')
    scheduled_start = data.get('scheduled_start')
    scheduled_end = data.get('scheduled_end')

    if not employee_ids or not title:
        return error_response("At least one employee selection and task title are required.", 400)

    # Verify location exists if provided
    if location_id:
        loc = query_one("SELECT id, name FROM locations WHERE id = %s", (location_id,))
        if not loc:
            return error_response("Selected location hub does not exist.", 404)

    created_tasks = []
    assigned_names = []

    for emp_id in employee_ids:
        emp = query_one("SELECT id, full_name, employee_code, status FROM employees WHERE id = %s", (emp_id,))
        if not emp:
            continue
        if emp['status'] != 'ACTIVE':
            continue

        res = execute(
            """INSERT INTO tasks
               (employee_id, assigned_by, title, description, location_id, priority, assigned_date, scheduled_start, scheduled_end, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ASSIGNED')""",
            (emp_id, g.user['id'], title, description, location_id, priority, assigned_date, scheduled_start, scheduled_end)
        )
        task_id = res['lastrowid']
        created_tasks.append(task_id)
        assigned_names.append(emp['full_name'])

        # In-app notification for each employee
        try:
            execute(
                """INSERT INTO notifications (employee_id, title, message, type)
                   VALUES (%s, %s, %s, 'TASK')""",
                (emp_id, "New Task Assigned", f"You have been assigned task: '{title}' for {assigned_date}")
            )
        except Exception as e:
            print(f"[WARN] Notification insert failed: {e}")

        # Audit log for each task creation
        log_audit(
            user_id=g.user['id'],
            action='TASK_ASSIGNED',
            entity_type='TASK',
            entity_id=task_id,
            description=f"Admin assigned task '{title}' to {emp['full_name']} ({emp['employee_code']}) for {assigned_date}"
        )

    if not created_tasks:
        return error_response("None of the selected employees are active or valid.", 400)

    assigned_str = ", ".join(assigned_names)
    first_task_id = created_tasks[0]

    return success_response(
        data={
            'task_id': first_task_id,
            'task_ids': created_tasks,
            'count': len(created_tasks),
            'title': title,
            'assigned_to': assigned_str
        },
        message=f"Task '{title}' successfully assigned to {len(created_tasks)} {'employee' if len(created_tasks) == 1 else 'employees'} ({assigned_str}).",
        status_code=201
    )

@task_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required
def get_task(task_id):
    """Retrieve full details of a specific task."""
    sql = """
        SELECT
            t.*,
            e.employee_code, e.full_name AS employee_name, e.department,
            l.name AS location_name, l.type AS location_type, l.address AS location_address,
            l.latitude AS hub_latitude, l.longitude AS hub_longitude, l.allowed_radius_meters,
            u.email AS assigned_by_email
        FROM tasks t
        JOIN employees e ON t.employee_id = e.id
        LEFT JOIN locations l ON t.location_id = l.id
        LEFT JOIN users u ON t.assigned_by = u.id
        WHERE t.id = %s
    """
    task = query_one(sql, (task_id,))
    if not task:
        return error_response("Task not found.", 404)

    # Security check: if STAFF, must be assigned employee
    if g.user.get('role') == 'STAFF' and task['employee_id'] != g.user.get('employee_id'):
        return error_response("Access forbidden: You can only view tasks assigned to you.", 403)

    return success_response(data={'task': task}, message="Task details retrieved.")

@task_bp.route('/<int:task_id>', methods=['PUT'])
@role_required(['ADMIN', 'HR'])
def update_task(task_id):
    """Admin updates task details, reassigns, or modifies schedule/status."""
    task = query_one("SELECT id, title, status FROM tasks WHERE id = %s", (task_id,))
    if not task:
        return error_response("Task not found.", 404)

    data = request.get_json() or {}
    title = (data.get('title') or task['title']).strip()
    description = data.get('description')
    employee_id = data.get('employee_id')
    location_id = data.get('location_id')
    priority = data.get('priority')
    assigned_date = data.get('assigned_date')
    scheduled_start = data.get('scheduled_start')
    scheduled_end = data.get('scheduled_end')
    status = data.get('status')

    execute(
        """UPDATE tasks
           SET title = %s, description = COALESCE(%s, description),
               employee_id = COALESCE(%s, employee_id),
               location_id = COALESCE(%s, location_id),
               priority = COALESCE(%s, priority),
               assigned_date = COALESCE(%s, assigned_date),
               scheduled_start = COALESCE(%s, scheduled_start),
               scheduled_end = COALESCE(%s, scheduled_end),
               status = COALESCE(%s, status)
           WHERE id = %s""",
        (title, description, employee_id, location_id, priority, assigned_date, scheduled_start, scheduled_end, status, task_id)
    )

    log_audit(
        user_id=g.user['id'],
        action='TASK_UPDATED',
        entity_type='TASK',
        entity_id=task_id,
        description=f"Admin updated task #{task_id} ('{title}')"
    )

    return success_response(message="Task updated successfully.")

@task_bp.route('/<int:task_id>', methods=['DELETE'])
@role_required(['ADMIN', 'HR'])
def delete_task(task_id):
    """
    Permanently delete an unnecessary or erroneous task from the system.
    Restricted strictly to ADMIN and HR users.
    """
    task = query_one("SELECT id, title, employee_id, status FROM tasks WHERE id = %s", (task_id,))
    if not task:
        return error_response("Task not found.", 404)

    execute("DELETE FROM tasks WHERE id = %s", (task_id,))

    log_audit(
        user_id=g.user['id'],
        action='TASK_DELETED',
        entity_type='TASK',
        entity_id=task_id,
        description=f"Admin {g.user.get('email')} permanently deleted task #{task_id} ('{task['title']}')"
    )

    return success_response(message=f"Task '{task['title']}' deleted successfully.")

@task_bp.route('/<int:task_id>/accept', methods=['POST'])
@jwt_required
def accept_task(task_id):
    """Staff accepts an assigned task (ASSIGNED -> ACCEPTED)."""
    employee_id = g.user.get('employee_id')
    task = query_one("SELECT id, employee_id, status, title FROM tasks WHERE id = %s", (task_id,))
    if not task:
        return error_response("Task not found.", 404)
    if task['employee_id'] != employee_id:
        return error_response("Unauthorized: You cannot accept another employee's task.", 403)
    if task['status'] != 'ASSIGNED':
        return error_response(f"Cannot accept task. Current status is {task['status']}.", 400)

    execute("UPDATE tasks SET status = 'ACCEPTED' WHERE id = %s", (task_id,))
    return success_response(data={'status': 'ACCEPTED'}, message=f"Task '{task['title']}' accepted.")

@task_bp.route('/<int:task_id>/start', methods=['POST'])
@jwt_required
def start_task(task_id):
    """
    Start task with GPS capture and Haversine geofence verification (Section 10 & 12).
    Enforces:
    1. Employee ownership
    2. Daily attendance check-in prerequisite
    3. Task status validation
    4. Geofence radius proximity to assigned logistics hub
    """
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return error_response("Only field staff can initiate tasks.", 403)

    # 1. Fetch task and hub coordinates
    sql = """
        SELECT
            t.id, t.employee_id, t.status, t.title, t.location_id,
            l.name AS location_name, l.latitude AS hub_lat, l.longitude AS hub_lng,
            COALESCE(l.allowed_radius_meters, 300) AS allowed_radius_meters
        FROM tasks t
        LEFT JOIN locations l ON t.location_id = l.id
        WHERE t.id = %s
    """
    task = query_one(sql, (task_id,))
    if not task:
        return error_response("Task not found.", 404)

    # 2. Verify employee ownership
    if task['employee_id'] != employee_id:
        return error_response("Unauthorized: You cannot start another employee's task.", 403)

    # 3. Verify task status
    if task['status'] in ['COMPLETED', 'CANCELLED', 'FAILED']:
        return error_response(f"Cannot start task because it is already {task['status']}.", 400)
    if task['status'] == 'IN_PROGRESS':
        return error_response("Task is already in progress.", 400)

    # 4. Enforce Attendance Prerequisite (Section 10)
    att = query_one(
        "SELECT id, status, check_in_time FROM attendance WHERE employee_id = %s AND attendance_date = CURDATE()",
        (employee_id,)
    )
    if not att or not att.get('check_in_time'):
        return error_response("You must start daily attendance before starting any assigned task.", 400)

    data = request.get_json() or {}
    lat = data.get('latitude')
    lng = data.get('longitude')
    accuracy = data.get('accuracy', 0.0)
    bypass_geofence = data.get('bypass_geofence', False)

    if lat is None or lng is None:
        return error_response("GPS coordinates are strictly required to start a field task.", 400)

    # 5. Geofence Verification via Haversine Formula (Section 12)
    if task.get('hub_lat') and task.get('hub_lng') and not bypass_geofence:
        hub_lat = float(task['hub_lat'])
        hub_lng = float(task['hub_lng'])
        allowed_radius = task['allowed_radius_meters']

        distance_meters = calculate_haversine_distance(lat, lng, hub_lat, hub_lng)
        if distance_meters > allowed_radius:
            if distance_meters >= 1000:
                dist_str = f"{distance_meters / 1000:.1f} km"
            else:
                dist_str = f"{int(distance_meters)} meters"

            return error_response(
                f"Geofence validation failed: You appear to be approximately {dist_str} away from the assigned location ({task['location_name']}). Allowed radius is {allowed_radius}m.",
                403,
                errors={'distance_meters': distance_meters, 'allowed_radius': allowed_radius, 'hub_name': task['location_name']}
            )

    # 6. Begin task
    execute(
        """UPDATE tasks
           SET status = 'IN_PROGRESS', actual_start = NOW(),
               start_latitude = %s, start_longitude = %s, start_accuracy = %s
           WHERE id = %s""",
        (lat, lng, accuracy, task_id)
    )

    now_time = datetime.now().strftime('%I:%M %p')

    log_audit(
        user_id=g.user['id'],
        action='TASK_START',
        entity_type='TASK',
        entity_id=task_id,
        description=f"Staff started task '{task['title']}' at {now_time} with GPS ({lat}, {lng}, ±{accuracy}m)"
    )

    return success_response(
        data={
            'task_id': task_id,
            'status': 'IN_PROGRESS',
            'actual_start': now_time,
            'hub': task.get('location_name')
        },
        message=f"Task '{task['title']}' started successfully."
    )

@task_bp.route('/<int:task_id>/end', methods=['POST'])
@jwt_required
def end_task(task_id):
    """Complete a task with GPS, calculate duration, and record site remarks (Section 11)."""
    employee_id = g.user.get('employee_id')
    if not employee_id:
        return error_response("Only field staff can end assigned tasks.", 403)

    task = query_one(
        "SELECT id, employee_id, status, actual_start, title FROM tasks WHERE id = %s",
        (task_id,)
    )
    if not task:
        return error_response("Task not found.", 404)
    if task['employee_id'] != employee_id:
        return error_response("Unauthorized: You cannot complete another employee's task.", 403)
    if task['status'] != 'IN_PROGRESS':
        return error_response(f"Task must be IN_PROGRESS to complete. Current status: {task['status']}", 400)

    data = request.get_json() or {}
    lat = data.get('latitude')
    lng = data.get('longitude')
    accuracy = data.get('accuracy', 0.0)
    remarks = (data.get('remarks') or 'Completed on site').strip()

    actual_start = task.get('actual_start') or datetime.now()
    now = datetime.now()
    duration = max(1, int((now - actual_start).total_seconds() // 60))

    execute(
        """UPDATE tasks
           SET status = 'COMPLETED', actual_end = NOW(),
               end_latitude = %s, end_longitude = %s, end_accuracy = %s,
               duration_minutes = %s, remarks = %s
           WHERE id = %s""",
        (lat, lng, accuracy, duration, remarks, task_id)
    )

    hours = duration // 60
    mins = duration % 60
    duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

    log_audit(
        user_id=g.user['id'],
        action='TASK_COMPLETE',
        entity_type='TASK',
        entity_id=task_id,
        description=f"Staff completed task '{task['title']}' in {duration_str}. Remarks: {remarks}"
    )

    return success_response(
        data={
            'task_id': task_id,
            'status': 'COMPLETED',
            'duration_minutes': duration,
            'formatted_duration': duration_str,
            'completed_at': now.strftime('%I:%M %p'),
            'remarks': remarks
        },
        message=f"Task '{task['title']}' completed successfully in {duration_str}."
    )
