"""
LLM (Large Language Model) subsystem for Pisarz.

This module provides AI-powered writing assistance including:
- Context-aware text generation
- Multiple LLM provider support
- Task-based prompt system
- Caching and optimization
"""

from .service import LLMService
from .tasks.registry import TaskRegistry
from .tasks.definitions import TaskDefinition, TaskParameter

__all__ = [
    'LLMService',
    'TaskRegistry', 
    'TaskDefinition',
    'TaskParameter'
]