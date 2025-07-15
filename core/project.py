"""Project management for Pisarz - create/open project folders and databases."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .db import init_project_db, execute_query, execute_insert, update_database_schema, rebuild_fts_index


class ProjectManager:
    """Manages Pisarz project creation and listing."""
    
    def __init__(self, projects_root: Optional[Path] = None):
        """Initialize project manager with root directory for projects."""
        if projects_root is None:
            projects_root = Path.home() / "Pisarz Projects"
        self.projects_root = projects_root
        self.projects_root.mkdir(exist_ok=True)
    
    def create_project(self, name: str) -> Path:
        """Create a new project folder with initialized database."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        
        project_dir = self.projects_root / name
        if project_dir.exists():
            raise ValueError("Project with this name already exists")
        
        project_dir.mkdir(parents=True)
        db_path = project_dir / "pisarz.db"
        
        # Initialize database
        init_project_db(db_path)
        
        # Insert project record
        execute_insert(
            db_path,
            "INSERT INTO projects (name) VALUES (?)",
            (name,)
        )
        
        return project_dir
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all available projects with their metadata."""
        projects = []
        
        if not self.projects_root.exists():
            return projects
        
        for item in self.projects_root.iterdir():
            if item.is_dir():
                db_path = item / "pisarz.db"
                if db_path.exists():
                    try:
                        # Try to get full project data first
                        project_data = execute_query(
                            db_path,
                            """SELECT name, created_at, modified_at, title, author, genre, 
                                     description, status, target_word_count, tags 
                               FROM projects ORDER BY created_at DESC LIMIT 1"""
                        )
                        if project_data:
                            data = project_data[0]
                            projects.append({
                                "name": data["name"],
                                "path": str(item),
                                "created_at": data["created_at"],
                                "modified_at": data.get("modified_at", data["created_at"]),
                                "title": data.get("title", data["name"]),
                                "author": data.get("author", ""),
                                "genre": data.get("genre", ""),
                                "description": data.get("description", ""),
                                "status": data.get("status", "draft"),
                                "target_word_count": data.get("target_word_count", 0),
                                "tags": data.get("tags", "")
                            })
                    except Exception:
                        # Fallback to basic data for older projects
                        try:
                            project_data = execute_query(
                                db_path,
                                "SELECT name, created_at FROM projects ORDER BY created_at DESC LIMIT 1"
                            )
                            if project_data:
                                data = project_data[0]
                                projects.append({
                                    "name": data["name"],
                                    "path": str(item),
                                    "created_at": data["created_at"],
                                    "modified_at": data["created_at"],
                                    "title": data["name"],
                                    "author": "",
                                    "genre": "",
                                    "description": "",
                                    "status": "draft",
                                    "target_word_count": 0,
                                    "tags": ""
                                })
                        except Exception:
                            # Skip corrupted projects
                            continue
        
        return sorted(projects, key=lambda x: x["modified_at"], reverse=True)
    
    def open_project(self, project_path: str) -> bool:
        """Validate and open an existing project."""
        project_dir = Path(project_path)
        db_path = project_dir / "pisarz.db"
        
        if not (project_dir.exists() and db_path.exists()):
            return False
            
        # Update database schema for existing projects
        try:
            update_database_schema(db_path)
            # Note: We don't rebuild FTS index here as it's expensive
            # and only needed if search is broken
        except Exception:
            # If schema update fails, project might still be usable
            pass
            
        return True
        
    def get_project_data(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Get project data including ID from database."""
        db_path = project_path / "pisarz.db"
        if not db_path.exists():
            return None
            
        try:
            # Try to get full project data first
            project_data = execute_query(
                db_path,
                """SELECT id, name, created_at, modified_at, title, author, genre, 
                         description, language, target_word_count, status, tags,
                         publisher, isbn, publication_date, copyright,
                         default_scene_template, auto_backup_enabled, 
                         daily_word_goal, weekly_word_goal
                   FROM projects ORDER BY created_at DESC LIMIT 1"""
            )
            return project_data[0] if project_data else None
        except Exception:
            # Fallback to basic data for older projects
            try:
                project_data = execute_query(
                    db_path,
                    "SELECT id, name, created_at FROM projects ORDER BY created_at DESC LIMIT 1"
                )
                if project_data:
                    data = project_data[0]
                    # Fill in default values for missing attributes
                    data.update({
                        "modified_at": data["created_at"],
                        "title": data["name"],
                        "author": "",
                        "genre": "",
                        "description": "",
                        "language": "en",
                        "target_word_count": 0,
                        "status": "draft",
                        "tags": "",
                        "publisher": "",
                        "isbn": "",
                        "publication_date": "",
                        "copyright": "",
                        "default_scene_template": "",
                        "auto_backup_enabled": True,
                        "daily_word_goal": 500,
                        "weekly_word_goal": 3500
                    })
                    return data
            except Exception:
                return None
    
    def update_project_properties(self, project_path: Path, properties: Dict[str, Any]) -> bool:
        """Update project properties in the database."""
        db_path = project_path / "pisarz.db"
        if not db_path.exists():
            return False
            
        try:
            # Update modified_at timestamp
            properties['modified_at'] = 'datetime(\'now\')'
            
            # Build the UPDATE query
            set_clauses = []
            values = []
            
            for key, value in properties.items():
                if key == 'modified_at':
                    set_clauses.append(f"{key} = datetime('now')")
                else:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = (SELECT id FROM projects ORDER BY created_at DESC LIMIT 1)"
            
            execute_query(db_path, query, values)
            return True
            
        except Exception as e:
            print(f"Error updating project properties: {e}")
            return False
    
    def rebuild_project_search_index(self, project_path: Path) -> bool:
        """Rebuild the FTS search index for a project."""
        db_path = project_path / "pisarz.db"
        if not db_path.exists():
            return False
            
        return rebuild_fts_index(db_path)


