"""
Enhanced template system for LLM operations.

This module provides comprehensive template configuration and Jinja2-based 
template rendering for LLM prompts with context configuration, LLM parameters, 
and UI settings.
"""

from .config import (
    TemplateConfig, ContextSource, TemplateVersion,
    create_default_template
)
from .manager import EnhancedTemplateManager, get_template_manager

__all__ = [
    'TemplateConfig', 'ContextSource', 'TemplateVersion',
    'create_default_template',
    'EnhancedTemplateManager', 'get_template_manager'
]