"""Search functionality controller for the main application."""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal

from core.database.search_repository import SearchManager, SearchResult
from i18n import _


class AppSearchController(QObject):
    """Handles search-related operations for the main application."""
    
    # Signals
    searchResultsReady = Signal(object)  # search_results
    searchRequested = Signal()
    statusMessage = Signal(str)  # message
    errorOccurred = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_manager: Optional[SearchManager] = None
        self.current_project_id: Optional[int] = None
        
    def set_manager(self, search_manager: SearchManager, project_id: int):
        """Set the current search manager and project ID."""
        self.search_manager = search_manager
        self.current_project_id = project_id
        
    def show_search_view(self):
        """Show search view."""
        if not self.search_manager:
            return False
        self.searchRequested.emit()
        self.statusMessage.emit(_("Search view - Enter text to search across your project"))
        return True
    
    def perform_search(self, query: str, filter_type: str, project_manager) -> bool:
        """Perform search and emit results."""
        if not self.search_manager or not query.strip():
            return False
            
        try:
            # Use current project ID
            if not self.current_project_id:
                return False
                
            project_id = self.current_project_id
            
            if not project_id:
                return False
            
            # Perform search based on filter type
            if filter_type == "scenes":
                results = self.search_manager.search_scenes(query, project_id, limit=50)
                search_results = SearchResult(query=query, results=results, total_count=len(results), search_time_ms=0.0)
            elif filter_type == "characters":
                results = self.search_manager.search_characters(query, project_id, limit=50)
                search_results = SearchResult(query=query, results=results, total_count=len(results), search_time_ms=0.0)
            elif filter_type == "locations":
                results = self.search_manager.search_locations(query, project_id, limit=50)
                search_results = SearchResult(query=query, results=results, total_count=len(results), search_time_ms=0.0)
            else:  # "all"
                search_results = self.search_manager.search_all(query, project_id, limit=100)
            
            # Emit results
            self.searchResultsReady.emit(search_results)
            
            # Update status
            result_count = len(search_results.results) if hasattr(search_results, 'results') else len(search_results)
            self.statusMessage.emit(_("Search completed - Found {} results for '{}'").format(result_count, query))
            return True
            
        except Exception as e:
            self.errorOccurred.emit(_("Search Error"), _("Failed to perform search: {}").format(e))
            self.statusMessage.emit(_("Search failed"))
            return False
    
    def get_search_manager(self) -> Optional[SearchManager]:
        """Get the current search manager."""
        return self.search_manager