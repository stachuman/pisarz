"""Service for handling UI events and coordinating between components."""

import logging
from typing import Dict, Any, Optional
from core.logging_config import get_logger
from i18n import _


class UIEventService:
    """Service for handling various UI events and coordinating component interactions."""
    
    def __init__(self, main_window):
        self.logger = get_logger("services.ui_events")
        self.main_window = main_window
    
    def handle_character_selection(self, character_id: int, character_name: str) -> bool:
        """
        Handle character selection - opens character editor.
        
        Args:
            character_id: ID of the character
            character_name: Name of the character
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.main_window.character_controller.open_character_editor(
                character_id, character_name, self.main_window.project_controller
            )
            return True
        except Exception as e:
            self.logger.error(f"Error handling character selection: {e}")
            return False
    
    def handle_location_selection(self, location_id: int, location_name: str) -> bool:
        """
        Handle location selection - opens location editor.
        
        Args:
            location_id: ID of the location
            location_name: Name of the location
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.main_window.location_controller.open_location_editor(
                location_id, location_name, self.main_window.project_controller
            )
            return True
        except Exception as e:
            self.logger.error(f"Error handling location selection: {e}")
            return False
    
    def handle_scene_character_addition(self, character_id: int, role: str) -> bool:
        """
        Handle adding character to current scene.
        
        Args:
            character_id: ID of the character
            role: Role of the character in the scene
            
        Returns:
            True if successful, False otherwise
        """
        try:
            scene_id = self.main_window.scene_controller.get_current_scene_id()
            if not scene_id:
                self.logger.warning("No current scene for character addition")
                return False
            managers = self.main_window.project_controller.get_current_managers()
            character_manager = managers.get('character_manager')
            
            if not character_manager:
                self.logger.error("No character manager available")
                return False
            
            success = character_manager.link_character_to_scene_with_role(character_id, scene_id, role)
            if success:
                self._refresh_scene_context_panel()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding character to scene: {e}")
            return False
    
    def handle_scene_character_removal(self, character_id: int) -> bool:
        """
        Handle removing character from current scene.
        
        Args:
            character_id: ID of the character
            
        Returns:
            True if successful, False otherwise
        """
        try:
            scene_id = self.main_window.scene_controller.get_current_scene_id()
            if not scene_id:
                self.logger.warning("No current scene for character removal")
                return False
            managers = self.main_window.project_controller.get_current_managers()
            character_manager = managers.get('character_manager')
            
            if not character_manager:
                self.logger.error("No character manager available")
                return False
            
            success = character_manager.unlink_character_from_scene(character_id, scene_id)
            if success:
                self._refresh_scene_context_panel()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error removing character from scene: {e}")
            return False
    
    def handle_scene_location_addition(self, location_id: int, role: str) -> bool:
        """
        Handle adding location to current scene.
        
        Args:
            location_id: ID of the location
            role: Role of the location in the scene
            
        Returns:
            True if successful, False otherwise
        """
        try:
            scene_id = self.main_window.scene_controller.get_current_scene_id()
            if not scene_id:
                self.logger.warning("No current scene for location addition")
                return False
            managers = self.main_window.project_controller.get_current_managers()
            location_manager = managers.get('location_manager')
            
            if not location_manager:
                self.logger.error("No location manager available")
                return False
            
            success = location_manager.link_location_to_scene(location_id, scene_id, role)
            if success:
                self._refresh_scene_context_panel()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding location to scene: {e}")
            return False
    
    def handle_scene_location_removal(self, location_id: int) -> bool:
        """
        Handle removing location from current scene.
        
        Args:
            location_id: ID of the location
            
        Returns:
            True if successful, False otherwise
        """
        try:
            scene_id = self.main_window.scene_controller.get_current_scene_id()
            if not scene_id:
                self.logger.warning("No current scene for location removal")
                return False
            managers = self.main_window.project_controller.get_current_managers()
            location_manager = managers.get('location_manager')
            
            if not location_manager:
                self.logger.error("No location manager available")
                return False
            
            success = location_manager.unlink_location_from_scene(location_id, scene_id)
            if success:
                self._refresh_scene_context_panel()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error removing location from scene: {e}")
            return False
    
    def handle_search_request(self) -> bool:
        """
        Handle search request.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # SearchView is a widget, not a dialog, so we show the search view in the workspace
            self.main_window.workspace.show_search_view()
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling search request: {e}")
            return False
    
    def handle_search_result_selection(self, result_type: str, result_id: int, 
                                     title: str, search_query: str) -> bool:
        """
        Handle selection of search result.
        
        Args:
            result_type: Type of result (scene, character, location)
            result_id: ID of the result
            title: Title of the result
            search_query: Original search query
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if result_type == "scene":
                # Use project management service for scene selection with search
                if hasattr(self.main_window, 'project_management_service'):
                    self.main_window.project_management_service.handle_scene_selection_with_search(result_id, title, search_query)
                else:
                    self.main_window.on_scene_selected_with_search(result_id, title, search_query)
            elif result_type == "character":
                self.handle_character_selection(result_id, title)
            elif result_type == "location":
                self.handle_location_selection(result_id, title)
            else:
                self.logger.warning(f"Unknown search result type: {result_type}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling search result selection: {e}")
            return False
    
    def _refresh_scene_context_panel(self):
        """Refresh the scene context panel if it exists."""
        try:
            if hasattr(self.main_window, 'scene_context_panel') and self.main_window.scene_context_panel:
                self.main_window.scene_context_panel.refresh()
        except Exception as e:
            self.logger.debug(f"Could not refresh scene context panel: {e}")
    
    def _show_status_message(self, message: str):
        """Show status message in the main window."""
        if hasattr(self.main_window, 'status_bar'):
            self.main_window.status_bar.showMessage(message)