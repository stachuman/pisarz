"""Qt bridge for project management functionality."""

from PySide6.QtCore import QObject, Signal, Slot, QAbstractListModel, QModelIndex, Qt
from PySide6.QtQml import QmlElement
from typing import List, Dict, Any
from .project import ProjectManager

QML_IMPORT_NAME = "Pisarz"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ProjectManagerBridge(QObject):
    """Qt bridge for ProjectManager to expose functionality to QML."""
    
    projectsChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self._projects_model = ProjectsModel(parent=self)
    
    @Slot(str)
    def createProject(self, name: str):
        """Create a new project and refresh the list."""
        try:
            self.project_manager.create_project(name)
            self.refreshProjects()
        except ValueError as e:
            print(f"Error creating project: {e}")
    
    @Slot()
    def refreshProjects(self):
        """Refresh the projects list."""
        projects = self.project_manager.list_projects()
        self._projects_model.setProjects(projects)
        self.projectsChanged.emit()
    
    @Slot(str, result=bool)
    def openProject(self, project_path: str) -> bool:
        """Open an existing project."""
        return self.project_manager.open_project(project_path)
    
    def getProjectsModel(self):
        """Get the projects model for QML ListView."""
        return self._projects_model


class ProjectsModel(QAbstractListModel):
    """List model for projects to use in QML ListView."""
    
    NameRole = Qt.UserRole + 1
    PathRole = Qt.UserRole + 2
    CreatedAtRole = Qt.UserRole + 3
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects = []
    
    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.PathRole: b"path", 
            self.CreatedAtRole: b"created_at"
        }
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._projects)
    
    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self._projects):
            return None
        
        project = self._projects[index.row()]
        
        if role == self.NameRole:
            return project["name"]
        elif role == self.PathRole:
            return project["path"]
        elif role == self.CreatedAtRole:
            return project["created_at"]
        
        return None
    
    def setProjects(self, projects: List[Dict[str, Any]]):
        """Update the projects list."""
        self.beginResetModel()
        self._projects = projects
        self.endResetModel()