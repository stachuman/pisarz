"""
Dynamic SQL query builder for database operations.
Provides a fluent interface for building SQL queries safely.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class QueryBuilder:
    """
    SQL query builder with parameter binding for safe database operations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.QueryBuilder")
    
    def select(self, table: str, 
               columns: Optional[List[str]] = None,
               where: Optional[Dict[str, Any]] = None,
               joins: Optional[List[str]] = None,
               order_by: Optional[str] = None,
               limit: Optional[int] = None,
               offset: Optional[int] = None) -> Tuple[str, List[Any]]:
        """
        Build a SELECT query.
        
        Args:
            table: Table name
            columns: List of columns to select (None for all)
            where: WHERE clause conditions
            joins: List of JOIN clauses
            order_by: ORDER BY clause
            limit: LIMIT clause
            offset: OFFSET clause
            
        Returns:
            Tuple of (query_string, parameters)
        """
        # Build SELECT clause
        if columns:
            select_clause = ", ".join(columns)
        else:
            select_clause = "*"
        
        query = f"SELECT {select_clause} FROM {table}"
        params = []
        
        # Add JOINs
        if joins:
            for join in joins:
                query += f" {join}"
        
        # Add WHERE clause
        if where:
            where_clause, where_params = self._build_where_clause(where)
            query += f" WHERE {where_clause}"
            params.extend(where_params)
        
        # Add ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Add LIMIT
        if limit:
            query += f" LIMIT {limit}"
        
        # Add OFFSET
        if offset:
            query += f" OFFSET {offset}"
        
        self.logger.debug(f"Built SELECT query: {query} with params: {params}")
        return query, params
    
    def insert(self, table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build an INSERT query.
        
        Args:
            table: Table name
            data: Dictionary of column -> value mappings
            
        Returns:
            Tuple of (query_string, parameters)
        """
        if not data:
            raise ValueError("No data provided for INSERT")
        
        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        params = list(data.values())
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        self.logger.debug(f"Built INSERT query: {query} with params: {params}")
        return query, params
    
    def update(self, table: str, data: Dict[str, Any], 
               where: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Any]]:
        """
        Build an UPDATE query.
        
        Args:
            table: Table name
            data: Dictionary of column -> value mappings to update
            where: WHERE clause conditions
            
        Returns:
            Tuple of (query_string, parameters)
        """
        if not data:
            raise ValueError("No data provided for UPDATE")
        
        # Build SET clause
        set_clauses = [f"{column} = ?" for column in data.keys()]
        params = list(data.values())
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        
        # Add WHERE clause
        if where:
            where_clause, where_params = self._build_where_clause(where)
            query += f" WHERE {where_clause}"
            params.extend(where_params)
        
        self.logger.debug(f"Built UPDATE query: {query} with params: {params}")
        return query, params
    
    def delete(self, table: str, 
               where: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Any]]:
        """
        Build a DELETE query.
        
        Args:
            table: Table name
            where: WHERE clause conditions
            
        Returns:
            Tuple of (query_string, parameters)
        """
        query = f"DELETE FROM {table}"
        params = []
        
        # Add WHERE clause
        if where:
            where_clause, where_params = self._build_where_clause(where)
            query += f" WHERE {where_clause}"
            params.extend(where_params)
        
        self.logger.debug(f"Built DELETE query: {query} with params: {params}")
        return query, params
    
    def count(self, table: str, 
              where: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Any]]:
        """
        Build a COUNT query.
        
        Args:
            table: Table name
            where: WHERE clause conditions
            
        Returns:
            Tuple of (query_string, parameters)
        """
        query = f"SELECT COUNT(*) FROM {table}"
        params = []
        
        # Add WHERE clause
        if where:
            where_clause, where_params = self._build_where_clause(where)
            query += f" WHERE {where_clause}"
            params.extend(where_params)
        
        self.logger.debug(f"Built COUNT query: {query} with params: {params}")
        return query, params
    
    def exists(self, table: str, 
               where: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build an EXISTS query.
        
        Args:
            table: Table name
            where: WHERE clause conditions
            
        Returns:
            Tuple of (query_string, parameters)
        """
        where_clause, params = self._build_where_clause(where)
        query = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {where_clause})"
        
        self.logger.debug(f"Built EXISTS query: {query} with params: {params}")
        return query, params
    
    def _build_where_clause(self, conditions: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build WHERE clause from conditions dictionary.
        
        Args:
            conditions: Dictionary of column -> value mappings
            
        Returns:
            Tuple of (where_clause, parameters)
        """
        if not conditions:
            return "", []
        
        clauses = []
        params = []
        
        for column, value in conditions.items():
            if value is None:
                clauses.append(f"{column} IS NULL")
            elif isinstance(value, (list, tuple)):
                # IN clause
                placeholders = ["?" for _ in value]
                clauses.append(f"{column} IN ({', '.join(placeholders)})")
                params.extend(value)
            elif isinstance(value, dict):
                # Handle operators like {'>=': 10}, {'LIKE': '%test%'}
                for operator, operand in value.items():
                    clauses.append(f"{column} {operator} ?")
                    params.append(operand)
            else:
                clauses.append(f"{column} = ?")
                params.append(value)
        
        return " AND ".join(clauses), params
    
    def build_custom_join(self, join_type: str, table: str, 
                         on_condition: str) -> str:
        """
        Build a custom JOIN clause.
        
        Args:
            join_type: Type of join (INNER, LEFT, RIGHT, etc.)
            table: Table to join
            on_condition: ON condition for the join
            
        Returns:
            JOIN clause string
        """
        return f"{join_type} JOIN {table} ON {on_condition}"
    
    def build_subquery(self, table: str, 
                      columns: Optional[List[str]] = None,
                      where: Optional[Dict[str, Any]] = None,
                      alias: Optional[str] = None) -> Tuple[str, List[Any]]:
        """
        Build a subquery.
        
        Args:
            table: Table name
            columns: List of columns to select
            where: WHERE clause conditions
            alias: Alias for the subquery
            
        Returns:
            Tuple of (subquery_string, parameters)
        """
        query, params = self.select(table, columns, where)
        
        if alias:
            query = f"({query}) AS {alias}"
        else:
            query = f"({query})"
        
        return query, params
    
    def build_union(self, queries: List[Tuple[str, List[Any]]], 
                   union_all: bool = False) -> Tuple[str, List[Any]]:
        """
        Build a UNION query from multiple SELECT queries.
        
        Args:
            queries: List of (query_string, parameters) tuples
            union_all: Whether to use UNION ALL instead of UNION
            
        Returns:
            Tuple of (union_query, all_parameters)
        """
        if not queries:
            raise ValueError("No queries provided for UNION")
        
        union_type = "UNION ALL" if union_all else "UNION"
        
        query_strings = []
        all_params = []
        
        for query, params in queries:
            query_strings.append(query)
            all_params.extend(params)
        
        final_query = f" {union_type} ".join(query_strings)
        
        self.logger.debug(f"Built UNION query: {final_query} with params: {all_params}")
        return final_query, all_params