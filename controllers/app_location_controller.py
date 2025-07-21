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
        self.current_project_path: Optional[str] = None
        self.location_editor_windows: Dict[int, LocationEditorDialog] = {}
        
    def set_manager(self, location_manager: LocationManager, project_path: str):
        """Set the current location manager and project path."""
        self.location_manager = location_manager
        self.current_project_path = project_path
        
    def open_location_editor(self, location_id: int, location_name: str, project_manager) -> bool:
        """Open location editor dialog."""
        if not self.location_manager or not self.current_project_path:
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
            
            # Get project data
            project_data = project_manager.get_project_data(Path(self.current_project_path))
            if not project_data:
                return False
            
            # Create and show dialog
            dialog = LocationEditorDialog(
                self.location_manager, 
                project_data['id'], 
                location=location,
                parent=self.parent()
            )
            
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
        if not self.location_manager or not self.current_project_path:
            return False
            
        try:
            # Get project ID
            project_data = project_manager.get_project_data(Path(self.current_project_path))
            if not project_data:
                return False
            
            # If name is empty, open dialog for new location
            if not name or name.strip() == "":
                dialog = LocationEditorDialog(
                    self.location_manager, 
                    project_data['id'],
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
                location_id = self.location_manager.create_location(project_data['id'], name)
                
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