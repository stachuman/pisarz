"""Qt bridge for scene management functionality."""

from PySide6.QtCore import QObject, Signal, Slot, QAbstractListModel, QModelIndex, Qt
from PySide6.QtQml import QmlElement
from pathlib import Path
from typing import List, Dict, Any
from .scene import SceneManager

QML_IMPORT_NAME = "Pisarz"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class SceneManagerBridge(QObject):
    """Qt bridge for SceneManager to expose functionality to QML."""
    
    scenesChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_manager = None
        self._scenes_model = ScenesModel(parent=self)
    
    @Slot(str)
    def setProjectPath(self, project_path: str):
        """Set the current project path."""
        try:
            self.scene_manager = SceneManager(Path(project_path))
        except Exception as e:
            print(f"Error setting project path: {e}")
            self.scene_manager = None
    
    @Slot(str)
    def createScene(self, title: str):
        """Create a new scene and refresh the list."""
        if not self.scene_manager:
            print("No project selected")
            return
        
        try:
            scene_id = self.scene_manager.create_scene(title)
            print(f"Created scene with ID: {scene_id}")
            self.refreshScenes()
        except ValueError as e:
            print(f"Error creating scene: {e}")
    
    @Slot()
    def refreshScenes(self):
        """Refresh the scenes list."""
        if not self.scene_manager:
            self._scenes_model.setScenes([])
            return
        
        try:
            scenes = self.scene_manager.list_scenes()
            self._scenes_model.setScenes(scenes)
            self.scenesChanged.emit()
        except Exception as e:
            print(f"Error refreshing scenes: {e}")
            self._scenes_model.setScenes([])
    
    @Slot(int, str, result=bool)
    def updateScene(self, scene_id: int, title: str) -> bool:
        """Update scene title."""
        if not self.scene_manager:
            return False
        
        try:
            result = self.scene_manager.update_scene(scene_id, title=title)
            if result:
                self.refreshScenes()
            return result
        except Exception as e:
            print(f"Error updating scene: {e}")
            return False
    
    @Slot(int, result=bool)
    def deleteScene(self, scene_id: int) -> bool:
        """Delete a scene."""
        if not self.scene_manager:
            return False
        
        try:
            result = self.scene_manager.delete_scene(scene_id)
            if result:
                self.refreshScenes()
            return result
        except Exception as e:
            print(f"Error deleting scene: {e}")
            return False
    
    @Slot(int, result='QVariant')
    def getScene(self, scene_id: int):
        """Get scene data for editing."""
        if not self.scene_manager:
            return None
        
        try:
            scene_data = self.scene_manager.get_scene(scene_id)
            return scene_data
        except Exception as e:
            print(f"Error getting scene: {e}")
            return None
    
    @Slot(int, str, result=bool)
    def updateSceneContent(self, scene_id: int, content_rtf: str) -> bool:
        """Update scene content."""
        if not self.scene_manager:
            return False
        
        try:
            result = self.scene_manager.update_scene(scene_id, content_rtf=content_rtf)
            if result:
                self.refreshScenes()
            return result
        except Exception as e:
            print(f"Error updating scene content: {e}")
            return False
    
    def getScenesModel(self):
        """Get the scenes model for QML ListView."""
        return self._scenes_model


class ScenesModel(QAbstractListModel):
    """List model for scenes to use in QML ListView/GridView."""
    
    IdRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    ContentRole = Qt.UserRole + 3
    OrderRole = Qt.UserRole + 4
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scenes = []
    
    def roleNames(self):
        return {
            self.IdRole: b"id",
            self.TitleRole: b"title",
            self.ContentRole: b"content_rtf",
            self.OrderRole: b"ord"
        }
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._scenes)
    
    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self._scenes):
            return None
        
        scene = self._scenes[index.row()]
        
        if role == self.IdRole:
            return scene["id"]
        elif role == self.TitleRole:
            return scene["title"]
        elif role == self.ContentRole:
            return scene["content_rtf"]
        elif role == self.OrderRole:
            return scene["ord"]
        
        return None
    
    def setScenes(self, scenes: List[Dict[str, Any]]):
        """Update the scenes list."""
        self.beginResetModel()
        self._scenes = scenes
        self.endResetModel()
