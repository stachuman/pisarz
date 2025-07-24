"""Service for handling LLM-related UI events and coordinating execution."""

import logging
from typing import Dict, Any, Optional
from core.logging_config import get_logger
from .llm_context_service import LLMContextService
from i18n import _


class LLMEventService:
    """Service for handling LLM-related UI events and coordinating execution."""
    
    def __init__(self, main_window):
        self.logger = get_logger("services.llm_events")
        self.main_window = main_window
        self.llm_context_service = LLMContextService()
    
    def handle_generate_context_request(self, scene_id: int, template_name: str) -> bool:
        """
        Handle request to generate narrative context using a template.
        
        Args:
            scene_id: ID of the scene
            template_name: Name of the template to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get project info and managers
            managers = self.main_window.project_controller.get_current_managers()
            if not managers.get('scene_manager'):
                self._show_status_message(_("No scene manager available"))
                return False
            
            project_id, project_name = self.main_window.project_controller.get_current_project_info()
            if not project_id:
                self._show_status_message(_("No project loaded"))
                return False
            
            # Prepare context using the service
            context_data = self.llm_context_service.prepare_template_execution(
                scene_id, template_name, managers, project_name
            )
            
            if not context_data:
                self._show_status_message(_("Failed to prepare context data"))
                return False
            
            # Validate context
            if not self.llm_context_service.validate_template_context(context_data):
                self._show_status_message(_("Invalid context data"))
                return False
            
            # Show AI Assistant panel if not visible
            if not self.main_window.llm_panel.isVisible():
                self.main_window.toggle_ai_assistant()
            
            # Set context and execute task
            self._setup_llm_panel_context(scene_id, context_data, template_name)
            
            # Execute the template with streaming
            template_id = context_data.get("template_id", "scene_summary")
            self.main_window.llm_panel.execute_task_streaming(template_id)
            
            self._show_status_message(_("Generating narrative context with template: {}").format(template_name))
            self.logger.info(f"Generated context for scene {scene_id} with template {template_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling generate context request: {e}")
            self._show_status_message(_("Failed to generate context"))
            return False
    
    def handle_refresh_context_request(self, scene_id: int) -> bool:
        """
        Handle request to refresh context for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get narrative context manager
            project_id, _project_name = self.main_window.project_controller.get_current_project_info()
            if not project_id:
                self._show_status_message(_("No project loaded"))
                return False
            
            from pathlib import Path
            from core.llm.context.narrative_context import NarrativeContextManager
            narrative_manager = NarrativeContextManager(project_id)
            
            # Get existing context for the scene
            existing_context = narrative_manager.get_contexts_by_scene(scene_id)
            
            if not existing_context:
                self._show_status_message(_("No context to refresh"))
                return False
            
            # Show confirmation dialog
            if not self._show_refresh_confirmation():
                return False
            
            # Trigger regeneration of the most recent context type
            latest_context = max(existing_context, key=lambda x: x.get("updated_at", ""))
            context_type = latest_context.get("context_type", "scene_summary")
            
            return self.handle_generate_context_request(scene_id, context_type)
            
        except Exception as e:
            self.logger.error(f"Error refreshing context for scene {scene_id}: {e}")
            self._show_status_message(_("Error refreshing context"))
            return False
    
    def _show_refresh_confirmation(self) -> bool:
        """Show confirmation dialog for refresh context operation."""
        try:
            from PySide6.QtWidgets import QMessageBox
            from i18n import _
            
            reply = QMessageBox.question(
                self.main_window,
                _("Refresh Context"),
                _("This will regenerate narrative context for this scene. Continue?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            return reply == QMessageBox.StandardButton.Yes
            
        except Exception as e:
            self.logger.error(f"Error showing refresh confirmation dialog: {e}")
            return False
    
    def handle_view_context_request(self, scene_id: int) -> bool:
        """
        Handle request to view context for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            True if successful, False otherwise
        """
        try:
            managers = self.main_window.project_controller.get_current_managers()
            narrative_context_manager = managers.get('narrative_context_manager')
            
            if not narrative_context_manager:
                self._show_status_message(_("No narrative context manager available"))
                return False
            
            # Get the context
            contexts = narrative_context_manager.get_contexts_for_scene(scene_id)
            
            if not contexts:
                self._show_status_message(_("No context found for this scene"))
                return False
            
            # Show narrative context panel if not visible
            if hasattr(self.main_window, 'narrative_context_panel'):
                if not self.main_window.narrative_context_panel.isVisible():
                    self.main_window.toggle_narrative_context()
                
                # Focus on the specific scene's context
                self.main_window.narrative_context_panel.focus_scene_context(scene_id)
            
            self._show_status_message(_("Viewing context for scene {}").format(scene_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Error viewing context for scene {scene_id}: {e}")
            self._show_status_message(_("Error viewing context"))
            return False
    
    def handle_edit_context_request(self, scene_id: int) -> bool:
        """
        Handle request to edit context for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            True if successful, False otherwise
        """
        try:
            managers = self.main_window.project_controller.get_current_managers()
            narrative_context_manager = managers.get('narrative_context_manager')
            
            if not narrative_context_manager:
                self._show_status_message(_("No narrative context manager available"))
                return False
            
            # Show narrative context panel in edit mode
            if hasattr(self.main_window, 'narrative_context_panel'):
                if not self.main_window.narrative_context_panel.isVisible():
                    self.main_window.toggle_narrative_context()
                
                # Enable edit mode for the specific scene
                self.main_window.narrative_context_panel.enable_edit_mode(scene_id)
            
            self._show_status_message(_("Editing context for scene {}").format(scene_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Error editing context for scene {scene_id}: {e}")
            self._show_status_message(_("Error editing context"))
            return False
    
    def _setup_llm_panel_context(self, scene_id: int, context_data: Dict[str, Any], template_name: str):
        """Setup LLM panel with context data."""
        try:
            # Set scene context
            scene_content = context_data.get("scene_content", "")
            self.main_window.llm_panel.set_scene_context(scene_id, scene_content)
            
            # Set additional context
            self.main_window.llm_panel.set_additional_context(context_data)
            
            # Set auto-save context info
            self.main_window.llm_panel.set_auto_save_context_info(scene_id, template_name)
            
        except Exception as e:
            self.logger.error(f"Error setting up LLM panel context: {e}")
    
    def _show_status_message(self, message: str):
        """Show status message in the main window."""
        if hasattr(self.main_window, 'status_bar'):
            self.main_window.status_bar.showMessage(message)