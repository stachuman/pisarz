"""Service for project management operations."""

import logging
from typing import Dict, Any, Optional
from core.logging_config import get_logger
from i18n import _


class ProjectManagementService:
    """Service for handling project management operations."""
    
    def __init__(self, main_window):
        self.logger = get_logger("services.project_management")
        self.main_window = main_window
    
    def handle_project_selection(self, project_id: int, project_name: str) -> bool:
        """
        Handle project selection and setup.
        
        Args:
            project_id: ID of the project
            project_name: Name of the project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Loading project: {project_name} (ID: {project_id})")
            
            # Load project using project controller
            success = self.main_window.project_controller.load_project(project_id)
            if not success:
                self._show_error(_("Error"), _("Failed to load project: {}").format(project_name))
                return False
            
            # Update UI components
            self._setup_project_ui(project_name)
            
            # Update LLM controller with project context
            self.main_window.llm_controller.update_project_context(project_name, project_id)
            
            # Set up narrative context panel
            self._setup_narrative_context_panel(project_id)
            
            self.logger.info(f"Project {project_name} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading project {project_name}: {e}")
            self._show_error(_("Error"), _("Failed to load project: {}").format(str(e)))
            return False
    
    def handle_category_selection(self, category: str) -> bool:
        """
        Handle category selection in project view.
        
        Args:
            category: Selected category
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.debug(f"Category selected: {category}")
            
            # Update main window state
            self.main_window.current_category = category
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling category selection: {e}")
            return False
    
    def handle_scene_selection(self, scene_id: int, scene_title: str) -> bool:
        """
        Handle scene selection and loading.
        
        Args:
            scene_id: ID of the scene
            scene_title: Title of the scene
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.debug(f"Scene selected: {scene_id} - {scene_title}")
        
        # Load scene using scene controller
        success = self.main_window.scene_controller.open_scene(scene_id, scene_title)
        if not success:
            self.logger.error(f"Failed to load scene {scene_id}")
            return False
        
        # Update AI Assistant window with scene context
        if hasattr(self.main_window, 'ai_assistant_window'):
            scene_content = self._get_scene_content(scene_id)
            self.main_window.ai_assistant_window.panel.set_scene_context(scene_id, scene_content)
        
        return True
    
    def handle_scene_selection_with_search(self, scene_id: int, scene_title: str, search_query: str) -> bool:
        """
        Handle scene selection from search results.
        
        Args:
            scene_id: ID of the scene
            scene_title: Title of the scene
            search_query: Search query that led to this selection
            
        Returns:
            True if successful, False otherwise
        """
        # First select the scene normally
        success = self.handle_scene_selection(scene_id, scene_title)
        if not success:
            return False
        
        # Apply search highlighting to current editor
        if (hasattr(self.main_window, 'workspace') and 
            hasattr(self.main_window.workspace, 'current_editor') and 
            self.main_window.workspace.current_editor and
            hasattr(self.main_window.workspace.current_editor, 'find_and_highlight_text')):
            self.main_window.workspace.current_editor.find_and_highlight_text(search_query)
        
        self.logger.debug(f"Scene {scene_id} selected with search query: {search_query}")
        return True
    
    def create_new_project(self, name: str) -> bool:
        """
        Create a new project.
        
        Args:
            name: Name of the new project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.main_window.project_controller.create_project(name)
            if success:
                self.logger.info(f"Created new project: {name}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating project {name}: {e}")
            return False
    
    def create_new_scene(self, title: str) -> bool:
        """
        Create a new scene.
        
        Args:
            title: Title of the new scene
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.main_window.scene_controller.create_scene(title)
            if success:
                self.logger.info(f"Created new scene: {title}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating scene {title}: {e}")
            return False
    
    def handle_scene_rename(self, scene_id: int, new_title: str) -> bool:
        """
        Handle scene rename request.
        
        Args:
            scene_id: ID of the scene
            new_title: New title for the scene
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.main_window.scene_controller.rename_scene(scene_id, new_title)
            if success:
                self.logger.info(f"Renamed scene {scene_id} to: {new_title}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error renaming scene {scene_id}: {e}")
            return False
    
    def save_scene_content(self, content: str, is_auto_save: bool = False) -> bool:
        """
        Save scene content.
        
        Args:
            content: Content to save
            is_auto_save: Whether this is an auto-save operation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.main_window.scene_controller.save_scene_content(content, is_auto_save)
            if success and not is_auto_save:
                self.logger.debug("Scene content saved")
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving scene content: {e}")
            return False
    
    def _setup_project_ui(self, project_name: str):
        """Setup UI components for the loaded project."""
        try:
            # Update window title
            if hasattr(self.main_window, 'setWindowTitle'):
                self.main_window.setWindowTitle(f"Pisarz - {project_name}")
            
            # Show workspace and hide projects view
            if hasattr(self.main_window, 'main_stack'):
                self.main_window.main_stack.setCurrentWidget(self.main_window.project_widget)
            
            # Update current view state
            self.main_window.current_view_state = "workspace"
            
        except Exception as e:
            self.logger.error(f"Error setting up project UI: {e}")
    
    def _setup_narrative_context_panel(self, project_id: int):
        """Setup narrative context panel for the project."""
        try:
            if hasattr(self.main_window, 'narrative_context_window'):
                self.main_window.narrative_context_window.set_project(project_id)
        except Exception as e:
            self.logger.debug(f"Could not setup narrative context panel: {e}")
    
    def _get_scene_content(self, scene_id: int) -> str:
        """Get content of a scene."""
        managers = self.main_window.project_controller.get_current_managers()
        scene_manager = managers.get('scene_manager')
        if scene_manager:
            scene = scene_manager.get_scene(scene_id)
            return scene.get('content_rtf', '') if scene else ''
        return ''
    
    def _show_error(self, title: str, message: str):
        """Show error dialog."""
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self.main_window, title, message)
        except Exception as e:
            self.logger.error(f"Error showing error dialog: {e}")