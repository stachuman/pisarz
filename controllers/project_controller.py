"""Project controller for managing project-related operations."""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from core.project import ProjectManager
from core.scene import SceneManager
from core.character import CharacterManager
from core.location import LocationManager
from core.search import SearchManager
from i18n import _


class ProjectController(QObject):
    """Controller for managing project operations."""
    
    # Signals
    projectLoaded = Signal(str, str)  # project_path, project_name
    projectListLoaded = Signal(list)  # projects list
    projectCreated = Signal(str)  # project_name
    error = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.current_project_path = None
        self.current_project_name = ""
        self.current_scene_manager = None
        self.current_character_manager = None
        self.current_location_manager = None
        self.current_search_manager = None
        
    def load_projects_list(self):
        """Load and emit the projects list."""
        try:
            projects = self.project_manager.list_projects()
            self.projectListLoaded.emit(projects)
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to load projects: {}").format(e))
    
    def select_project(self, project_path: str, project_name: str):
        """Select and load a project."""
        self.current_project_path = project_path
        self.current_project_name = project_name
        
        try:
            # Initialize managers for the selected project
            self.current_scene_manager = SceneManager(Path(project_path))
            self.current_character_manager = CharacterManager(Path(project_path))
            self.current_location_manager = LocationManager(Path(project_path) / "pisarz.db")
            self.current_search_manager = SearchManager(Path(project_path) / "pisarz.db")
            
            # Emit success signal
            self.projectLoaded.emit(project_path, project_name)
            
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to load project: {}").format(e))
    
    def create_new_project(self, name: str):
        """Create a new project."""
        try:
            success = self.project_manager.create_project(name)
            if success:
                self.projectCreated.emit(name)
            else:
                self.error.emit(_("Error"), _("Failed to create project"))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to create project: {}").format(e))
    
    def get_project_data(self) -> Optional[dict]:
        """Get current project data."""
        if not self.current_project_path:
            return None
        try:
            return self.project_manager.get_project_data(Path(self.current_project_path))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to get project data: {}").format(e))
            return None
    
    def get_project_id(self) -> Optional[int]:
        """Get current project ID."""
        project_data = self.get_project_data()
        return project_data['id'] if project_data else None
    
    def get_current_managers(self) -> dict:
        """Get current managers dictionary."""
        return {
            'project_manager': self.project_manager,
            'scene_manager': self.current_scene_manager,
            'character_manager': self.current_character_manager,
            'location_manager': self.current_location_manager,
            'search_manager': self.current_search_manager
        }
    
    def has_active_project(self) -> bool:
        """Check if there's an active project."""
        return self.current_project_path is not None
    
    def get_current_project_info(self) -> tuple:
        """Get current project path and name."""
        return self.current_project_path, self.current_project_name