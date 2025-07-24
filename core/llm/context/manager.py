"""
Context manager for handling UI signals and context updates.

This module provides the ContextManager class which listens to UI signals
and maintains current context state for LLM operations.
"""

import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer
from core.logging_config import get_logger
from .builder import ContextBuilder
from i18n import _


class ContextManager(QObject):
    """
    Manages context state and handles UI signals for LLM operations.
    
    This class listens to text selection changes, scene updates, and other
    UI events to maintain current context for LLM tasks.
    """
    
    # Signals
    context_updated = Signal(dict)  # Emitted when context changes
    context_ready = Signal(dict)    # Emitted when context is ready for use
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("llm.context.manager")
        self.context_builder = ContextBuilder()
        
        # Current context state
        self.current_context: Dict[str, Any] = {}
        self.last_context_hash: Optional[str] = None
        
        # Scene state
        self.current_scene_id: Optional[int] = None
        self.current_scene_title: str = ""
        self.current_scene_content: str = ""
        self.current_project_name: str = ""
        self.current_project_id: Optional[int] = None
        
        # Text state
        self.current_text: str = ""
        self.selected_text: str = ""
        
        # Debounce timer for text selection changes
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._process_context_update)
        self.debounce_delay = 300  # 300ms debounce
        
        # Context update callback
        self.context_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        self.logger.info(_("Context manager initialized"))
    
    def set_context_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback function to be called when context updates."""
        self.context_callback = callback
        self.logger.debug(_("Context callback set"))
    
    def set_scene_context(self, scene_id: int, scene_title: str, scene_content: str):
        """
        Update scene context information.
        
        Args:
            scene_id: ID of the current scene
            scene_title: Title of the current scene
            scene_content: Full content of the current scene
        """
        try:
            self.logger.debug(_("Setting scene context - ID: {}, Title: {}").format(scene_id, scene_title))
            
            self.current_scene_id = scene_id
            self.current_scene_title = scene_title
            self.current_scene_content = scene_content
            
            # Trigger context update
            self._schedule_context_update()
            
        except Exception as e:
            self.logger.error(_("Failed to set scene context: {}").format(str(e)))
    
    def set_project_context(self, project_name: str, project_id: Optional[int] = None):
        """
        Update project context information.
        
        Args:
            project_name: Name of the current project
            project_id: ID of the current project
        """
        try:
            self.logger.debug(_("Setting project context - Name: {}, ID: {}").format(project_name, project_id))
            
            self.current_project_name = project_name
            self.current_project_id = project_id
            
            # Trigger context update
            self._schedule_context_update()
            
        except Exception as e:
            self.logger.error(_("Failed to set project context: {}").format(str(e)))
    
    def set_text_selection(self, selected_text: str, current_text: str = ""):
        """
        Update text selection context.
        
        Args:
            selected_text: Currently selected text
            current_text: Current text at cursor position
        """
        try:
            self.logger.debug(_("Setting text selection - Selected: {} chars, Current: {} chars").format(
                len(selected_text), len(current_text)))
            
            self.selected_text = selected_text
            self.current_text = current_text
            
            # Trigger debounced context update
            self._schedule_context_update()
            
        except Exception as e:
            self.logger.error(_("Failed to set text selection: {}").format(str(e)))
    
    def get_current_context(self) -> Dict[str, Any]:
        """
        Get current context dictionary.
        
        Returns:
            Current context dictionary
        """
        if not self.current_context:
            self._build_context()
        
        return self.current_context.copy()
    
    def get_text_selection(self) -> Dict[str, str]:
        """
        Get current text selection information.
        
        Returns:
            Dictionary with 'selected_text' and 'current_text' keys
        """
        return {
            'selected_text': self.selected_text or '',
            'current_text': self.current_text or ''
        }
    
    def refresh_context(self):
        """Force refresh of current context."""
        self.logger.debug(_("Forcing context refresh"))
        self._build_context()
    
    def _schedule_context_update(self):
        """Schedule a debounced context update."""
        self.update_timer.start(self.debounce_delay)
    
    def _process_context_update(self):
        """Process context update (called by timer)."""
        try:
            self.logger.debug(_("Processing context update"))
            
            # Build new context
            new_context = self._build_context()
            
            # Check if context actually changed
            context_hash = self._hash_context(new_context)
            if context_hash != self.last_context_hash:
                self.logger.debug(_("Context changed, emitting updates"))
                
                self.last_context_hash = context_hash
                self.current_context = new_context
                
                # Emit signals
                self.context_updated.emit(new_context)
                
                # Call callback if set
                if self.context_callback:
                    self.context_callback(new_context)
                
                # Check if context is ready for use
                if self.context_builder.validate_context(new_context):
                    self.context_ready.emit(new_context)
            else:
                self.logger.debug(_("Context unchanged, skipping update"))
                
        except Exception as e:
            self.logger.error(_("Failed to process context update: {}").format(str(e)))
    
    def _build_context(self) -> Dict[str, Any]:
        """
        Build context dictionary from current state.
        
        Returns:
            Context dictionary
        """
        try:
            context = self.context_builder.build_scene_context(
                current_text=self.current_text,
                selected_text=self.selected_text,
                scene_title=self.current_scene_title,
                scene_content=self.current_scene_content,
                scene_id=self.current_scene_id,
                project_name=self.current_project_name,
                project_id=self.current_project_id
            )
            
            return context
            
        except Exception as e:
            self.logger.error(_("Failed to build context: {}").format(str(e)))
            return self.context_builder._get_empty_context()
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """
        Create hash of context to detect changes.
        
        Args:
            context: Context dictionary
            
        Returns:
            Hash string
        """
        try:
            # Create hash from key context elements
            hash_elements = [
                context.get('current_text', ''),
                context.get('selected_text', ''),
                context.get('scene_title', ''),
                str(context.get('scene_id', 0)),
                context.get('project_name', '')
            ]
            
            return hash(tuple(hash_elements))
            
        except Exception as e:
            self.logger.warning(_("Failed to hash context: {}").format(str(e)))
            return str(hash(str(context)))
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug(_("Cleaning up context manager"))
            
            if self.update_timer.isActive():
                self.update_timer.stop()
            
            self.context_callback = None
            self.current_context.clear()
            
        except Exception as e:
            self.logger.error(_("Failed to cleanup context manager: {}").format(str(e)))
    
    def get_context_summary(self) -> str:
        """
        Get human-readable summary of current context.
        
        Returns:
            Context summary string
        """
        try:
            context = self.get_current_context()
            
            summary_parts = []
            
            # Project info
            if context.get('project_name'):
                summary_parts.append(f"{_('Project')}: {context['project_name']}")
            
            # Scene info
            if context.get('scene_title'):
                summary_parts.append(f"{_('Scene')}: {context['scene_title']}")
            
            # Text info
            if context.get('has_selection'):
                summary_parts.append(f"{_('Selected text')}: {len(context.get('selected_text', ''))} {_('chars')}")
            elif context.get('current_text'):
                summary_parts.append(f"{_('Current text')}: {len(context.get('current_text', ''))} {_('chars')}")
            
            # Word count
            if context.get('word_count', 0) > 0:
                summary_parts.append(f"{_('Scene words')}: {context['word_count']}")
            
            return " | ".join(summary_parts) if summary_parts else _("No context available")
            
        except Exception as e:
            self.logger.error(_("Failed to get context summary: {}").format(str(e)))
            return _("Context summary unavailable")