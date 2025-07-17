"""
Template engine for LLM prompt rendering.

This module provides the TemplateEngine class which uses Jinja2 to render
LLM prompts with context variables.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound, TemplateSyntaxError
from core.logging_config import get_logger
from i18n import _


class TemplateEngine:
    """
    Jinja2-based template engine for LLM prompt rendering.
    
    This class handles loading and rendering of Jinja2 templates with context
    variables for LLM operations.
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template engine.
        
        Args:
            template_dir: Directory containing template files
        """
        self.logger = get_logger("llm.template.engine")
        
        # Set up template directory
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates"
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Add custom filters
        self._add_custom_filters()
        
        # Template cache
        self.template_cache: Dict[str, Template] = {}
        
        self.logger.info(_("Template engine initialized - Template dir: {}").format(self.template_dir))
    
    def _add_custom_filters(self):
        """Add custom Jinja2 filters for LLM templates."""
        try:
            # Filter to truncate text
            def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
                if not text or len(text) <= max_length:
                    return text
                return text[:max_length] + suffix
            
            # Filter to count words
            def word_count(text: str) -> int:
                if not text:
                    return 0
                return len(text.split())
            
            # Filter to format text for prompt
            def format_for_prompt(text: str) -> str:
                if not text:
                    return ""
                # Clean up text for prompt use
                return text.strip().replace('\n\n', '\n').replace('\r', '')
            
            # Filter to extract last N paragraphs
            def last_paragraphs(text: str, count: int = 1) -> str:
                if not text:
                    return ""
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                return '\n\n'.join(paragraphs[-count:]) if paragraphs else ""
            
            # Register filters
            self.env.filters['truncate_text'] = truncate_text
            self.env.filters['word_count'] = word_count
            self.env.filters['format_for_prompt'] = format_for_prompt
            self.env.filters['last_paragraphs'] = last_paragraphs
            
            self.logger.debug(_("Custom template filters added"))
            
        except Exception as e:
            self.logger.error(_("Failed to add custom filters: {}").format(str(e)))
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with given context.
        
        Args:
            template_name: Name of the template file (e.g., 'continue_scene.j2')
            context: Context variables for template rendering
            
        Returns:
            Rendered template string
            
        Raises:
            TemplateNotFound: If template file doesn't exist
            TemplateSyntaxError: If template has syntax errors
        """
        try:
            self.logger.debug(_("Rendering template: {} with context keys: {}").format(
                template_name, list(context.keys())))
            
            # Get template (with caching)
            template = self._get_template(template_name)
            
            # Add default context variables
            enhanced_context = self._enhance_context(context)
            
            # Render template
            rendered = template.render(enhanced_context)
            
            self.logger.debug(_("Template rendered successfully - {} characters").format(len(rendered)))
            return rendered
            
        except TemplateNotFound as e:
            self.logger.error(_("Template not found: {}").format(template_name))
            raise
        except TemplateSyntaxError as e:
            self.logger.error(_("Template syntax error in {}: {}").format(template_name, str(e)))
            raise
        except Exception as e:
            self.logger.error(_("Failed to render template {}: {}").format(template_name, str(e)))
            raise
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template from string with given context.
        
        Args:
            template_string: Template string to render
            context: Context variables for template rendering
            
        Returns:
            Rendered template string
        """
        try:
            self.logger.debug(_("Rendering template string with context keys: {}").format(list(context.keys())))
            
            # Create template from string
            template = self.env.from_string(template_string)
            
            # Add default context variables
            enhanced_context = self._enhance_context(context)
            
            # Render template
            rendered = template.render(enhanced_context)
            
            self.logger.debug(_("Template string rendered successfully - {} characters").format(len(rendered)))
            return rendered
            
        except Exception as e:
            self.logger.error(_("Failed to render template string: {}").format(str(e)))
            raise
    
    def _get_template(self, template_name: str) -> Template:
        """
        Get template with caching.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Jinja2 Template object
        """
        try:
            # Check cache first
            if template_name in self.template_cache:
                return self.template_cache[template_name]
            
            # Load template
            template = self.env.get_template(template_name)
            
            # Cache template
            self.template_cache[template_name] = template
            
            self.logger.debug(_("Template loaded and cached: {}").format(template_name))
            return template
            
        except Exception as e:
            self.logger.error(_("Failed to get template {}: {}").format(template_name, str(e)))
            raise
    
    def _enhance_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add default context variables and utilities.
        
        Args:
            context: Original context dictionary
            
        Returns:
            Enhanced context dictionary
        """
        try:
            enhanced = context.copy()
            
            # Add utility functions
            enhanced['_'] = _  # Translation function
            
            # Add template metadata
            enhanced['template_engine'] = 'Jinja2'
            enhanced['template_version'] = '1.0'
            
            return enhanced
            
        except Exception as e:
            self.logger.error(_("Failed to enhance context: {}").format(str(e)))
            return context
    
    def list_templates(self) -> list:
        """
        List available templates.
        
        Returns:
            List of template filenames
        """
        try:
            templates = []
            
            for template_file in self.template_dir.glob("*.j2"):
                templates.append(template_file.name)
            
            self.logger.debug(_("Found {} templates").format(len(templates)))
            return sorted(templates)
            
        except Exception as e:
            self.logger.error(_("Failed to list templates: {}").format(str(e)))
            return []
    
    def template_exists(self, template_name: str) -> bool:
        """
        Check if template exists.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            True if template exists, False otherwise
        """
        try:
            template_path = self.template_dir / template_name
            return template_path.exists()
            
        except Exception as e:
            self.logger.error(_("Failed to check template existence: {}").format(str(e)))
            return False
    
    def clear_cache(self):
        """Clear template cache."""
        try:
            self.template_cache.clear()
            self.logger.debug(_("Template cache cleared"))
            
        except Exception as e:
            self.logger.error(_("Failed to clear template cache: {}").format(str(e)))
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get information about a template.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Template information dictionary
        """
        try:
            template_path = self.template_dir / template_name
            
            if not template_path.exists():
                return {'exists': False}
            
            stat = template_path.stat()
            
            return {
                'exists': True,
                'name': template_name,
                'path': str(template_path),
                'size': stat.st_size,
                'modified': stat.st_mtime
            }
            
        except Exception as e:
            self.logger.error(_("Failed to get template info: {}").format(str(e)))
            return {'exists': False, 'error': str(e)}