"""
Scene repository using the new database access layer.
Replaces scene management with clean repository pattern.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from .base_repository import BaseRepository


@dataclass
class Scene:
    """Represents a scene."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    title: str = ""
    content: str = ""
    content_rtf: str = ""
    summary: str = ""
    ord: int = 0
    word_count: int = 0
    character_count: int = 0
    scene_type: str = "narrative"
    status: str = "draft"
    notes: str = ""
    created_at: Optional[str] = None
    modified_at: Optional[str] = None


class SceneRepository(BaseRepository[Scene]):
    """Repository for scene data access."""
    
    @property
    def table_name(self) -> str:
        return "scenes"
    
    @property
    def model_class(self) -> type[Scene]:
        return Scene
    
    @property
    def required_fields(self) -> List[str]:
        return ["project_id", "title"]
    
    def get_by_project(self, project_id: int) -> List[Scene]:
        """Get all scenes for a project in order."""
        return self.get_all(
            where={"project_id": project_id},
            order_by="ord ASC"
        )
    
    def search_content(self, project_id: int, search_term: str) -> List[Scene]:
        """Search scenes by content."""
        return self.get_all(
            where={
                "project_id": project_id,
                "content": {"LIKE": f"%{search_term}%"}
            },
            order_by="ord ASC"
        )
    
    def get_by_character(self, character_id: int) -> List[Scene]:
        """Get scenes containing a specific character."""
        query = """
            SELECT s.* FROM scenes s
            JOIN scene_characters sc ON s.id = sc.scene_id
            WHERE sc.character_id = ?
            ORDER BY s.ord ASC
        """
        rows = self.execute_custom_query(query, [character_id])
        return [self._row_to_model(row) for row in rows]
    
    def get_next_order_index(self, project_id: int) -> int:
        """Get the next order index for a new scene."""
        query = "SELECT COALESCE(MAX(ord), 0) + 1 FROM scenes WHERE project_id = ?"
        rows = self.execute_custom_query(query, [project_id])
        return rows[0][0] if rows else 1
    
    def reorder_scenes(self, scene_orders: List[tuple[int, int]]) -> bool:
        """Reorder scenes by updating their ord."""
        try:
            for scene_id, new_order in scene_orders:
                self.update(scene_id, ord=new_order)
            return True
        except Exception as e:
            self.logger.error(f"Error reordering scenes: {e}")
            return False
    
    def get_word_count_stats(self, project_id: int) -> Dict[str, Any]:
        """Get word count statistics for a project."""
        query = """
            SELECT 
                COUNT(*) as scene_count,
                SUM(word_count) as total_words,
                AVG(word_count) as avg_words_per_scene,
                MIN(word_count) as min_words,
                MAX(word_count) as max_words
            FROM scenes 
            WHERE project_id = ?
        """
        rows = self.execute_custom_query(query, [project_id])
        if rows:
            row = rows[0]
            return {
                "scene_count": row[0] or 0,
                "total_words": row[1] or 0,
                "avg_words_per_scene": round(row[2] or 0, 2),
                "min_words": row[3] or 0,
                "max_words": row[4] or 0
            }
        return {"scene_count": 0, "total_words": 0, "avg_words_per_scene": 0, "min_words": 0, "max_words": 0}


class SceneManager:
    """
    Scene manager using the new repository pattern.
    Provides backward compatibility while using the new database layer.
    """
    
    def __init__(self, db_path: Path = None):
        from core.llm.settings import GLOBAL_DB_PATH
        self.db_path = db_path or GLOBAL_DB_PATH
        self.scene_repo = SceneRepository(db_path)
    
    def create_scene(self, project_id: int, title: str, **kwargs) -> Optional[int]:
        """Create a new scene."""
        # Set order_index if not provided
        if 'ord' not in kwargs:
            kwargs['ord'] = self.scene_repo.get_next_order_index(project_id)
        
        return self.scene_repo.create(project_id=project_id, title=title, **kwargs)
    
    def get_scene(self, scene_id: int) -> Optional[Dict[str, Any]]:
        """Get a scene by ID."""
        scene = self.scene_repo.get_by_id(scene_id)
        return asdict(scene) if scene else None
    
    def get_scenes_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all scenes for a project."""
        scenes = self.scene_repo.get_by_project(project_id)
        return [asdict(scene) for scene in scenes]
    
    def update_scene(self, scene_id: int, **kwargs) -> bool:
        """Update a scene."""
        return self.scene_repo.update(scene_id, **kwargs)
    
    def delete_scene(self, scene_id: int) -> bool:
        """Delete a scene."""
        return self.scene_repo.delete(scene_id)
    
    def search_scenes(self, project_id: int, search_term: str) -> List[Scene]:
        """Search scenes by content."""
        return self.scene_repo.search_content(project_id, search_term)
    
    def get_scenes_by_character(self, character_id: int) -> List[Scene]:
        """Get scenes containing a character."""
        return self.scene_repo.get_by_character(character_id)
    
    def reorder_scenes(self, scene_orders: List[tuple[int, int]]) -> bool:
        """Reorder scenes."""
        return self.scene_repo.reorder_scenes(scene_orders)
    
    def get_word_count_stats(self, project_id: int) -> Dict[str, Any]:
        """Get word count statistics."""
        return self.scene_repo.get_word_count_stats(project_id)
    
    def scene_exists(self, project_id: int, title: str) -> bool:
        """Check if a scene with the given title exists."""
        return self.scene_repo.exists({"project_id": project_id, "title": title})
    
    def get_scene_count(self, project_id: int) -> int:
        """Get the number of scenes in a project."""
        return self.scene_repo.count({"project_id": project_id})
    
    def get_total_word_count(self, project_id: int) -> int:
        """Get total word count for a project."""
        stats = self.get_word_count_stats(project_id)
        return stats.get("total_words", 0)