"""Navigation controller for managing UI navigation and view switching."""

from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QStackedWidget, QStatusBar

from i18n import _


class NavigationController(QObject):
    """Controller for managing UI navigation and view switching."""
    
    # Signals
    viewChanged = Signal(str)  # view_name
    categorySelected = Signal(str)  # category
    statusUpdated = Signal(str)  # message
    
    def __init__(self, main_stack: QStackedWidget, status_bar: QStatusBar, parent=None):
        super().__init__(parent)
        self.main_stack = main_stack
        self.status_bar = status_bar
        self.current_view = "projects"
        self.current_category = None
        
    def show_projects_view(self):
        """Show projects view."""
        self.main_stack.setCurrentIndex(0)
        self.current_view = "projects"
        self.current_category = None
        self.viewChanged.emit("projects")
    
    def show_project_view(self, project_name: str, scenes_count: int):
        """Show project view."""
        self.main_stack.setCurrentIndex(1)
        self.current_view = "project"
        self.current_category = None
        self.viewChanged.emit("project")
        self.update_status(_("Project: {} ({} scenes)").format(project_name, scenes_count))
    
    def show_category_view(self, category: str, item_count: int = 0):
        """Show category view."""
        self.current_category = category
        self.categorySelected.emit(category)
        
        if category == "scenes":
            self.update_status(_("Scenes view ({} scenes)").format(item_count))
        elif category == "characters":
            self.update_status(_("Characters view ({} characters)").format(item_count))
        elif category == "locations":
            self.update_status(_("Locations view ({} locations)").format(item_count))
        elif category == "search":
            self.update_status(_("Search view - Enter text to search across your project"))
        else:
            self.update_status(_("View {} (function unavailable)").format(category))
    
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_bar.showMessage(message)
        self.statusUpdated.emit(message)
    
    def get_current_view(self) -> str:
        """Get current view name."""
        return self.current_view
    
    def get_current_category(self) -> Optional[str]:
        """Get current category."""
        return self.current_category
    
    def set_projects_list_status(self, count: int):
        """Set status for projects list."""
        self.update_status(_("Projects list ({} projects)").format(count))
    
    def set_ready_status(self):
        """Set ready status."""
        self.update_status(_("Select project to start"))
    
    def set_editing_scene_status(self, scene_title: str):
        """Set status for editing scene."""
        self.update_status(_("Editing scene: {}").format(scene_title))
    
    def set_editing_character_status(self, character_name: str):
        """Set status for editing character."""
        self.update_status(_("Editing character: {}").format(character_name))
    
    def set_editing_location_status(self, location_name: str):
        """Set status for editing location."""
        self.update_status(_("Editing location: {}").format(location_name))