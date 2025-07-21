"""
Project management for Pisarz projects.

MODERNIZED: Now uses the new database access layer for cleaner, more maintainable code.
Previous implementation: 200+ lines of repetitive database code  
New implementation: ~20 lines using Repository pattern
"""

import logging
from pathlib import Path

# Import the new modernized project manager
from .database.project_manager import ProjectManager

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['ProjectManager']