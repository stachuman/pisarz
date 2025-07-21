"""Scene management controller for the main application."""

from typing import Optional
from PySide6.QtCore import QObject, Signal

from core.scene import SceneManager
from i18n import _


class AppSceneController(QObject):
    """Handles scene-related operations for the main application."""
    
    # Signals
    sceneOpened = Signal(int, str, str)  # scene_id, scene_title, content
    sceneSaved = Signal(bool)  # is_auto_save
    sceneCreated = Signal(str)  # title
    sceneRenamed = Signal(int, str)  # scene_id, new_title
    scenesRefreshNeeded = Signal()
    statusMessage = Signal(str)  # message
    errorOccurred = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_manager: Optional[SceneManager] = None
        self.current_scene_id: Optional[int] = None
        self.current_project_id: Optional[int] = None
        
    def set_scene_manager(self, scene_manager: SceneManager, project_id: Optional[int] = None):
        """Set the current scene manager and project ID."""
        self.scene_manager = scene_manager
        self.current_project_id = project_id
        
    def auto_save_current_scene(self, content: str) -> bool:
        """Auto-save the current scene before switching."""
        if not self.scene_manager or not self.current_scene_id:
            return True
            
        try:
            success = self.scene_manager.update_scene(self.current_scene_id, content_rtf=content)
            if success:
                self.statusMessage.emit(_("Auto-saved previous scene"))
                return True
            else:
                self.statusMessage.emit(_("Failed to auto-save previous scene"))
                return False
        except Exception as e:
            self.statusMessage.emit(_("Auto-save failed: {}").format(str(e)))
            return False
    
    def open_scene(self, scene_id: int, scene_title: str) -> bool:
        """Open a scene for editing."""
        if not self.scene_manager:
            return False
            
        try:
            self.current_scene_id = scene_id
            scene_data = self.scene_manager.get_scene(scene_id)
            content = scene_data.get("content_rtf", f"<p>{_('Start writing your scene...')}</p>") if scene_data else f"<p>{_('Scene loading error')}</p>"
            
            self.sceneOpened.emit(scene_id, scene_title, content)
            self.statusMessage.emit(_("Editing scene: {}").format(scene_title))
            return True
            
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to open scene: {}").format(e))
            return False
    
    def save_scene_content(self, content: str, is_auto_save: bool = False) -> bool:
        """Save scene content."""
        if not self.scene_manager or not self.current_scene_id:
            return False
            
        try:
            success = self.scene_manager.update_scene(self.current_scene_id, content_rtf=content)
            if success:
                if is_auto_save:
                    self.statusMessage.emit(_("Auto-saved"))
                else:
                    self.statusMessage.emit(_("Scene saved successfully"))
                    self.scenesRefreshNeeded.emit()
                self.sceneSaved.emit(is_auto_save)
                return True
            else:
                if not is_auto_save:
                    self.statusMessage.emit(_("Failed to save scene"))
                    self.errorOccurred.emit(_("Warning"), _("Failed to save scene"))
                return False
        except Exception as e:
            if not is_auto_save:
                self.errorOccurred.emit(_("Error"), _("Failed to save scene: {}").format(e))
            return False
    
    def auto_save_scene_content(self, content: str) -> bool:
        """Handle periodic auto-save."""
        if not self.scene_manager or not self.current_scene_id:
            return False
            
        try:
            success = self.scene_manager.update_scene(self.current_scene_id, content_rtf=content)
            if success:
                self.statusMessage.emit(_("Auto-saved"))
                return True
            return False
        except Exception as e:
            # Silently fail for auto-save
            return False
    
    def create_scene(self, title: str) -> bool:
        """Create a new scene."""
        if not self.scene_manager:
            return False
            
        try:
            scene_id = self.scene_manager.create_scene(title)
            self.sceneCreated.emit(title)
            self.scenesRefreshNeeded.emit()
            self.statusMessage.emit(_("Created scene: {}").format(title))
            return True
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to create scene: {}").format(e))
            return False
    
    def rename_scene(self, scene_id: int, new_title: str) -> bool:
        """Rename a scene."""
        if not self.scene_manager:
            return False
            
        try:
            success = self.scene_manager.update_scene(scene_id, title=new_title)
            if success:
                self.sceneRenamed.emit(scene_id, new_title)
                self.scenesRefreshNeeded.emit()
                self.statusMessage.emit(_("Scene renamed to: {}").format(new_title))
                return True
            else:
                self.errorOccurred.emit(_("Warning"), _("Failed to rename scene"))
                return False
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to rename scene: {}").format(e))
            return False
    
    def get_scenes_list(self) -> list:
        """Get list of scenes."""
        if not self.scene_manager:
            return []
        try:
            if self.current_project_id is None:
                return []
            return self.scene_manager.get_scenes_by_project(self.current_project_id)
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to load scenes: {}").format(e))
            return []
    
    def get_current_scene_id(self) -> Optional[int]:
        """Get current scene ID."""
        return self.current_scene_id