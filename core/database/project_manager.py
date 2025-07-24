"""
Project manager using the new database access layer.
Replaces project management with clean repository pattern for single global database.
"""

from pathlib import Path
from core.llm.settings import GLOBAL_DB_PATH
from typing import List, Dict, Any, Optional

from .project_repository import ProjectRepository, Project
from ..db import init_project_db, update_database_schema, rebuild_fts_index
from ..error_handler import get_error_handler, ErrorLevel, ErrorCategory


class ProjectManager:
    """
    Project manager using the new repository pattern with single global database.
    All projects are stored in one database, identified by project_id.
    """
    
    def __init__(self):
        """Initialize project manager with global database."""
        self.error_handler = get_error_handler()
        self.db_path = GLOBAL_DB_PATH
        
        # Ensure global database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if it doesn't exist
        if not self.db_path.exists():
            init_project_db()
    
    def create_project(self, name: str, **kwargs) -> Optional[int]:
        """Create a new project in the global database and return project_id."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        
        try:
            # Check if project with this name already exists
            if self.project_exists_by_name(name):
                raise ValueError(f"Project with name '{name}' already exists")
            
            # Initialize database if needed
            init_project_db()
            
            # Create project repository and insert project record
            project_repo = ProjectRepository(self.db_path)
            project_id = project_repo.create(name=name, **kwargs)
            
            if not project_id:
                raise RuntimeError("Failed to create project record in database")
            
            return project_id
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Creating project '{name}'",
                show_to_user=True
            )
            return None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects from the global database."""
        try:
            project_repo = ProjectRepository(self.db_path)
            projects_data = []
            
            # Get all projects from database
            projects = project_repo.get_all(order_by="modified_at DESC")
            
            for project in projects:
                projects_data.append({
                    'id': project.id,
                    'name': project.name,
                    'title': project.title or project.name,
                    'author': project.author or '',
                    'description': project.description or '',
                    'genre': project.genre or '',
                    'status': project.status or 'draft',
                    'created_at': project.created_at or '',
                    'modified_at': project.modified_at or '',
                    'target_word_count': project.target_word_count or 0,
                    'daily_word_goal': project.daily_word_goal or 500,
                    'weekly_word_goal': project.weekly_word_goal or 3500,
                })
            
            return projects_data
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context="Listing projects",
                show_to_user=False
            )
            return []
    
    def get_project_data(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project data by project_id."""
        try:
            project_repo = ProjectRepository(self.db_path)
            project = project_repo.get_by_id(project_id)
            
            if project:
                return {
                    'id': project.id,
                    'name': project.name,
                    'title': project.title or project.name,
                    'description': project.description or '',
                    'author': project.author or '',
                    'genre': project.genre or '',
                    'language': project.language or 'en',
                    'target_word_count': project.target_word_count or 0,
                    'status': project.status or 'draft',
                    'tags': project.tags or '',
                    'publisher': project.publisher or '',
                    'isbn': project.isbn or '',
                    'publication_date': project.publication_date or '',
                    'copyright': project.copyright or '',
                    'default_scene_template': project.default_scene_template or '',
                    'auto_backup_enabled': project.auto_backup_enabled or True,
                    'daily_word_goal': project.daily_word_goal or 500,
                    'weekly_word_goal': project.weekly_word_goal or 3500,
                    'created_at': project.created_at or '',
                    'modified_at': project.modified_at or ''
                }
            return None
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Getting project data for ID {project_id}",
                show_to_user=False
            )
            return None
    
    def get_project_data_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get project data by name."""
        try:
            project_repo = ProjectRepository(self.db_path)
            projects = project_repo.get_all(where={"name": name})
            
            if projects:
                project = projects[0]  # Take first match
                return self.get_project_data(project.id)
            return None
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Getting project data for name '{name}'",
                show_to_user=False
            )
            return None
    
    def update_project_properties(self, project_id: int, properties: Dict[str, Any]) -> bool:
        """Update project properties by project_id."""
        try:
            project_repo = ProjectRepository(self.db_path)
            
            # Update with provided properties
            success = project_repo.update(project_id, **properties)
            
            if success:
                # Update database schema if needed
                update_database_schema()
                rebuild_fts_index()
            
            return success
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Updating project properties for ID {project_id}",
                show_to_user=False
            )
            return False
    
    def project_exists_by_name(self, name: str) -> bool:
        """Check if a project with the given name exists."""
        try:
            project_repo = ProjectRepository(self.db_path)
            return project_repo.exists({"name": name})
        except Exception:
            return False
    
    def project_exists_by_id(self, project_id: int) -> bool:
        """Check if a project with the given ID exists."""
        try:
            project_repo = ProjectRepository(self.db_path)
            return project_repo.get_by_id(project_id) is not None
        except Exception:
            return False
    
    def get_project_id_by_name(self, name: str) -> Optional[int]:
        """Get project ID by name."""
        try:
            project_repo = ProjectRepository(self.db_path)
            projects = project_repo.get_all(where={"name": name})
            return projects[0].id if projects else None
        except Exception:
            return None
    
    def get_project_name_by_id(self, project_id: int) -> Optional[str]:
        """Get project name by ID."""
        try:
            project_repo = ProjectRepository(self.db_path)
            project = project_repo.get_by_id(project_id)
            return project.name if project else None
        except Exception:
            return None
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project from the database."""
        try:
            project_repo = ProjectRepository(self.db_path)
            return project_repo.delete(project_id)
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Deleting project ID {project_id}",
                show_to_user=False
            )
            return False
    
    def get_recent_projects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently modified projects."""
        try:
            project_repo = ProjectRepository(self.db_path)
            projects = project_repo.get_recent_projects(limit)
            
            return [{
                'id': p.id,
                'name': p.name,
                'title': p.title or p.name,
                'modified_at': p.modified_at or '',
                'status': p.status or 'draft'
            } for p in projects]
            
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context="Getting recent projects",
                show_to_user=False
            )
            return []
    
    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Get statistics for a project."""
        try:
            # This would need to query scenes, characters, locations tables
            # For now, return basic structure
            return {
                'scenes_count': 0,
                'characters_count': 0,
                'locations_count': 0,
                'total_words': 0,
                'last_modified': None
            }
        except Exception as e:
            self.error_handler.log_error(
                e, ErrorCategory.DATABASE,
                context=f"Getting project stats for ID {project_id}",
                show_to_user=False
            )
            return {}