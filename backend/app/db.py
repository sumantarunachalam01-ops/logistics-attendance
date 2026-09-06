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
