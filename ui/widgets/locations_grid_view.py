"""
Locations grid view widget for the Pisarz writing application.

Displays locations in a grid layout with filtering and search capabilities.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QScrollArea, QLabel, QPushButton, QLineEdit, 
                               QComboBox, QMessageBox, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from .location_card import LocationCard
from .location_editor_dialog import LocationEditorDialog


class LocationsGridView(QWidget):
    """Grid view for displaying and managing locations."""
    
    # Signals
    location_selected = Signal(int, str)  # location_id, name
    location_edited = Signal(int)  # location_id
    
    def __init__(self, location_manager, project_id, parent=None):
        super().__init__(parent)
        self.location_manager = location_manager
        self.project_id = project_id
        self.locations = []
        self.filtered_locations = []
        self.location_cards = {}
        
        # Search and filter state
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._apply_filters)
        
        self._setup_ui()
        self._connect_signals()
        self.refresh_locations()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel(_("Locations"))
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # New location button
        self.new_location_button = QPushButton(_("New Location"))
        self.new_location_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        header_layout.addWidget(self.new_location_button)
        
        layout.addLayout(header_layout)
        
        # Filters
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(12)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_("Search locations..."))
        self.search_input.setMaximumWidth(300)
        filters_layout.addWidget(self.search_input)
        
        # Type filter
        type_label = QLabel(_("Type:"))
        filters_layout.addWidget(type_label)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            _("All Types"),
            _("Indoor"),
            _("Outdoor"), 
            _("Mixed"),
            _("Virtual")
        ])
        self.type_filter.setMaximumWidth(120)
        filters_layout.addWidget(self.type_filter)
        
        filters_layout.addStretch()
        
        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        filters_layout.addWidget(self.stats_label)
        
        layout.addLayout(filters_layout)
        
        # Scroll area for locations grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Grid container
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_container.setLayout(self.grid_layout)
        
        scroll_area.setWidget(self.grid_container)
        layout.addWidget(scroll_area)
        
        # Empty state
        self.empty_state = QFrame()
        empty_layout = QVBoxLayout()
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(16)
        
        empty_icon = QLabel("🏢")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setStyleSheet("font-size: 48px;")
        empty_layout.addWidget(empty_icon)
        
        empty_title = QLabel(_("No Locations Yet"))
        empty_title.setAlignment(Qt.AlignCenter)
        empty_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #666;")
        empty_layout.addWidget(empty_title)
        
        empty_text = QLabel(_("Create your first location to start organizing your story world."))
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setWordWrap(True)
        empty_text.setStyleSheet("color: #888; font-size: 14px;")
        empty_layout.addWidget(empty_text)
        
        self.empty_create_button = QPushButton(_("Create First Location"))
        self.empty_create_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        empty_layout.addWidget(self.empty_create_button)
        
        self.empty_state.setLayout(empty_layout)
        layout.addWidget(self.empty_state)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.new_location_button.clicked.connect(self._create_new_location)
        self.empty_create_button.clicked.connect(self._create_new_location)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.type_filter.currentTextChanged.connect(self._apply_filters)
    
    def _on_search_changed(self):
        """Handle search input changes with debouncing."""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay
    
    def _apply_filters(self):
        """Apply search and filter criteria."""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        
        self.filtered_locations = []
        
        for location in self.locations:
            # Apply search filter
            if search_text:
                searchable_text = f"{location.name} {location.description} {location.type} {location.atmosphere}".lower()
                if search_text not in searchable_text:
                    continue
            
            # Apply type filter
            if type_filter != _("All Types"):
                if location.type != type_filter:
                    continue
            
            self.filtered_locations.append(location)
        
        self._update_grid()
        self._update_stats()
    
    def _update_grid(self):
        """Update the locations grid display."""
        # Clear existing cards
        for card in self.location_cards.values():
            card.setParent(None)
        self.location_cards.clear()
        
        # Clear grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Show/hide empty state
        has_locations = len(self.filtered_locations) > 0
        self.grid_container.setVisible(has_locations)
        self.empty_state.setVisible(not has_locations and len(self.locations) == 0)
        
        if not has_locations:
            return
        
        # Add location cards to grid
        columns = 3  # Number of columns in grid
        
        for i, location in enumerate(self.filtered_locations):
            row = i // columns
            col = i % columns
            
            # Get counts for this location
            scene_count = self._get_location_scene_count(location.id)
            character_count = self._get_location_character_count(location.id)
            
            # Create location card
            card = LocationCard(
                location_id=location.id,
                name=location.name,
                description=getattr(location, 'description', ''),
                scene_count=scene_count,
                character_count=character_count,
                location_type=getattr(location, 'type', ''),
                atmosphere=getattr(location, 'atmosphere', '')
            )
            
            # Connect card signals
            card.clicked.connect(self.location_selected.emit)
            card.edit_requested.connect(self._edit_location)
            card.delete_requested.connect(self._delete_location)
            
            self.location_cards[location.id] = card
            self.grid_layout.addWidget(card, row, col)
        
        # Add stretch to fill remaining space
        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)
    
    def _update_stats(self):
        """Update the statistics display."""
        total = len(self.locations)
        showing = len(self.filtered_locations)
        
        if total == 0:
            self.stats_label.setText("")
        elif showing == total:
            self.stats_label.setText(_("{} locations").format(total))
        else:
            self.stats_label.setText(_("{} of {} locations").format(showing, total))
    
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
    
    def _create_new_location(self):
        """Create a new location."""
        dialog = LocationEditorDialog(self.location_manager, self.project_id, parent=self)
        dialog.accepted.connect(self.refresh_locations)
        dialog.show()
    
    def _edit_location(self, location_id):
        """Edit an existing location."""
        location = self.location_manager.get_location(location_id)
        if location:
            dialog = LocationEditorDialog(
                self.location_manager, 
                self.project_id, 
                location=location,
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
        self.locations = self.location_manager.get_locations(self.project_id)
        self._apply_filters()
    
    def clear_filters(self):
        """Clear all filters and show all locations."""
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)
        self._apply_filters()


def _(text):
    """Placeholder for translation function."""
    return text