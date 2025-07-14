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
    _ensure_all_tables(db_path)


def ensure_database_schema(db_path: Path) -> None:
    """Ensure database has all required tables for new projects."""
    _ensure_all_tables(db_path)


def _ensure_all_tables(db_path: Path) -> None:
    """Create all required tables if they don't exist."""
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
            
            CREATE TABLE IF NOT EXISTS characters (
                id         INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                name       TEXT NOT NULL,
                full_name  TEXT,
                alias      TEXT,
                age        INTEGER,
                gender     TEXT,
                occupation TEXT,
                location   TEXT,
                description TEXT,
                personality TEXT,
                background TEXT,
                goals      TEXT,
                conflicts  TEXT,
                relationships TEXT,
                appearance TEXT,
                notes      TEXT,
                importance INTEGER DEFAULT 1,
                is_protagonist INTEGER DEFAULT 0,
                is_antagonist INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            
            CREATE TABLE IF NOT EXISTS scene_characters (
                scene_id     INTEGER,
                character_id INTEGER,
                role         TEXT,
                PRIMARY KEY (scene_id, character_id),
                FOREIGN KEY(scene_id) REFERENCES scenes(id),
                FOREIGN KEY(character_id) REFERENCES characters(id)
            );
            
            CREATE TABLE IF NOT EXISTS character_relationships (
                id              INTEGER PRIMARY KEY,
                character_a_id  INTEGER NOT NULL,
                character_b_id  INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                description     TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(character_a_id) REFERENCES characters(id),
                FOREIGN KEY(character_b_id) REFERENCES characters(id)
            );
            
            -- Performance indexes
            CREATE INDEX IF NOT EXISTS idx_characters_project_id ON characters(project_id);
            CREATE INDEX IF NOT EXISTS idx_characters_importance ON characters(importance DESC);
            CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
            CREATE INDEX IF NOT EXISTS idx_scene_characters_scene_id ON scene_characters(scene_id);
            CREATE INDEX IF NOT EXISTS idx_scene_characters_character_id ON scene_characters(character_id);
            CREATE INDEX IF NOT EXISTS idx_character_relationships_a ON character_relationships(character_a_id);
            CREATE INDEX IF NOT EXISTS idx_character_relationships_b ON character_relationships(character_b_id);
            CREATE INDEX IF NOT EXISTS idx_scenes_project_id ON scenes(project_id);
            CREATE INDEX IF NOT EXISTS idx_scenes_ord ON scenes(ord);
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