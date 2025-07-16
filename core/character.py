"""Character management for Pisarz projects."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from .db import execute_query, execute_insert, execute_update
from .error_handler import get_error_handler, ErrorLevel, ErrorCategory
from i18n import _


class CharacterManager:
    """Manager for character CRUD operations."""
    
    def __init__(self, project_path: Path):
        """Initialize character manager for a project."""
        self.project_path = project_path
        self.db_path = project_path / "pisarz.db"
        self.error_handler = get_error_handler()
        
    def get_characters(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all characters for a project."""
        query = """
            SELECT id, name, full_name, alias, age, gender, occupation, location,
                   description, personality, background, goals, conflicts, 
                   relationships, appearance, notes, importance, 
                   is_protagonist, is_antagonist, created_at
            FROM characters 
            WHERE project_id = ?
            ORDER BY importance DESC, name ASC
        """
        return execute_query(self.db_path, query, (project_id,))
        
    def create_character(self, project_id: int, name: str, **kwargs) -> int:
        """Create a new character with comprehensive attributes."""
        # Default values for all fields
        defaults = {
            'full_name': kwargs.get('full_name', ''),
            'alias': kwargs.get('alias', ''),
            'age': kwargs.get('age', None),
            'gender': kwargs.get('gender', ''),
            'occupation': kwargs.get('occupation', ''),
            'location': kwargs.get('location', ''),
            'description': kwargs.get('description', ''),
            'personality': kwargs.get('personality', ''),
            'background': kwargs.get('background', ''),
            'goals': kwargs.get('goals', ''),
            'conflicts': kwargs.get('conflicts', ''),
            'relationships': kwargs.get('relationships', ''),
            'appearance': kwargs.get('appearance', ''),
            'notes': kwargs.get('notes', ''),
            'importance': kwargs.get('importance', 1),
            'is_protagonist': kwargs.get('is_protagonist', 0),
            'is_antagonist': kwargs.get('is_antagonist', 0)
        }
        
        query = """
            INSERT INTO characters (
                project_id, name, full_name, alias, age, gender, occupation, location,
                description, personality, background, goals, conflicts, 
                relationships, appearance, notes, importance, is_protagonist, is_antagonist
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            project_id, name, defaults['full_name'], defaults['alias'], 
            defaults['age'], defaults['gender'], defaults['occupation'], defaults['location'],
            defaults['description'], defaults['personality'], defaults['background'], 
            defaults['goals'], defaults['conflicts'], defaults['relationships'], 
            defaults['appearance'], defaults['notes'], defaults['importance'],
            defaults['is_protagonist'], defaults['is_antagonist']
        )
        
        return execute_insert(self.db_path, query, params)
        
    def get_character(self, character_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific character by ID."""
        query = """
            SELECT id, project_id, name, full_name, alias, age, gender, occupation, location,
                   description, personality, background, goals, conflicts, 
                   relationships, appearance, notes, importance, 
                   is_protagonist, is_antagonist, created_at
            FROM characters 
            WHERE id = ?
        """
        results = execute_query(self.db_path, query, (character_id,))
        return results[0] if results else None
        
    def update_character(self, character_id: int, **kwargs) -> bool:
        """Update an existing character with any fields."""
        # Build dynamic update query based on provided fields
        fields = []
        values = []
        
        allowed_fields = [
            'name', 'full_name', 'alias', 'age', 'gender', 'occupation', 'location',
            'description', 'personality', 'background', 'goals', 'conflicts', 
            'relationships', 'appearance', 'notes', 'importance', 'is_protagonist', 'is_antagonist'
        ]
        
        for field in allowed_fields:
            if field in kwargs:
                fields.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if not fields:
            return False
            
        values.append(character_id)
        query = f"UPDATE characters SET {', '.join(fields)} WHERE id = ?"
        
        rows_affected = execute_update(self.db_path, query, tuple(values))
        return rows_affected > 0
        
    def delete_character(self, character_id: int) -> bool:
        """Delete a character and its scene associations."""
        # First remove all scene associations
        delete_associations_query = "DELETE FROM scene_characters WHERE character_id = ?"
        execute_update(self.db_path, delete_associations_query, (character_id,))
        
        # Then delete the character
        delete_character_query = "DELETE FROM characters WHERE id = ?"
        rows_affected = execute_update(self.db_path, delete_character_query, (character_id,))
        return rows_affected > 0
        
    def link_character_to_scene(self, character_id: int, scene_id: int) -> bool:
        """Link a character to a scene."""
        query = """
            INSERT OR IGNORE INTO scene_characters (scene_id, character_id)
            VALUES (?, ?)
        """
        try:
            execute_insert(self.db_path, query, (scene_id, character_id))
            return True
        except sqlite3.Error as e:
            # Log specific database errors
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Linking character {character_id} to scene {scene_id}",
                                        show_to_user=False)
            return False
        except Exception as e:
            # Log unexpected errors
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                        context="Linking character to scene",
                                        show_to_user=False)
            return False
            
    def unlink_character_from_scene(self, character_id: int, scene_id: int) -> bool:
        """Unlink a character from a scene."""
        query = "DELETE FROM scene_characters WHERE scene_id = ? AND character_id = ?"
        rows_affected = execute_update(self.db_path, query, (scene_id, character_id))
        return rows_affected > 0
        
    def get_characters_for_scene(self, scene_id: int) -> List[Dict[str, Any]]:
        """Get all characters linked to a specific scene."""
        query = """
            SELECT c.id, c.name, c.description, c.notes
            FROM characters c
            JOIN scene_characters sc ON c.id = sc.character_id
            WHERE sc.scene_id = ?
            ORDER BY c.name ASC
        """
        return execute_query(self.db_path, query, (scene_id,))
    
    def get_characters_for_scene_with_roles(self, scene_id: int) -> List[tuple]:
        """Get all characters linked to a specific scene with their roles."""
        query = """
            SELECT c.id, c.name, c.description, c.notes, sc.role
            FROM characters c
            JOIN scene_characters sc ON c.id = sc.character_id
            WHERE sc.scene_id = ?
            ORDER BY c.name ASC
        """
        results = execute_query(self.db_path, query, (scene_id,))
        
        # Convert to (character_dict, role) tuples
        character_role_pairs = []
        for row in results:
            character_dict = {
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'notes': row['notes']
            }
            role = row['role'] or ''
            character_role_pairs.append((character_dict, role))
        
        return character_role_pairs
        
    def get_scenes_for_character(self, character_id: int) -> List[Dict[str, Any]]:
        """Get all scenes linked to a specific character."""
        query = """
            SELECT s.id, s.title, s.ord
            FROM scenes s
            JOIN scene_characters sc ON s.id = sc.scene_id
            WHERE sc.character_id = ?
            ORDER BY s.ord ASC, s.title ASC
        """
        return execute_query(self.db_path, query, (character_id,))
        
    def add_character_relationship(self, character_a_id: int, character_b_id: int, 
                                 relationship_type: str, description: str = "") -> int:
        """Add a relationship between two characters."""
        query = """
            INSERT INTO character_relationships (character_a_id, character_b_id, relationship_type, description)
            VALUES (?, ?, ?, ?)
        """
        return execute_insert(self.db_path, query, (character_a_id, character_b_id, relationship_type, description))
        
    def get_character_relationships(self, character_id: int) -> List[Dict[str, Any]]:
        """Get all relationships for a character."""
        query = """
            SELECT r.id, r.relationship_type, r.description, r.created_at,
                   CASE 
                       WHEN r.character_a_id = ? THEN c2.name
                       ELSE c1.name
                   END as related_character_name,
                   CASE 
                       WHEN r.character_a_id = ? THEN r.character_b_id
                       ELSE r.character_a_id
                   END as related_character_id
            FROM character_relationships r
            JOIN characters c1 ON r.character_a_id = c1.id
            JOIN characters c2 ON r.character_b_id = c2.id
            WHERE r.character_a_id = ? OR r.character_b_id = ?
            ORDER BY r.created_at DESC
        """
        return execute_query(self.db_path, query, (character_id, character_id, character_id, character_id))
        
    def remove_character_relationship(self, relationship_id: int) -> bool:
        """Remove a character relationship."""
        query = "DELETE FROM character_relationships WHERE id = ?"
        rows_affected = execute_update(self.db_path, query, (relationship_id,))
        return rows_affected > 0
        
    def link_character_to_scene_with_role(self, character_id: int, scene_id: int, role: str = "") -> bool:
        """Link a character to a scene with a specific role."""
        query = """
            INSERT OR REPLACE INTO scene_characters (scene_id, character_id, role)
            VALUES (?, ?, ?)
        """
        try:
            execute_insert(self.db_path, query, (scene_id, character_id, role))
            return True
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Linking character {character_id} to scene {scene_id} with role '{role}'",
                                        show_to_user=False)
            return False
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                        context="Linking character to scene with role",
                                        show_to_user=False)
            return False
            
    def get_character_importance_levels(self) -> List[Dict[str, Any]]:
        """Get character importance level definitions."""
        return [
            {"value": 1, "label": "Minor Character", "description": "Background character, minimal impact"},
            {"value": 2, "label": "Supporting Character", "description": "Important for plot development"},
            {"value": 3, "label": "Major Character", "description": "Central to the story"},
            {"value": 4, "label": "Main Character", "description": "Protagonist or key character"},
            {"value": 5, "label": "Primary Character", "description": "Main protagonist or central figure"}
        ]