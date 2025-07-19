"""Scene CRUD operations for Pisarz projects."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .db import execute_query, execute_insert, execute_update
from i18n import _


class SceneManager:
    """Manages scene operations within a project."""
    
    def __init__(self, project_path: Path):
        """Initialize scene manager for a specific project."""
        self.project_path = project_path
        self.db_path = project_path / "pisarz.db"
        
        if not self.db_path.exists():
            raise ValueError(_("Project database not found"))
    
    def create_scene(self, title: str, content_rtf: str = "") -> int:
        """Create a new scene and return its ID."""
        if not title or not title.strip():
            raise ValueError(_("Scene title cannot be empty"))
        
        # Get project ID
        project_data = execute_query(
            self.db_path,
            "SELECT id FROM projects LIMIT 1"
        )
        if not project_data:
            raise ValueError(_("Project not found in database"))
        
        project_id = project_data[0]["id"]
        
        # Get next order number
        max_ord_data = execute_query(
            self.db_path,
            "SELECT COALESCE(MAX(ord), 0) as max_ord FROM scenes WHERE project_id = ?",
            (project_id,)
        )
        next_ord = max_ord_data[0]["max_ord"] + 1 if max_ord_data else 1
        
        # Insert new scene with timestamps
        scene_id = execute_insert(
            self.db_path,
            "INSERT INTO scenes (project_id, title, content_rtf, ord, created_at, modified_at) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
            (project_id, title.strip(), content_rtf, next_ord)
        )
        
        return scene_id
    
    def list_scenes(self) -> List[Dict[str, Any]]:
        """List all scenes in the project ordered by ord."""
        return execute_query(
            self.db_path,
            """SELECT id, title, content_rtf, ord, created_at, modified_at 
               FROM scenes s 
               WHERE project_id = (SELECT id FROM projects LIMIT 1)
               ORDER BY ord ASC"""
        )
    
    def get_scene(self, scene_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific scene by ID."""
        scenes = execute_query(
            self.db_path,
            "SELECT id, title, content_rtf, ord, created_at, modified_at FROM scenes WHERE id = ?",
            (scene_id,)
        )
        return scenes[0] if scenes else None
    
    def update_scene(self, scene_id: int, title: str = None, content_rtf: str = None) -> bool:
        """Update scene title and/or content."""
        scene = self.get_scene(scene_id)
        if not scene:
            return False
        
        updates = []
        params = []
        
        if title is not None:
            if not title.strip():
                raise ValueError(_("Scene title cannot be empty"))
            updates.append("title = ?")
            params.append(title.strip())
        
        if content_rtf is not None:
            updates.append("content_rtf = ?")
            params.append(content_rtf)
        
        # Always update modified_at when making changes
        if updates:
            updates.append("modified_at = datetime('now')")
            params.append(scene_id)
            
            execute_update(
                self.db_path,
                f"UPDATE scenes SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
        
        return True
    
    def delete_scene(self, scene_id: int) -> bool:
        """Delete a scene by ID."""
        rows_affected = execute_update(
            self.db_path,
            "DELETE FROM scenes WHERE id = ?",
            (scene_id,)
        )
        return rows_affected > 0
    
    def reorder_scene(self, scene_id: int, new_ord: int) -> bool:
        """Change the order of a scene."""
        if new_ord < 1:
            return False
        
        # Update the scene's order
        rows_affected = execute_update(
            self.db_path,
            "UPDATE scenes SET ord = ? WHERE id = ?",
            (new_ord, scene_id)
        )
        
        return rows_affected > 0