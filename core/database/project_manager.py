"""
Project manager using the new database access layer.
Replaces project management with clean repository pattern.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from .project_repository import ProjectRepository, Project
from ..db import init_project_db, update_database_schema, rebuild_fts_index
from ..error_handler import get_error_handler, ErrorLevel, ErrorCategory


class ProjectManager:
    """
    Project manager using the new repository pattern.
    Handles project creation, listing, and management operations.
    """
    
    def __init__(self, projects_root: Optional[Path] = None):
        """Initialize project manager with root directory for projects."""
        if projects_root is None:
            projects_root = Path.home() / "Pisarz Projects"
        self.error_handler = get_error_handler()
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
        
        # Create project repository and insert project record
        project_repo = ProjectRepository(db_path)
        project_id = project_repo.create(name=name)
        
        if not project_id:
            raise RuntimeError("Failed to create project record in database")
        
        return project_dir
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all existing projects."""
        projects = []
        
        if not self.projects_root.exists():
            return projects
        
        try:
            for project_dir in self.projects_root.iterdir():
                if project_dir.is_dir():
                    db_path = project_dir / "pisarz.db"
                    if db_path.exists():
                        try:
                            project_data = self.get_project_data(project_dir)
                            if project_data:
                                projects.append({
                                    'name': project_data['name'],
                                    'path': str(project_dir),
                                    'created_at': project_data.get('created_at', ''),
                                    'modified_at': project_data.get('modified_at', '')
                                })
                        except Exception as e:
                            self.error_handler.log_error(
                                e, ErrorCategory.DATABASE,
                                context=f"Reading project data from {project_dir}",
                                show_to_user=False
                            )
                            continue
            
            # Sort by most recently modified
            projects.sort(key=lambda x: x.get('modified_at', ''), reverse=True)
            return projects
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.FILESYSTEM,
                context="Listing projects",
                show_to_user=False
            )
            return []
    
    def get_project_data(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Get project data from database."""
        db_path = project_path / "pisarz.db"
        if not db_path.exists():
            return None
        
        try:
            project_repo = ProjectRepository(db_path)
            
            # Get the most recent project (should be only one per database)
            projects = project_repo.get_recent_projects(limit=1)
            if projects:
                project = projects[0]
                return {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'author': project.author,
                    'genre': project.genre,
                    'target_audience': project.target_audience,
                    'status': project.status,
                    'word_count_target': project.word_count_target,
                    'auto_backup_enabled': project.auto_backup_enabled,
                    'created_at': project.created_at,
                    'modified_at': project.modified_at
                }
            return None
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Getting project data from {project_path}",
                show_to_user=False
            )
            return None
    
    def update_project_properties(self, project_path: Path, properties: Dict[str, Any]) -> bool:
        """Update project properties."""
        db_path = project_path / "pisarz.db"
        if not db_path.exists():
            return False
        
        try:
            project_repo = ProjectRepository(db_path)
            
            # Get the project ID (should be only one per database)
            projects = project_repo.get_recent_projects(limit=1)
            if not projects:
                return False
            
            project_id = projects[0].id
            
            # Update with provided properties
            success = project_repo.update(project_id, **properties)
            
            if success:
                # Update database schema if needed
                update_database_schema(db_path)
                rebuild_fts_index(db_path)
            
            return success
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Updating project properties in {project_path}",
                show_to_user=False
            )
            return False
    
    def project_exists(self, name: str) -> bool:
        """Check if a project with the given name exists."""
        project_dir = self.projects_root / name
        return project_dir.exists() and (project_dir / "pisarz.db").exists()
    
    def get_project_path(self, name: str) -> Optional[Path]:
        """Get the path to a project by name."""
        project_dir = self.projects_root / name
        if self.project_exists(name):
            return project_dir
        return None
    
    def delete_project(self, project_path: Path) -> bool:
        """Delete a project (move to trash if possible)."""
        try:
            if project_path.exists():
                # On most systems, we should move to trash rather than permanent deletion
                # For now, we'll just rename to indicate deletion
                deleted_path = project_path.with_suffix('.deleted')
                project_path.rename(deleted_path)
                return True
            return False
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.FILESYSTEM,
                context=f"Deleting project {project_path}",
                show_to_user=False
            )
            return False