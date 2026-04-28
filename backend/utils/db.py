import sqlite3
from contextlib import contextmanager


@contextmanager
def get_connection(db_path):
    """Context manager for SQLite connections with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
