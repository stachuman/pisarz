"""Projects overview widget for initial app view."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QPushButton, QInputDialog, QGridLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .project_card import ProjectCard
from ..styles.styles import HEADER_COLOR, INFO_TEXT_COLOR
from ..base.enhanced_theme_manager import EnhancedThemeManager
from i18n import _


class ProjectsView(QWidget):
    """Widok z listą projektów - główny ekran aplikacji."""
    
    projectSelected = Signal(int, str)      # project_id, name
    newProjectRequested = Signal(str)       # name
    settingsRequested = Signal()            # settings dialog
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = EnhancedThemeManager()
        self.setup_ui()
        self.apply_theme()
        
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
        self.settings_btn = QPushButton(_("Settings"))
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        self.settings_btn.setFixedSize(120, 40)
        header_layout.addWidget(self.settings_btn)
        
        # Przycisk nowy projekt
        self.new_project_btn = QPushButton(_("New Project"))
        self.new_project_btn.clicked.connect(self._on_new_project_clicked)
        self.new_project_btn.setFixedSize(150, 40)
        header_layout.addWidget(self.new_project_btn)
        
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
        
    def apply_theme(self):
        """Apply standard theme styling to buttons."""
        colors = self.theme_manager.get_theme_colors()
        
        # Primary button style for new project
        primary_button_style = f"""
            QPushButton {{
                background-color: {colors["accent"]};
                color: white;
                border: 1px solid {colors["accent"]};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors["accent_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["accent_pressed"]};
            }}
        """
        
        # Secondary button style for settings
        secondary_button_style = f"""
            QPushButton {{
                background-color: {colors["secondary_button"]};
                color: white;
                border: 1px solid {colors["secondary_button"]};
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 11px;
                margin-right: 10px;
            }}
            QPushButton:hover {{
                background-color: {colors["secondary_button_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["secondary_button_pressed"]};
            }}
        """
        
        self.new_project_btn.setStyleSheet(primary_button_style)
        self.settings_btn.setStyleSheet(secondary_button_style)
    
    def refresh_theme(self):
        """Odśwież motywy wszystkich kafelków."""
        self.apply_theme()
        for i in range(self.projects_grid.count()):
            item = self.projects_grid.itemAt(i)
            if item and hasattr(item.widget(), '_apply_theme_style'):
                item.widget()._apply_theme_style()