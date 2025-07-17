"""
Context builder for extracting scene data for LLM operations.

This module provides the ContextBuilder class which extracts relevant
context information from the current scene for LLM task execution.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from core.logging_config import get_logger
from i18n import _


class ContextBuilder:
    """Extracts and builds context data from current scene for LLM operations."""
    
    def __init__(self):
        self.logger = get_logger("llm.context.builder")
        self.logger.info(_("Context builder initialized"))
    
    def build_scene_context(self, 
                           current_text: str = "",
                           selected_text: str = "",
                           scene_title: str = "",
                           scene_content: str = "",
                           scene_id: Optional[int] = None,
                           project_name: str = "",
                           project_path: Optional[Path] = None,
                           context_length: int = 500) -> Dict[str, Any]:
        """
        Build context dictionary from scene data.
        
        Args:
            current_text: Current text at cursor position
            selected_text: Currently selected text
            scene_title: Title of the current scene
            scene_content: Full content of the current scene
            scene_id: ID of the current scene
            project_name: Name of the current project
            project_path: Path to the project file
            context_length: Maximum length for scene summary context
            
        Returns:
            Dictionary containing context variables for LLM templates
        """
        try:
            self.logger.debug(_("Building scene context"))
            
            # Extract meaningful current text
            extracted_text = self._extract_current_text(current_text, selected_text, scene_content)
            
            # Create scene summary
            scene_summary = self._create_scene_summary(scene_title, scene_content, context_length)
            
            # Clean selected text for context
            cleaned_selected_text = self._clean_html_css(selected_text) if selected_text else ""
            
            # Build context dictionary
            context = {
                'current_text': extracted_text,
                'selected_text': cleaned_selected_text,
                'scene_summary': scene_summary,
                'scene_title': scene_title,
                'scene_id': scene_id or 0,
                'project_name': project_name,
                'has_selection': bool(cleaned_selected_text.strip()),
                'scene_length': len(scene_content) if scene_content else 0,
                'word_count': len(scene_content.split()) if scene_content else 0
            }
            
            self.logger.debug(_("Scene context built successfully - {} words").format(context['word_count']))
            return context
            
        except Exception as e:
            self.logger.error(_("Failed to build scene context: {}").format(str(e)))
            return self._get_empty_context()
    
    def _extract_current_text(self, current_text: str, selected_text: str, scene_content: str) -> str:
        """
        Extract the most relevant current text for context.
        
        Priority: selected_text > current_text > last_paragraph
        """
        try:
            # If there's selected text, use it (clean HTML/CSS first)
            if selected_text and selected_text.strip():
                self.logger.debug(_("Using selected text as current context"))
                cleaned_selected = self._clean_html_css(selected_text)
                return cleaned_selected.strip()
            
            # If there's current text (cursor position), use it (clean HTML/CSS first)
            if current_text and current_text.strip():
                self.logger.debug(_("Using current text as context"))
                cleaned_current = self._clean_html_css(current_text)
                return cleaned_current.strip()
            
            # Fall back to last paragraph of scene
            if scene_content:
                paragraphs = [p.strip() for p in scene_content.split('\n\n') if p.strip()]
                if paragraphs:
                    last_paragraph = paragraphs[-1]
                    self.logger.debug(_("Using last paragraph as context"))
                    return last_paragraph
            
            self.logger.debug(_("No meaningful current text found"))
            return ""
            
        except Exception as e:
            self.logger.warning(_("Error extracting current text: {}").format(str(e)))
            return ""
    
    def _create_scene_summary(self, scene_title: str, scene_content: str, context_length: int = 500) -> str:
        """
        Create a summary of the scene for context.
        
        Args:
            scene_title: Title of the scene
            scene_content: Content of the scene
            context_length: Maximum length of content to include
        
        Format: "Scene: [title] - [first N chars]"
        """
        try:
            # Start with scene title
            summary_parts = []
            
            if scene_title and scene_title.strip():
                summary_parts.append(f"{_('Scene')}: {scene_title.strip()}")
            
            # Add content preview
            if scene_content and scene_content.strip():
                # Clean CSS and HTML from content first
                clean_content = self._clean_html_css(scene_content)
                
                # Clean and truncate content to specified length
                content_preview = clean_content.strip()[:context_length]
                if len(clean_content) > context_length:
                    content_preview += "..."
                
                if summary_parts:
                    summary_parts.append(f" - {content_preview}")
                else:
                    summary_parts.append(content_preview)
            
            summary = "".join(summary_parts)
            
            if not summary:
                summary = _("Empty scene")
            
            self.logger.debug(_("Scene summary created: {} characters").format(len(summary)))
            return summary
            
        except Exception as e:
            self.logger.warning(_("Error creating scene summary: {}").format(str(e)))
            return _("Scene summary unavailable")
    
    def _clean_html_css(self, content: str) -> str:
        """
        Clean HTML tags and CSS from content to produce plain text.
        
        Args:
            content: Raw content that may contain HTML/CSS
            
        Returns:
            Cleaned plain text content
        """
        import re
        
        # First, remove all HTML tags (including script, style, etc.)
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove HTML entities
        content = re.sub(r'&[a-zA-Z0-9#]+;', '', content)
        
        # Remove CSS style blocks completely (anything between braces)
        content = re.sub(r'\{[^}]*\}', '', content)
        
        # Remove CSS property lines (property: value;)
        content = re.sub(r'^[a-zA-Z0-9_-]+\s*:\s*[^;]+;?\s*$', '', content, flags=re.MULTILINE)
        
        # Remove CSS selectors and pseudo-selectors
        content = re.sub(r'[a-zA-Z0-9_-]+::[a-zA-Z0-9_-]+', '', content)
        content = re.sub(r'[a-zA-Z0-9_.-]+\s*\{', '', content)
        
        # Remove common CSS selector patterns (aggressive cleaning)
        content = re.sub(r'^p,\s*li\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^hr\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^li\.\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^li\.[a-zA-Z0-9_-]*\s*$', '', content, flags=re.MULTILINE)
        
        # Remove remaining CSS-like patterns
        content = re.sub(r'[a-zA-Z-]+\s*:\s*[^;{}]+;?', '', content)
        
        # Remove CSS selector fragments
        content = re.sub(r'^[a-zA-Z0-9_.-]+\s*$', '', content, flags=re.MULTILINE)
        
        # Remove Unicode escape sequences
        content = re.sub(r'\\[0-9a-fA-F]{4}', '', content)
        
        # Replace paragraph separators with regular spaces
        content = content.replace('\u2029', ' ')
        content = content.replace('\u2028', ' ')
        
        # Remove content property values with quotes
        content = re.sub(r'content:\s*"[^"]*"', '', content)
        
        # Remove empty lines and excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'^\s*$', '', content, flags=re.MULTILINE)
        
        # Remove lines that are just punctuation or special characters
        content = re.sub(r'^\s*[{}();,.\-_\s]*$', '', content, flags=re.MULTILINE)
        
        # Final cleanup
        content = content.strip()
        
        # Remove multiple consecutive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    def _get_empty_context(self) -> Dict[str, Any]:
        """Return empty context dictionary with default values."""
        return {
            'current_text': "",
            'selected_text': "",
            'scene_summary': _("No scene loaded"),
            'scene_title': "",
            'scene_id': 0,
            'project_name': _("Unknown project"),
            'has_selection': False,
            'scene_length': 0,
            'word_count': 0
        }
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that context dictionary has required fields.
        
        Args:
            context: Context dictionary to validate
            
        Returns:
            True if context is valid, False otherwise
        """
        try:
            required_fields = [
                'current_text', 'scene_summary', 'scene_id', 'project_name'
            ]
            
            for field in required_fields:
                if field not in context:
                    self.logger.warning(_("Missing required context field: {}").format(field))
                    return False
            
            # Check if we have some meaningful content
            if not context.get('current_text') and not context.get('scene_summary'):
                self.logger.warning(_("Context has no meaningful content"))
                return False
            
            self.logger.debug(_("Context validation successful"))
            return True
            
        except Exception as e:
            self.logger.error(_("Context validation failed: {}").format(str(e)))
            return False