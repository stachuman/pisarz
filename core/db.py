"""SQLite database helper with context manager for Pisarz projects."""

import sqlite3
import logging
from pathlib import Path
from core.llm.settings import GLOBAL_DB_PATH 
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from .error_handler import get_error_handler, ErrorLevel, ErrorCategory

logger = logging.getLogger(__name__)
error_handler = get_error_handler()


@contextmanager
def get_db_connection(db_path: Path = GLOBAL_DB_PATH):
    """Context manager for SQLite database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_project_db(db_path: Path = GLOBAL_DB_PATH) -> None:
    """Initialize a new project database with required tables."""
    _ensure_all_tables(db_path)
    _set_initial_schema_version(db_path)


def ensure_database_schema(db_path: Path = GLOBAL_DB_PATH) -> None:
    """Ensure database has all required tables for new projects."""
    _ensure_all_tables(db_path)


def _ensure_all_tables(db_path: Path = GLOBAL_DB_PATH) -> None:
    """Create all required tables if they don't exist."""
    with get_db_connection(db_path) as conn:
        conn.executescript("""
            -- Schema version tracking table
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL,
                migrated_at TEXT DEFAULT (datetime('now'))
            );
            
            -- Core project data
            CREATE TABLE IF NOT EXISTS projects (
                id        INTEGER PRIMARY KEY,
                name      TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                modified_at TEXT DEFAULT (datetime('now')),
                
                -- Core Information
                title     TEXT,  -- Display title (can differ from directory name)
                author    TEXT,
                genre     TEXT,
                description TEXT,
                language  TEXT DEFAULT 'en',
                
                -- Writing Details
                target_word_count INTEGER,
                status    TEXT DEFAULT 'draft',
                tags      TEXT,
                
                -- Publishing Information
                publisher TEXT,
                isbn      TEXT,
                publication_date TEXT,
                copyright TEXT,
                
                -- Project Settings
                default_scene_template TEXT,
                auto_backup_enabled INTEGER DEFAULT 1,
                daily_word_goal INTEGER DEFAULT 500,
                weekly_word_goal INTEGER DEFAULT 3500
            );
            
            CREATE TABLE IF NOT EXISTS scenes (
                id         INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                title      TEXT NOT NULL,
                content_rtf TEXT,
                ord        INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                modified_at TEXT DEFAULT (datetime('now')),
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
            
            -- LLM cache table
            CREATE TABLE IF NOT EXISTS llm_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                task_id TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
            );
            
            -- LLM settings
            CREATE TABLE IF NOT EXISTS llm_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- LLM conversation history
            CREATE TABLE IF NOT EXISTS llm_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                scene_id INTEGER,
                task_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                context_data TEXT,  -- JSON
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (scene_id) REFERENCES scenes (id)
            );
            
            -- Indexes for LLM performance
            CREATE INDEX IF NOT EXISTS idx_llm_cache_key ON llm_cache (cache_key);
            CREATE INDEX IF NOT EXISTS idx_llm_cache_expires ON llm_cache (expires_at);
            CREATE INDEX IF NOT EXISTS idx_llm_conversations_project ON llm_conversations (project_id);
            CREATE INDEX IF NOT EXISTS idx_llm_conversations_scene ON llm_conversations (scene_id);
            
            -- Narrative context table for story continuity
            CREATE TABLE IF NOT EXISTS narrative_context (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                scene_id INTEGER,
                context_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(scene_id) REFERENCES scenes(id)
            );
            
            -- Indexes for narrative context
            CREATE INDEX IF NOT EXISTS idx_narrative_context_project_id ON narrative_context(project_id);
            CREATE INDEX IF NOT EXISTS idx_narrative_context_type ON narrative_context(context_type);
            CREATE INDEX IF NOT EXISTS idx_narrative_context_active ON narrative_context(is_active);
            CREATE INDEX IF NOT EXISTS idx_narrative_context_scene ON narrative_context(scene_id);
        """)
        
        # Create FTS5 virtual tables for search functionality
        _create_fts_tables(conn)
        
        conn.commit()


# Current schema version - increment when making schema changes
CURRENT_SCHEMA_VERSION = 6

def _set_initial_schema_version(db_path: Path = GLOBAL_DB_PATH) -> None:
    """Set the schema version for a newly created database."""
    try:
        with get_db_connection(db_path) as conn:
            # Check if version is already set
            cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                # Set initial version
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (CURRENT_SCHEMA_VERSION,))
                conn.commit()
                logger.info(f"Set initial schema version to {CURRENT_SCHEMA_VERSION}")
    except Exception as e:
        error_handler.log_error(e, ErrorCategory.DATABASE,
                               context="Setting initial schema version",
                               show_to_user=False)


def get_schema_version(db_path: Path = GLOBAL_DB_PATH) -> int:
    """Get the current schema version of a database."""
    try:
        with get_db_connection(db_path) as conn:
            # Check if schema_version table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            if not cursor.fetchone():
                return 0  # No schema_version table means original schema
            
            # Get version from table
            cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else 0
            
    except Exception as e:
        error_handler.log_error(e, ErrorCategory.DATABASE,
                               context=f"Checking schema version for {db_path}",
                               show_to_user=False)
        return -1


def set_schema_version(db_path: Path = GLOBAL_DB_PATH, version: int = CURRENT_SCHEMA_VERSION) -> bool:
    """Set the schema version in the database."""
    try:
        with get_db_connection(db_path) as conn:
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()
            return True
    except Exception as e:
        error_handler.log_error(e, ErrorCategory.DATABASE,
                               context=f"Setting schema version for {db_path}",
                               show_to_user=False)
        return False


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
    
    # Create triggers to synchronize FTS tables with main tables
    _create_fts_triggers(conn)


def _create_fts_triggers(conn):
    """Create triggers to synchronize FTS5 external content tables with main tables.
    
    FTS5 external content tables with content='table' parameter should automatically
    synchronize, but in practice this doesn't always work reliably. These triggers
    ensure proper synchronization when data is inserted, updated, or deleted.
    """
    
    # Triggers for scenes_fts synchronization
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS scenes_fts_insert AFTER INSERT ON scenes
        BEGIN
            INSERT INTO scenes_fts(rowid, title, content_rtf) 
            VALUES (new.id, new.title, new.content_rtf);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS scenes_fts_update AFTER UPDATE ON scenes
        BEGIN
            INSERT INTO scenes_fts(scenes_fts, rowid, title, content_rtf) 
            VALUES ('delete', old.id, old.title, old.content_rtf);
            INSERT INTO scenes_fts(rowid, title, content_rtf) 
            VALUES (new.id, new.title, new.content_rtf);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS scenes_fts_delete AFTER DELETE ON scenes
        BEGIN
            INSERT INTO scenes_fts(scenes_fts, rowid, title, content_rtf) 
            VALUES ('delete', old.id, old.title, old.content_rtf);
        END
    """)
    
    # Triggers for characters_fts synchronization
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS characters_fts_insert AFTER INSERT ON characters
        BEGIN
            INSERT INTO characters_fts(rowid, name, description, personality, background, notes) 
            VALUES (new.id, new.name, new.description, new.personality, new.background, new.notes);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS characters_fts_update AFTER UPDATE ON characters
        BEGIN
            INSERT INTO characters_fts(characters_fts, rowid, name, description, personality, background, notes) 
            VALUES ('delete', old.id, old.name, old.description, old.personality, old.background, old.notes);
            INSERT INTO characters_fts(rowid, name, description, personality, background, notes) 
            VALUES (new.id, new.name, new.description, new.personality, new.background, new.notes);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS characters_fts_delete AFTER DELETE ON characters
        BEGIN
            INSERT INTO characters_fts(characters_fts, rowid, name, description, personality, background, notes) 
            VALUES ('delete', old.id, old.name, old.description, old.personality, old.background, old.notes);
        END
    """)
    
    # Triggers for locations_fts synchronization
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS locations_fts_insert AFTER INSERT ON locations
        BEGIN
            INSERT INTO locations_fts(rowid, name, type, description, atmosphere, details, significance, notes) 
            VALUES (new.id, new.name, new.type, new.description, new.atmosphere, new.details, new.significance, new.notes);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS locations_fts_update AFTER UPDATE ON locations
        BEGIN
            INSERT INTO locations_fts(locations_fts, rowid, name, type, description, atmosphere, details, significance, notes) 
            VALUES ('delete', old.id, old.name, old.type, old.description, old.atmosphere, old.details, old.significance, old.notes);
            INSERT INTO locations_fts(rowid, name, type, description, atmosphere, details, significance, notes) 
            VALUES (new.id, new.name, new.type, new.description, new.atmosphere, new.details, new.significance, new.notes);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS locations_fts_delete AFTER DELETE ON locations
        BEGIN
            INSERT INTO locations_fts(locations_fts, rowid, name, type, description, atmosphere, details, significance, notes) 
            VALUES ('delete', old.id, old.name, old.type, old.description, old.atmosphere, old.details, old.significance, old.notes);
        END
    """)


def update_database_schema(db_path: Path = GLOBAL_DB_PATH) -> bool:
    """Update existing database with latest schema including FTS triggers."""
    try:
        with get_db_connection(db_path) as conn:
            # Create FTS triggers for existing databases
            _create_fts_triggers(conn)
            conn.commit()
            return True
    except Exception as e:
        error_handler.log_error(e, ErrorCategory.DATABASE,
                               context="Updating database schema",
                               show_to_user=False)
        return False


def rebuild_fts_index(db_path: Path = GLOBAL_DB_PATH) -> bool:
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
        error_handler.log_error(e, ErrorCategory.DATABASE,
                               context="Rebuilding FTS index",
                               show_to_user=False)
        return False

def execute_query(db_path: Path = GLOBAL_DB_PATH, query: str="", params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return results as list of dictionaries."""
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def execute_insert(db_path: Path = GLOBAL_DB_PATH, query: str="", params: tuple = ()) -> int:
    """Execute an INSERT query and return the last row ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def execute_update(db_path: Path = GLOBAL_DB_PATH, query: str="", params: tuple = ()) -> int:
    """Execute an UPDATE/DELETE query and return number of affected rows."""
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount


def validate_schema_integrity(db_path: Path = GLOBAL_DB_PATH) -> bool:
    """Validate that the database schema is complete and correct."""
    try:
        with get_db_connection(db_path) as conn:
            # Define all required tables and their key columns
            required_tables = {
                'schema_version': ['version'],
                'projects': ['id', 'name'],
                'scenes': ['id', 'project_id', 'title', 'content_rtf', 'ord'],
                'characters': ['id', 'project_id', 'name', 'description', 'importance'],
                'scene_characters': ['scene_id', 'character_id', 'role'],
                'character_relationships': ['id', 'character_a_id', 'character_b_id', 'relationship_type'],
                'locations': ['id', 'project_id', 'name', 'type', 'description'],
                'plot_threads': ['id', 'project_id', 'name', 'status'],
                'scene_locations': ['scene_id', 'location_id'],
                'character_locations': ['character_id', 'location_id'],
                'scene_plot_threads': ['scene_id', 'plot_thread_id'],
                'scenes_fts': [],  # FTS virtual table
                'characters_fts': [],  # FTS virtual table  
                'locations_fts': []  # FTS virtual table
            }
            
            # Check that all required tables exist
            for table_name, required_columns in required_tables.items():
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                if not cursor.fetchone():
                    error_handler.log_warning(f"Missing required table: {table_name}",
                                             ErrorCategory.DATABASE, show_to_user=False)
                    return False
                
                # For regular tables, check key columns exist
                if required_columns and not table_name.endswith('_fts'):
                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    existing_columns = {row[1] for row in cursor.fetchall()}
                    
                    missing_columns = set(required_columns) - existing_columns
                    if missing_columns:
                        error_handler.log_warning(f"Table {table_name} missing columns: {missing_columns}",
                                                 ErrorCategory.DATABASE, show_to_user=False)
                        return False
            
            # Check FTS triggers exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='trigger' AND name LIKE '%_fts_%'
            """)
            fts_triggers = [row[0] for row in cursor.fetchall()]
            
            expected_triggers = [
                'scenes_fts_insert', 'scenes_fts_update', 'scenes_fts_delete',
                'characters_fts_insert', 'characters_fts_update', 'characters_fts_delete',
                'locations_fts_insert', 'locations_fts_update', 'locations_fts_delete'
            ]
            
            missing_triggers = set(expected_triggers) - set(fts_triggers)
            if missing_triggers:
                error_handler.log_warning(f"Missing FTS triggers: {missing_triggers}",
                                         ErrorCategory.DATABASE, show_to_user=False)
                # Don't fail validation for missing triggers, they can be added automatically
            
            return True
            
    except Exception as e:
        error_handler.log_error(e, ErrorCategory.DATABASE,
                               context="Schema validation",
                               show_to_user=False)
        return False


def get_database_info(db_path: Path = GLOBAL_DB_PATH) -> Dict[str, Any]:
    """Get comprehensive information about the database."""
    info = {
        'path': str(db_path),
        'exists': db_path.exists(),
        'schema_version': -1,
        'tables': [],
        'indexes': [],
        'triggers': [],
        'valid': False
    }
    
    if not db_path.exists():
        return info
    
    try:
        with get_db_connection(db_path) as conn:
            # Get schema version
            info['schema_version'] = get_schema_version(db_path)
            
            # Get all tables
            cursor = conn.execute("""
                SELECT name, type FROM sqlite_master 
                WHERE type IN ('table', 'view') 
                ORDER BY name
            """)
            info['tables'] = [{'name': row[0], 'type': row[1]} for row in cursor.fetchall()]
            
            # Get all indexes
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            info['indexes'] = [row[0] for row in cursor.fetchall()]
            
            # Get all triggers
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='trigger'
                ORDER BY name
            """)
            info['triggers'] = [row[0] for row in cursor.fetchall()]
            
            # Validate schema
            info['valid'] = validate_schema_integrity(db_path)
            
    except Exception as e:
        error_handler.log_error(e, ErrorCategory.DATABASE,
                               context="Getting database info",
                               show_to_user=False)
    
    return info