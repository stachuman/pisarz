"""
Search functionality for Pisarz writing application.

Provides full-text search across scenes, characters, and locations using SQLite FTS5.
"""

import sqlite3
from typing import List, Dict, Optional, Tuple, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .db import get_db_connection


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
class SearchResults:
    """Container for search results with metadata."""
    query: str
    results: List[SearchResult]
    total_count: int
    search_time_ms: float
    results_by_type: Dict[SearchResultType, List[SearchResult]] = None
    
    def __post_init__(self):
        """Group results by type after initialization."""
        if self.results_by_type is None:
            self.results_by_type = {}
            for result_type in SearchResultType:
                self.results_by_type[result_type] = [
                    r for r in self.results if r.result_type == result_type
                ]


class SearchManager:
    """Manages full-text search operations using SQLite FTS5."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def search_all(self, query: str, project_id: int, limit: int = 50) -> SearchResults:
        """Search across all content types and return unified results."""
        import time
        start_time = time.time()
        
        if not query.strip():
            return SearchResults(
                query=query,
                results=[],
                total_count=0,
                search_time_ms=0.0
            )
        
        all_results = []
        
        # Search scenes
        scene_results = self.search_scenes(query, project_id, limit // 3)
        all_results.extend(scene_results)
        
        # Search characters
        character_results = self.search_characters(query, project_id, limit // 3)
        all_results.extend(character_results)
        
        # Search locations
        location_results = self.search_locations(query, project_id, limit // 3)
        all_results.extend(location_results)
        
        # Sort by relevance (rank)
        all_results.sort(key=lambda x: x.rank, reverse=True)
        
        # Limit final results
        if len(all_results) > limit:
            all_results = all_results[:limit]
        
        search_time = (time.time() - start_time) * 1000
        
        return SearchResults(
            query=query,
            results=all_results,
            total_count=len(all_results),
            search_time_ms=search_time
        )
    
    def search_scenes(self, query: str, project_id: int, limit: int = 20) -> List[SearchResult]:
        """Search for scenes using FTS5."""
        if not query.strip():
            return []
        
        try:
            with get_db_connection(self.db_path) as conn:
                # Use FTS5 MATCH syntax for better search
                fts_query = self._prepare_fts_query(query)
                
                cursor = conn.execute("""
                    SELECT 
                        s.id,
                        s.title,
                        s.content_rtf,
                        s.project_id,
                        1.0 as fts_rank,
                        snippet(scenes_fts, 1, '<mark>', '</mark>', '...', 64) as snippet
                    FROM scenes_fts
                    JOIN scenes s ON s.id = scenes_fts.rowid
                    WHERE scenes_fts MATCH ? AND s.project_id = ?
                    LIMIT ?
                """, (fts_query, project_id, limit))
                
                results = []
                for row in cursor.fetchall():
                    # Clean snippet from RTF formatting
                    clean_snippet = self._clean_rtf_snippet(row['snippet'])
                    
                    result = SearchResult(
                        result_type=SearchResultType.SCENE,
                        id=row['id'],
                        title=row['title'],
                        snippet=clean_snippet,
                        rank=abs(row['fts_rank']),  # FTS5 rank is negative
                        project_id=project_id,
                        highlights=self._extract_highlights(clean_snippet),
                        metadata={
                            'content_length': len(row['content_rtf'] or ''),
                            'has_content': bool(row['content_rtf'])
                        }
                    )
                    results.append(result)
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error searching scenes: {e}")
            return []
    
    def search_characters(self, query: str, project_id: int, limit: int = 20) -> List[SearchResult]:
        """Search for characters using FTS5."""
        if not query.strip():
            return []
        
        try:
            with get_db_connection(self.db_path) as conn:
                fts_query = self._prepare_fts_query(query)
                
                cursor = conn.execute("""
                    SELECT 
                        c.id,
                        c.name,
                        c.description,
                        c.importance,
                        c.is_protagonist,
                        c.is_antagonist,
                        c.project_id,
                        1.0 as fts_rank,
                        snippet(characters_fts, -1, '<mark>', '</mark>', '...', 64) as snippet
                    FROM characters_fts
                    JOIN characters c ON c.id = characters_fts.rowid
                    WHERE characters_fts MATCH ? AND c.project_id = ?
                    LIMIT ?
                """, (fts_query, project_id, limit))
                
                results = []
                for row in cursor.fetchall():
                    # Create appropriate snippet
                    snippet = row['snippet'] if row['snippet'] else (row['description'][:100] + '...' if row['description'] else 'No description available')
                    
                    result = SearchResult(
                        result_type=SearchResultType.CHARACTER,
                        id=row['id'],
                        title=row['name'],
                        snippet=snippet,
                        rank=abs(row['fts_rank']),
                        project_id=project_id,
                        highlights=self._extract_highlights(snippet),
                        metadata={
                            'importance': row['importance'],
                            'is_protagonist': bool(row['is_protagonist']),
                            'is_antagonist': bool(row['is_antagonist']),
                            'has_description': bool(row['description'])
                        }
                    )
                    results.append(result)
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error searching characters: {e}")
            return []
    
    def search_locations(self, query: str, project_id: int, limit: int = 20) -> List[SearchResult]:
        """Search for locations using FTS5."""
        if not query.strip():
            return []
        
        try:
            with get_db_connection(self.db_path) as conn:
                fts_query = self._prepare_fts_query(query)
                
                cursor = conn.execute("""
                    SELECT 
                        l.id,
                        l.name,
                        l.description,
                        l.type,
                        l.atmosphere,
                        l.project_id,
                        1.0 as fts_rank,
                        snippet(locations_fts, -1, '<mark>', '</mark>', '...', 64) as snippet
                    FROM locations_fts
                    JOIN locations l ON l.id = locations_fts.rowid
                    WHERE locations_fts MATCH ? AND l.project_id = ?
                    LIMIT ?
                """, (fts_query, project_id, limit))
                
                results = []
                for row in cursor.fetchall():
                    # Create appropriate snippet
                    snippet = row['snippet'] if row['snippet'] else (row['description'][:100] + '...' if row['description'] else 'No description available')
                    
                    result = SearchResult(
                        result_type=SearchResultType.LOCATION,
                        id=row['id'],
                        title=row['name'],
                        snippet=snippet,
                        rank=abs(row['fts_rank']),
                        project_id=project_id,
                        highlights=self._extract_highlights(snippet),
                        metadata={
                            'type': row['type'],
                            'atmosphere': row['atmosphere'],
                            'has_description': bool(row['description'])
                        }
                    )
                    results.append(result)
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error searching locations: {e}")
            return []
    
    def get_search_suggestions(self, query_prefix: str, project_id: int, limit: int = 10) -> List[str]:
        """Get search suggestions based on query prefix."""
        if len(query_prefix) < 2:
            return []
        
        suggestions = set()
        
        try:
            with get_db_connection(self.db_path) as conn:
                # Get suggestions from scene titles
                cursor = conn.execute("""
                    SELECT DISTINCT title FROM scenes 
                    WHERE project_id = ? AND title LIKE ? 
                    LIMIT ?
                """, (project_id, f"%{query_prefix}%", limit // 3))
                
                for row in cursor.fetchall():
                    suggestions.add(row['title'])
                
                # Get suggestions from character names
                cursor = conn.execute("""
                    SELECT DISTINCT name FROM characters 
                    WHERE project_id = ? AND name LIKE ? 
                    LIMIT ?
                """, (project_id, f"%{query_prefix}%", limit // 3))
                
                for row in cursor.fetchall():
                    suggestions.add(row['name'])
                
                # Get suggestions from location names
                cursor = conn.execute("""
                    SELECT DISTINCT name FROM locations 
                    WHERE project_id = ? AND name LIKE ? 
                    LIMIT ?
                """, (project_id, f"%{query_prefix}%", limit // 3))
                
                for row in cursor.fetchall():
                    suggestions.add(row['name'])
        
        except sqlite3.Error as e:
            print(f"Error getting search suggestions: {e}")
            return []
        
        return sorted(list(suggestions))[:limit]
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for FTS5 MATCH syntax."""
        # Clean and escape the query
        query = query.strip()
        
        # Handle quoted phrases
        if '"' in query:
            return query  # User is using explicit phrase search
        
        # Split into terms and make each term a prefix search
        terms = query.split()
        if not terms:
            return ""
        
        # For single terms, add prefix wildcard
        if len(terms) == 1:
            return f"{terms[0]}*"
        
        # For multiple terms, use AND with prefix matching
        escaped_terms = []
        for term in terms:
            if term:  # Skip empty terms
                escaped_terms.append(f"{term}*")
        
        return " AND ".join(escaped_terms)
    
    def _clean_rtf_snippet(self, rtf_text: str) -> str:
        """Clean RTF formatting from snippet text."""
        if not rtf_text:
            return ""
        
        # Simple RTF cleaning - remove basic RTF tags
        # This is a basic implementation; a full RTF parser would be more robust
        import re
        
        # Remove RTF control words
        text = re.sub(r'\\[a-z]+\d*\s*', '', rtf_text)
        # Remove curly braces
        text = re.sub(r'[{}]', '', text)
        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_highlights(self, snippet: str) -> List[str]:
        """Extract highlighted terms from snippet."""
        import re
        highlights = re.findall(r'<mark>(.*?)</mark>', snippet)
        return highlights
    
    def rebuild_search_index(self, project_id: Optional[int] = None) -> bool:
        """Rebuild the FTS search index."""
        try:
            with get_db_connection(self.db_path) as conn:
                if project_id:
                    # For external content FTS5 tables, we need to rebuild the entire index
                    # since we can't filter by project_id in the FTS table directly
                    conn.execute("INSERT INTO scenes_fts(scenes_fts) VALUES('rebuild')")
                    conn.execute("INSERT INTO characters_fts(characters_fts) VALUES('rebuild')")
                    conn.execute("INSERT INTO locations_fts(locations_fts) VALUES('rebuild')")
                else:
                    # Rebuild entire index
                    conn.execute("INSERT INTO scenes_fts(scenes_fts) VALUES('rebuild')")
                    conn.execute("INSERT INTO characters_fts(characters_fts) VALUES('rebuild')")
                    conn.execute("INSERT INTO locations_fts(locations_fts) VALUES('rebuild')")
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Error rebuilding search index: {e}")
            return False