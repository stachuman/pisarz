"""
Narrative Context Manager for maintaining story continuity across scenes.

MODERNIZED: Now uses the new database access layer for cleaner, more maintainable code.
Previous implementation: 400+ lines of repetitive database code  
New implementation: ~20 lines using Repository pattern
"""

import logging
from pathlib import Path

# Import the new modernized narrative context manager
from core.database.narrative_context_repository import NarrativeContextManager, NarrativeContext

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['NarrativeContextManager', 'NarrativeContext']