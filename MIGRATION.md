# Database Migration Guide for Pisarz

This document explains how to migrate existing Pisarz project databases to the latest schema.

## Overview

Pisarz uses a schema versioning system to manage database migrations. Each version introduces new features and database structure changes. The migration system is separate from the main application to ensure data safety and controlled updates.

## Current Schema Versions

- **Version 0**: Original schema (basic characters table)
- **Version 1**: Comprehensive character fields (full_name, alias, age, gender, occupation, personality, etc.)
- **Version 2**: Scene-character linking with roles, character relationships, performance indexes

## Migration Script Usage

### Check Migration Status

To see which projects need migration without making changes:

```bash
# Check all projects in default directory (~/Pisarz Projects)
python migrate_database.py --check-only

# Check all projects in specific directory
python migrate_database.py /path/to/projects --check-only

# Check single project
python migrate_database.py --project /path/to/project --check-only
```

### Migrate Projects

To perform actual migration:

```bash
# Migrate all projects in default directory
python migrate_database.py

# Migrate all projects in specific directory
python migrate_database.py /path/to/projects

# Migrate single project
python migrate_database.py --project /path/to/project
```

### Force Migration

To force migration even if schema appears up to date:

```bash
python migrate_database.py --force
```

## Migration Process

1. **Backup Creation**: The script automatically creates a backup (.db.backup) before migration
2. **Schema Detection**: Checks current schema version using `schema_version` table
3. **Sequential Migration**: Applies migrations in order (1 → 2 → ... → latest)
4. **Version Tracking**: Updates schema version after each successful migration
5. **Cleanup**: Removes backup file if migration succeeds

## Safety Features

- **Automatic Backups**: Every database is backed up before migration
- **Non-Destructive**: Migrations only add new tables/columns, never remove data
- **Rollback Support**: Backup files allow manual rollback if needed
- **Error Handling**: Migration stops on first error, preserving data integrity
- **Dry Run Mode**: `--check-only` flag shows what would be migrated

## Migration Details

### Version 1: Comprehensive Character Fields

Adds new columns to the `characters` table:
- `full_name`, `alias` - Extended naming
- `age`, `gender`, `occupation`, `location` - Demographics  
- `personality`, `background`, `goals`, `conflicts` - Character development
- `relationships`, `appearance` - Additional details
- `importance`, `is_protagonist`, `is_antagonist` - Story role

### Version 2: Scene-Character Linking & Performance

- Adds `role` column to `scene_characters` table
- Creates `character_relationships` table for character connections
- Adds performance indexes on frequently queried columns
- Improves database query speed for large projects

## Troubleshooting

### "Could not determine schema version"

The database might be corrupted or have permissions issues. Check:
- File permissions (readable/writable)
- Disk space availability
- Database integrity with `sqlite3 database.db ".schema"`

### "Migration failed"

Check the error message for specific issues:
- **Column already exists**: Usually safe to ignore, migration will continue
- **Table locked**: Close Pisarz application before migration
- **Disk full**: Free up space and retry

### "Backup creation failed"

Migration will continue but without backup. Manually backup your projects:
```bash
cp project/pisarz.db project/pisarz.db.backup
```

## Manual Rollback

If you need to restore from backup:

```bash
# Stop Pisarz application first
cp project/pisarz.db.backup project/pisarz.db
```

## Best Practices

1. **Close Pisarz**: Always close the main application before migration
2. **Backup First**: Create manual backups of important projects
3. **Test Migration**: Try migration on a copy of your project first
4. **Check Results**: Open projects in Pisarz after migration to verify
5. **Keep Backups**: Don't immediately delete backup files

## Integration with Application

The main Pisarz application expects the latest schema version. After migration:

1. Projects will have full character features available
2. Scene-character linking will work properly
3. Performance should be improved for large projects
4. No data loss - existing characters retain all original information

## Future Migrations

New versions of Pisarz may introduce additional schema changes. Always:

1. Run the migration script when updating Pisarz
2. Check release notes for migration requirements
3. Keep this script updated with the Pisarz application

## Example Session

```bash
$ python migrate_database.py --check-only
Found 3 Pisarz project database(s)
OK:    My Novel - Schema version 2 (up to date)
NEEDS: Short Story - Schema version 0 -> 2
NEEDS: Old Project - Schema version 1 -> 2

Summary:
  Up to date: 1
  Need migration: 2
  Errors: 0

$ python migrate_database.py
============================================================
Migrating database: /home/user/Pisarz Projects/Short Story/pisarz.db
  Current schema version: 0
  Target schema version: 2
  Created backup: /home/user/Pisarz Projects/Short Story/pisarz.db.backup
  Applying migration to version 1: Add comprehensive character fields
    Existing characters columns: ['created_at', 'description', 'id', 'name', 'notes', 'project_id']
    ✓ Added column 'full_name'
    ✓ Added column 'alias'
    [... more columns ...]
    Added 15 new character columns
  ✓ Successfully migrated to version 1
  Applying migration to version 2: Add scene_characters role column and performance indexes
    ✓ Added 'role' column to scene_characters table
    ✓ Created 9 performance indexes
  ✓ Successfully migrated to version 2
  ✓ Migration completed successfully
  Removed backup file

============================================================
Migration Summary:
  Successful: 2/2
  Failed: 0/2
✓ All databases migrated successfully!
```