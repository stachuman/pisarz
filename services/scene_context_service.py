"""Service for building scene context data with characters and locations."""

import logging
from typing import Dict, List, Any, Optional
from core.logging_config import get_logger


class SceneContextService:
    """Service for extracting and building scene context data."""
    
    def __init__(self):
        self.logger = get_logger("services.scene_context")
    
    def build_scene_context(self, scene_id: int, managers: Dict[str, Any], 
                           project_name: str = "", template_name: str = "") -> Optional[Dict[str, Any]]:
        """
        Build complete scene context including characters, locations, and metadata.
        
        Args:
            scene_id: ID of the scene
            managers: Dictionary containing data managers
            project_name: Name of the current project
            template_name: Template type being used
            
        Returns:
            Dictionary containing complete scene context or None if scene not found
        """
        try:
            self.logger.debug(f"Available managers: {list(managers.keys())}")
            scene_manager = managers.get('scene_manager')
            if not scene_manager:
                self.logger.error("No scene manager available")
                return None
                
            scene = scene_manager.get_scene(scene_id)
            if not scene:
                self.logger.error(f"Scene {scene_id} not found")
                return None
            
            # Extract characters and locations
            scene_characters = self._extract_scene_characters(scene_id, managers)
            scene_locations = self._extract_scene_locations(scene_id, managers)
            
            # Ensure we have valid lists
            scene_characters = scene_characters or []
            scene_locations = scene_locations or []
            
            self.logger.debug(f"Found {len(scene_characters)} characters, {len(scene_locations)} locations for scene {scene_id}")
            
            # Build complete context
            context_data = {
                "scene_id": scene_id,
                "scene_title": scene.get("title", ""),
                "scene_content": scene.get("content_rtf", ""),
                "project_description": getattr(managers.get("project_controller"), 'description', ''),
                "project_name": project_name,
                "template_type": template_name,
                "characters": scene_characters,
                "locations": scene_locations,
                "character_count": len(scene_characters),
                "location_count": len(scene_locations)
            }
            
            self.logger.debug(f"Built context for scene {scene_id}: {len(scene_characters)} chars, {len(scene_locations)} locs")
            return context_data
            
        except Exception as e:
            self.logger.error(f"Error building scene context for scene {scene_id}: {e}")
            return None
    
    def _extract_scene_characters(self, scene_id: int, managers: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract characters linked to a scene with their details."""
        scene_characters = []
        character_manager = managers.get('character_manager')
        
        if not character_manager:
            return scene_characters
            
        try:
            # Get characters with roles for this scene
            character_role_pairs = character_manager.get_characters_for_scene_with_roles(scene_id)
            character_role_pairs = character_role_pairs or []
            scene_characters = [
                {
                    "id": char_dict["id"],
                    "name": char_dict["name"],
                    "full_name": char_dict.get("full_name", ""),
                    "alias": char_dict.get("alias", ""),
                    "age": char_dict.get("age"),
                    "gender": char_dict.get("gender", ""),
                    "occupation": char_dict.get("occupation", ""),
                    "location": char_dict.get("location", ""),
                    "description": char_dict.get("description", ""),
                    "notes": char_dict.get("notes", ""),
                    "role": role or "participant"
                }
                for char_dict, role in character_role_pairs
            ]
            self.logger.debug(f"Extracted {len(scene_characters)} characters for scene {scene_id}")
            
        except Exception as e:
            self.logger.warning(f"Failed to extract characters for scene {scene_id}: {e}")
            
        return scene_characters
    
    def _extract_scene_locations(self, scene_id: int, managers: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract locations linked to a scene with their details."""
        scene_locations = []
        location_manager = managers.get('location_manager')
        
        if not location_manager:
            return scene_locations
            
        try:
            # Get locations with roles for this scene
            location_role_pairs = location_manager.get_scene_locations(scene_id)
            location_role_pairs = location_role_pairs or []
            scene_locations = [
                {
                    "id": location.id,
                    "name": location.name,
                    "type": getattr(location, 'type', '') or "",
                    "description": location.description or "",
                    "atmosphere": getattr(location, 'atmosphere', '') or "",
                    "details": getattr(location, 'details', '') or "",
                    "significance": getattr(location, 'significance', '') or "",
                    "notes": location.notes or "",
                    "role": role or "setting"
                }
                for location, role in location_role_pairs
            ]
            self.logger.debug(f"Extracted {len(scene_locations)} locations for scene {scene_id}")
            
        except Exception as e:
            self.logger.warning(f"Failed to extract locations for scene {scene_id}: {e}")
            
        return scene_locations
    
    def get_characters_for_custom_prompt(self, scene_id: int, managers: Dict[str, Any], 
                                        format_for_llm: bool = False) -> List[Any]:
        """
        Get characters for custom prompt usage.
        
        Args:
            scene_id: ID of the scene
            managers: Dictionary containing data managers
            format_for_llm: If True, return formatted strings; if False, return raw data dicts
            
        Returns:
            List of character data (dicts or formatted strings)
        """
        characters = self._extract_scene_characters(scene_id, managers)
        
        if format_for_llm:
            from .context_formatter_service import ContextFormatterService
            formatter = ContextFormatterService()
            return formatter.format_characters_list(characters)
        
        return characters
    
    def get_locations_for_custom_prompt(self, scene_id: int, managers: Dict[str, Any], 
                                       format_for_llm: bool = False) -> List[Any]:
        """
        Get locations for custom prompt usage.
        
        Args:
            scene_id: ID of the scene
            managers: Dictionary containing data managers
            format_for_llm: If True, return formatted strings; if False, return raw data dicts
            
        Returns:
            List of location data (dicts or formatted strings)
        """
        locations = self._extract_scene_locations(scene_id, managers)
        
        if format_for_llm:
            from .context_formatter_service import ContextFormatterService
            formatter = ContextFormatterService()
            return formatter.format_locations_list(locations)
        
        return locations