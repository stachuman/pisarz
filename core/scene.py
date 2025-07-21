"""
Scene management for Pisarz projects.

MODERNIZED: Now uses the new database access layer for cleaner, more maintainable code.
Previous implementation: 123 lines of repetitive database code  
New implementation: ~20 lines using BaseRepository pattern
"""

import logging
from pathlib import Path

# Import the new modernized scene manager
from .database.scene_repository import SceneManager, Scene

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['SceneManager', 'Scene']