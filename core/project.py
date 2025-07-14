"""Project management for Pisarz - create/open project folders and databases."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .db import init_project_db, execute_query, execute_insert


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
                        project_data = execute_query(
                            db_path,
                            "SELECT name, created_at FROM projects ORDER BY created_at DESC LIMIT 1"
                        )
                        if project_data:
                            projects.append({
                                "name": project_data[0]["name"],
                                "path": str(item),
                                "created_at": project_data[0]["created_at"]
                            })
                    except Exception:
                        # Skip corrupted projects
                        continue
        
        return sorted(projects, key=lambda x: x["created_at"], reverse=True)
    
    def open_project(self, project_path: str) -> bool:
        """Validate and open an existing project."""
        project_dir = Path(project_path)
        db_path = project_dir / "pisarz.db"
        
        return project_dir.exists() and db_path.exists()
        
    def get_project_data(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Get project data including ID from database."""
        db_path = project_path / "pisarz.db"
        if not db_path.exists():
            return None
            
        try:
            project_data = execute_query(
                db_path,
                "SELECT id, name, created_at FROM projects ORDER BY created_at DESC LIMIT 1"
            )
            return project_data[0] if project_data else None
        except Exception:
            return None


