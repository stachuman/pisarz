"""Project management controller for the main application."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject, Signal

from core.project import ProjectManager
from core.scene import SceneManager
from core.character import CharacterManager
from core.location import LocationManager
from core.search import SearchManager
from core.error_handler import get_error_handler, ErrorLevel, ErrorCategory
from i18n import _


class AppProjectController(QObject):
    """Handles project-related operations for the main application."""
    
    # Signals
    projectDataLoaded = Signal(str, str, dict)  # project_path, project_name, managers_dict
    projectCreated = Signal(str)  # project_name
    statusMessage = Signal(str)  # message
    errorOccurred = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.error_handler = get_error_handler()
        self.current_project_path: Optional[str] = None
        self.current_project_name: str = ""
        
        # Current managers
        self.current_scene_manager: Optional[SceneManager] = None
        self.current_character_manager: Optional[CharacterManager] = None
        self.current_location_manager: Optional[LocationManager] = None
        self.current_search_manager: Optional[SearchManager] = None
        
    def list_projects(self) -> list:
        """Get list of all projects."""
        try:
            return self.project_manager.list_projects()
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE, 
                                        context="Loading projects list",
                                        show_to_user=False)
            self.errorOccurred.emit(_("Error"), _("Failed to load projects: {}").format(e))
            return []
    
    def load_project(self, project_path: str, project_name: str) -> bool:
        """Load a project and initialize all managers."""
        try:
            self.current_project_path = project_path
            self.current_project_name = project_name
            
            # Initialize managers
            self.current_scene_manager = SceneManager(Path(project_path))
            self.current_character_manager = CharacterManager(Path(project_path))
            self.current_location_manager = LocationManager(Path(project_path) / "pisarz.db")
            self.current_search_manager = SearchManager(Path(project_path) / "pisarz.db")
            
            # Get project data and load entities
            project_data = self.project_manager.get_project_data(Path(project_path))
            project_id = project_data['id']
            
            scenes = self.current_scene_manager.list_scenes()
            characters = self.current_character_manager.get_characters(project_id)
            locations = self.current_location_manager.get_locations(project_id)
            
            managers_dict = {
                'scene_manager': self.current_scene_manager,
                'character_manager': self.current_character_manager,
                'location_manager': self.current_location_manager,
                'search_manager': self.current_search_manager,
                'project_data': project_data,
                'scenes': scenes,
                'characters': characters,
                'locations': locations
            }
            
            self.projectDataLoaded.emit(project_path, project_name, managers_dict)
            self.statusMessage.emit(_("Project: {} ({} scenes)").format(project_name, len(scenes)))
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                        context=f"Loading project: {project_name}",
                                        show_to_user=False)
            self.errorOccurred.emit(_("Error"), _("Failed to load project: {}").format(e))
            return False
    
    def create_project(self, name: str) -> bool:
        """Create a new project."""
        try:
            project_path = self.project_manager.create_project(name)
            self.projectCreated.emit(name)
            self.statusMessage.emit(_("Created project: {}").format(name))
            return True
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                        context=f"Creating project: {name}",
                                        show_to_user=False)
            self.errorOccurred.emit(_("Error"), _("Failed to create project: {}").format(e))
            return False
    
    def get_project_data(self, project_path: Path) -> dict:
        """Get project data by path."""
        return self.project_manager.get_project_data(project_path)
    
    def update_project_properties(self, project_path: Path, properties: dict) -> bool:
        """Update project properties."""
        try:
            success = self.project_manager.update_project_properties(project_path, properties)
            if success:
                self.statusMessage.emit(_("Project properties saved successfully"))
                return True
            else:
                self.errorOccurred.emit(_("Error"), _("Failed to save project properties"))
                return False
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                        context="Updating project properties",
                                        show_to_user=False)
            self.errorOccurred.emit(_("Error"), _("Failed to save project properties: {}").format(e))
            return False
    
    def get_current_managers(self) -> dict:
        """Get current project managers."""
        return {
            'scene_manager': self.current_scene_manager,
            'character_manager': self.current_character_manager,
            'location_manager': self.current_location_manager,
            'search_manager': self.current_search_manager
        }
    
    def get_current_project_info(self) -> tuple:
        """Get current project path and name."""
        return self.current_project_path, self.current_project_name