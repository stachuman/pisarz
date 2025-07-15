"""SQLite database helper with context manager for Pisarz projects."""

import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


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
            
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                description TEXT,
                atmosphere TEXT,
                details TEXT,
                significance TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            
            CREATE TABLE IF NOT EXISTS plot_threads (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                description TEXT,
                status TEXT DEFAULT 'planned',
                priority INTEGER DEFAULT 1,
                start_scene_id INTEGER,
                end_scene_id INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(start_scene_id) REFERENCES scenes(id),
                FOREIGN KEY(end_scene_id) REFERENCES scenes(id)
            );
            
            CREATE TABLE IF NOT EXISTS scene_locations (
                scene_id INTEGER,
                location_id INTEGER,
                role TEXT,
                PRIMARY KEY (scene_id, location_id),
                FOREIGN KEY(scene_id) REFERENCES scenes(id),
                FOREIGN KEY(location_id) REFERENCES locations(id)
            );
            
            CREATE TABLE IF NOT EXISTS character_locations (
                character_id INTEGER,
                location_id INTEGER,
                relationship_type TEXT,
                description TEXT,
                PRIMARY KEY (character_id, location_id),
                FOREIGN KEY(character_id) REFERENCES characters(id),
                FOREIGN KEY(location_id) REFERENCES locations(id)
            );
            
            CREATE TABLE IF NOT EXISTS scene_plot_threads (
                scene_id INTEGER,
                plot_thread_id INTEGER,
                role TEXT,
                PRIMARY KEY (scene_id, plot_thread_id),
                FOREIGN KEY(scene_id) REFERENCES scenes(id),
                FOREIGN KEY(plot_thread_id) REFERENCES plot_threads(id)
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
            CREATE INDEX IF NOT EXISTS idx_locations_project_id ON locations(project_id);
            CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);
            CREATE INDEX IF NOT EXISTS idx_plot_threads_project_id ON plot_threads(project_id);
            CREATE INDEX IF NOT EXISTS idx_plot_threads_status ON plot_threads(status);
            CREATE INDEX IF NOT EXISTS idx_scene_locations_scene_id ON scene_locations(scene_id);
            CREATE INDEX IF NOT EXISTS idx_scene_locations_location_id ON scene_locations(location_id);
            CREATE INDEX IF NOT EXISTS idx_character_locations_character_id ON character_locations(character_id);
            CREATE INDEX IF NOT EXISTS idx_character_locations_location_id ON character_locations(location_id);
            CREATE INDEX IF NOT EXISTS idx_scene_plot_threads_scene_id ON scene_plot_threads(scene_id);
            CREATE INDEX IF NOT EXISTS idx_scene_plot_threads_plot_id ON scene_plot_threads(plot_thread_id);
        """)
        
        # Create FTS5 virtual tables for search functionality
        _create_fts_tables(conn)
        
        conn.commit()


def _create_fts_tables(conn):
    """Create FTS5 virtual tables for full-text search."""
    # FTS5 table for scenes
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS scenes_fts USING fts5(
            title,
            content_rtf,
            content='scenes',
            content_rowid='id'
        )
    """)
    
    # FTS5 table for characters  
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS characters_fts USING fts5(
            name,
            description,
            personality,
            background,
            notes,
            content='characters',
            content_rowid='id'
        )
    """)
    
    # FTS5 table for locations
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS locations_fts USING fts5(
            name,
            type,
            description,
            atmosphere,
            details,
            significance,
            notes,
            content='locations',
            content_rowid='id'
        )
    """)
    
    # Note: FTS5 external content tables automatically sync with main tables
    # No manual triggers needed when using content='table_name' and content_rowid='id'


def _create_fts_triggers(conn):
    """FTS5 external content tables handle synchronization automatically.
    
    This function is kept for compatibility but does nothing since
    FTS5 external content tables with content='table' and content_rowid='id'
    automatically stay synchronized with the main tables.
    """
    pass


def rebuild_fts_index(db_path: Path) -> bool:
    """Rebuild FTS index from existing data."""
    try:
        with get_db_connection(db_path) as conn:
            # Rebuild scenes FTS
            conn.execute("INSERT INTO scenes_fts(scenes_fts) VALUES('rebuild')")
            
            # Rebuild characters FTS 
            conn.execute("INSERT INTO characters_fts(characters_fts) VALUES('rebuild')")
            
            # Rebuild locations FTS
            conn.execute("INSERT INTO locations_fts(locations_fts) VALUES('rebuild')")
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error rebuilding FTS index: {e}")
        return False

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