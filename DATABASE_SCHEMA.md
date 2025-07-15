# Pisarz Database Schema Documentation

## Overview

The Pisarz writing application uses SQLite as its database backend. The complete database schema is defined in `core/db.py` and represents version 4 of the schema.

## Schema Management

- **Current Version**: 4
- **Schema Location**: `core/db.py` in `_ensure_all_tables()` function
- **Version Tracking**: `schema_version` table tracks migration history
- **Migration Support**: Compatible with `migrate_database.py` for existing projects

## Core Tables

### 1. Schema Management

#### `schema_version`
Tracks database schema versions for migration management.
```sql
CREATE TABLE schema_version (
    version INTEGER NOT NULL,
    migrated_at TEXT DEFAULT (datetime('now'))
);
```

### 2. Project Structure

#### `projects`
Main project information and metadata.
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### `scenes`
Individual scenes within projects with content and ordering.
```sql
CREATE TABLE scenes (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content_rtf TEXT,
    ord INTEGER,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
```

### 3. Character Management

#### `characters`
Comprehensive character definitions with all attributes.
```sql
CREATE TABLE characters (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT,
    alias TEXT,
    age INTEGER,
    gender TEXT,
    occupation TEXT,
    location TEXT,
    description TEXT,
    personality TEXT,
    background TEXT,
    goals TEXT,
    conflicts TEXT,
    relationships TEXT,
    appearance TEXT,
    notes TEXT,
    importance INTEGER DEFAULT 1,
    is_protagonist INTEGER DEFAULT 0,
    is_antagonist INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
```

### 4. Location Management

#### `locations`
Location definitions with atmosphere and environmental details.
```sql
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
);
```

### 5. Plot Structure

#### `plot_threads`
Plot threads and story arcs with status tracking.
```sql
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
);
```

## Relationship Tables

### Many-to-Many Relationships

#### `scene_characters`
Links scenes to characters with role definitions.
```sql
CREATE TABLE scene_characters (
    scene_id INTEGER,
    character_id INTEGER,
    role TEXT,
    PRIMARY KEY (scene_id, character_id),
    FOREIGN KEY(scene_id) REFERENCES scenes(id),
    FOREIGN KEY(character_id) REFERENCES characters(id)
);
```

#### `character_relationships`
Defines relationships between characters.
```sql
CREATE TABLE character_relationships (
    id INTEGER PRIMARY KEY,
    character_a_id INTEGER NOT NULL,
    character_b_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(character_a_id) REFERENCES characters(id),
    FOREIGN KEY(character_b_id) REFERENCES characters(id)
);
```

#### `scene_locations`
Links scenes to locations with role information.
```sql
CREATE TABLE scene_locations (
    scene_id INTEGER,
    location_id INTEGER,
    role TEXT,
    PRIMARY KEY (scene_id, location_id),
    FOREIGN KEY(scene_id) REFERENCES scenes(id),
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
```

#### `character_locations`
Links characters to locations with relationship types.
```sql
CREATE TABLE character_locations (
    character_id INTEGER,
    location_id INTEGER,
    relationship_type TEXT,
    description TEXT,
    PRIMARY KEY (character_id, location_id),
    FOREIGN KEY(character_id) REFERENCES characters(id),
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
```

#### `scene_plot_threads`
Links scenes to plot threads.
```sql
CREATE TABLE scene_plot_threads (
    scene_id INTEGER,
    plot_thread_id INTEGER,
    role TEXT,
    PRIMARY KEY (scene_id, plot_thread_id),
    FOREIGN KEY(scene_id) REFERENCES scenes(id),
    FOREIGN KEY(plot_thread_id) REFERENCES plot_threads(id)
);
```

## Full-Text Search (FTS5)

### Virtual Tables

#### `scenes_fts`
Full-text search index for scene content.
```sql
CREATE VIRTUAL TABLE scenes_fts USING fts5(
    title,
    content_rtf,
    content='scenes',
    content_rowid='id'
);
```

#### `characters_fts`
Full-text search index for character information.
```sql
CREATE VIRTUAL TABLE characters_fts USING fts5(
    name,
    description,
    personality,
    background,
    notes,
    content='characters',
    content_rowid='id'
);
```

#### `locations_fts`
Full-text search index for location information.
```sql
CREATE VIRTUAL TABLE locations_fts USING fts5(
    name,
    type,
    description,
    atmosphere,
    details,
    significance,
    notes,
    content='locations',
    content_rowid='id'
);
```

### FTS Synchronization Triggers

Each FTS table has three triggers for automatic synchronization:
- `{table}_fts_insert`: Sync on INSERT
- `{table}_fts_update`: Sync on UPDATE  
- `{table}_fts_delete`: Sync on DELETE

## Performance Indexes

The schema includes comprehensive indexes for optimal query performance:

### Character Indexes
- `idx_characters_project_id`: Project-based queries
- `idx_characters_importance`: Importance-based sorting
- `idx_characters_name`: Name-based lookups

### Scene Indexes
- `idx_scenes_project_id`: Project-based queries
- `idx_scenes_ord`: Scene ordering

### Location Indexes
- `idx_locations_project_id`: Project-based queries
- `idx_locations_name`: Name-based lookups

### Relationship Indexes
- `idx_scene_characters_scene_id`, `idx_scene_characters_character_id`
- `idx_character_relationships_a`, `idx_character_relationships_b`
- `idx_scene_locations_scene_id`, `idx_scene_locations_location_id`
- `idx_character_locations_character_id`, `idx_character_locations_location_id`
- `idx_scene_plot_threads_scene_id`, `idx_scene_plot_threads_plot_id`

### Plot Thread Indexes
- `idx_plot_threads_project_id`: Project-based queries
- `idx_plot_threads_status`: Status-based filtering

## Schema Validation

The database includes built-in validation functions:

- `validate_schema_integrity()`: Validates complete schema
- `get_database_info()`: Returns comprehensive database metadata
- `get_schema_version()`: Returns current schema version

## Usage

### Creating New Database
```python
from core.db import init_project_db
init_project_db(Path("project/pisarz.db"))
```

### Validating Existing Database
```python
from core.db import validate_schema_integrity
is_valid = validate_schema_integrity(Path("project/pisarz.db"))
```

### Getting Database Information
```python
from core.db import get_database_info
info = get_database_info(Path("project/pisarz.db"))
```

## Migration Support

The schema is compatible with the migration system:
- Schema versions are tracked in `schema_version` table
- Migration scripts can update older databases to current schema
- Automatic schema updates applied when opening projects

## Notes

- All tables use INTEGER PRIMARY KEY for optimal SQLite performance
- Foreign key constraints ensure referential integrity
- FTS5 provides powerful full-text search capabilities
- Comprehensive indexing ensures fast queries across all access patterns
- Schema is designed for both simple and complex writing projects