import os
import time
import queue
import logging
import threading
from contextlib import contextmanager
import pymysql
from pymysql.cursors import DictCursor
from app.config import Config

logger = logging.getLogger(__name__)

class MySQLConnectionPool:
    """
    High-performance thread-safe connection pool for PyMySQL.
    Eliminates the 150-400ms TCP + SSL TLS handshake overhead on every single SQL query.
    Keeps connections warm and automatically recovers from cloud DB timeouts / drops.
    """
    def __init__(self, max_connections=10, timeout=15):
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = queue.LifoQueue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0

    def _create_raw_connection(self):
        kwargs = {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'autocommit': False,
            'connect_timeout': 10,
            'read_timeout': 20,
            'write_timeout': 20
        }

        # Enable SSL for cloud MySQL providers (Aiven, TiDB Cloud, Railway, etc.)
        if getattr(Config, 'DB_SSL', False):
            kwargs['ssl'] = {'ssl_mode': 'REQUIRED'}

        return pymysql.connect(**kwargs)

    def get_connection(self):
        """Acquire an active, validated connection from the pool or create a new one."""
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            # 1. Try to get an idle connection from the pool
            try:
                conn = self._pool.get_nowait()
                try:
                    # Validate connection liveness; automatically reconnect if dropped
                    conn.ping(reconnect=True)
                    return conn
                except Exception:
                    # Connection is dead; close and decrement count
                    try:
                        conn.close()
                    except Exception:
                        pass
                    with self._lock:
                        self._created_connections = max(0, self._created_connections - 1)
                    continue
            except queue.Empty:
                pass

            # 2. Try to create a new connection if under max capacity
            with self._lock:
                if self._created_connections < self.max_connections:
                    self._created_connections += 1
                    try:
                        conn = self._create_raw_connection()
                        return conn
                    except Exception:
                        self._created_connections = max(0, self._created_connections - 1)
                        raise

            # 3. If pool is full and exhausted, wait for a connection to be returned
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                conn = self._pool.get(timeout=min(remaining, 1.0))
                try:
                    conn.ping(reconnect=True)
                    return conn
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    with self._lock:
                        self._created_connections = max(0, self._created_connections - 1)
                    continue
            except queue.Empty:
                continue

        # Fallback: if pool timed out, create a direct one-off connection
        return self._create_raw_connection()

    def release_connection(self, conn, discard=False):
        """Return a connection back to the pool or discard if broken."""
        if conn is None:
            return

        if discard:
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._created_connections = max(0, self._created_connections - 1)
            return

        try:
            # Rollback any uncommitted transaction state before returning to pool
            conn.rollback()
            self._pool.put_nowait(conn)
        except (queue.Full, Exception):
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._created_connections = max(0, self._created_connections - 1)


# Global connection pool instance
_pool_size = int(os.getenv('DB_POOL_SIZE', 10))
_db_pool = MySQLConnectionPool(max_connections=_pool_size)


def get_connection():
    """Acquire a managed, pooled database connection."""
    return _db_pool.get_connection()


@contextmanager
def get_db_cursor(commit=False):
    """Context manager for acquiring a database cursor with connection reuse & automatic cleanup."""
    conn = _db_pool.get_connection()
    is_broken = False
    try:
        with conn.cursor() as cursor:
            yield cursor
        if commit:
            conn.commit()
    except (pymysql.OperationalError, pymysql.InterfaceError):
        is_broken = True
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        _db_pool.release_connection(conn, discard=is_broken)


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


# Guard flags to ensure schema checks execute only ONCE at startup per process
_overtime_schema_initialized = False
_selfie_schema_initialized = False


def ensure_selfie_table():
    """Ensure that the persistent selfie_storage table exists in MySQL (runs once)."""
    global _selfie_schema_initialized
    if _selfie_schema_initialized:
        return

    try:
        execute("""
            CREATE TABLE IF NOT EXISTS selfie_storage (
                filename VARCHAR(255) PRIMARY KEY,
                image_data MEDIUMBLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        _selfie_schema_initialized = True
    except Exception as e:
        logger.warning(f"Selfie schema check warning: {e}")


def ensure_overtime_schema():
    """
    Safely and non-destructively ensures that overtime tracking columns 
    and attendance_overtime session table exist in the MySQL database.
    Guarantees zero data loss or alteration of existing attendance records.
    Cached so it only runs once per worker lifecycle, preventing DDL table locks.
    """
    global _overtime_schema_initialized
    if _overtime_schema_initialized:
        return

    try:
        existing_cols = query_all("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'attendance'
        """, (Config.DB_NAME,))
        existing_names = {r['COLUMN_NAME'] for r in (existing_cols or [])}

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

        # Also guarantee selfie_storage exists once
        ensure_selfie_table()

        _overtime_schema_initialized = True
    except Exception as e:
        logger.warning(f"Overtime schema check warning: {e}")
