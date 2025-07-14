"""Grid view widget for displaying scenes as tiles with preview."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QGridLayout, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .scene_card import SceneCard
from ..styles.styles import HEADER_COLOR, NEW_SCENE_BUTTON_STYLE


class ScenesGridView(QWidget):
    """Widok siatki scen z kafelkami preview."""
    
    sceneSelected = Signal(int, str)        # id, title
    newSceneRequested = Signal(str)         # title
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenes_data = []
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja widoku siatki scen."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Nagłówek z przyciskiem
        header_layout = QHBoxLayout()
        
        title = QLabel("📝 Sceny")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Przycisk nowa scena
        new_scene_btn = QPushButton("+ Nowa Scena")
        new_scene_btn.clicked.connect(self._on_new_scene_clicked)
        new_scene_btn.setStyleSheet(NEW_SCENE_BUTTON_STYLE)
        new_scene_btn.setFixedSize(120, 35)
        header_layout.addWidget(new_scene_btn)
        
        layout.addLayout(header_layout)
        
        # Separator
        layout.addSpacing(15)
        
        # Instrukcje
        instructions = QLabel("Kliknij na scenę aby ją edytować lub stwórz nową scenę.")
        instructions.setFont(QFont("Arial", 11))
        instructions.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(instructions)
        
        layout.addSpacing(15)
        
        # Siatka scen
        self.scenes_scroll = QScrollArea()
        self.scenes_widget = QWidget()
        self.scenes_grid = QGridLayout(self.scenes_widget)
        self.scenes_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scenes_grid.setSpacing(20)
        
        self.scenes_scroll.setWidget(self.scenes_widget)
        self.scenes_scroll.setWidgetResizable(True)
        layout.addWidget(self.scenes_scroll)
        
    def load_scenes(self, scenes):
        """Załaduj sceny do siatki."""
        self.scenes_data = scenes
        
        # Wyczyść istniejące karty
        for i in reversed(range(self.scenes_grid.count())):
            item = self.scenes_grid.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    
        if not scenes:
            # Brak scen - pokaż komunikat
            no_scenes = QLabel("Nie masz jeszcze żadnych scen.\\nStwórz pierwszą scenę aby rozpocząć pisanie!")
            no_scenes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_scenes.setFont(QFont("Arial", 14))
            no_scenes.setStyleSheet("color: #95a5a6; font-style: italic; padding: 50px;")
            self.scenes_grid.addWidget(no_scenes, 0, 0)
            return
            
        # Dodaj karty scen w siatce (3 kolumny)
        for i, scene in enumerate(scenes):
            row = i // 3
            col = i % 3
            
            card = SceneCard(scene)
            card.sceneSelected.connect(self.sceneSelected.emit)
            self.scenes_grid.addWidget(card, row, col)
            
    def _on_new_scene_clicked(self):
        """Obsługa kliknięcia przycisku nowa scena."""
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, "Nowa Scena", "Tytuł sceny:")
        if ok and title.strip():
            self.newSceneRequested.emit(title.strip())
            
    def refresh_theme(self):
        """Odśwież motywy wszystkich kafelków."""
        for i in range(self.scenes_grid.count()):
            item = self.scenes_grid.itemAt(i)
            if item and hasattr(item.widget(), '_apply_theme_style'):
                item.widget()._apply_theme_style()