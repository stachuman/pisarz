"""Grid view widget for displaying scenes as tiles with preview."""

from PySide6.QtWidgets import QComboBox, QLabel, QInputDialog
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from .scene_card import SceneCard
from ..base.base_grid_view import BaseGridView
from i18n import _


class ScenesGridView(BaseGridView):
    """Widok siatki scen z kafelkami preview."""
    
    sceneSelected = Signal(int, str)        # id, title
    newSceneRequested = Signal(str)         # title
    sceneRenameRequested = Signal(int, str) # id, new_title
    
    def __init__(self, export_controller=None, parent=None):
        super().__init__(
            title=_("Scenes"), 
            icon="📝", 
            new_item_label=_("New Scene"), 
            parent=parent
        )
        self.scenes_data = []
        self.character_manager = None
        self.location_manager = None
        self.export_controller = export_controller
        
        # Add scene-specific filters
        self._setup_scene_filters()
        self._connect_signals()
        
    def _setup_scene_filters(self):
        """Add scene-specific character and location filters."""
        # Character filter
        self.character_filter = QComboBox()
        self.character_filter.addItem(_("All Characters"), None)
        self.character_filter.currentTextChanged.connect(self.filter_items)
        self.filter_layout.addWidget(QLabel(_("Character:")))
        self.filter_layout.addWidget(self.character_filter)
        
        # Location filter
        self.location_filter = QComboBox()
        self.location_filter.addItem(_("All Locations"), None)
        self.location_filter.currentTextChanged.connect(self.filter_items)
        self.filter_layout.addWidget(QLabel(_("Location:")))
        self.filter_layout.addWidget(self.location_filter)
        
    def _connect_signals(self):
        """Connect widget signals."""
        self.newItemRequested.connect(self._on_new_scene_clicked)
        
    def set_managers(self, character_manager, location_manager):
        """Set the character and location managers."""
        self.character_manager = character_manager
        self.location_manager = location_manager
        self._populate_filters()
        
    def load_scenes(self, scenes):
        """Załaduj sceny do siatki."""
        self.scenes_data = scenes
        self.load_items(scenes)
        self._populate_filters()
        
    def get_item_search_text(self, item):
        """Get searchable text for a scene."""
        title = item.get('title', '')
        content = item.get('content_rtf', '')
        return f"{title} {content}"
        
    def apply_additional_filters(self, items, filter_text):
        """Apply scene-specific character and location filtering."""
        selected_character_id = self.character_filter.currentData()
        selected_location_id = self.location_filter.currentData()
        
        if selected_character_id is None and selected_location_id is None:
            return items
        
        filtered_items = []
        
        for scene in items:
            scene_id = scene.get('id')
            if not scene_id:
                continue
                
            # Check character filter
            if selected_character_id is not None:
                scene_characters = self.character_manager.get_characters_by_scene(scene_id) if self.character_manager else []
                scene_characters = scene_characters or []
                character_ids = [char.id if hasattr(char, 'id') else char.get('id') for char in scene_characters]
                if selected_character_id not in character_ids:
                    continue
            
            # Check location filter
            if selected_location_id is not None:
                scene_locations = self.location_manager.get_scene_locations(scene_id) if self.location_manager else []
                location_ids = [loc.id for loc, role in scene_locations]
                if selected_location_id not in location_ids:
                    continue
            
            # Scene passed all filters
            filtered_items.append(scene)
            
        return filtered_items
        
    def create_item_card(self, item):
        """Create a scene card for an item."""
        card = SceneCard(item, self.character_manager, self.location_manager, self.export_controller)
        card.sceneSelected.connect(self.sceneSelected.emit)
        card.sceneRenameRequested.connect(self.sceneRenameRequested.emit)
        return card
            
    def _on_new_scene_clicked(self, title):
        """Obsługa kliknięcia przycisku nowa scena."""
        title, ok = QInputDialog.getText(self, _("New Scene"), _("Scene title:"))
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
                    characters = self.character_manager.get_characters_by_scene(scene_id)
                    characters = characters or []
                    character_ids.update(char.id if hasattr(char, 'id') else char.get('id') for char in characters)
                    
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
                    
        except:
            pass
            # Silently handle error - filters won't be populated
        finally:
            self.character_filter.blockSignals(False)
            self.location_filter.blockSignals(False)