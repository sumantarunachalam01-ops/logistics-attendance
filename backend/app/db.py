import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from app.config import Config

def get_connection():
    """Create and return a raw PyMySQL database connection."""
    kwargs = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,
        'autocommit': False
    }

    # Enable SSL for cloud MySQL providers (Aiven, TiDB Cloud, Railway, etc.)
    if getattr(Config, 'DB_SSL', False):
        kwargs['ssl'] = {'ssl_mode': 'REQUIRED'}

    return pymysql.connect(**kwargs)

@contextmanager
def get_db_cursor(commit=False):
    """Context manager for acquiring a database cursor with automatic cleanup."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def query_one(sql, params=None):
    """Execute query and fetch a single dictionary row."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()

def query_all(sql, params=None):
    """Execute query and fetch all dictionary rows."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()

def execute(sql, params=None):
    """Execute insert/update/delete statement and return lastrowid and rowcount."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(sql, params or ())
        return {
            'lastrowid': cursor.lastrowid,
            'rowcount': cursor.rowcount
        }

def ensure_overtime_schema():
    """
    Safely and non-destructively ensures that overtime tracking columns 
    and attendance_overtime session table exist in the MySQL database.
    Guarantees zero data loss or alteration of existing attendance records.
    """
    try:
        existing_cols = query_all("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'attendance'
        """, (Config.DB_NAME,))
        existing_names = {r['COLUMN_NAME'] for r in existing_cols}

        columns_to_add = [
            ("ot_check_in_time", "DATETIME NULL"),
            ("ot_check_out_time", "DATETIME NULL"),
            ("ot_check_in_latitude", "DECIMAL(10, 7) NULL"),
            ("ot_check_in_longitude", "DECIMAL(10, 7) NULL"),
            ("ot_check_in_accuracy", "DECIMAL(8, 2) NULL"),
            ("ot_check_out_latitude", "DECIMAL(10, 7) NULL"),
            ("ot_check_out_longitude", "DECIMAL(10, 7) NULL"),
            ("ot_check_out_accuracy", "DECIMAL(8, 2) NULL"),
            ("ot_check_in_selfie", "VARCHAR(255) NULL"),
            ("ot_check_out_selfie", "VARCHAR(255) NULL"),
            ("ot_work_minutes", "INT NOT NULL DEFAULT 0"),
            ("ot_status", "VARCHAR(20) NULL")
        ]

        for col_name, col_def in columns_to_add:
            if col_name not in existing_names:
                try:
                    execute(f"ALTER TABLE attendance ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass

        execute("""
            CREATE TABLE IF NOT EXISTS attendance_overtime (
                id INT AUTO_INCREMENT PRIMARY KEY,
                attendance_id INT NOT NULL,
                employee_id INT NOT NULL,
                overtime_date DATE NOT NULL,
                check_in_time DATETIME NOT NULL,
                check_out_time DATETIME NULL,
                check_in_latitude DECIMAL(10, 7) NULL,
                check_in_longitude DECIMAL(10, 7) NULL,
                check_in_accuracy DECIMAL(8, 2) NULL,
                check_out_latitude DECIMAL(10, 7) NULL,
                check_out_longitude DECIMAL(10, 7) NULL,
                check_out_accuracy DECIMAL(8, 2) NULL,
                check_in_selfie VARCHAR(255) NULL,
                check_out_selfie VARCHAR(255) NULL,
                duration_minutes INT NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                remarks TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_ot_emp_date (employee_id, overtime_date),
                INDEX idx_ot_attendance (attendance_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
    except Exception:
        pass

