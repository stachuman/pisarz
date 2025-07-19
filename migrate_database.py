#!/usr/bin/env python3
"""
Database Migration Script for Pisarz Writing Application

This script migrates existing Pisarz project databases to the latest schema.
It should be run separately from the main application to update old projects.

Usage:
    python migrate_database.py                    # Migrate all projects in default directory
    python migrate_database.py /path/to/projects  # Migrate all projects in specific directory
    python migrate_database.py --project /path/to/specific/project  # Migrate single project
    python migrate_database.py --check-only       # Check which projects need migration
"""

import sys
import sqlite3
import argparse
from pathlib import Path
from typing import List, Dict, Set
from contextlib import contextmanager


# Database schema versions and migration steps
CURRENT_SCHEMA_VERSION = 6
MIGRATION_STEPS = {
    1: "Add comprehensive character fields",
    2: "Add scene_characters role column and performance indexes",
    3: "Add locations and plot threads with tri-directional linking",
    4: "Add FTS5 full-text search tables and triggers",
    5: "Add project attributes and metadata fields",
    6: "Add scene timestamp tracking for narrative context freshness"
}


@contextmanager
def get_db_connection(db_path: Path):
    """Context manager for SQLite database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_schema_version(db_path: Path) -> int:
    """Get the current schema version of a database."""
    try:
        with get_db_connection(db_path) as conn:
            # Check if schema_version table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            if not cursor.fetchone():
                # No schema_version table means original schema (version 0)
                return 0
            
            # Get version from table
            cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else 0
            
    except sqlite3.Error as e:
        print(f"Error checking schema version for {db_path}: {e}")
        return -1


def set_schema_version(db_path: Path, version: int) -> bool:
    """Set the schema version in the database."""
    try:
        with get_db_connection(db_path) as conn:
            # Create schema_version table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER NOT NULL,
                    migrated_at TEXT DEFAULT (datetime('now'))
                )
            """)
            
            # Insert new version
            conn.execute("""
                INSERT INTO schema_version (version) VALUES (?)
            """, (version,))
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"Error setting schema version for {db_path}: {e}")
        return False


def get_table_columns(conn, table_name: str) -> Set[str]:
    """Get the set of column names for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def migrate_to_version_1(db_path: Path) -> bool:
    """Migrate database to version 1: Add comprehensive character fields."""
    print(f"  Migrating to version 1: Adding comprehensive character fields...")
    
    try:
        with get_db_connection(db_path) as conn:
            # Check if characters table exists
            if not table_exists(conn, 'characters'):
                print(f"    Characters table doesn't exist, creating it...")
                # Create the complete characters table with all fields
                conn.execute("""
                    CREATE TABLE characters (
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
                    )
                """)
                print(f"    ✓ Created characters table with all comprehensive fields")
                conn.commit()
                return True
            
            # Get existing columns
            existing_columns = get_table_columns(conn, 'characters')
            print(f"    Existing characters columns: {sorted(existing_columns)}")
            
            # Define required columns for comprehensive character schema
            required_columns = {
                'full_name': 'TEXT',
                'alias': 'TEXT', 
                'age': 'INTEGER',
                'gender': 'TEXT',
                'occupation': 'TEXT',
                'location': 'TEXT',
                'personality': 'TEXT',
                'background': 'TEXT',
                'goals': 'TEXT',
                'conflicts': 'TEXT',
                'relationships': 'TEXT',
                'appearance': 'TEXT',
                'importance': 'INTEGER DEFAULT 1',
                'is_protagonist': 'INTEGER DEFAULT 0',
                'is_antagonist': 'INTEGER DEFAULT 0'
            }
            
            # Add missing columns
            columns_added = 0
            for column_name, column_type in required_columns.items():
                if column_name not in existing_columns:
                    try:
                        alter_query = f"ALTER TABLE characters ADD COLUMN {column_name} {column_type}"
                        conn.execute(alter_query)
                        print(f"    ✓ Added column '{column_name}'")
                        columns_added += 1
                    except sqlite3.OperationalError as e:
                        print(f"    ✗ Failed to add column '{column_name}': {e}")
                        return False
            
            if columns_added == 0:
                print(f"    All character columns already exist")
            else:
                print(f"    Added {columns_added} new character columns")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"    Error during version 1 migration: {e}")
        return False


def migrate_to_version_2(db_path: Path) -> bool:
    """Migrate database to version 2: Add scene_characters role column and indexes."""
    print(f"  Migrating to version 2: Adding scene_characters role column and performance indexes...")
    
    try:
        with get_db_connection(db_path) as conn:
            # Create scene_characters table if it doesn't exist
            if not table_exists(conn, 'scene_characters'):
                print(f"    Creating scene_characters table...")
                conn.execute("""
                    CREATE TABLE scene_characters (
                        scene_id     INTEGER,
                        character_id INTEGER,
                        role         TEXT,
                        PRIMARY KEY (scene_id, character_id),
                        FOREIGN KEY(scene_id) REFERENCES scenes(id),
                        FOREIGN KEY(character_id) REFERENCES characters(id)
                    )
                """)
            else:
                # Add role column if missing
                existing_sc_columns = get_table_columns(conn, 'scene_characters')
                if 'role' not in existing_sc_columns:
                    conn.execute("ALTER TABLE scene_characters ADD COLUMN role TEXT")
                    print(f"    ✓ Added 'role' column to scene_characters table")
                else:
                    print(f"    Role column already exists in scene_characters table")
            
            # Create character_relationships table if it doesn't exist
            if not table_exists(conn, 'character_relationships'):
                print(f"    Creating character_relationships table...")
                conn.execute("""
                    CREATE TABLE character_relationships (
                        id              INTEGER PRIMARY KEY,
                        character_a_id  INTEGER NOT NULL,
                        character_b_id  INTEGER NOT NULL,
                        relationship_type TEXT NOT NULL,
                        description     TEXT,
                        created_at      TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY(character_a_id) REFERENCES characters(id),
                        FOREIGN KEY(character_b_id) REFERENCES characters(id)
                    )
                """)
            
            # Add performance indexes
            indexes = [
                ("idx_characters_project_id", "characters", "project_id"),
                ("idx_characters_importance", "characters", "importance DESC"),
                ("idx_characters_name", "characters", "name"),
                ("idx_scene_characters_scene_id", "scene_characters", "scene_id"),
                ("idx_scene_characters_character_id", "scene_characters", "character_id"),
                ("idx_character_relationships_a", "character_relationships", "character_a_id"),
                ("idx_character_relationships_b", "character_relationships", "character_b_id"),
                ("idx_scenes_project_id", "scenes", "project_id"),
                ("idx_scenes_ord", "scenes", "ord")
            ]
            
            indexes_created = 0
            for index_name, table_name, columns in indexes:
                if table_exists(conn, table_name):
                    try:
                        conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})")
                        indexes_created += 1
                    except sqlite3.OperationalError as e:
                        print(f"    Warning: Could not create index {index_name}: {e}")
            
            print(f"    ✓ Created {indexes_created} performance indexes")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"    Error during version 2 migration: {e}")
        return False


def migrate_to_version_3(db_path: Path) -> bool:
    """Migrate database to version 3: Add locations and plot threads with tri-directional linking."""
    print(f"  Migrating to version 3: Adding locations and plot threads with tri-directional linking...")
    
    try:
        with get_db_connection(db_path) as conn:
            # Create locations table
            if not table_exists(conn, 'locations'):
                print(f"    Creating locations table...")
                conn.execute("""
                    CREATE TABLE locations (
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
                    )
                """)
            
            # Create plot_threads table
            if not table_exists(conn, 'plot_threads'):
                print(f"    Creating plot_threads table...")
                conn.execute("""
                    CREATE TABLE plot_threads (
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
                    )
                """)
            
            # Create scene_locations table for scene-location linking
            if not table_exists(conn, 'scene_locations'):
                print(f"    Creating scene_locations table...")
                conn.execute("""
                    CREATE TABLE scene_locations (
                        scene_id INTEGER,
                        location_id INTEGER,
                        role TEXT,
                        PRIMARY KEY (scene_id, location_id),
                        FOREIGN KEY(scene_id) REFERENCES scenes(id),
                        FOREIGN KEY(location_id) REFERENCES locations(id)
                    )
                """)
            
            # Create character_locations table for character-location linking
            if not table_exists(conn, 'character_locations'):
                print(f"    Creating character_locations table...")
                conn.execute("""
                    CREATE TABLE character_locations (
                        character_id INTEGER,
                        location_id INTEGER,
                        relationship_type TEXT,
                        description TEXT,
                        PRIMARY KEY (character_id, location_id),
                        FOREIGN KEY(character_id) REFERENCES characters(id),
                        FOREIGN KEY(location_id) REFERENCES locations(id)
                    )
                """)
            
            # Create scene_plot_threads table for scene-plot linking
            if not table_exists(conn, 'scene_plot_threads'):
                print(f"    Creating scene_plot_threads table...")
                conn.execute("""
                    CREATE TABLE scene_plot_threads (
                        scene_id INTEGER,
                        plot_thread_id INTEGER,
                        role TEXT,
                        PRIMARY KEY (scene_id, plot_thread_id),
                        FOREIGN KEY(scene_id) REFERENCES scenes(id),
                        FOREIGN KEY(plot_thread_id) REFERENCES plot_threads(id)
                    )
                """)
            
            # Add performance indexes for new tables
            new_indexes = [
                ("idx_locations_project_id", "locations", "project_id"),
                ("idx_locations_name", "locations", "name"),
                ("idx_plot_threads_project_id", "plot_threads", "project_id"),
                ("idx_plot_threads_status", "plot_threads", "status"),
                ("idx_scene_locations_scene_id", "scene_locations", "scene_id"),
                ("idx_scene_locations_location_id", "scene_locations", "location_id"),
                ("idx_character_locations_character_id", "character_locations", "character_id"),
                ("idx_character_locations_location_id", "character_locations", "location_id"),
                ("idx_scene_plot_threads_scene_id", "scene_plot_threads", "scene_id"),
                ("idx_scene_plot_threads_plot_id", "scene_plot_threads", "plot_thread_id")
            ]
            
            indexes_created = 0
            for index_name, table_name, columns in new_indexes:
                if table_exists(conn, table_name):
                    try:
                        conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})")
                        indexes_created += 1
                    except sqlite3.OperationalError as e:
                        print(f"    Warning: Could not create index {index_name}: {e}")
            
            print(f"    ✓ Created {indexes_created} new performance indexes")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"    Error during version 3 migration: {e}")
        return False


def migrate_to_version_4(db_path: Path) -> bool:
    """Migrate database to version 4: Add FTS5 full-text search tables and triggers."""
    print(f"  Migrating to version 4: Adding FTS5 full-text search tables and triggers...")
    
    try:
        with get_db_connection(db_path) as conn:
            # Create FTS5 virtual tables
            print(f"    Creating FTS5 virtual tables...")
            
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
            
            print(f"    ✓ Created FTS5 virtual tables")
            
            # Note: FTS5 external content tables automatically sync with main tables
            # No manual triggers needed when using content='table_name' and content_rowid='id'
            print(f"    ✓ FTS5 external content tables configured for automatic sync")
            
            # Populate FTS tables with existing data
            print(f"    Populating FTS tables with existing data...")
            
            # Populate scenes FTS
            conn.execute("""
                INSERT INTO scenes_fts(title, content_rtf)
                SELECT title, content_rtf FROM scenes
            """)
            
            # Populate characters FTS
            conn.execute("""
                INSERT INTO characters_fts(name, description, personality, background, notes)
                SELECT name, description, personality, background, notes FROM characters
            """)
            
            # Populate locations FTS (only if locations table exists)
            if table_exists(conn, 'locations'):
                conn.execute("""
                    INSERT INTO locations_fts(name, type, description, atmosphere, details, significance, notes)
                    SELECT name, type, description, atmosphere, details, significance, notes FROM locations
                """)
            
            print(f"    ✓ Populated FTS tables with existing data")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"    Error during version 4 migration: {e}")
        return False


def migrate_to_version_5(db_path: Path) -> bool:
    """Migrate database to version 5: Add project attributes and metadata fields."""
    print(f"  Migrating to version 5: Adding project attributes and metadata fields...")
    
    try:
        with get_db_connection(db_path) as conn:
            # Get existing columns in projects table
            existing_columns = get_table_columns(conn, 'projects')
            print(f"    Existing projects columns: {sorted(existing_columns)}")
            
            # Define new project attribute columns
            new_columns = {
                'modified_at': 'TEXT DEFAULT (datetime(\'now\'))',
                'title': 'TEXT',
                'author': 'TEXT',
                'genre': 'TEXT',
                'description': 'TEXT',
                'language': 'TEXT DEFAULT \'en\'',
                'target_word_count': 'INTEGER',
                'status': 'TEXT DEFAULT \'draft\'',
                'tags': 'TEXT',
                'publisher': 'TEXT',
                'isbn': 'TEXT',
                'publication_date': 'TEXT',
                'copyright': 'TEXT',
                'default_scene_template': 'TEXT',
                'auto_backup_enabled': 'INTEGER DEFAULT 1',
                'daily_word_goal': 'INTEGER DEFAULT 500',
                'weekly_word_goal': 'INTEGER DEFAULT 3500'
            }
            
            # Add missing columns
            columns_added = 0
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    try:
                        alter_query = f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}"
                        conn.execute(alter_query)
                        print(f"    ✓ Added column '{column_name}'")
                        columns_added += 1
                    except sqlite3.OperationalError as e:
                        print(f"    ✗ Failed to add column '{column_name}': {e}")
                        return False
            
            if columns_added == 0:
                print(f"    All project attribute columns already exist")
            else:
                print(f"    Added {columns_added} new project attribute columns")
            
            # Set title to name for existing projects where title is NULL
            conn.execute("UPDATE projects SET title = name WHERE title IS NULL")
            print(f"    ✓ Set title to name for existing projects")
            
            # Set modified_at to created_at for existing projects where modified_at is NULL
            conn.execute("UPDATE projects SET modified_at = created_at WHERE modified_at IS NULL")
            print(f"    ✓ Set modified_at to created_at for existing projects")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"    Error during version 5 migration: {e}")
        return False


def migrate_to_version_6(db_path: Path) -> bool:
    """Migrate database to version 6: Add scene timestamp tracking for narrative context freshness."""
    print(f"  Migrating to version 6: Adding scene timestamp tracking...")
    
    try:
        with get_db_connection(db_path) as conn:
            # Get existing columns in scenes table
            existing_columns = get_table_columns(conn, 'scenes')
            print(f"    Existing scenes columns: {sorted(existing_columns)}")
            
            # Define new timestamp columns for scenes
            new_columns = {
                'created_at': 'TEXT DEFAULT (datetime(\'now\'))',
                'modified_at': 'TEXT DEFAULT (datetime(\'now\'))'
            }
            
            # Add missing timestamp columns
            columns_added = 0
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    try:
                        alter_query = f"ALTER TABLE scenes ADD COLUMN {column_name} {column_type}"
                        conn.execute(alter_query)
                        print(f"    ✓ Added column '{column_name}' to scenes table")
                        columns_added += 1
                    except sqlite3.OperationalError as e:
                        print(f"    ✗ Failed to add column '{column_name}' to scenes: {e}")
                        return False
            
            if columns_added == 0:
                print(f"    All scene timestamp columns already exist")
            else:
                print(f"    Added {columns_added} new timestamp columns to scenes table")
            
            # Set created_at and modified_at to current time for existing scenes that don't have timestamps
            conn.execute("UPDATE scenes SET created_at = datetime('now') WHERE created_at IS NULL")
            conn.execute("UPDATE scenes SET modified_at = datetime('now') WHERE modified_at IS NULL")
            print(f"    ✓ Initialized timestamps for existing scenes")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"    Error during version 6 migration: {e}")
        return False


def validate_schema_integrity(db_path: Path) -> bool:
    """Validate that the database schema matches its reported version."""
    try:
        with get_db_connection(db_path) as conn:
            version = get_schema_version(db_path)
            
            # For version 1+, characters table must exist
            if version >= 1:
                if not table_exists(conn, 'characters'):
                    print(f"  ⚠ Schema validation failed: Missing characters table for version {version}")
                    return False
            
            # For version 2+, scene_characters must have role column
            if version >= 2:
                if table_exists(conn, 'scene_characters'):
                    columns = get_table_columns(conn, 'scene_characters')
                    if 'role' not in columns:
                        print(f"  ⚠ Schema validation failed: Missing role column for version {version}")
                        return False
            
            # For version 3+, locations and plot tables must exist
            if version >= 3:
                required_tables = ['locations', 'plot_threads', 'scene_locations', 'character_locations']
                for table in required_tables:
                    if not table_exists(conn, table):
                        print(f"  ⚠ Schema validation failed: Missing {table} table for version {version}")
                        return False
            
            # For version 4+, FTS5 tables must exist
            if version >= 4:
                required_fts_tables = ['scenes_fts', 'characters_fts', 'locations_fts']
                for table in required_fts_tables:
                    if not table_exists(conn, table):
                        print(f"  ⚠ Schema validation failed: Missing FTS table {table} for version {version}")
                        return False
            
            # For version 5+, projects table must have extended attributes
            if version >= 5:
                if table_exists(conn, 'projects'):
                    projects_columns = get_table_columns(conn, 'projects')
                    required_project_columns = ['title', 'author', 'genre', 'description', 'language', 'status', 'modified_at']
                    missing_columns = [col for col in required_project_columns if col not in projects_columns]
                    if missing_columns:
                        print(f"  ⚠ Schema validation failed: Missing project columns {missing_columns} for version {version}")
                        return False
            
            # For version 6+, scenes table must have timestamp columns
            if version >= 6:
                if table_exists(conn, 'scenes'):
                    scenes_columns = get_table_columns(conn, 'scenes')
                    required_scene_columns = ['created_at', 'modified_at']
                    missing_columns = [col for col in required_scene_columns if col not in scenes_columns]
                    if missing_columns:
                        print(f"  ⚠ Schema validation failed: Missing scene timestamp columns {missing_columns} for version {version}")
                        return False
            
            return True
            
    except Exception as e:
        print(f"  Error during schema validation: {e}")
        return False


def migrate_database(db_path: Path, force: bool = False) -> bool:
    """Migrate a single database to the latest schema version."""
    if not db_path.exists():
        print(f"Database file does not exist: {db_path}")
        return False
    
    print(f"Migrating database: {db_path}")
    
    # Get current schema version
    current_version = get_schema_version(db_path)
    if current_version == -1:
        print(f"  Error: Could not determine schema version")
        return False
    
    print(f"  Current schema version: {current_version}")
    print(f"  Target schema version: {CURRENT_SCHEMA_VERSION}")
    
    # Validate schema integrity
    if current_version > 0 and not validate_schema_integrity(db_path):
        print(f"  Schema integrity check failed - forcing re-migration")
        force = True
    
    if current_version >= CURRENT_SCHEMA_VERSION and not force:
        print(f"  ✓ Database is already up to date")
        return True
    
    # Backup database before migration
    backup_path = db_path.with_suffix('.db.backup')
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"  Created backup: {backup_path}")
    except Exception as e:
        print(f"  Warning: Could not create backup: {e}")
    
    # Apply migrations in sequence
    success = True
    start_version = current_version + 1 if not force else 1
    
    for version in range(start_version, CURRENT_SCHEMA_VERSION + 1):
        print(f"  Applying migration to version {version}: {MIGRATION_STEPS.get(version, 'Unknown')}")
        
        if version == 1:
            success = migrate_to_version_1(db_path)
        elif version == 2:
            success = migrate_to_version_2(db_path)
        elif version == 3:
            success = migrate_to_version_3(db_path)
        elif version == 4:
            success = migrate_to_version_4(db_path)
        elif version == 5:
            success = migrate_to_version_5(db_path)
        elif version == 6:
            success = migrate_to_version_6(db_path)
        else:
            print(f"    Error: Unknown migration version {version}")
            success = False
        
        if not success:
            print(f"  ✗ Migration to version {version} failed")
            break
        
        # Update schema version
        if not set_schema_version(db_path, version):
            print(f"  ✗ Failed to update schema version to {version}")
            success = False
            break
        
        print(f"  ✓ Successfully migrated to version {version}")
    
    if success:
        print(f"  ✓ Migration completed successfully")
        # Remove backup if migration was successful
        try:
            backup_path.unlink()
            print(f"  Removed backup file")
        except Exception:
            pass
    else:
        print(f"  ✗ Migration failed - backup available at {backup_path}")
    
    return success


def find_project_databases(projects_root: Path) -> List[Path]:
    """Find all Pisarz project databases in a directory."""
    databases = []
    
    if not projects_root.exists():
        print(f"Projects directory does not exist: {projects_root}")
        return databases
    
    # Look for pisarz.db files in subdirectories
    for item in projects_root.iterdir():
        if item.is_dir():
            db_path = item / "pisarz.db"
            if db_path.exists():
                databases.append(db_path)
    
    return databases


def check_migration_status(projects_root: Path) -> Dict[str, List[Path]]:
    """Check which projects need migration."""
    databases = find_project_databases(projects_root)
    
    status = {
        'up_to_date': [],
        'needs_migration': [],
        'error': []
    }
    
    for db_path in databases:
        version = get_schema_version(db_path)
        project_name = db_path.parent.name
        
        if version == -1:
            status['error'].append(db_path)
            print(f"ERROR: {project_name} - Could not determine schema version")
        elif version >= CURRENT_SCHEMA_VERSION:
            status['up_to_date'].append(db_path)
            print(f"OK:    {project_name} - Schema version {version} (up to date)")
        else:
            status['needs_migration'].append(db_path)
            print(f"NEEDS: {project_name} - Schema version {version} -> {CURRENT_SCHEMA_VERSION}")
    
    return status


def main():
    parser = argparse.ArgumentParser(description='Migrate Pisarz project databases to latest schema')
    parser.add_argument('projects_dir', nargs='?', 
                       help='Directory containing Pisarz projects (default: ~/Pisarz Projects)')
    parser.add_argument('--project', '-p', type=Path,
                       help='Migrate a single project directory')
    parser.add_argument('--check-only', '-c', action='store_true',
                       help='Only check migration status, do not migrate')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force migration even if already up to date')
    
    args = parser.parse_args()
    
    # Determine projects directory
    if args.project:
        # Single project mode
        project_path = args.project
        if not project_path.is_dir():
            print(f"Error: Project directory does not exist: {project_path}")
            return 1
        
        db_path = project_path / "pisarz.db"
        if not db_path.exists():
            print(f"Error: No pisarz.db found in project directory: {project_path}")
            return 1
        
        databases = [db_path]
        
    else:
        # Multiple projects mode
        if args.projects_dir:
            projects_root = Path(args.projects_dir)
        else:
            projects_root = Path.home() / "Pisarz Projects"
        
        databases = find_project_databases(projects_root)
        
        if not databases:
            print(f"No Pisarz project databases found in: {projects_root}")
            return 0
        
        print(f"Found {len(databases)} Pisarz project database(s)")
    
    # Check migration status
    if args.check_only:
        if args.project:
            version = get_schema_version(databases[0])
            project_name = databases[0].parent.name
            print(f"Project: {project_name}")
            print(f"Current schema version: {version}")
            print(f"Target schema version: {CURRENT_SCHEMA_VERSION}")
            print(f"Status: {'Up to date' if version >= CURRENT_SCHEMA_VERSION else 'Needs migration'}")
        else:
            status = check_migration_status(projects_root)
            print(f"\nSummary:")
            print(f"  Up to date: {len(status['up_to_date'])}")
            print(f"  Need migration: {len(status['needs_migration'])}")
            print(f"  Errors: {len(status['error'])}")
        return 0
    
    # Perform migrations
    success_count = 0
    total_count = len(databases)
    
    for db_path in databases:
        print(f"\n{'='*60}")
        if migrate_database(db_path, force=args.force):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Migration Summary:")
    print(f"  Successful: {success_count}/{total_count}")
    print(f"  Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print(f"✓ All databases migrated successfully!")
        return 0
    else:
        print(f"✗ Some migrations failed. Check the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())