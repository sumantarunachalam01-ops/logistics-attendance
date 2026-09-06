from functools import wraps
from flask import request, g
import jwt
from app.services.auth_service import decode_token
from app.utils.response import error_response
from app.db import query_one

def jwt_required(f):
    """Decorator to require a valid JWT in Authorization header or query parameter."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif request.args.get('token'):
            token = request.args.get('token').strip()

        if not token:
            return error_response("Missing authentication token. Use 'Bearer <token>' or '?token=<token>'", 401)
        
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error_response("Token has expired. Please login again.", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid authentication token.", 401)
        
        # Verify user exists and is active in database
        user = query_one(
            "SELECT u.id, u.email, u.role, u.is_active, e.id AS employee_id, e.employee_code, e.full_name, e.department, e.designation "
            "FROM users u "
            "LEFT JOIN employees e ON u.id = e.user_id "
            "WHERE u.id = %s",
            (payload.get('user_id'),)
        )
        if not user:
            return error_response("User account no longer exists.", 401)
        if not user['is_active']:
            return error_response("User account has been disabled.", 403)
        
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """Decorator to enforce role-based access control (RBAC)."""
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        @jwt_required
        def decorated_function(*args, **kwargs):
            if g.user.get('role') not in roles:
                return error_response(f"Access forbidden: requires one of {roles} role.", 403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
