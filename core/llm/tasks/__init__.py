"""
Task system for LLM operations.

Provides structured task definitions, parameters, and registry
for different types of AI writing assistance.
"""

from .definitions import TaskDefinition, TaskParameter
from .registry import TaskRegistry

__all__ = ['TaskDefinition', 'TaskParameter', 'TaskRegistry']