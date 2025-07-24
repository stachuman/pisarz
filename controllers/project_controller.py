"""Project controller using project_id as primary key."""

from typing import Optional
from PySide6.QtCore import QObject, Signal

from core.database.project_manager import ProjectManager
from core.database.scene_repository import SceneManager
from core.database.character_repository import CharacterManager
from core.database.location_repository import LocationManager
from core.database.search_repository import SearchManager
from i18n import _


class ProjectController(QObject):
    """Handles project operations using project_id as primary key."""
    
    # Updated signals to use project_id
    projectLoaded = Signal(int, str)  # project_id, project_name
    projectListLoaded = Signal(list)  # projects list
    projectCreated = Signal(str)  # project_name
    error = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.current_project_id: Optional[int] = None
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
    
    def select_project(self, project_id: int, project_name: str):
        """Select and load a project by project_id."""
        self.current_project_id = project_id
        self.current_project_name = project_name
        
        try:
            # Initialize managers for the selected project
            self.current_scene_manager = SceneManager()
            self.current_character_manager = CharacterManager()
            self.current_location_manager = LocationManager()
            self.current_search_manager = SearchManager()
            
            self.projectLoaded.emit(project_id, project_name)
            
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to load project: {}").format(e))
    
    def select_project_by_name(self, project_name: str):
        """Select and load a project by name."""
        try:
            project_id = self.project_manager.get_project_id_by_name(project_name)
            if project_id is None:
                self.error.emit(_("Error"), _("Project not found: {}").format(project_name))
                return
            
            self.select_project(project_id, project_name)
            
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to load project: {}").format(e))
    
    def create_new_project(self, project_name: str, **kwargs):
        """Create a new project."""
        try:
            project_id = self.project_manager.create_project(project_name, **kwargs)
            if project_id:
                self.projectCreated.emit(project_name)
                # Auto-select the newly created project
                self.select_project(project_id, project_name)
            else:
                self.error.emit(_("Error"), _("Failed to create project"))
                
        except ValueError as e:
            # Handle validation errors (like duplicate names)
            self.error.emit(_("Error"), str(e))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to create project: {}").format(e))
    
    def get_current_project_info(self) -> tuple[Optional[int], str]:
        """Get current project ID and name."""
        return self.current_project_id, self.current_project_name
    
    def get_project_id(self) -> Optional[int]:
        """Get current project ID."""
        return self.current_project_id
    
    def get_project_name(self) -> str:
        """Get current project name."""
        return self.current_project_name
    
    def has_current_project(self) -> bool:
        """Check if there is a currently loaded project."""
        return self.current_project_id is not None
    
    def get_project_data(self) -> Optional[dict]:
        """Get current project data."""
        if not self.current_project_id:
            return None
        
        try:
            return self.project_manager.get_project_data(self.current_project_id)
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to get project data: {}").format(e))
            return None
    
    def update_project_properties(self, properties: dict) -> bool:
        """Update current project properties."""
        if not self.current_project_id:
            self.error.emit(_("Error"), _("No project loaded"))
            return False
        
        try:
            success = self.project_manager.update_project_properties(
                self.current_project_id, properties
            )
            
            if success:
                # Update local project name if it was changed
                if 'name' in properties:
                    self.current_project_name = properties['name']
            
            return success
            
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to update project: {}").format(e))
            return False
    
    def close_current_project(self):
        """Close the current project."""
        self.current_project_id = None
        self.current_project_name = ""
        self.current_scene_manager = None
        self.current_character_manager = None
        self.current_location_manager = None
        self.current_search_manager = None