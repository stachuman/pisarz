"""Grid view widget for displaying scenes as tiles with preview."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QGridLayout, QPushButton, QFrame,
                              QLineEdit, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .scene_card import SceneCard
from ..styles.styles import HEADER_COLOR, NEW_SCENE_BUTTON_STYLE


class ScenesGridView(QWidget):
    """Widok siatki scen z kafelkami preview."""
    
    sceneSelected = Signal(int, str)        # id, title
    newSceneRequested = Signal(str)         # title
    sceneRenameRequested = Signal(int, str) # id, new_title
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenes_data = []
        self.filtered_scenes = []
        self.character_manager = None
        self.location_manager = None
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
        
        # Filter section
        filter_layout = QHBoxLayout()
        
        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search scenes...")
        self.search_field.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_field)
        
        # Character filter
        self.character_filter = QComboBox()
        self.character_filter.addItem("All Characters", None)
        self.character_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Character:"))
        filter_layout.addWidget(self.character_filter)
        
        # Location filter
        self.location_filter = QComboBox()
        self.location_filter.addItem("All Locations", None)
        self.location_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Location:"))
        filter_layout.addWidget(self.location_filter)
        
        layout.addLayout(filter_layout)
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
    
    def set_managers(self, character_manager, location_manager):
        """Set the character and location managers."""
        self.character_manager = character_manager
        self.location_manager = location_manager
        self._populate_filters()
        
    def load_scenes(self, scenes):
        """Załaduj sceny do siatki."""
        self.scenes_data = scenes
        self.filtered_scenes = scenes[:]  # Initially show all scenes
        self._populate_filters()
        self._update_scene_display()
        
    def _update_scene_display(self):
        """Update the scene display with current filtered scenes."""
        # Wyczyść istniejące karty
        for i in reversed(range(self.scenes_grid.count())):
            item = self.scenes_grid.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    
        if not self.filtered_scenes:
            # Brak scen - pokaż komunikat
            no_scenes = QLabel("Nie znaleziono scen spełniających kryteria.\\nSpróbuj zmienić filtry.")
            no_scenes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_scenes.setFont(QFont("Arial", 14))
            no_scenes.setStyleSheet("color: #95a5a6; font-style: italic; padding: 50px;")
            self.scenes_grid.addWidget(no_scenes, 0, 0)
            return
            
        # Dodaj karty scen w siatce (3 kolumny)
        for i, scene in enumerate(self.filtered_scenes):
            row = i // 3
            col = i % 3
            
            card = SceneCard(scene, self.character_manager, self.location_manager)
            card.sceneSelected.connect(self.sceneSelected.emit)
            card.sceneRenameRequested.connect(self.sceneRenameRequested.emit)
            self.scenes_grid.addWidget(card, row, col)
            
    def _on_new_scene_clicked(self):
        """Obsługa kliknięcia przycisku nowa scena."""
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, "Nowa Scena", "Tytuł sceny:")
        if ok and title.strip():
            self.newSceneRequested.emit(title.strip())
    
    def _populate_filters(self):
        """Populate the filter dropdown menus."""
        if not self.character_manager or not self.location_manager:
            return
        
        # Block signals to prevent triggering during population
        self.character_filter.blockSignals(True)
        self.location_filter.blockSignals(True)
        
        # Clear existing items (except "All")
        while self.character_filter.count() > 1:
            self.character_filter.removeItem(1)
        while self.location_filter.count() > 1:
            self.location_filter.removeItem(1)
        
        try:
            # Get all characters and locations from the current scenes
            character_ids = set()
            location_ids = set()
            
            for scene in self.scenes_data:
                scene_id = scene.get('id')
                if scene_id:
                    # Get characters for this scene
                    characters = self.character_manager.get_characters_for_scene(scene_id)
                    character_ids.update(char.get('id') for char in characters)
                    
                    # Get locations for this scene
                    locations = self.location_manager.get_scene_locations(scene_id)
                    location_ids.update(loc.id for loc, role in locations)
            
            # Populate character filter
            for char_id in character_ids:
                char = self.character_manager.get_character(char_id)
                if char:
                    self.character_filter.addItem(char['name'], char_id)
            
            # Populate location filter
            for loc_id in location_ids:
                location = self.location_manager.get_location(loc_id)
                if location:
                    self.location_filter.addItem(location.name, loc_id)
                    
        except Exception as e:
            print(f"Error populating filters: {e}")
        finally:
            self.character_filter.blockSignals(False)
            self.location_filter.blockSignals(False)
    
    def _on_filter_changed(self):
        """Handle filter changes."""
        self._apply_filters()
        self._update_scene_display()
    
    def _apply_filters(self):
        """Apply current filters to scenes."""
        search_text = self.search_field.text().lower()
        selected_character_id = self.character_filter.currentData()
        selected_location_id = self.location_filter.currentData()
        
        self.filtered_scenes = []
        
        for scene in self.scenes_data:
            # Check text search
            if search_text:
                title = scene.get('title', '').lower()
                content = scene.get('content_rtf', '').lower()
                if search_text not in title and search_text not in content:
                    continue
            
            # Check character filter
            if selected_character_id is not None:
                scene_id = scene.get('id')
                if scene_id:
                    scene_characters = self.character_manager.get_characters_for_scene(scene_id)
                    character_ids = [char.get('id') for char in scene_characters]
                    if selected_character_id not in character_ids:
                        continue
            
            # Check location filter
            if selected_location_id is not None:
                scene_id = scene.get('id')
                if scene_id:
                    scene_locations = self.location_manager.get_scene_locations(scene_id)
                    location_ids = [loc.id for loc, role in scene_locations]
                    if selected_location_id not in location_ids:
                        continue
            
            # Scene passed all filters
            self.filtered_scenes.append(scene)
            
    def refresh_theme(self):
        """Odśwież motywy wszystkich kafelków."""
        for i in range(self.scenes_grid.count()):
            item = self.scenes_grid.itemAt(i)
            if item and hasattr(item.widget(), '_apply_theme_style'):
                item.widget()._apply_theme_style()