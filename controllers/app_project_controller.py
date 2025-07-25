"""Project management controller for the main application using project_id."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject, Signal

from core.database.project_manager import ProjectManager
from core.database.scene_repository import SceneManager
from core.database.character_repository import CharacterManager
from core.database.location_repository import LocationManager
from core.database.search_repository import SearchManager
from core.error_handler import get_error_handler, ErrorLevel, ErrorCategory
from i18n import _


class AppProjectController(QObject):
    """Handles project-related operations for the main application using project_id."""
    
    # Signals
    projectDataLoaded = Signal(int, str, dict)  # project_id, project_name, managers_dict
    projectCreated = Signal(str)  # project_name
    statusMessage = Signal(str)  # message
    errorOccurred = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.error_handler = get_error_handler()
        self.current_project_id: Optional[int] = None
        self.current_project_name: str = ""
        self.project_description: str = ""
        
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
    
    def load_project(self, project_id: int) -> bool:
        """Load a project by project_id and initialize all managers."""
        try:
            # Get project data
            project_data = self.project_manager.get_project_data(project_id)
            if not project_data:
                self.errorOccurred.emit(_("Error"), _("Project not found"))
                return False
            
            project_name = project_data['name']
            project_description = project_data['description']
            
            # Create managers for this project
            self.current_scene_manager = SceneManager()
            self.current_character_manager = CharacterManager()
            self.current_location_manager = LocationManager()
            self.current_search_manager = SearchManager()
            
            # Store current project info
            self.current_project_id = project_id
            self.current_project_name = project_name
            self.project_description = project_description
            
            # Load data for UI
            scenes = self.current_scene_manager.get_scenes_by_project(project_id)
            characters = self.current_character_manager.get_characters(project_id)
            locations = self.current_location_manager.get_locations(project_id)
            
            # Prepare managers dictionary
            managers_dict = {
                'project_manager': self.project_manager,
                'scene_manager': self.current_scene_manager,
                'character_manager': self.current_character_manager,
                'location_manager': self.current_location_manager,
                'search_manager': self.current_search_manager,
                'scenes': scenes,
                'characters': characters,
                'locations': locations
            }
            
            self.statusMessage.emit(_("Loaded project: {}").format(project_name))
            self.projectDataLoaded.emit(project_id, project_name, managers_dict)
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE, 
                                        context=f"Loading project ID {project_id}",
                                        show_to_user=True)
            self.errorOccurred.emit(_("Error"), _("Failed to load project: {}").format(e))
            return False
    
    def load_project_by_name(self, project_name: str) -> bool:
        """Load a project by name."""
        try:
            project_id = self.project_manager.get_project_id_by_name(project_name)
            if project_id is None:
                self.errorOccurred.emit(_("Error"), _("Project '{}' not found").format(project_name))
                return False
            
            return self.load_project(project_id)
            
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Loading project by name '{project_name}'",
                                        show_to_user=False)
            self.errorOccurred.emit(_("Error"), _("Failed to load project: {}").format(e))
            return False
    
    def create_project(self, project_name: str, **kwargs) -> bool:
        """Create a new project."""
        try:
            project_id = self.project_manager.create_project(project_name, **kwargs)
            if project_id:
                self.statusMessage.emit(_("Created project: {}").format(project_name))
                self.projectCreated.emit(project_name)
                
                # Automatically load the newly created project
                return self.load_project(project_id)
            else:
                self.errorOccurred.emit(_("Error"), _("Failed to create project"))
                return False
                
        except ValueError as e:
            # Handle validation errors (like duplicate names)
            self.errorOccurred.emit(_("Error"), str(e))
            return False
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Creating project '{project_name}'",
                                        show_to_user=True)
            self.errorOccurred.emit(_("Error"), _("Failed to create project: {}").format(e))
            return False
    
    def get_current_project_info(self) -> tuple[Optional[int], str]:
        """Get current project ID and name."""
        return self.current_project_id, self.current_project_name
    
    def get_project_id(self) -> Optional[int]:
        """Get current project ID."""
        return self.current_project_id
    
    def get_project_name(self) -> str:
        """Get current project name."""
        return self.current_project_name
    
    def get_project_data(self, project_id: int) -> dict:
        """Get project data by project_id."""
        return self.project_manager.get_project_data(project_id)
    
    def get_current_managers(self) -> dict:
        """Get dictionary of current managers."""
        return {
            'project_controller': self,
            'project_manager': self.project_manager,
            'scene_manager': self.current_scene_manager,
            'character_manager': self.current_character_manager,
            'location_manager': self.current_location_manager,
            'search_manager': self.current_search_manager
        }
    
    def has_current_project(self) -> bool:
        """Check if there is a currently loaded project."""
        return self.current_project_id is not None
    
    def update_project_properties(self, properties: dict) -> bool:
        """Update current project properties."""
        if not self.current_project_id:
            self.errorOccurred.emit(_("Error"), _("No project loaded"))
            return False
        
        try:
            success = self.project_manager.update_project_properties(
                self.current_project_id, properties
            )
            
            if success:
                # Update local project name if it was changed
                if 'name' in properties:
                    self.current_project_name = properties['name']
                
                self.statusMessage.emit(_("Project properties updated"))
            else:
                self.errorOccurred.emit(_("Error"), _("Failed to update project properties"))
            
            return success
            
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Updating properties for project ID {self.current_project_id}",
                                        show_to_user=False)
            self.errorOccurred.emit(_("Error"), _("Failed to update project: {}").format(e))
            return False
    
    def delete_current_project(self) -> bool:
        """Delete the currently loaded project."""
        if not self.current_project_id:
            self.errorOccurred.emit(_("Error"), _("No project loaded"))
            return False
        
        try:
            project_name = self.current_project_name
            success = self.project_manager.delete_project(self.current_project_id)
            
            if success:
                # Clear current project
                self.current_project_id = None
                self.current_project_name = ""
                #self.project_description = ""
                self.current_scene_manager = None
                self.current_character_manager = None
                self.current_location_manager = None
                self.current_search_manager = None
                
                self.statusMessage.emit(_("Deleted project: {}").format(project_name))
            else:
                self.errorOccurred.emit(_("Error"), _("Failed to delete project"))
            
            return success
            
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Deleting project ID {self.current_project_id}",
                                        show_to_user=False)
            self.errorOccurred.emit(_("Error"), _("Failed to delete project: {}").format(e))
            return False
    
    def get_project_stats(self) -> dict:
        """Get statistics for current project."""
        if not self.current_project_id:
            return {}
        
        try:
            return self.project_manager.get_project_stats(self.current_project_id)
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting stats for project ID {self.current_project_id}",
                                        show_to_user=False)
            return {}
    
    def close_current_project(self):
        """Close the current project without deleting it."""
        self.current_project_id = None
        self.current_project_name = ""
        #self.project_description = ""
        self.current_scene_manager = None
        self.current_character_manager = None
        self.current_location_manager = None
        self.current_search_manager = None