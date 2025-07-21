"""
Base repository with generic CRUD operations for database access.
Provides a consistent interface for all database operations.
"""

import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, Generic
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, asdict, fields

from .query_builder import QueryBuilder
from ..error_handler import get_error_handler, ErrorLevel, ErrorCategory

T = TypeVar('T')

logger = logging.getLogger(__name__)
error_handler = get_error_handler()


@contextmanager
def get_db_connection(db_path: Path):
    """Context manager for SQLite database connections with proper error handling."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        error_handler.handle_error(
            e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
            f"Database connection error: {e}"
        )
        raise
    finally:
        if conn:
            conn.close()


class BaseRepository(Generic[T]):
    """
    Base repository class providing generic CRUD operations.
    
    Subclasses should define:
    - table_name: str - The database table name
    - model_class: Type[T] - The dataclass model type
    - required_fields: List[str] - Fields required for creation
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.query_builder = QueryBuilder()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the database table name."""
        pass
    
    @property
    @abstractmethod
    def model_class(self) -> Type[T]:
        """Return the model class for this repository."""
        pass
    
    @property
    def required_fields(self) -> List[str]:
        """Return list of required fields for creation. Override if needed."""
        return []
    
    def create(self, **data) -> Optional[int]:
        """
        Create a new record in the database.
        
        Args:
            **data: Field values for the new record
            
        Returns:
            ID of created record or None if creation failed
        """
        try:
            # Validate required fields
            missing_fields = [field for field in self.required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Remove None values and id field
            clean_data = {k: v for k, v in data.items() if v is not None and k != 'id'}
            
            if not clean_data:
                raise ValueError("No data provided for creation")
            
            query, params = self.query_builder.insert(self.table_name, clean_data)
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                record_id = cursor.lastrowid
                
                self.logger.info(f"Created {self.table_name} record with ID {record_id}")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Error creating {self.table_name} record: {e}")
            error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to create {self.table_name} record"
            )
            return None
    
    def get_by_id(self, record_id: int) -> Optional[T]:
        """
        Get a record by its ID.
        
        Args:
            record_id: The record ID
            
        Returns:
            Model instance or None if not found
        """
        try:
            query, params = self.query_builder.select(
                self.table_name, 
                where={"id": record_id}
            )
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_model(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting {self.table_name} record {record_id}: {e}")
            return None
    
    def get_all(self, where: Optional[Dict[str, Any]] = None, 
                order_by: Optional[str] = None, limit: Optional[int] = None) -> List[T]:
        """
        Get all records matching the criteria.
        
        Args:
            where: WHERE clause conditions
            order_by: ORDER BY clause
            limit: LIMIT clause
            
        Returns:
            List of model instances
        """
        try:
            query, params = self.query_builder.select(
                self.table_name, 
                where=where, 
                order_by=order_by, 
                limit=limit
            )
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting {self.table_name} records: {e}")
            return []
    
    def update(self, record_id: int, **data) -> bool:
        """
        Update a record by ID.
        
        Args:
            record_id: The record ID to update
            **data: Field values to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Remove None values and id field
            clean_data = {k: v for k, v in data.items() if v is not None and k != 'id'}
            
            if not clean_data:
                self.logger.warning(f"No data provided for updating {self.table_name} record {record_id}")
                return True  # Nothing to update is considered success
            
            query, params = self.query_builder.update(
                self.table_name, 
                clean_data, 
                where={"id": record_id}
            )
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Updated {self.table_name} record {record_id}")
                    return True
                else:
                    self.logger.warning(f"No {self.table_name} record found with ID {record_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error updating {self.table_name} record {record_id}: {e}")
            error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to update {self.table_name} record {record_id}"
            )
            return False
    
    def delete(self, record_id: int) -> bool:
        """
        Delete a record by ID.
        
        Args:
            record_id: The record ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            query, params = self.query_builder.delete(
                self.table_name, 
                where={"id": record_id}
            )
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Deleted {self.table_name} record {record_id}")
                    return True
                else:
                    self.logger.warning(f"No {self.table_name} record found with ID {record_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error deleting {self.table_name} record {record_id}: {e}")
            error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to delete {self.table_name} record {record_id}"
            )
            return False
    
    def count(self, where: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching the criteria.
        
        Args:
            where: WHERE clause conditions
            
        Returns:
            Number of matching records
        """
        try:
            query, params = self.query_builder.count(self.table_name, where=where)
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error(f"Error counting {self.table_name} records: {e}")
            return 0
    
    def exists(self, where: Dict[str, Any]) -> bool:
        """
        Check if a record exists matching the criteria.
        
        Args:
            where: WHERE clause conditions
            
        Returns:
            True if record exists, False otherwise
        """
        return self.count(where) > 0
    
    def execute_custom_query(self, query: str, params: Optional[Union[List, Dict]] = None) -> List[sqlite3.Row]:
        """
        Execute a custom SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(query, params or [])
                return cursor.fetchall()
                
        except Exception as e:
            self.logger.error(f"Error executing custom query: {e}")
            error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to execute custom query"
            )
            return []
    
    def _row_to_model(self, row: sqlite3.Row) -> T:
        """
        Convert a database row to a model instance.
        
        Args:
            row: SQLite row object
            
        Returns:
            Model instance
        """
        try:
            # Get all field names from the model class
            model_fields = {f.name for f in fields(self.model_class)}
            
            # Create dictionary with only fields that exist in the model
            data = {key: row[key] for key in row.keys() if key in model_fields}
            
            return self.model_class(**data)
            
        except Exception as e:
            self.logger.error(f"Error converting row to {self.model_class.__name__}: {e}")
            # Return empty model instance as fallback
            return self.model_class()