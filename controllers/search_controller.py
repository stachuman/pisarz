"""Search controller for managing search operations."""

from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from i18n import _


class SearchController(QObject):
    """Controller for managing search operations."""
    
    # Signals
    searchRequested = Signal()  # Show search view
    searchPerformed = Signal(str, str)  # query, filter_type
    searchResultsReady = Signal(list)  # results
    searchResultSelected = Signal(str, int, str, str)  # result_type, result_id, title, query
    error = Signal(str, str)  # title, message
    statusMessage = Signal(str)  # message
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        
    def request_search(self):
        """Request to show search view."""
        self.searchRequested.emit()
    
    def perform_search(self, query: str, filter_type: str = "all"):
        """Perform search operation."""
        search_manager = self.project_controller.current_search_manager
        if not search_manager:
            return
            
        try:
            project_id = self.project_controller.get_project_id()
            if project_id is None:
                return
                
            results = search_manager.search_all(query, project_id, limit=50)
            
            if results.results:
                self.searchResultsReady.emit(results.results)
                self.statusMessage.emit(_("Search completed: {} results found in {:.2f}ms").format(
                    results.total_count, results.search_time_ms))
            else:
                self.searchResultsReady.emit([])
                self.statusMessage.emit(_("No results found for '{}'").format(query))
                
            self.searchPerformed.emit(query, filter_type)
            
        except Exception as e:
            self.error.emit(_("Error"), _("Search failed: {}").format(e))
    
    def select_search_result(self, result_type: str, result_id: int, title: str, search_query: str):
        """Handle search result selection."""
        try:
            self.searchResultSelected.emit(result_type, result_id, title, search_query)
            
            if result_type == "scene":
                self.statusMessage.emit(_("Opening scene: {}").format(title))
            elif result_type == "character":
                self.statusMessage.emit(_("Opening character: {}").format(title))
            elif result_type == "location":
                self.statusMessage.emit(_("Opening location: {}").format(title))
                
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to open search result: {}").format(e))
    
    def get_search_suggestions(self, query_prefix: str) -> list:
        """Get search suggestions."""
        search_manager = self.project_controller.current_search_manager
        if not search_manager:
            return []
            
        try:
            project_id = self.project_controller.get_project_id()
            if project_id is None:
                return []
            return search_manager.get_search_suggestions(query_prefix, project_id)
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to get search suggestions: {}").format(e))
            return []