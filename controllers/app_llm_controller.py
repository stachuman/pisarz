"""
Main LLM controller for Pisarz application.
Coordinates LLM operations and integrates with the main application.
"""

import logging
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from core.logging_config import get_logger
from core.llm.service import LLMService
from core.llm.settings import get_llm_settings


class AppLLMController(QObject):
    """Main controller for LLM operations."""
    
    # Signals
    llm_response_ready = Signal(str, str)  # task_id, response
    llm_error = Signal(str, str)  # task_id, error_message
    llm_status_changed = Signal(str)  # status message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("llm.controller")
        self.settings_manager = get_llm_settings()
        self.llm_service = LLMService()
        self._initialized = False
        
    def initialize(self):
        """Initialize the LLM controller."""
        try:
            self.logger.info("Initializing LLM controller")
            
            # Get provider from settings manager
            provider_name = self.settings_manager.get_current_provider()
            
            # Initialize LLM service
            self.llm_service.initialize(provider_name)
            
            # Connect context manager signals
            context_manager = self.llm_service.get_context_manager()
            context_manager.context_updated.connect(self._on_context_updated)
            context_manager.context_ready.connect(self._on_context_ready)
            
            self._initialized = True
            self.llm_status_changed.emit("LLM system initialized")
            self.logger.info("LLM controller initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM controller: {e}")
            self.llm_error.emit("initialization", str(e))
            raise
    
    def is_initialized(self) -> bool:
        """Check if controller is initialized."""
        return self._initialized and self.llm_service.is_initialized()
    
    def execute_task(self, task_id: str, context: Dict[str, Any]) -> bool:
        """Execute an LLM task with given context."""
        if not self.is_initialized():
            self.logger.error("LLM controller not initialized")
            self.llm_error.emit(task_id, "LLM system not initialized")
            return False
        
        try:
            self.logger.info(f"Executing LLM task: {task_id}")
            self.llm_status_changed.emit(f"Executing task: {task_id}")
            
            # Execute task
            response = self.llm_service.execute_task(task_id, context)
            
            # Emit success signal
            self.llm_response_ready.emit(task_id, response)
            self.llm_status_changed.emit("Task completed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {e}")
            self.llm_error.emit(task_id, str(e))
            self.llm_status_changed.emit("Task failed")
            return False
    
    def get_available_tasks(self) -> list:
        """Get list of available LLM tasks."""
        if not self.is_initialized():
            return []
        
        return self.llm_service.get_available_tasks()
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific task."""
        if not self.is_initialized():
            return None
        
        return self.llm_service.get_task_info(task_id)
    
    def clear_cache(self):
        """Clear the LLM response cache."""
        if not self.is_initialized():
            return
        
        self.llm_service.clear_cache()
        self.llm_status_changed.emit("Cache cleared")
        self.logger.info("LLM cache cleared")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get LLM service information."""
        if not self.is_initialized():
            return {'initialized': False}
        
        return self.llm_service.get_service_info()
    
    def set_provider(self, provider_name: str):
        """Change LLM provider."""
        try:
            self.logger.info(f"Changing LLM provider to: {provider_name}")
            
            # Save to settings manager
            self.settings_manager.set_current_provider(provider_name)
            
            # Reinitialize service
            self.llm_service.initialize(provider_name)
            
            self.llm_status_changed.emit(f"Provider changed to: {provider_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to change provider: {e}")
            self.llm_error.emit("provider_change", str(e))
    
    def get_current_provider(self) -> str:
        """Get current LLM provider name."""
        return self.settings_manager.get_current_provider()
    
    def on_settings_changed(self):
        """Handle LLM settings changes."""
        try:
            self.logger.info("LLM settings changed, reinitializing service")
            
            # Get current provider
            current_provider = self.settings_manager.get_current_provider()
            
            # Reinitialize service with new settings
            self.llm_service.initialize(current_provider)
            
            self.llm_status_changed.emit("Settings updated")
            
        except Exception as e:
            self.logger.error(f"Failed to apply settings changes: {e}")
            self.llm_error.emit("settings_change", str(e))
    
    def test_connection(self) -> bool:
        """Test LLM connection with a simple task."""
        if not self.is_initialized():
            return False
        
        try:
            # Test with a simple context
            test_context = {
                'current_text': 'Test text',
                'scene_summary': 'Test scene',
                'scene_title': 'Test Scene',
                'scene_id': 1,
                'project_name': 'Test Project',
                'selected_text': '',
                'has_selection': False,
                'scene_length': 9,
                'word_count': 2
            }
            
            response = self.llm_service.execute_task('continue_scene', test_context)
            
            self.logger.info("LLM connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"LLM connection test failed: {e}")
            return False
    
    def update_scene_context(self, scene_id: int, scene_title: str, scene_content: str):
        """Update current scene context."""
        if not self.is_initialized():
            return
        
        try:
            self.llm_service.update_scene_context(scene_id, scene_title, scene_content)
            self.logger.debug(f"Scene context updated: {scene_title}")
            
        except Exception as e:
            self.logger.error(f"Failed to update scene context: {e}")
    
    def update_project_context(self, project_name: str, project_path: str = None):
        """Update current project context."""
        if not self.is_initialized():
            return
        
        try:
            self.llm_service.update_project_context(project_name, project_path)
            self.logger.debug(f"Project context updated: {project_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to update project context: {e}")
    
    def update_text_selection(self, selected_text: str, current_text: str = ""):
        """Update current text selection context."""
        if not self.is_initialized():
            return
        
        try:
            self.llm_service.update_text_selection(selected_text, current_text)
            self.logger.debug(f"Text selection updated: {len(selected_text)} chars selected")
            
        except Exception as e:
            self.logger.error(f"Failed to update text selection: {e}")
    
    def _on_context_updated(self, context):
        """Handle context update from context manager."""
        try:
            # Could emit signal or update UI status here
            self.logger.debug("Context updated in LLM controller")
            
        except Exception as e:
            self.logger.error(f"Error handling context update: {e}")
    
    def _on_context_ready(self, context):
        """Handle context ready signal from context manager."""
        try:
            # Context is ready for use
            self.logger.debug("Context ready for LLM operations")
            
        except Exception as e:
            self.logger.error(f"Error handling context ready: {e}")
    
    def get_context_summary(self) -> str:
        """Get human-readable summary of current context."""
        if not self.is_initialized():
            return "LLM not initialized"
        
        try:
            context_manager = self.llm_service.get_context_manager()
            return context_manager.get_context_summary()
            
        except Exception as e:
            self.logger.error(f"Failed to get context summary: {e}")
            return "Context unavailable"


# Global controller instance
_llm_controller = None


def get_llm_controller() -> Optional['AppLLMController']:
    """Get the global LLM controller instance."""
    return _llm_controller


def set_llm_controller(controller: 'AppLLMController'):
    """Set the global LLM controller instance."""
    global _llm_controller
    _llm_controller = controller