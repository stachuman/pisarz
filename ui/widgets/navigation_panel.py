"""Navigation panel widget containing projects and scenes."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                              QPushButton, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .project_card import ProjectCard
from .scene_card import SceneCard
from ..styles.styles import (HEADER_COLOR, NEW_PROJECT_BUTTON_STYLE, 
                           NEW_SCENE_BUTTON_STYLE, MUTED_TEXT_COLOR)
from i18n import _


class NavigationPanel(QWidget):
    """Panel nawigacji z projektami i scenami."""
    
    projectSelected = Signal(str, str)  # path, name
    sceneSelected = Signal(int, str)    # id, title
    newProjectRequested = Signal(str)   # name
    newSceneRequested = Signal(str)     # title
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja panelu nawigacji."""
        layout = QVBoxLayout(self)
        
        # === PROJEKTY ===
        projects_header = QLabel("PROJEKTY")
        projects_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        projects_header.setStyleSheet(HEADER_COLOR)
        layout.addWidget(projects_header)
        
        # Lista projektów
        self.projects_scroll = QScrollArea()
        self.projects_widget = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_widget)
        self.projects_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.projects_scroll.setWidget(self.projects_widget)
        self.projects_scroll.setWidgetResizable(True)
        self.projects_scroll.setMaximumHeight(300)
        layout.addWidget(self.projects_scroll)
        
        # Przycisk nowy projekt
        new_project_btn = QPushButton("+ Nowy Projekt")
        new_project_btn.clicked.connect(self._on_new_project_clicked)
        new_project_btn.setStyleSheet(NEW_PROJECT_BUTTON_STYLE)
        layout.addWidget(new_project_btn)
        
        # === SCENY ===
        scenes_header = QLabel("SCENY")
        scenes_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        scenes_header.setStyleSheet(HEADER_COLOR)
        layout.addWidget(scenes_header)
        
        # Lista scen
        self.scenes_scroll = QScrollArea()
        self.scenes_widget = QWidget()
        self.scenes_layout = QVBoxLayout(self.scenes_widget)
        self.scenes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scenes_scroll.setWidget(self.scenes_widget)
        self.scenes_scroll.setWidgetResizable(True)
        layout.addWidget(self.scenes_scroll)
        
        # Przycisk nowa scena
        self.new_scene_btn = QPushButton("+ Nowa Scena")
        self.new_scene_btn.clicked.connect(self._on_new_scene_clicked)
        self.new_scene_btn.setEnabled(False)
        self.new_scene_btn.setStyleSheet(NEW_SCENE_BUTTON_STYLE)
        layout.addWidget(self.new_scene_btn)
        
    def load_projects(self, projects):
        """Załaduj projekty do panelu nawigacji."""
        # Wyczyść istniejące karty
        for i in reversed(range(self.projects_layout.count())):
            self.projects_layout.itemAt(i).widget().setParent(None)
            
        for project in projects:
            card = ProjectCard(project)
            card.projectSelected.connect(self.projectSelected.emit)
            self.projects_layout.addWidget(card)
            
        if not projects:
            no_projects_label = QLabel(_("No projects\nCreate a new project to get started"))
            no_projects_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_projects_label.setStyleSheet(MUTED_TEXT_COLOR)
            self.projects_layout.addWidget(no_projects_label)
            
    def load_scenes(self, scenes):
        """Załaduj sceny dla wybranego projektu."""
        # Wyczyść istniejące karty scen
        for i in reversed(range(self.scenes_layout.count())):
            self.scenes_layout.itemAt(i).widget().setParent(None)
            
        for scene in scenes:
            card = SceneCard(scene)
            card.sceneSelected.connect(self.sceneSelected.emit)
            self.scenes_layout.addWidget(card)
            
        self.new_scene_btn.setEnabled(True)
        
        if not scenes:
            no_scenes_label = QLabel(_("No scenes\nCreate a new scene to start writing"))
            no_scenes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_scenes_label.setStyleSheet(MUTED_TEXT_COLOR)
            self.scenes_layout.addWidget(no_scenes_label)
            
    def clear_scenes(self):
        """Wyczyść listę scen."""
        for i in reversed(range(self.scenes_layout.count())):
            self.scenes_layout.itemAt(i).widget().setParent(None)
        self.new_scene_btn.setEnabled(False)
        
    def _on_new_project_clicked(self):
        """Obsługa kliknięcia przycisku nowy projekt."""
        name, ok = QInputDialog.getText(self, "Nowy Projekt", "Nazwa projektu:")
        if ok and name.strip():
            self.newProjectRequested.emit(name.strip())
            
    def _on_new_scene_clicked(self):
        """Obsługa kliknięcia przycisku nowa scena."""
        title, ok = QInputDialog.getText(self, _("New Scene"), _("Scene title:"))
        if ok and title.strip():
            self.newSceneRequested.emit(title.strip())