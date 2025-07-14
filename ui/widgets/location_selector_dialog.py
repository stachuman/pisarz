"""
Location selector dialog for linking locations to scenes.

Provides a dialog for selecting existing locations to link to the current scene.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class LocationSelectorDialog(QDialog):
    """Dialog for selecting locations to link to a scene."""
    
    # Signals
    location_selected = Signal(int, str)  # location_id, role
    
    def __init__(self, location_manager, project_id, already_linked_location_ids=None, parent=None):
        super().__init__(parent)
        self.location_manager = location_manager
        self.project_id = project_id
        self.already_linked_location_ids = set(already_linked_location_ids or [])
        self.available_locations = []
        
        self.setWindowTitle(_("Select Location"))
        self.setModal(True)
        self.resize(450, 400)
        
        self._setup_ui()
        self._connect_signals()
        self._load_locations()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Title
        title = QLabel(_("Select Location for Scene"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Search
        search_layout = QHBoxLayout()
        search_label = QLabel(_("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_("Filter locations by name..."))
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Available locations
        locations_group = QGroupBox(_("Available Locations"))
        locations_layout = QVBoxLayout()
        
        self.locations_list = QListWidget()
        self.locations_list.setMinimumHeight(200)
        locations_layout.addWidget(self.locations_list)
        
        locations_group.setLayout(locations_layout)
        layout.addWidget(locations_group)
        
        # Role selection
        role_group = QGroupBox(_("Location Role in Scene"))
        role_layout = QHBoxLayout()
        
        role_label = QLabel(_("Role:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            _("Primary"),
            _("Secondary"), 
            _("Mentioned"),
            _("Background")
        ])
        self.role_combo.setCurrentText(_("Primary"))
        
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_combo)
        role_layout.addStretch()
        
        role_group.setLayout(role_layout)
        layout.addWidget(role_group)
        
        # Info label
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton(_("Cancel"))
        self.select_button = QPushButton(_("Select Location"))
        self.select_button.setDefault(True)
        self.select_button.setEnabled(False)
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.select_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.search_input.textChanged.connect(self._filter_locations)
        self.locations_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.locations_list.itemDoubleClicked.connect(self._select_location)
        self.select_button.clicked.connect(self._select_location)
        self.cancel_button.clicked.connect(self.reject)
    
    def _load_locations(self):
        """Load available locations from the database."""
        try:
            all_locations = self.location_manager.get_locations(self.project_id)
            
            # Filter out already linked locations
            self.available_locations = [
                loc for loc in all_locations 
                if loc.id not in self.already_linked_location_ids
            ]
            
            self._populate_locations_list()
            self._update_info()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load locations: {}").format(str(e)))
            print(f"Error loading locations: {e}")
    
    def _populate_locations_list(self):
        """Populate the locations list widget."""
        self.locations_list.clear()
        
        if not self.available_locations:
            item = QListWidgetItem(_("No available locations"))
            item.setFlags(Qt.NoItemFlags)
            item.setData(Qt.UserRole, None)
            self.locations_list.addItem(item)
            return
        
        for location in self.available_locations:
            # Create display text
            display_text = location.name
            if location.type:
                display_text += f" ({location.type})"
            if location.description:
                preview = location.description.strip()[:50]
                if len(location.description) > 50:
                    preview += "..."
                display_text += f"\n  {preview}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, location.id)
            self.locations_list.addItem(item)
    
    def _filter_locations(self):
        """Filter locations based on search input."""
        search_text = self.search_input.text().lower()
        
        for i in range(self.locations_list.count()):
            item = self.locations_list.item(i)
            location_id = item.data(Qt.UserRole)
            
            if location_id is None:  # "No available locations" item
                item.setHidden(False)
                continue
            
            # Find the location data
            location = next((loc for loc in self.available_locations if loc.id == location_id), None)
            if not location:
                item.setHidden(True)
                continue
            
            # Check if search text matches
            if not search_text:
                item.setHidden(False)
            else:
                searchable_text = f"{location.name} {location.type} {location.description}".lower()
                item.setHidden(search_text not in searchable_text)
    
    def _on_selection_changed(self):
        """Handle location selection changes."""
        selected_items = self.locations_list.selectedItems()
        has_valid_selection = (
            len(selected_items) > 0 and 
            selected_items[0].data(Qt.UserRole) is not None
        )
        self.select_button.setEnabled(has_valid_selection)
    
    def _update_info(self):
        """Update the info label."""
        total_available = len(self.available_locations)
        total_linked = len(self.already_linked_location_ids)
        
        if total_available == 0:
            if total_linked == 0:
                self.info_label.setText(_("No locations in project. Create locations first."))
            else:
                self.info_label.setText(_("All locations are already linked to this scene."))
        else:
            self.info_label.setText(_("{} location(s) available for linking").format(total_available))
    
    def _select_location(self):
        """Select the current location."""
        selected_items = self.locations_list.selectedItems()
        if not selected_items:
            return
        
        location_id = selected_items[0].data(Qt.UserRole)
        if location_id is None:
            return
        
        role = self.role_combo.currentText().lower()
        self.location_selected.emit(location_id, role)
        self.accept()


def _(text):
    """Placeholder for translation function."""
    return text