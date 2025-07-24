"""Location management controller for the main application."""

from pathlib import Path
from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal

from core.location import LocationManager
from ui.widgets.location_editor_dialog import LocationEditorDialog
from i18n import _


class AppLocationController(QObject):
    """Handles location-related operations for the main application."""
    
    # Signals
    locationEditorOpened = Signal(int, str)  # location_id, location_name
    locationCreated = Signal(str)  # name
    locationUpdated = Signal(int, str)  # location_id, name
    locationsRefreshNeeded = Signal()
    statusMessage = Signal(str)  # message
    errorOccurred = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.location_manager: Optional[LocationManager] = None
        self.scene_manager = None
        self.current_project_id: Optional[int] = None
        self.location_editor_windows: Dict[int, LocationEditorDialog] = {}
        
    def set_manager(self, location_manager: LocationManager, project_id: int):
        """Set the current location manager and project ID."""
        self.location_manager = location_manager
        self.current_project_id = project_id
        
    def set_managers(self, location_manager: LocationManager, scene_manager, project_id: int):
        """Set the current location manager, scene manager and project ID."""
        self.location_manager = location_manager
        self.scene_manager = scene_manager
        self.current_project_id = project_id
        
    def open_location_editor(self, location_id: int, location_name: str, project_manager) -> bool:
        """Open location editor dialog."""
        if not self.location_manager or not self.current_project_id:
            return False
            
        try:
            # Check if window is already open for this location
            if location_id in self.location_editor_windows:
                window = self.location_editor_windows[location_id]
                window.raise_()
                window.activateWindow()
                return True
            
            # Get location data as dataclass object for the dialog
            location = self.location_manager.get_location_object(location_id)
            if not location:
                self.errorOccurred.emit(_("Warning"), _("Location not found"))
                return False
            
            # Get linked scenes with roles for the location
            location_data = self.location_manager.get_location(location_id)  # Get as dict
            if location_data:
                linked_scenes = self.location_manager.get_location_scenes(location_id)
                # Convert scenes to the format expected by the dialog
                scenes_list = []
                for scene_dict, role in linked_scenes:
                    scene_data = scene_dict.copy()
                    scene_data['role'] = role
                    scene_data['importance'] = 3  # Default importance
                    scenes_list.append(scene_data)
                location_data['scenes'] = scenes_list
            
            # Get project data
            project_data = project_manager.get_project_data(self.current_project_id)
            if not project_data:
                return False
            
            # Get all scenes in project for linking
            all_scenes = self.scene_manager.get_scenes_by_project(project_data['id']) if self.scene_manager else []
            
            # Create and show dialog
            dialog = LocationEditorDialog(
                self.location_manager, 
                project_data['id'], 
                location=location,
                scenes_data=all_scenes,
                parent=self.parent()
            )
            
            # Set the location data with linked scenes
            if location_data and 'scenes' in location_data:
                dialog.linked_scenes = location_data['scenes']
                dialog.update_scenes_list()
            
            # Connect signals
            dialog.locationSaved.connect(self._on_location_saved)
            dialog.sceneLinked.connect(self._on_scene_linked)
            dialog.sceneUnlinked.connect(self._on_scene_unlinked)
            
            # Store reference and handle window closing
            self.location_editor_windows[location_id] = dialog
            dialog.finished.connect(lambda: self.location_editor_windows.pop(location_id, None))
            dialog.accepted.connect(lambda: self._on_location_updated(location_id, location_name))
            
            dialog.show()
            self.locationEditorOpened.emit(location_id, location_name)
            return True
            
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to open location: {}").format(e))
            return False
    
    def create_location(self, name: str, project_manager) -> bool:
        """Create a new location."""
        if not self.location_manager or not self.current_project_id:
            return False
            
        try:
            # Get project ID
            project_data = project_manager.get_project_data(self.current_project_id)
            if not project_data:
                return False
            
            # If name is empty, open dialog for new location
            if not name or name.strip() == "":
                # Get all scenes in project for linking
                all_scenes = self.scene_manager.get_scenes_by_project(project_data['id']) if self.scene_manager else []
                
                dialog = LocationEditorDialog(
                    self.location_manager, 
                    project_data['id'],
                    scenes_data=all_scenes,
                    parent=self.parent()
                )
                
                # For new locations, we don't need to track by ID since ID doesn't exist yet
                dialog.accepted.connect(lambda: (
                    self.locationsRefreshNeeded.emit(),
                    self.statusMessage.emit(_("Created new location"))
                ))
                
                dialog.show()
                return True
            else:
                # Create location with the provided name
                location_id = self.location_manager.create_location(self.current_project_id, name)
                
                if location_id:
                    self.locationCreated.emit(name)
                    self.locationsRefreshNeeded.emit()
                    self.statusMessage.emit(_("Created location: {}").format(name))
                    return True
                else:
                    self.errorOccurred.emit(_("Warning"), _("Failed to create location"))
                    return False
                    
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to create location: {}").format(e))
            return False
    
    def _on_location_updated(self, location_id: int, location_name: str):
        """Handle location updated signal."""
        self.locationUpdated.emit(location_id, location_name)
        self.locationsRefreshNeeded.emit()
        self.statusMessage.emit(_("Location updated: {}").format(location_name))
    
    def _on_location_saved(self, location_data: dict):
        """Handle location saved signal."""
        self.locationsRefreshNeeded.emit()
        location_name = location_data.get('name', _('Location'))
        if 'id' in location_data:
            self.statusMessage.emit(_("Location updated: {}").format(location_name))
        else:
            self.statusMessage.emit(_("Location created: {}").format(location_name))
    
    def _on_scene_linked(self, location_id: int, scene_id: int, role: str, importance: int):
        """Handle scene linked to location."""
        try:
            # Link the scene to the location in the database
            if self.location_manager:
                success = self.location_manager.link_location_to_scene(location_id, scene_id, role)
                if success:
                    self.statusMessage.emit(_("Scene linked to location"))
                else:
                    self.errorOccurred.emit(_("Error"), _("Failed to link scene to location"))
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to link scene: {}").format(e))
    
    def _on_scene_unlinked(self, location_id: int, scene_id: int):
        """Handle scene unlinked from location."""
        try:
            # Unlink the scene from the location in the database
            if self.location_manager:
                success = self.location_manager.unlink_location_from_scene(location_id, scene_id)
                if success:
                    self.statusMessage.emit(_("Scene unlinked from location"))
                else:
                    self.errorOccurred.emit(_("Error"), _("Failed to unlink scene from location"))
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to unlink scene: {}").format(e))
    
    def get_locations_list(self, project_id: int) -> list:
        """Get list of locations for project."""
        if not self.location_manager:
            return []
        try:
            return self.location_manager.get_locations(project_id)
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to load locations: {}").format(e))
            return []
    
    def get_location(self, location_id: int):
        """Get location by ID."""
        if not self.location_manager:
            return None
        try:
            return self.location_manager.get_location(location_id)
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to get location: {}").format(e))
            return None