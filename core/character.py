"""
Character management for Pisarz projects.

MODERNIZED: Now uses the new database access layer for cleaner, more maintainable code.
Previous implementation: 262 lines of repetitive database code
New implementation: ~20 lines using BaseRepository pattern
"""

import logging
from pathlib import Path

# Import the new modernized character manager
from .database.character_repository import CharacterManager, Character

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['CharacterManager', 'Character']