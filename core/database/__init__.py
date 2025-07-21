"""
Consolidated database access layer for Pisarz.

This module provides:
- BaseRepository: Generic CRUD operations
- QueryBuilder: Dynamic SQL query building
- Centralized connection management and error handling
"""

from .base_repository import BaseRepository, get_db_connection
from .query_builder import QueryBuilder

__all__ = ['BaseRepository', 'QueryBuilder', 'get_db_connection']