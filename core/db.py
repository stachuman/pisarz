"""SQLite database helper with context manager for Pisarz projects."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager


@contextmanager
def get_db_connection(db_path: Path):
    """Context manager for SQLite database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_project_db(db_path: Path) -> None:
    """Initialize a new project database with required tables."""
    with get_db_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id        INTEGER PRIMARY KEY,
                name      TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            
            CREATE TABLE IF NOT EXISTS scenes (
                id         INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                title      TEXT NOT NULL,
                content_rtf TEXT,
                ord        INTEGER,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
        """)
        conn.commit()


def execute_query(db_path: Path, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return results as list of dictionaries."""
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def execute_insert(db_path: Path, query: str, params: tuple = ()) -> int:
    """Execute an INSERT query and return the last row ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def execute_update(db_path: Path, query: str, params: tuple = ()) -> int:
    """Execute an UPDATE/DELETE query and return number of affected rows."""
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount