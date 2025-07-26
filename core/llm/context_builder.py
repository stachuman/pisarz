"""Context builder for LLM tasks - extracted from llm_assistant_panel."""

import re
import logging
from typing import Dict, Any, Optional
from core.logging_config import get_logger


class ContextBuilder:
    """Builds context for LLM tasks from scene content and user selections."""
    
    def __init__(self):
        self.logger = get_logger("core.llm.context_builder")
    
    def build_context(self, current_scene_content: str, current_scene_id: Optional[int], 
                     additional_context: Dict[str, Any], content_source_selection: int = 0) -> Dict[str, Any]:
        """
        Build context for LLM task from current scene.
        
        Args:
            current_scene_content: The current scene content (HTML)
            current_scene_id: ID of the current scene
            additional_context: Additional context data (project, characters, locations, etc.)
            content_source_selection: Index of content source selection (0-4)
            
        Returns:
            Context dictionary for LLM processing
        """
        # Extract text content (remove HTML tags and CSS for context)
        text_content = self._clean_html_css(current_scene_content)
        
        # Get user's content source selection
        content_source = self._map_content_source_selection(content_source_selection)
        
        # Get current text selection from LLM service (updated via signals)
        selected_text = ""
        current_selection_text = ""
        
        try:
            from controllers.app_llm_controller import get_llm_controller
            llm_controller = get_llm_controller()
            if llm_controller and llm_controller.llm_service and llm_controller.llm_service.context_manager:
                # Get current selection from context manager
                selection_info = llm_controller.llm_service.context_manager.get_text_selection()
                if selection_info:
                    selected_text = selection_info.get('selected_text', '')
                    current_selection_text = selection_info.get('current_text', '')
                    if selected_text:
                        self.logger.debug(f"Using selected text: {selected_text[:50]}...")
        except Exception as e:
            self.logger.warning(f"Could not get text selection: {e}")
        
        # Apply content source selection to override template behavior
        from core.llm.templates.config import ContextSource
        
        # Store original selection state for logging
        original_selected_text = selected_text
        original_has_selection = bool(selected_text.strip())
        
        if content_source == ContextSource.SELECTION:
            # Use actual text selection from editor - keep what we got from context manager
            has_selection = bool(selected_text.strip())
        elif content_source == ContextSource.FULL_SCENE:
            # Use full scene as both selected and current text
            selected_text = text_content
            current_selection_text = text_content
            has_selection = True
        elif content_source == ContextSource.SCENE_BEGINNING:
            # Use configurable length for scene beginning
            beginning_length = self._get_scene_beginning_length_from_settings()
            scene_beginning = text_content[:beginning_length] if text_content else ""
            selected_text = scene_beginning
            current_selection_text = scene_beginning
            has_selection = bool(scene_beginning.strip())
        elif content_source == ContextSource.SCENE_END:
            # Use configurable length for scene end
            end_length = self._get_scene_end_length_from_settings()
            scene_end = text_content[-end_length:] if text_content else ""
            selected_text = scene_end
            current_selection_text = scene_end
            has_selection = bool(scene_end.strip())
        elif content_source == ContextSource.CUSTOM_LENGTH:
            # Use configurable custom length
            custom_length = self._get_custom_length_from_settings()
            custom_text = text_content[:custom_length] if text_content else ""
            selected_text = custom_text
            current_selection_text = custom_text
            has_selection = bool(custom_text.strip())
        
        # Build basic context - enhanced template manager will handle the rest
        context = {
            'scene_content': text_content,
            'selected_text': selected_text,
            'current_text': current_selection_text,
            'scene_summary': text_content,  # Full scene as summary
            'scene_id': current_scene_id,
            'project_name': additional_context.get('project_name', 'Current Project'),
            'has_selection': has_selection,
            'characters': additional_context.get('characters', []),
            'locations': additional_context.get('locations', []),
            'character_count': additional_context.get('character_count', 0),
            'location_count': additional_context.get('location_count', 0),
            'content_source': content_source.value
        }
        
        # Add any other additional context data
        for key, value in additional_context.items():
            if key not in context:  # Don't override existing keys
                context[key] = value
        
        self.logger.debug(f"Built context with {content_source.value}: {len(text_content)} chars, {len(context['characters'])} characters, {len(context['locations'])} locations")
        return context
    
    def _clean_html_css(self, content: str) -> str:
        """Clean HTML tags and CSS from content to produce plain text."""
        from core.utils.text_cleaner import clean_html_css
        return clean_html_css(content)
    
    def _map_content_source_selection(self, selected_index: int):
        """Map content source selection index to ContextSource enum."""
        from core.llm.templates.config import ContextSource
        
        content_source_map = {
            0: ContextSource.SELECTION,      # "Selection (if any)"
            1: ContextSource.FULL_SCENE,     # "Full Scene" 
            2: ContextSource.SCENE_BEGINNING, # "Scene Beginning"
            3: ContextSource.SCENE_END,      # "Scene End"
            4: ContextSource.CUSTOM_LENGTH   # "Custom Length"
        }
        
        return content_source_map.get(selected_index, ContextSource.SELECTION)
    
    def _get_scene_beginning_length_from_settings(self) -> int:
        """Get scene beginning length from settings."""
        try:
            from ui.widgets.ai_content_settings_widget import AIContentSettingsWidget
            return AIContentSettingsWidget.get_scene_beginning_length_from_settings()
        except Exception as e:
            self.logger.error(f"Failed to get scene beginning length from settings: {e}")
            raise RuntimeError(f"Cannot get scene beginning length from settings: {e}")
    
    def _get_scene_end_length_from_settings(self) -> int:
        """Get scene end length from settings."""
        try:
            from ui.widgets.ai_content_settings_widget import AIContentSettingsWidget
            return AIContentSettingsWidget.get_scene_end_length_from_settings()
        except Exception as e:
            self.logger.error(f"Failed to get scene end length from settings: {e}")
            raise RuntimeError(f"Cannot get scene end length from settings: {e}")
    
    def _get_custom_length_from_settings(self) -> int:
        """Get custom length from settings."""
        try:
            from ui.widgets.ai_content_settings_widget import AIContentSettingsWidget
            return AIContentSettingsWidget.get_custom_length_from_settings()
        except Exception as e:
            self.logger.error(f"Failed to get custom length from settings: {e}")
            raise RuntimeError(f"Cannot get custom length from settings: {e}")