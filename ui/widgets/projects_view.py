"""Projects overview widget for initial app view."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QPushButton, QInputDialog, QGridLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .project_card import ProjectCard
from ..styles.styles import HEADER_COLOR, NEW_PROJECT_BUTTON_STYLE, INFO_TEXT_COLOR
from i18n import _


class ProjectsView(QWidget):
    """Widok z listą projektów - główny ekran aplikacji."""
    
    projectSelected = Signal(str, str)      # path, name
    newProjectRequested = Signal(str)       # name
    settingsRequested = Signal()            # settings dialog
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja widoku projektów."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        
        title = QLabel(_("Your Projects"))
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Przycisk ustawienia
        settings_btn = QPushButton(_("Settings"))
        settings_btn.clicked.connect(self._on_settings_clicked)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        settings_btn.setFixedSize(120, 40)
        header_layout.addWidget(settings_btn)
        
        # Przycisk nowy projekt
        new_project_btn = QPushButton(_("New Project"))
        new_project_btn.clicked.connect(self._on_new_project_clicked)
        new_project_btn.setStyleSheet(NEW_PROJECT_BUTTON_STYLE)
        new_project_btn.setFixedSize(150, 40)
        header_layout.addWidget(new_project_btn)
        
        layout.addLayout(header_layout)
        
        # Separator
        layout.addSpacing(30)
        
        # Instrukcje
        instructions = QLabel(_("Select existing project or create new one to start writing.") + "\n" + 
                            _("Each project contains scenes, characters and locations to help you organize your story."))
        instructions.setFont(QFont("Arial", 12))
        instructions.setStyleSheet(INFO_TEXT_COLOR)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        layout.addSpacing(25)
        
        # Siatka projektów
        self.projects_scroll = QScrollArea()
        self.projects_widget = QWidget()
        self.projects_grid = QGridLayout(self.projects_widget)
        self.projects_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.projects_grid.setSpacing(25)
        
        self.projects_scroll.setWidget(self.projects_widget)
        self.projects_scroll.setWidgetResizable(True)
        layout.addWidget(self.projects_scroll)
        
    def load_projects(self, projects):
        """Załaduj projekty do siatki."""
        # Wyczyść istniejące karty
        for i in reversed(range(self.projects_grid.count())):
            item = self.projects_grid.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    
        if not projects:
            # Brak projektów - pokaż komunikat
            no_projects = QLabel(_("You don't have any projects yet.\\nCreate your first project to start!"))
            no_projects.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_projects.setFont(QFont("Arial", 14))
            no_projects.setStyleSheet("color: #95a5a6; font-style: italic; padding: 50px;")
            self.projects_grid.addWidget(no_projects, 0, 0)
            return
            
        # Dodaj karty projektów w siatce (3 kolumny)
        for i, project in enumerate(projects):
            row = i // 3
            col = i % 3
            
            card = ProjectCard(project)
            card.projectSelected.connect(self.projectSelected.emit)
            self.projects_grid.addWidget(card, row, col)
            
    def _on_new_project_clicked(self):
        """Obsługa kliknięcia przycisku nowy projekt."""
        name, ok = QInputDialog.getText(self, _("New Project"), _("Project name:"))
        if ok and name.strip():
            self.newProjectRequested.emit(name.strip())
            
    def _on_settings_clicked(self):
        """Obsługa kliknięcia przycisku ustawienia."""
        self.settingsRequested.emit()
        
    def refresh_theme(self):
        """Odśwież motywy wszystkich kafelków."""
        for i in range(self.projects_grid.count()):
            item = self.projects_grid.itemAt(i)
            if item and hasattr(item.widget(), '_apply_theme_style'):
                item.widget()._apply_theme_style()