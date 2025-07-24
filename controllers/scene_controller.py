"""Scene controller for managing scene-related operations."""

from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from i18n import _


class SceneController(QObject):
    """Controller for managing scene operations."""
    
    # Signals
    sceneSelected = Signal(int, str)  # scene_id, scene_title
    sceneLoaded = Signal(int, str)  # scene_id, content
    sceneSaved = Signal(int)  # scene_id
    sceneCreated = Signal(int, str)  # scene_id, title
    sceneRenamed = Signal(int, str)  # scene_id, new_title
    scenesListUpdated = Signal(list)  # scenes list
    error = Signal(str, str)  # title, message
    statusMessage = Signal(str)  # message
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.current_scene_id = None
        
    def select_scene(self, scene_id: int, scene_title: str):
        """Select and load a scene."""
        scene_manager = self.project_controller.current_scene_manager
        if not scene_manager:
            return
            
        self.current_scene_id = scene_id
        
        try:
            scene_data = scene_manager.get_scene(scene_id)
            content = scene_data.get("content_rtf", f"<p>{_('Start writing your scene...')}</p>") if scene_data else f"<p>{_('Scene loading error')}</p>"
            
            self.sceneLoaded.emit(scene_id, content)
            self.statusMessage.emit(_("Editing scene: {}").format(scene_title))
            
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to open scene: {}").format(e))
    
    def save_scene_content(self, content: str):
        """Save scene content."""
        scene_manager = self.project_controller.current_scene_manager
        if not scene_manager or not self.current_scene_id:
            return
            
        try:
            success = scene_manager.update_scene(self.current_scene_id, content_rtf=content)
            if success:
                self.sceneSaved.emit(self.current_scene_id)
                self.statusMessage.emit(_("Scene saved successfully"))
                self._refresh_scenes_data()
            else:
                self.statusMessage.emit(_("Failed to save scene"))
                self.error.emit(_("Warning"), _("Failed to save scene"))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to save scene: {}").format(e))
    
    def create_new_scene(self, title: str):
        """Create a new scene."""
        scene_manager = self.project_controller.current_scene_manager
        if not scene_manager:
            return
            
        try:
            project_id = self.project_controller.get_project_id()
            if project_id is None:
                return
            scene_id = scene_manager.create_scene(project_id, title)
            if scene_id:
                self.sceneCreated.emit(scene_id, title)
                self._refresh_scenes_data()
            else:
                self.error.emit(_("Error"), _("Failed to create scene"))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to create scene: {}").format(e))
    
    def rename_scene(self, scene_id: int, new_title: str):
        """Rename a scene."""
        scene_manager = self.project_controller.current_scene_manager
        if not scene_manager:
            return
            
        try:
            success = scene_manager.update_scene(scene_id, title=new_title)
            if success:
                self.sceneRenamed.emit(scene_id, new_title)
                self._refresh_scenes_data()
            else:
                self.error.emit(_("Error"), _("Failed to rename scene"))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to rename scene: {}").format(e))
    
    def get_scenes_list(self) -> list:
        """Get the list of scenes."""
        scene_manager = self.project_controller.current_scene_manager
        if not scene_manager:
            return []
            
        try:
            project_id = self.project_controller.get_project_id()
            if project_id is None:
                return []
            return scene_manager.get_scenes_by_project(project_id)
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to load scenes: {}").format(e))
            return []
    
    def _refresh_scenes_data(self):
        """Refresh scenes data."""
        try:
            scenes = self.get_scenes_list()
            self.scenesListUpdated.emit(scenes)
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to refresh scenes: {}").format(e))
    
    def get_current_scene_id(self) -> Optional[int]:
        """Get current scene ID."""
        return self.current_scene_id