"""
Location selector dialog for linking locations to scenes.

Provides a dialog for selecting existing locations to link to the current scene.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QMessageBox, QGroupBox)

from ui.base.base_dialog import BaseDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from i18n import _


class LocationSelectorDialog(BaseDialog):
    """Dialog for selecting locations to link to a scene."""
    
    # Signals
    location_selected = Signal(int, str)  # location_id, role
    
    def __init__(self, location_manager, project_id, already_linked_location_ids=None, parent=None):
        self.location_manager = location_manager
        self.project_id = project_id
        self.already_linked_location_ids = set(already_linked_location_ids or [])
        self.available_locations = []
        
        super().__init__(
            title=_("Select Location"),
            width=450,
            height=400,
            modal=True,
            parent=parent
        )
        
        self._setup_ui()
        self._connect_signals()
        self._load_locations()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Title
        title = QLabel(_("Select Location for Scene"))
        title.setFont(self.font_manager.get_font(14, bold=True))
        self.add_content_widget(title)
        
        # Search
        search_layout, self.search_input = self.create_search_widget(_("Filter locations by name..."), self._filter_locations)
        self.add_content_layout(search_layout)
        
        # Available locations
        locations_group, locations_layout = self.create_form_section(_("Available Locations"))
        
        self.locations_list = self.create_selection_list_widget(self._select_location, self._on_selection_changed)
        self.locations_list.setMinimumHeight(200)
        locations_layout.addWidget(self.locations_list)
        
        self.add_content_widget(locations_group)
        
        # Role selection
        role_group, role_layout = self.create_form_section(_("Location Role in Scene"))
        
        role_label = QLabel(_("Role:"))
        self.role_combo = QComboBox()
        roles = [
            _("Primary"),
            _("Secondary"), 
            _("Mentioned"),
            _("Background")
        ]
        self.role_combo.addItems(roles)
        self.role_combo.setCurrentText(_("Primary"))
        
        role_layout.addRow(role_label, self.role_combo)
        
        self.add_content_widget(role_group)
        
        # Info label
        self.info_label = self.create_info_label("", "muted")
        self.info_label.setFont(self.font_manager.get_font(12))
        self.add_content_widget(self.info_label)
        
        # Buttons using BaseDialog functionality
        buttons = self.create_standard_buttons(_("Select Location"), self._select_location, _("Cancel"))
        self.select_button = buttons['save']
        self.select_button.setEnabled(False)
    
    def _connect_signals(self):
        """Connect widget signals."""
        # Search and list connections are handled by BaseDialog helpers
        pass
    
    def _load_locations(self):
        """Load available locations from the database."""
        try:
            # Use get_locations_by_project() to get Location objects (not dictionaries)
            all_locations = self.location_manager.get_locations_by_project(self.project_id)
            
            # Filter out already linked locations
            self.available_locations = [
                loc for loc in all_locations 
                if loc.id not in self.already_linked_location_ids
            ]
            
            self._populate_locations_list()
            self._update_info()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load locations: {}").format(str(e)))
    
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

