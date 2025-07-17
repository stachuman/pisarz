"""
Context management for LLM operations.

This module provides context extraction and management for LLM tasks,
including scene data extraction, text selection handling, and context updates.
"""

from .builder import ContextBuilder
from .manager import ContextManager

__all__ = ['ContextBuilder', 'ContextManager']