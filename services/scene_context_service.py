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
            
            # Extract characters, locations, and scene contexts
            scene_characters = self._extract_scene_characters(scene_id, managers)
            scene_locations = self._extract_scene_locations(scene_id, managers)
            scene_contexts = self._extract_scene_contexts(scene_id, managers)
            
            # Ensure we have valid lists
            scene_characters = scene_characters or []
            scene_locations = scene_locations or []
            scene_contexts = scene_contexts or []
            
            self.logger.debug(f"Found {len(scene_characters)} characters, {len(scene_locations)} locations, {len(scene_contexts)} scene contexts for scene {scene_id}")
            
            # Build complete context with fresh project data
            project_controller = managers.get("project_controller")
            project_description = ''
            project_name_from_db = project_name
            
            # Get fresh project data from database instead of controller attributes
            if project_controller and hasattr(project_controller, 'get_project_data'):
                current_project_id = project_controller.get_project_id()
                if current_project_id:
                    project_data = project_controller.get_project_data(current_project_id) or {}
                    project_description = project_data.get('description', '')
                    project_name_from_db = project_data.get('name', project_name)
                    self.logger.debug(f"Fresh project data - name: '{project_name_from_db}', description: '{project_description}'")
                else:
                    self.logger.debug("No current project ID available")
            else:
                self.logger.debug(f"Project controller missing get_project_data method: {project_controller is not None}")
            
            context_data = {
                "scene_id": scene_id,
                "scene_title": scene.get("title", ""),
                "scene_content": scene.get("content_rtf", ""),
                "project_description": project_description,
                "project_name": project_name_from_db,  # Use fresh project name from database
                "template_type": template_name,
                "characters": scene_characters,
                "locations": scene_locations,
                "scene_contexts": scene_contexts,
                "character_count": len(scene_characters),
                "location_count": len(scene_locations),
                "scene_contexts_count": len(scene_contexts)
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
            character_dicts = character_manager.get_characters_for_scene_with_roles(scene_id)
            character_dicts = character_dicts or []
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
                    "role": char_dict.get("role", "participant")
                }
                for char_dict in character_dicts
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
    
    def _extract_scene_contexts(self, scene_id: int, managers: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all scene contexts for the project, ordered by scene order."""
        scene_contexts = []
        scene_manager = managers.get('scene_manager')
        narrative_manager = managers.get('narrative_context_manager')
        
        if not scene_manager or not narrative_manager:
            return scene_contexts
            
        try:
            # Get current scene to find its project
            current_scene = scene_manager.get_scene(scene_id)
            if not current_scene:
                return scene_contexts
            
            project_id = current_scene.get('project_id')
            if not project_id:
                return scene_contexts
            
            # Get all scenes for the project, ordered by ord
            all_scenes = scene_manager.get_scenes_by_project(project_id)
            if not all_scenes:
                return scene_contexts
                
            all_scenes.sort(key=lambda x: x.get('ord', 0))
            
            # Extract contexts for each scene
            for scene in all_scenes:
                scene_context_data = {
                    "scene_id": scene.get('id'),
                    "scene_title": scene.get('title', ''),
                    "scene_ord": scene.get('ord', 0),
                    "content": "",
                    "has_content": False
                }
                
                # Get narrative context for this scene
                contexts = narrative_manager.get_contexts_by_scene(scene.get('id'))
                if contexts:
                    # Use the most recent context
                    contexts.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
                    scene_context_data["content"] = contexts[0].get('content', '')
                    scene_context_data["has_content"] = bool(scene_context_data["content"].strip())
                
                scene_contexts.append(scene_context_data)
            
            self.logger.debug(f"Extracted {len(scene_contexts)} scene contexts for project")
            
        except Exception as e:
            self.logger.warning(f"Failed to extract scene contexts: {e}")
            
        return scene_contexts
    
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