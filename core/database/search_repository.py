"""
Search repository using the new database access layer.
Replaces search functionality with clean repository pattern.
"""

from typing import List, Optional, Dict, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .base_repository import BaseRepository


class SearchResultType(Enum):
    """Types of search results."""
    SCENE = "scene"
    CHARACTER = "character"
    LOCATION = "location"


@dataclass
class SearchResult:
    """Represents a single search result."""
    result_type: SearchResultType
    id: int
    title: str
    snippet: str
    rank: float
    project_id: int
    highlights: List[str] = None  # Highlighted search terms
    metadata: Dict[str, Any] = None  # Additional type-specific data


@dataclass
class SearchFilter:
    """Search filter configuration."""
    search_types: List[SearchResultType] = None
    project_id: Optional[int] = None
    character_id: Optional[int] = None
    location_id: Optional[int] = None
    max_results: int = 50
    min_rank: float = 0.0


class SearchRepository(BaseRepository):
    """Repository for full-text search operations."""
    
    @property
    def table_name(self) -> str:
        return "search_index"  # Virtual table name
    
    @property
    def model_class(self) -> type:
        return SearchResult
    
    @property
    def required_fields(self) -> List[str]:
        return []
    
    def search_all(self, query: str, search_filter: SearchFilter = None) -> List[SearchResult]:
        """Perform full-text search across all content."""
        if not query or not query.strip():
            return []
        
        if search_filter is None:
            search_filter = SearchFilter()
        
        results = []
        
        # Search scenes if enabled
        if not search_filter.search_types or SearchResultType.SCENE in search_filter.search_types:
            scene_results = self._search_scenes(query, search_filter)
            results.extend(scene_results)
        
        # Search characters if enabled
        if not search_filter.search_types or SearchResultType.CHARACTER in search_filter.search_types:
            character_results = self._search_characters(query, search_filter)
            results.extend(character_results)
        
        # Search locations if enabled
        if not search_filter.search_types or SearchResultType.LOCATION in search_filter.search_types:
            location_results = self._search_locations(query, search_filter)
            results.extend(location_results)
        
        # Sort by rank and limit results
        results.sort(key=lambda x: x.rank, reverse=True)
        
        if search_filter.max_results > 0:
            results = results[:search_filter.max_results]
        
        return results
    
    def _search_scenes(self, query: str, search_filter: SearchFilter) -> List[SearchResult]:
        """Search in scenes using FTS."""
        search_query = """
            SELECT s.id, s.title, s.project_id, snippet(scenes_fts, 1, '<mark>', '</mark>', '...', 64) as snippet
            FROM scenes_fts
            JOIN scenes s ON s.id = scenes_fts.rowid
            WHERE scenes_fts MATCH ?
        """
        
        params = [query]
        
        if search_filter.project_id:
            search_query += " AND s.project_id = ?"
            params.append(search_filter.project_id)
        
        if search_filter.min_rank > 0:
            search_query += " AND rank >= ?"
            params.append(search_filter.min_rank)
        
        search_query += " ORDER BY rank DESC"
        
        try:
            rows = self.execute_custom_query(search_query, params)
            results = []
            
            for row in rows:
                result = SearchResult(
                    result_type=SearchResultType.SCENE,
                    id=row[0],
                    title=row[1],
                    project_id=row[2],
                    snippet=row[3],
                    rank=1.0,  # Default rank since FTS5 rank not available in this query
                    highlights=self._extract_highlights(row[3]),
                    metadata={"content_type": "scene"}
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching scenes: {e}")
            return []
    
    def _search_characters(self, query: str, search_filter: SearchFilter) -> List[SearchResult]:
        """Search in characters using FTS."""
        search_query = """
            SELECT c.id, c.name, c.project_id, snippet(characters_fts, 1, '<mark>', '</mark>', '...', 64) as snippet
            FROM characters_fts
            JOIN characters c ON c.id = characters_fts.rowid
            WHERE characters_fts MATCH ?
        """
        
        params = [query]
        
        if search_filter.project_id:
            search_query += " AND c.project_id = ?"
            params.append(search_filter.project_id)
        
        if search_filter.min_rank > 0:
            search_query += " AND rank >= ?"
            params.append(search_filter.min_rank)
        
        search_query += " ORDER BY rank DESC"
        
        try:
            rows = self.execute_custom_query(search_query, params)
            results = []
            
            for row in rows:
                result = SearchResult(
                    result_type=SearchResultType.CHARACTER,
                    id=row[0],
                    title=row[1],
                    project_id=row[2],
                    snippet=row[3],
                    rank=1.0,  # Default rank since FTS5 rank not available in this query
                    highlights=self._extract_highlights(row[3]),
                    metadata={"content_type": "character"}
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching characters: {e}")
            return []
    
    def _search_locations(self, query: str, search_filter: SearchFilter) -> List[SearchResult]:
        """Search in locations using FTS."""
        search_query = """
            SELECT l.id, l.name, l.project_id, snippet(locations_fts, 1, '<mark>', '</mark>', '...', 64) as snippet
            FROM locations_fts
            JOIN locations l ON l.id = locations_fts.rowid
            WHERE locations_fts MATCH ?
        """
        
        params = [query]
        
        if search_filter.project_id:
            search_query += " AND l.project_id = ?"
            params.append(search_filter.project_id)
        
        if search_filter.min_rank > 0:
            search_query += " AND rank >= ?"
            params.append(search_filter.min_rank)
        
        search_query += " ORDER BY rank DESC"
        
        try:
            rows = self.execute_custom_query(search_query, params)
            results = []
            
            for row in rows:
                result = SearchResult(
                    result_type=SearchResultType.LOCATION,
                    id=row[0],
                    title=row[1],
                    project_id=row[2],
                    snippet=row[3],
                    rank=1.0,  # Default rank since FTS5 rank not available in this query
                    highlights=self._extract_highlights(row[3]),
                    metadata={"content_type": "location"}
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching locations: {e}")
            return []
    
    def _extract_highlights(self, snippet: str) -> List[str]:
        """Extract highlighted terms from FTS snippet."""
        highlights = []
        if snippet:
            # Extract text between <mark> tags
            import re
            matches = re.findall(r'<mark>(.*?)</mark>', snippet)
            highlights = [match.strip() for match in matches if match.strip()]
        return highlights
    
    def get_search_suggestions(self, partial_query: str, project_id: Optional[int] = None) -> List[str]:
        """Get search suggestions based on partial query."""
        suggestions = []
        
        try:
            # Get unique titles from each content type
            queries = [
                "SELECT DISTINCT title FROM scenes",
                "SELECT DISTINCT name FROM characters", 
                "SELECT DISTINCT name FROM locations"
            ]
            
            for query in queries:
                if project_id:
                    query += " WHERE project_id = ?"
                    params = [project_id]
                else:
                    params = []
                
                query += " ORDER BY title LIMIT 10"
                
                rows = self.execute_custom_query(query, params)
                for row in rows:
                    title = row[0]
                    if partial_query.lower() in title.lower():
                        suggestions.append(title)
            
            return list(set(suggestions))[:10]  # Remove duplicates and limit
            
        except Exception as e:
            self.logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def rebuild_search_index(self) -> bool:
        """Rebuild the full-text search indexes."""
        try:
            # Rebuild FTS indexes
            rebuild_queries = [
                "INSERT INTO scenes_fts(scenes_fts) VALUES('rebuild')",
                "INSERT INTO characters_fts(characters_fts) VALUES('rebuild')",
                "INSERT INTO locations_fts(locations_fts) VALUES('rebuild')"
            ]
            
            for query in rebuild_queries:
                self.execute_custom_query(query, [])
            
            self.logger.info("Search indexes rebuilt successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rebuilding search indexes: {e}")
            return False


class SearchManager:
    """
    Search manager using the new repository pattern.
    Provides backward compatibility while using the new database layer.
    """
    
    def __init__(self, db_path: Path):
        """Initialize search manager."""
        self.db_path = db_path
        self.search_repo = SearchRepository(db_path)
    
    def search(self, query: str, search_filter: SearchFilter = None) -> List[SearchResult]:
        """Perform a search across all content."""
        return self.search_repo.search_all(query, search_filter)
    
    def search_all(self, query: str, project_id: Optional[int] = None, limit: int = 50) -> List[SearchResult]:
        """Search across all content types."""
        search_filter = SearchFilter(
            project_id=project_id,
            max_results=limit
        )
        return self.search_repo.search_all(query, search_filter)
    
    def search_scenes(self, query: str, project_id: Optional[int] = None, limit: int = 50) -> List[SearchResult]:
        """Search only in scenes."""
        search_filter = SearchFilter(
            search_types=[SearchResultType.SCENE],
            project_id=project_id,
            max_results=limit
        )
        return self.search_repo.search_all(query, search_filter)
    
    def search_characters(self, query: str, project_id: Optional[int] = None, limit: int = 50) -> List[SearchResult]:
        """Search only in characters."""
        search_filter = SearchFilter(
            search_types=[SearchResultType.CHARACTER],
            project_id=project_id,
            max_results=limit
        )
        return self.search_repo.search_all(query, search_filter)
    
    def search_locations(self, query: str, project_id: Optional[int] = None, limit: int = 50) -> List[SearchResult]:
        """Search only in locations."""
        search_filter = SearchFilter(
            search_types=[SearchResultType.LOCATION],
            project_id=project_id,
            max_results=limit
        )
        return self.search_repo.search_all(query, search_filter)
    
    def get_suggestions(self, partial_query: str, project_id: Optional[int] = None) -> List[str]:
        """Get search suggestions."""
        return self.search_repo.get_search_suggestions(partial_query, project_id)
    
    def rebuild_index(self) -> bool:
        """Rebuild search indexes."""
        return self.search_repo.rebuild_search_index()