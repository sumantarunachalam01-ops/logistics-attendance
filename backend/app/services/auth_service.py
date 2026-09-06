import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.config import Config

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def generate_token(user_id: int, role: str, email: str, employee_id: int = None, full_name: str = None) -> str:
    """Generate a signed JWT token with user context and expiration."""
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'user_id': user_id,
        'role': role,
        'email': email,
        'employee_id': employee_id,
        'full_name': full_name,
        'iat': now,
        'exp': now + timedelta(hours=Config.JWT_EXP_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate a signed JWT token."""
    return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
