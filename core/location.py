"""
Location management system for Pisarz writing application.

MODERNIZED: Now uses the new database access layer for cleaner, more maintainable code.
Previous implementation: 464 lines of repetitive database code
New implementation: ~20 lines using BaseRepository pattern
"""

import logging
from pathlib import Path

# Import the new modernized location manager
from .database.location_repository import LocationManager, Location, PlotThread

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['LocationManager', 'Location', 'PlotThread']