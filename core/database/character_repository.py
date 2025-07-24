"""
Character repository using the new database access layer.
Replaces character management with clean repository pattern.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict, fields

from .base_repository import BaseRepository


@dataclass
class Character:
    """Represents a character."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    name: str = ""
    full_name: str = ""
    alias: str = ""
    age: Optional[int] = None
    gender: str = ""
    occupation: str = ""
    location: str = ""
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
            where={"project_id": project_id, "is_protagonist": 1},
            order_by="importance DESC, name ASC"
        )
    
    def get_antagonists(self, project_id: int) -> List[Character]:
        """Get antagonist characters."""
        return self.get_all(
            where={"project_id": project_id, "is_antagonist": 1},
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
    
    def get_by_scene_with_roles(self, scene_id: int) -> List[tuple]:
        """Get characters in a scene with their roles. Returns list of (Character, role) tuples."""
        query = """
            SELECT c.*, sc.role FROM characters c
            JOIN scene_characters sc ON c.id = sc.character_id
            WHERE sc.scene_id = ?
            ORDER BY c.importance DESC, c.name ASC
        """
        rows = self.execute_custom_query(query, [scene_id])
        
        result = []
        for row in rows:
            try:
                # Convert row to dictionary first
                row_dict = dict(row) if hasattr(row, 'keys') else {}
                if not row_dict:
                    continue
                    
                # Extract role and remove it from character data
                role = row_dict.pop('role', '')
                
                # Create character from remaining data
                character = self.model_class(**{k: v for k, v in row_dict.items() 
                                              if k in {f.name for f in fields(self.model_class)}})
                result.append((character, role))
            except Exception as e:
                self.logger.error(f"Error processing character with role from scene {scene_id}: {e}")
                continue
        
        return result
    
    def link_to_scene(self, character_id: int, scene_id: int, role: str = "") -> bool:
        """Link a character to a scene."""
        try:
            # Use direct database connection with commit for INSERT operation
            from core.db import get_db_connection
            with get_db_connection(self.db_path) as conn:
                query = "INSERT OR REPLACE INTO scene_characters (scene_id, character_id, role) VALUES (?, ?, ?)"
                cursor = conn.execute(query, [scene_id, character_id, role])
                conn.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error linking character {character_id} to scene {scene_id}: {e}")
            return False
    
    def unlink_from_scene(self, character_id: int, scene_id: int) -> bool:
        """Unlink a character from a scene."""
        try:
            # Use direct database connection with commit for DELETE operation
            from core.db import get_db_connection
            with get_db_connection(self.db_path) as conn:
                query = "DELETE FROM scene_characters WHERE scene_id = ? AND character_id = ?"
                cursor = conn.execute(query, [scene_id, character_id])
                conn.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error unlinking character {character_id} from scene {scene_id}: {e}")
            return False


class CharacterManager:
    """
    Character manager using the new repository pattern.
    Provides backward compatibility while using the new database layer.
    """
    
    def __init__(self, db_path: Path = None):
        from core.llm.settings import GLOBAL_DB_PATH
        self.db_path = db_path or GLOBAL_DB_PATH
        self.character_repo = CharacterRepository(db_path)
    
    def create_character(self, project_id: int, name: str, **kwargs) -> Optional[int]:
        """Create a new character."""
        return self.character_repo.create(project_id=project_id, name=name, **kwargs)
    
    def get_character(self, character_id: int) -> Optional[Dict[str, Any]]:
        """Get a character by ID."""
        character = self.character_repo.get_by_id(character_id)
        return asdict(character) if character else None
    
    def get_characters(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all characters for a project."""
        characters = self.character_repo.get_by_project(project_id)
        return [asdict(char) for char in characters]
    
    def get_characters_by_project(self, project_id: int) -> List[Character]:
        """Get all characters for a project (returns dataclass objects)."""
        return self.character_repo.get_by_project(project_id)
    
    def update_character(self, character_id: int, **kwargs) -> bool:
        """Update a character."""
        return self.character_repo.update(character_id, **kwargs)
    
    def delete_character(self, character_id: int) -> bool:
        """Delete a character."""
        return self.character_repo.delete(character_id)
    
    def search_characters(self, project_id: int, name_pattern: str) -> List[Character]:
        """Search characters by name."""
        return self.character_repo.search_by_name(project_id, name_pattern)
    
    def get_protagonists(self, project_id: int) -> List[Character]:
        """Get protagonist characters."""
        return self.character_repo.get_protagonists(project_id)
    
    def get_antagonists(self, project_id: int) -> List[Character]:
        """Get antagonist characters."""
        return self.character_repo.get_antagonists(project_id)
    
    def get_characters_by_scene(self, scene_id: int) -> List[Character]:
        """Get characters in a scene."""
        return self.character_repo.get_by_scene(scene_id)
    
    def get_characters_for_scene_with_roles(self, scene_id: int) -> List[Dict[str, Any]]:
        """Get characters in a scene with their roles. Returns list of character dicts with role field."""
        character_role_pairs = self.character_repo.get_by_scene_with_roles(scene_id)
        result = []
        for character, role in character_role_pairs:
            char_dict = asdict(character)
            char_dict["role"] = role
            result.append(char_dict)
        return result
    
    def link_character_to_scene(self, character_id: int, scene_id: int, role: str = "") -> bool:
        """Link a character to a scene."""
        return self.character_repo.link_to_scene(character_id, scene_id, role)
    
    def link_character_to_scene_with_role(self, character_id: int, scene_id: int, role: str = "") -> bool:
        """Link a character to a scene with a specific role (alias for link_character_to_scene)."""
        return self.character_repo.link_to_scene(character_id, scene_id, role)
    
    def unlink_character_from_scene(self, character_id: int, scene_id: int) -> bool:
        """Unlink a character from a scene."""
        return self.character_repo.unlink_from_scene(character_id, scene_id)
    
    def character_exists(self, project_id: int, name: str) -> bool:
        """Check if a character with the given name exists."""
        return self.character_repo.exists({"project_id": project_id, "name": name})
    
    def get_character_count(self, project_id: int) -> int:
        """Get the number of characters in a project."""
        return self.character_repo.count({"project_id": project_id})
    
    def get_scenes_for_character(self, character_id: int) -> List[Dict[str, Any]]:
        """Get all scenes that feature a specific character."""
        try:
            query = """
                SELECT s.* FROM scenes s
                JOIN scene_characters sc ON s.id = sc.scene_id
                WHERE sc.character_id = ?
                ORDER BY s.ord ASC, s.title ASC
            """
            rows = self.character_repo.execute_custom_query(query, [character_id])
            
            # Convert rows to scene dictionaries
            scenes = []
            for row in rows:
                scene_dict = dict(row) if hasattr(row, 'keys') else {}
                scenes.append(scene_dict)
            return scenes
        except Exception as e:
            self.character_repo.logger.error(f"Error getting scenes for character {character_id}: {e}")
            return []