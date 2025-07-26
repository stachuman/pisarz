"""
Locations grid view widget for the Pisarz writing application.

Displays locations in a grid layout with filtering and search capabilities.
"""

from PySide6.QtWidgets import QComboBox, QMessageBox, QInputDialog
from PySide6.QtCore import Signal, QTimer

from .location_card import LocationCard
from .location_editor_dialog import LocationEditorDialog
from ..base.base_grid_view import BaseGridView
from i18n import _


class LocationsGridView(BaseGridView):
    """Grid view for displaying and managing locations."""
    
    # Signals
    location_selected = Signal(int, str)  # location_id, name
    location_edited = Signal(int)  # location_id
    
    def __init__(self, location_manager, project_id, scene_manager=None, parent=None):
        super().__init__(
            title=_("Locations"), 
            icon="🏢", 
            new_item_label=_("New Location"), 
            parent=parent
        )
        self.location_manager = location_manager
        self.scene_manager = scene_manager
        self.project_id = project_id
        self.locations = []
        self.location_cards = {}
        
        # Add location-specific type filter
        self._setup_location_filters()
        self._connect_signals()
        self.refresh_locations()
    
    def _setup_location_filters(self):
        """Add location-specific type filter to the base filter layout."""
        # Add location type filter to the existing filter layout
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            _("All Types"),
            _("Indoor"),
            _("Outdoor"), 
            _("Mixed"),
            _("Virtual")
        ])
        self.type_filter.setMaximumWidth(120)
        self.type_filter.currentTextChanged.connect(self.filter_items)
        
        # Add to the base class filter layout
        self.filter_layout.addWidget(self.type_filter)
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.newItemRequested.connect(self._create_new_location)
    
    def get_item_search_text(self, item):
        """Get searchable text for a location."""
        return f"{item.name} {getattr(item, 'description', '')} {getattr(item, 'type', '')} {getattr(item, 'atmosphere', '')}"
    
    def apply_additional_filters(self, items, filter_text):
        """Apply location-specific type filtering."""
        type_filter = self.type_filter.currentText()
        
        if type_filter == _("All Types"):
            return items
        
        # Filter by location type
        filtered_items = []
        for item in items:
            if hasattr(item, 'type') and item.type == type_filter:
                filtered_items.append(item)
        
        return filtered_items
    
    def create_item_card(self, item):
        """Create a location card for an item."""
        # Get counts for this location
        scene_count = self._get_location_scene_count(item.id)
        character_count = self._get_location_character_count(item.id)
        
        # Create location card
        card = LocationCard(
            location_id=item.id,
            name=item.name,
            description=getattr(item, 'description', ''),
            scene_count=scene_count,
            character_count=character_count,
            location_type=getattr(item, 'type', ''),
            atmosphere=getattr(item, 'atmosphere', '')
        )
        
        # Connect card signals
        card.clicked.connect(self.location_selected.emit)
        card.edit_requested.connect(self._edit_location)
        card.delete_requested.connect(self._delete_location)
        
        self.location_cards[item.id] = card
        return card
    
    def _get_location_scene_count(self, location_id):
        """Get the number of scenes for a location."""
        try:
            scenes = self.location_manager.get_location_scenes(location_id)
            return len(scenes)
        except Exception:
            return 0
    
    def _get_location_character_count(self, location_id):
        """Get the number of characters associated with a location."""
        try:
            characters = self.location_manager.get_location_characters(location_id)
            return len(characters)
        except Exception:
            return 0
    
    def _create_new_location(self, title):
        """Create a new location."""
        # Get all scenes in project for linking
        all_scenes = self.scene_manager.get_scenes_by_project(self.project_id) if self.scene_manager else []
        
        dialog = LocationEditorDialog(self.location_manager, self.project_id, scenes_data=all_scenes, parent=self)
        dialog.accepted.connect(self.refresh_locations)
        dialog.show()
    
    def _edit_location(self, location_id):
        """Edit an existing location."""
        location = self.location_manager.get_location_object(location_id)
        if location:
            # Get all scenes in project for linking
            all_scenes = self.scene_manager.get_scenes_by_project(self.project_id) if self.scene_manager else []
            
            dialog = LocationEditorDialog(
                self.location_manager, 
                self.project_id, 
                location=location,
                scenes_data=all_scenes,
                parent=self
            )
            dialog.accepted.connect(lambda: (
                self.refresh_locations(),
                self.location_edited.emit(location_id)
            ))
            dialog.show()
    
    def _delete_location(self, location_id):
        """Delete a location with confirmation."""
        location = self.location_manager.get_location(location_id)
        if not location:
            return
        
        # Check if location has relationships
        scene_count = self._get_location_scene_count(location_id)
        character_count = self._get_location_character_count(location_id)
        
        if scene_count > 0 or character_count > 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(_("Delete Location"))
            msg.setText(_("This location is linked to {} scene(s) and {} character(s).").format(scene_count, character_count))
            msg.setInformativeText(_("Deleting this location will remove all these relationships. This action cannot be undone."))
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Cancel)
            
            if msg.exec() != QMessageBox.Yes:
                return
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle(_("Delete Location"))
            msg.setText(_("Are you sure you want to delete '{}'?").format(location.name))
            msg.setInformativeText(_("This action cannot be undone."))
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Cancel)
            
            if msg.exec() != QMessageBox.Yes:
                return
        
        # Delete the location
        if self.location_manager.delete_location(location_id):
            self.refresh_locations()
        else:
            QMessageBox.critical(self, _("Error"), _("Failed to delete location."))
    
    def refresh_locations(self):
        """Refresh the locations list from the database."""
        self.locations = self.location_manager.get_location_objects(self.project_id)
        self.load_items(self.locations)
    
    def clear_filters(self):
        """Clear all filters and show all locations."""
        self.search_field.clear()
        self.type_filter.setCurrentIndex(0)
        self.filter_items()