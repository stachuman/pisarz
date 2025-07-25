"""Service for managing LLM context building and template execution."""

import logging
from typing import Dict, List, Any, Optional
from core.logging_config import get_logger
from .scene_context_service import SceneContextService


class LLMContextService:
    """Service for building LLM context and coordinating template execution."""
    
    def __init__(self):
        self.logger = get_logger("services.llm_context")
        self.scene_context_service = SceneContextService()
    
    def prepare_template_execution(self, scene_id: int, template_name: str, 
                                 managers: Dict[str, Any], project_name: str = "") -> Optional[Dict[str, Any]]:
        """
        Prepare all context data needed for LLM template execution.
        
        Args:
            scene_id: ID of the scene
            template_name: Name of the template to execute
            managers: Dictionary containing data managers
            project_name: Name of the current project
            
        Returns:
            Complete context data for LLM execution or None if preparation failed
        """
        try:
            # Build scene context with characters and locations
            context_data = self.scene_context_service.build_scene_context(
                scene_id, managers, project_name, template_name
            )
            
            if not context_data:
                self.logger.error(f"Failed to build scene context for scene {scene_id}")
                return None
            
            # Add template-specific metadata
            context_data.update({
                "template_id": self._map_template_name_to_id(template_name),
                "execution_timestamp": self._get_current_timestamp(),
                "context_type": "template_execution"
            })
            
            self.logger.info(f"Prepared LLM context for scene {scene_id} with template {template_name}")
            return context_data
            
        except Exception as e:
            self.logger.error(f"Error preparing template execution for scene {scene_id}: {e}")
            return None
    
    def prepare_custom_prompt_context(self, scene_id: int, managers: Dict[str, Any], 
                                    include_characters: bool = True, 
                                    include_locations: bool = True) -> Dict[str, Any]:
        """
        Prepare context data specifically for custom prompt execution.
        
        Args:
            scene_id: ID of the scene
            managers: Dictionary containing data managers
            include_characters: Whether to include character data
            include_locations: Whether to include location data
            
        Returns:
            Context data formatted for custom prompt usage
        """
        try:
            context_data = {
                "characters": [],
                "locations": [],
                "scene_id": scene_id,
                "context_type": "custom_prompt"
            }
            
            if include_characters:
                context_data["characters"] = self.scene_context_service.get_characters_for_custom_prompt(
                    scene_id, managers
                )
            
            if include_locations:
                context_data["locations"] = self.scene_context_service.get_locations_for_custom_prompt(
                    scene_id, managers
                )
            
            # Add project information
            scene_manager = managers.get('scene_manager')
            if scene_manager:
                scene = scene_manager.get_scene(scene_id)
                if scene:
                    context_data.update({
                        "scene_title": scene.get("title", ""),
                        "project_name": getattr(managers.get('project_controller'), 'current_project_name', ''),
                        "project_description": getattr(managers.get("project_controller"), 'project_description', ''),
                        "character_count": len(context_data["characters"]),
                        "location_count": len(context_data["locations"])
                    })
            
            self.logger.debug(f"Prepared custom prompt context for scene {scene_id}")
            return context_data
            
        except Exception as e:
            self.logger.error(f"Error preparing custom prompt context for scene {scene_id}: {e}")
            return {"characters": [], "locations": [], "scene_id": scene_id}
    
    def _map_template_name_to_id(self, template_name: str) -> str:
        """Map template name to standardized template ID."""
        available_templates = {
            "scene_summary": "scene_summary",
            "continue_with_context": "continue_with_context", 
            "dialogue_enhancement": "dialogue_enhancement",
            "expand_scene": "expand_scene",
            "rewrite_scene": "rewrite_scene",
            "continue_scene_enhanced": "continue_scene_enhanced",
            "continue_scene": "continue_scene"
        }
        
        return available_templates.get(template_name, "scene_summary")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for context metadata."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def validate_template_context(self, context_data: Dict[str, Any]) -> bool:
        """
        Validate that context data has all required fields for template execution.
        
        Args:
            context_data: Context data to validate
            
        Returns:
            True if context is valid, False otherwise
        """
        required_fields = ["scene_id", "scene_content", "template_type"]
        
        for field in required_fields:
            if field not in context_data:
                self.logger.warning(f"Missing required field in context: {field}")
                return False
                
        if not context_data.get("scene_content"):
            self.logger.warning("Scene content is empty")
            return False
            
        return True