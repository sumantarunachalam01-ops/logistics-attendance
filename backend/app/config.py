import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'selfies')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'logistics_attendance')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')
    DB_SSL = os.getenv('DB_SSL', 'false').lower() in ('true', '1', 'yes')
    JWT_SECRET = os.getenv('JWT_SECRET', 'default_jwt_secret_dev_key')
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_HOURS = 24
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
    STANDARD_WORK_MINUTES = int(os.getenv('STANDARD_WORK_MINUTES', 480)) # 8 hours
    UPLOAD_FOLDER = UPLOAD_FOLDER
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
