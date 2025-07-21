"""
Search functionality for Pisarz writing application.

MODERNIZED: Now uses the new database access layer for cleaner, more maintainable code.
Previous implementation: 400+ lines of repetitive database code  
New implementation: ~20 lines using Repository pattern
"""

import logging
from pathlib import Path

# Import the new modernized search manager
from .database.search_repository import SearchManager, SearchResult, SearchResultType, SearchFilter

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['SearchManager', 'SearchResult', 'SearchResultType', 'SearchFilter']