"""Service for handling application settings and configuration."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from core.logging_config import get_logger
from i18n import _


class SettingsService:
    """Service for managing application settings and configuration."""
    
    def __init__(self, main_window):
        self.logger = get_logger("services.settings")
        self.main_window = main_window
    
    def show_settings_dialog(self) -> bool:
        """
        Show the settings dialog.
        
        Returns:
            True if settings were changed, False otherwise
        """
        try:
            from ui.widgets.settings_dialog import SettingsDialog
            
            dialog = SettingsDialog(self.main_window)
            dialog.themeChanged.connect(self.handle_theme_change)
            dialog.llmSettingsChanged.connect(self.handle_llm_settings_change)
            dialog.languageChanged.connect(self.handle_language_change)
            
            result = dialog.exec()
            return result == dialog.DialogCode.Accepted
            
        except Exception as e:
            self.logger.error(f"Error showing settings dialog: {e}")
            return False
    
    def handle_theme_change(self, theme_name: str) -> bool:
        """
        Handle theme change.
        
        Args:
            theme_name: Name of the new theme
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Changing theme to: {theme_name}")
            
            # Apply theme using theme manager
            from ui.base.enhanced_theme_manager import EnhancedThemeManager
            theme_manager = EnhancedThemeManager()
            theme_manager.set_theme(theme_name)
            
            # Notify focus controller about theme change
            if hasattr(self.main_window, 'focus_controller'):
                self.main_window.focus_controller.on_theme_changed(theme_name)
            
            self.logger.info(f"Theme changed to {theme_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error changing theme: {e}")
            return False
    
    def handle_llm_settings_change(self) -> bool:
        """
        Handle LLM settings change.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("LLM settings changed, reinitializing...")
            
            # Notify LLM controller of settings change
            if hasattr(self.main_window, 'llm_controller'):
                self.main_window.llm_controller.on_settings_changed()
                self.logger.info("LLM controller settings updated")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error handling LLM settings change: {e}")
            return False
    
    def handle_language_change(self, language_code: str) -> bool:
        """
        Handle language change.
        
        Args:
            language_code: Code of the new language (e.g., 'en_US', 'pl_PL')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Changing language to: {language_code}")
            
            # Set language using i18n manager
            from ui.base.i18n_manager import I18nManager
            i18n_manager = I18nManager()
            success = i18n_manager.set_language(language_code)
            
            if success:
                # Show restart message
                self._show_restart_message()
                self.logger.info(f"Language changed to {language_code}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error changing language: {e}")
            return False
    
    def show_project_properties(self) -> bool:
        """
        Show project properties dialog.
        
        Returns:
            True if properties were changed, False otherwise
        """
        try:
            # Get current project info
            project_id, project_name = self.main_window.project_controller.get_current_project_info()
            if not project_id:
                self._show_error(_("Error"), _("No project loaded"))
                return False
            
            # Get project data
            managers = self.main_window.project_controller.get_current_managers()
            project_manager = managers.get('project_manager')
            if not project_manager:
                self._show_error(_("Error"), _("Project manager not available"))
                return False
            
            project_data = project_manager.get_project_data(project_id)
            if not project_data:
                self._show_error(_("Error"), _("Could not load project data"))
                return False
            
            # Show dialog
            from ui.widgets.project_properties_dialog import ProjectPropertiesDialog
            dialog = ProjectPropertiesDialog(project_data, self.main_window)
            dialog.properties_saved.connect(self.handle_project_properties_save)
            
            result = dialog.exec()
            return result == dialog.DialogCode.Accepted
            
        except Exception as e:
            self.logger.error(f"Error showing project properties: {e}")
            return False
    
    def handle_project_properties_save(self, properties: Dict[str, Any]) -> bool:
        """
        Handle saving of project properties.
        
        Args:
            properties: Dictionary containing project properties
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Saving project properties")
            
            # Get project manager and current project path
            managers = self.main_window.project_controller.get_current_managers()
            project_manager = managers.get('project_manager')
            if not project_manager:
                self.logger.error("Project manager not available")
                return False
            
            # Get current project ID
            project_id, _ = self.main_window.project_controller.get_current_project_info()
            if not project_id:
                self.logger.error("No current project ID available")
                return False
            
            # Update project properties
            success = project_manager.update_project_properties(project_id, properties)
            if success:
                self.logger.info("Project properties saved successfully")
                
                # Update window title if name changed
                if 'name' in properties:
                    self.main_window.setWindowTitle(f"Pisarz - {properties['name']}")
                
                # Refresh UI components that might show project info
                self._refresh_project_dependent_ui()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving project properties: {e}")
            return False
    
    def handle_text_selection_change(self, selected_text: str, current_text: str) -> bool:
        """
        Handle text selection change in workspace.
        
        Args:
            selected_text: Currently selected text
            current_text: Current text content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update LLM controller with text selection
            if hasattr(self.main_window, 'llm_controller'):
                self.main_window.llm_controller.update_text_selection(selected_text, current_text)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling text selection change: {e}")
            return False
    
    def toggle_focus_mode(self) -> bool:
        """
        Toggle focus mode.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if hasattr(self.main_window, 'focus_controller'):
                success = self.main_window.focus_controller.toggle_focus_mode()
                self.logger.info(f"Focus mode toggled: {success}")
                return success
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error toggling focus mode: {e}")
            return False
    
    def exit_focus_mode_if_active(self) -> bool:
        """
        Exit focus mode if currently active.
        
        Returns:
            True if successful or not in focus mode, False otherwise
        """
        try:
            if hasattr(self.main_window, 'focus_controller'):
                return self.main_window.focus_controller.exit_focus_mode_if_active()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exiting focus mode: {e}")
            return False
    
    def _show_restart_message(self):
        """Show message about application restart."""
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self.main_window,
                _("Language Changed"),
                _("Please restart the application for the language change to take full effect.")
            )
        except Exception as e:
            self.logger.error(f"Error showing restart message: {e}")
    
    def _show_error(self, title: str, message: str):
        """Show error dialog."""
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self.main_window, title, message)
        except Exception as e:
            self.logger.error(f"Error showing error dialog: {e}")
    
    def _refresh_project_dependent_ui(self):
        """Refresh UI components that depend on project information."""
        try:
            # Refresh project tree view if it exists
            if hasattr(self.main_window, 'project_tree_view'):
                self.main_window.project_tree_view.refresh()
            
            # Refresh other project-dependent components as needed
            
        except Exception as e:
            self.logger.debug(f"Could not refresh project-dependent UI: {e}")