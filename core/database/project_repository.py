"""
Project repository using the new database access layer.
Demonstrates additional patterns for complex queries and relationships.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from .base_repository import BaseRepository


@dataclass
class Project:
    """Represents a project."""
    id: Optional[int] = None
    name: str = ""
    title: str = ""  # Display title (can differ from directory name)
    description: str = ""
    author: str = ""
    genre: str = ""
    language: str = "en"
    target_word_count: int = 0
    status: str = "draft"
    tags: str = ""
    publisher: str = ""
    isbn: str = ""
    publication_date: str = ""
    copyright: str = ""
    default_scene_template: str = ""
    auto_backup_enabled: bool = True
    daily_word_goal: int = 500
    weekly_word_goal: int = 3500
    created_at: Optional[str] = None
    modified_at: Optional[str] = None


@dataclass
class Scene:
    """Represents a scene."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    title: str = ""
    content: str = ""
    summary: str = ""
    ord: int = 0
    word_count: int = 0
    character_count: int = 0
    scene_type: str = "narrative"
    status: str = "draft"
    notes: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass  
class Character:
    """Represents a character."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    name: str = ""
    description: str = ""
    personality: str = ""
    background: str = ""
    goals: str = ""
    conflicts: str = ""
    relationships: str = ""
    appearance: str = ""
    notes: str = ""
    importance: int = 1
    is_protagonist: bool = False
    is_antagonist: bool = False
    created_at: Optional[str] = None


class ProjectRepository(BaseRepository[Project]):
    """Repository for project data access."""
    
    @property
    def table_name(self) -> str:
        return "projects"
    
    @property
    def model_class(self) -> type[Project]:
        return Project
    
    @property
    def required_fields(self) -> List[str]:
        return ["name"]
    
    def search_by_name(self, name_pattern: str) -> List[Project]:
        """Search projects by name pattern."""
        return self.get_all(
            where={"name": {"LIKE": f"%{name_pattern}%"}},
            order_by="name ASC"
        )
    
    def get_by_status(self, status: str) -> List[Project]:
        """Get projects by status."""
        return self.get_all(where={"status": status}, order_by="modified_at DESC")
    
    def get_recent_projects(self, limit: int = 10) -> List[Project]:
        """Get recently modified projects."""
        return self.get_all(order_by="modified_at DESC", limit=limit)


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


class CharacterRepository(BaseRepository[Character]):
    """Repository for character data access."""
    
    @property
    def table_name(self) -> str:
        return "characters"
    
    @property
    def model_class(self) -> type[Character]:
        return Character
    
    @property
    def required_fields(self) -> List[str]:
        return ["project_id", "name"]
    
    def get_by_project(self, project_id: int) -> List[Character]:
        """Get all characters for a project."""
        return self.get_all(
            where={"project_id": project_id},
            order_by="importance DESC, name ASC"
        )
    
    def get_protagonists(self, project_id: int) -> List[Character]:
        """Get protagonist characters."""
        return self.get_all(
            where={"project_id": project_id, "is_protagonist": True},
            order_by="importance DESC, name ASC"
        )
    
    def get_antagonists(self, project_id: int) -> List[Character]:
        """Get antagonist characters."""
        return self.get_all(
            where={"project_id": project_id, "is_antagonist": True},
            order_by="importance DESC, name ASC"
        )
    
    def search_by_name(self, project_id: int, name_pattern: str) -> List[Character]:
        """Search characters by name pattern."""
        return self.get_all(
            where={
                "project_id": project_id,
                "name": {"LIKE": f"%{name_pattern}%"}
            },
            order_by="name ASC"
        )
    
    def get_by_scene(self, scene_id: int) -> List[Character]:
        """Get characters in a specific scene."""
        query = """
            SELECT c.* FROM characters c
            JOIN scene_characters sc ON c.id = sc.character_id
            WHERE sc.scene_id = ?
            ORDER BY c.importance DESC, c.name ASC
        """
        rows = self.execute_custom_query(query, [scene_id])
        return [self._row_to_model(row) for row in rows]
    
    def link_to_scene(self, character_id: int, scene_id: int, role: str = "") -> bool:
        """Link a character to a scene."""
        try:
            query = "INSERT OR REPLACE INTO scene_characters (scene_id, character_id, role) VALUES (?, ?, ?)"
            self.execute_custom_query(query, [scene_id, character_id, role])
            return True
        except Exception as e:
            self.logger.error(f"Error linking character {character_id} to scene {scene_id}: {e}")
            return False
    
    def unlink_from_scene(self, character_id: int, scene_id: int) -> bool:
        """Unlink a character from a scene."""
        try:
            query = "DELETE FROM scene_characters WHERE scene_id = ? AND character_id = ?"
            self.execute_custom_query(query, [scene_id, character_id])
            return True
        except Exception as e:
            self.logger.error(f"Error unlinking character {character_id} from scene {scene_id}: {e}")
            return False