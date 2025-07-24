"""UI state management controller for the main application."""

from typing import Optional
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QSplitter, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QObject, Signal, Qt

from ui.widgets import ProjectsView, ProjectTreeView, Workspace
from i18n import _


class AppUIController(QObject):
    """Handles UI state management for the main application."""
    
    # Signals
    categorySelected = Signal(str)  # category
    statusMessage = Signal(str)  # message
    errorOccurred = Signal(str, str)  # title, message
    
    def __init__(self, main_window: QMainWindow, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.main_stack: Optional[QStackedWidget] = None
        self.projects_view: Optional[ProjectsView] = None
        self.project_tree: Optional[ProjectTreeView] = None
        self.workspace: Optional[Workspace] = None
        self.project_widget: Optional[QWidget] = None
        
    def setup_ui_components(self, main_stack: QStackedWidget, projects_view: ProjectsView,
                           project_tree: ProjectTreeView, workspace: Workspace, project_widget: QWidget):
        """Set references to UI components."""
        self.main_stack = main_stack
        self.projects_view = projects_view
        self.project_tree = project_tree
        self.workspace = workspace
        self.project_widget = project_widget
        
    def show_projects_view(self, projects: list):
        """Show the projects view with project list."""
        if not self.projects_view or not self.main_stack:
            return
            
        try:
            self.projects_view.load_projects(projects)
            self.main_stack.setCurrentIndex(0)
            self.statusMessage.emit(_("Projects list ({} projects)").format(len(projects)))
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to load projects view: {}").format(e))
    
    def show_project_view(self, project_name: str, scenes: list, characters: list, locations: list):
        """Show the project view with loaded data."""
        if not self.project_tree or not self.workspace or not self.main_stack:
            return
            
        try:
            # Update navigation tree
            self.project_tree.update_project_name(project_name)
            self.project_tree.load_scenes(scenes, preserve_selection=False)
            self.project_tree.load_characters(characters, preserve_selection=False)
            
            # Locations are already dictionaries from the repository
            self.project_tree.load_locations(locations, preserve_selection=False)
            
            # Show welcome screen in workspace
            self.workspace.show_welcome()
            
            # Switch to project view
            self.main_stack.setCurrentIndex(1)
            
            self.statusMessage.emit(_("Project: {} ({} scenes)").format(project_name, len(scenes)))
            
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to show project view: {}").format(e))
    
    def show_category_view(self, category: str, data_dict: dict):
        """Show category-specific view (scenes, characters, locations, search)."""
        if not self.workspace:
            return
            
        try:
            if category == "scenes":
                scenes = data_dict.get('scenes', [])
                character_manager = data_dict.get('character_manager')
                location_manager = data_dict.get('location_manager')
                self.workspace.show_scenes_grid(scenes, character_manager, location_manager)
                self.statusMessage.emit(_("Scenes view ({} scenes)").format(len(scenes)))
                
            elif category == "characters":
                characters = data_dict.get('characters', [])
                location_manager = data_dict.get('location_manager')
                self.workspace.show_characters_grid(characters, location_manager)
                self.statusMessage.emit(_("Characters view ({} characters)").format(len(characters)))
                
            elif category == "locations":
                location_manager = data_dict.get('location_manager')
                scene_manager = data_dict.get('scene_manager')
                project_id = data_dict.get('project_id')
                self.workspace.show_locations_grid(location_manager, project_id, scene_manager)
                locations = location_manager.get_locations(project_id) if location_manager else []
                self.statusMessage.emit(_("Locations view ({} locations)").format(len(locations)))
                
            elif category == "search":
                self.workspace.show_search_view()
                self.statusMessage.emit(_("Search view - Enter text to search across your project"))
                
            else:
                self.workspace.show_welcome()
                self.statusMessage.emit(_("View {} (function unavailable)").format(category))
                
            self.categorySelected.emit(category)
            
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to load view: {}").format(e))
    
    def refresh_scenes_data(self, scenes: list):
        """Refresh scenes data in UI components."""
        if self.project_tree:
            self.project_tree.load_scenes(scenes, preserve_selection=True)
            
        if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
            self.workspace.scenes_grid_view.load_scenes(scenes)
    
    def refresh_characters_data(self, characters: list, location_manager):
        """Refresh characters data in UI components."""
        if self.project_tree:
            self.project_tree.load_characters(characters, preserve_selection=True)
            
        if hasattr(self.workspace, 'characters_grid_view') and self.workspace.characters_grid_view:
            self.workspace.characters_grid_view.set_location_manager(location_manager)
            self.workspace.characters_grid_view.load_characters(characters)
    
    def refresh_locations_data(self, locations: list):
        """Refresh locations data in UI components."""
        if self.project_tree:
            # Locations are already dictionaries from the repository
            self.project_tree.load_locations(locations, preserve_selection=True)
            
        if hasattr(self.workspace, 'locations_grid_view') and self.workspace.locations_grid_view:
            self.workspace.locations_grid_view.refresh_locations()
    
    def update_project_name(self, project_name: str):
        """Update project name in navigation tree."""
        if self.project_tree:
            self.project_tree.update_project_name(project_name)
    
    def refresh_icons(self):
        """Refresh icons in navigation tree."""
        if self.project_tree:
            self.project_tree.refresh_icons()
    
    def refresh_theme(self):
        """Refresh theme in UI components."""
        if self.projects_view:
            self.projects_view.refresh_theme()
        if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
            self.workspace.scenes_grid_view.refresh_theme()