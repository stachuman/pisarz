"""
Scene context panel for in-editor character and location management.

Provides a collapsible side panel that shows and manages characters, locations,
and their relationships within the current scene.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame, QListWidget,
                               QListWidgetItem, QComboBox, QMessageBox, QGroupBox,
                               QSizePolicy, QToolButton, QMenu)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor


class SceneContextPanel(QWidget):
    """Context panel for managing scene characters and locations."""
    
    # Signals
    character_added = Signal(int, str)  # character_id, role
    character_removed = Signal(int)  # character_id
    location_added = Signal(int, str)  # location_id, role
    location_removed = Signal(int)  # location_id
    new_character_requested = Signal(str)  # name
    new_location_requested = Signal(str)  # name
    character_selected = Signal(int)  # character_id for editing
    location_selected = Signal(int)  # location_id for editing
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_id = None
        self.character_manager = None
        self.location_manager = None
        self.project_id = None
        
        # Current scene data
        self.scene_characters = []  # List of (character_data, role)
        self.scene_locations = []   # List of (location_data, role)
        self.all_characters = []    # All project characters
        self.all_locations = []     # All project locations
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the user interface."""
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header
        header = QLabel(_("Scene Context"))
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 8px; background-color: #ecf0f1; border-radius: 4px;")
        layout.addWidget(header)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)
        
        # Locations section
        self._setup_locations_section(content_layout)
        
        # Characters section  
        self._setup_characters_section(content_layout)
        
        # Relationships section
        self._setup_relationships_section(content_layout)
        
        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        layout.addWidget(scroll_area)
        self.setLayout(layout)
    
    def _setup_locations_section(self, layout):
        """Set up the locations section."""
        # Locations group
        locations_group = QGroupBox(_("📍 Locations"))
        locations_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        locations_layout = QVBoxLayout()
        
        # Current locations list
        self.locations_list = QListWidget()
        self.locations_list.setMaximumHeight(100)
        self.locations_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        locations_layout.addWidget(self.locations_list)
        
        # Locations buttons
        locations_buttons = QHBoxLayout()
        
        self.add_location_btn = QPushButton(_("+ Add"))
        self.add_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        self.remove_location_btn = QPushButton(_("Remove"))
        self.remove_location_btn.setEnabled(False)
        self.remove_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.new_location_btn = QPushButton(_("New"))
        self.new_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        
        locations_buttons.addWidget(self.add_location_btn)
        locations_buttons.addWidget(self.remove_location_btn)
        locations_buttons.addWidget(self.new_location_btn)
        
        locations_layout.addLayout(locations_buttons)
        locations_group.setLayout(locations_layout)
        layout.addWidget(locations_group)
    
    def _setup_characters_section(self, layout):
        """Set up the characters section."""
        # Characters group
        characters_group = QGroupBox(_("👥 Characters"))
        characters_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        characters_layout = QVBoxLayout()
        
        # Current characters list
        self.characters_list = QListWidget()
        self.characters_list.setMaximumHeight(120)
        self.characters_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        characters_layout.addWidget(self.characters_list)
        
        # Characters buttons
        characters_buttons = QHBoxLayout()
        
        self.add_character_btn = QPushButton(_("+ Add"))
        self.add_character_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.remove_character_btn = QPushButton(_("Remove"))
        self.remove_character_btn.setEnabled(False)
        self.remove_character_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.new_character_btn = QPushButton(_("New"))
        self.new_character_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        characters_buttons.addWidget(self.add_character_btn)
        characters_buttons.addWidget(self.remove_character_btn)
        characters_buttons.addWidget(self.new_character_btn)
        
        characters_layout.addLayout(characters_buttons)
        characters_group.setLayout(characters_layout)
        layout.addWidget(characters_group)
    
    def _setup_relationships_section(self, layout):
        """Set up the relationships section."""
        # Relationships group
        relationships_group = QGroupBox(_("🔗 Relationships"))
        relationships_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        relationships_layout = QVBoxLayout()
        
        # Relationships display
        self.relationships_label = QLabel(_("No relationships to display"))
        self.relationships_label.setWordWrap(True)
        self.relationships_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 3px;
                border: 1px solid #e9ecef;
            }
        """)
        relationships_layout.addWidget(self.relationships_label)
        
        relationships_group.setLayout(relationships_layout)
        layout.addWidget(relationships_group)
    
    def _connect_signals(self):
        """Connect widget signals."""
        # Location signals
        self.add_location_btn.clicked.connect(self._show_location_selector)
        self.remove_location_btn.clicked.connect(self._remove_selected_location)
        self.new_location_btn.clicked.connect(self._create_new_location)
        self.locations_list.itemSelectionChanged.connect(self._on_location_selection_changed)
        self.locations_list.itemDoubleClicked.connect(self._edit_selected_location)
        
        # Character signals
        self.add_character_btn.clicked.connect(self._show_character_selector)
        self.remove_character_btn.clicked.connect(self._remove_selected_character)
        self.new_character_btn.clicked.connect(self._create_new_character)
        self.characters_list.itemSelectionChanged.connect(self._on_character_selection_changed)
        self.characters_list.itemDoubleClicked.connect(self._edit_selected_character)
    
    def set_managers(self, character_manager, location_manager, project_id):
        """Set the managers for character and location operations."""
        self.character_manager = character_manager
        self.location_manager = location_manager
        self.project_id = project_id
        
        # Load all characters and locations
        self._refresh_all_data()
    
    def set_scene_id(self, scene_id):
        """Set the current scene ID and load its context."""
        self.scene_id = scene_id
        self._load_scene_context()
    
    def _refresh_all_data(self):
        """Refresh all characters and locations from database."""
        if not self.character_manager or not self.location_manager or not self.project_id:
            return
        
        try:
            self.all_characters = self.character_manager.get_characters(self.project_id)
            self.all_locations = self.location_manager.get_locations(self.project_id)
        except Exception as e:
            print(f"Error refreshing data: {e}")
    
    def _load_scene_context(self):
        """Load the current scene's characters and locations."""
        if not self.scene_id or not self.character_manager or not self.location_manager:
            return
        
        try:
            # Load scene characters with roles
            character_links = self.character_manager.get_characters_for_scene_with_roles(self.scene_id)
            self.scene_characters = character_links
            
            # Load scene locations
            location_links = self.location_manager.get_scene_locations(self.scene_id)
            self.scene_locations = location_links
            
            # Update UI
            self._update_locations_list()
            self._update_characters_list()
            self._update_relationships()
            
        except Exception as e:
            print(f"Error loading scene context: {e}")
    
    def _update_locations_list(self):
        """Update the locations list widget."""
        self.locations_list.clear()
        
        for location, role in self.scene_locations:
            item_text = f"{location.name}"
            if role:
                item_text += f" ({role})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, location.id)
            self.locations_list.addItem(item)
    
    def _update_characters_list(self):
        """Update the characters list widget."""
        self.characters_list.clear()
        
        for item in self.scene_characters:
            try:
                # Handle different possible formats
                if isinstance(item, tuple) and len(item) == 2:
                    character, role = item
                elif isinstance(item, dict):
                    # Legacy format - character dict without role
                    character = item
                    role = ""
                else:
                    print(f"Unexpected character item format: {item}")
                    continue
                
                item_text = f"{character.get('name', 'Unknown')}"
                if role:
                    item_text += f" ({role})"
                
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, character.get('id'))
                self.characters_list.addItem(list_item)
            except Exception as e:
                print(f"Error processing character item {item}: {e}")
                continue
    
    def _update_relationships(self):
        """Update the relationships display."""
        relationships = []
        
        try:
            # Find character-location relationships within this scene
            for item in self.scene_characters:
                try:
                    if isinstance(item, tuple) and len(item) == 2:
                        character, char_role = item
                    elif isinstance(item, dict):
                        character = item
                        char_role = ""
                    else:
                        continue
                    
                    char_id = character.get('id')
                    char_name = character.get('name', 'Unknown')
                except Exception as e:
                    print(f"Error processing character in relationships: {e}")
                    continue
                
                # Get character's location relationships
                if self.location_manager:
                    char_locations = self.location_manager.get_character_locations(char_id)
                    
                    for loc_in_scene, scene_role in self.scene_locations:
                        for char_loc, rel_type, description in char_locations:
                            if char_loc.id == loc_in_scene.id:
                                rel_text = f"• {char_name} {rel_type} {char_loc.name}"
                                if description:
                                    rel_text += f" ({description})"
                                relationships.append(rel_text)
        except Exception as e:
            print(f"Error updating relationships: {e}")
        
        if relationships:
            self.relationships_label.setText("\n".join(relationships))
            self.relationships_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    padding: 8px;
                    background-color: #e8f5e8;
                    border-radius: 3px;
                    border: 1px solid #27ae60;
                }
            """)
        else:
            self.relationships_label.setText(_("No character-location relationships in this scene"))
            self.relationships_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-style: italic;
                    padding: 8px;
                    background-color: #f8f9fa;
                    border-radius: 3px;
                    border: 1px solid #e9ecef;
                }
            """)
    
    def _on_location_selection_changed(self):
        """Handle location selection changes."""
        has_selection = bool(self.locations_list.currentItem())
        self.remove_location_btn.setEnabled(has_selection)
    
    def _on_character_selection_changed(self):
        """Handle character selection changes."""
        has_selection = bool(self.characters_list.currentItem())
        self.remove_character_btn.setEnabled(has_selection)
    
    def _show_location_selector(self):
        """Show location selector dialog."""
        if not self.location_manager or not self.scene_id:
            return
        
        try:
            # Get already linked location IDs
            linked_location_ids = [loc.id for loc, role in self.scene_locations]
            
            from .location_selector_dialog import LocationSelectorDialog
            dialog = LocationSelectorDialog(
                self.location_manager, 
                self.project_id, 
                already_linked_location_ids=linked_location_ids,
                parent=self
            )
            
            dialog.location_selected.connect(self._on_location_selected_from_dialog)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open location selector: {}").format(str(e)))
    
    def _show_character_selector(self):
        """Show character selector dialog."""
        if not self.character_manager or not self.scene_id:
            return
        
        try:
            # Get already linked character IDs
            linked_character_ids = []
            for item in self.scene_characters:
                try:
                    if isinstance(item, tuple) and len(item) == 2:
                        character, role = item
                        linked_character_ids.append(character.get('id'))
                    elif isinstance(item, dict):
                        linked_character_ids.append(item.get('id'))
                except Exception as e:
                    print(f"Error getting character ID: {e}")
            
            from .character_selector_dialog import CharacterSelectorDialog
            dialog = CharacterSelectorDialog(
                self.character_manager, 
                self.project_id, 
                already_linked_character_ids=linked_character_ids,
                parent=self
            )
            
            dialog.character_selected.connect(self._on_character_selected_from_dialog)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open character selector: {}").format(str(e)))
    
    def _remove_selected_location(self):
        """Remove selected location from scene."""
        current_item = self.locations_list.currentItem()
        if not current_item:
            return
        
        location_id = current_item.data(Qt.UserRole)
        
        try:
            # Unlink location from scene
            if self.location_manager and self.scene_id:
                success = self.location_manager.unlink_location_from_scene(location_id, self.scene_id)
                if success:
                    # Emit signal for main app to handle
                    self.location_removed.emit(location_id)
                    # Refresh the context
                    self._load_scene_context()
                else:
                    QMessageBox.warning(self, _("Warning"), _("Failed to unlink location from scene."))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to unlink location: {}").format(str(e)))
    
    def _remove_selected_character(self):
        """Remove selected character from scene."""
        current_item = self.characters_list.currentItem()
        if not current_item:
            return
        
        character_id = current_item.data(Qt.UserRole)
        
        try:
            # Unlink character from scene
            if self.character_manager and self.scene_id:
                success = self.character_manager.unlink_character_from_scene(character_id, self.scene_id)
                if success:
                    # Emit signal for main app to handle
                    self.character_removed.emit(character_id)
                    # Refresh the context
                    self._load_scene_context()
                else:
                    QMessageBox.warning(self, _("Warning"), _("Failed to unlink character from scene."))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to unlink character: {}").format(str(e)))
    
    def _create_new_location(self):
        """Create a new location."""
        self.new_location_requested.emit("")
    
    def _create_new_character(self):
        """Create a new character."""
        self.new_character_requested.emit("")
    
    def _edit_selected_location(self):
        """Edit the selected location."""
        current_item = self.locations_list.currentItem()
        if not current_item:
            return
        
        location_id = current_item.data(Qt.UserRole)
        self.location_selected.emit(location_id)
    
    def _edit_selected_character(self):
        """Edit the selected character."""
        current_item = self.characters_list.currentItem()
        if not current_item:
            return
        
        character_id = current_item.data(Qt.UserRole)
        self.character_selected.emit(character_id)
    
    def refresh_context(self):
        """Refresh the entire context panel."""
        self._refresh_all_data()
        self._load_scene_context()
    
    def _on_location_selected_from_dialog(self, location_id, role):
        """Handle location selection from selector dialog."""
        try:
            # Link location to scene
            if self.location_manager and self.scene_id:
                success = self.location_manager.link_location_to_scene(location_id, self.scene_id, role)
                if success:
                    # Emit signal for main app to handle
                    self.location_added.emit(location_id, role)
                    # Refresh the context
                    self._load_scene_context()
                else:
                    QMessageBox.warning(self, _("Warning"), _("Failed to link location to scene."))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to link location: {}").format(str(e)))
    
    def _on_character_selected_from_dialog(self, character_id, role):
        """Handle character selection from selector dialog."""
        try:
            # Link character to scene
            if self.character_manager and self.scene_id:
                success = self.character_manager.link_character_to_scene_with_role(character_id, self.scene_id, role)
                if success:
                    # Emit signal for main app to handle
                    self.character_added.emit(character_id, role)
                    # Refresh the context
                    self._load_scene_context()
                else:
                    QMessageBox.warning(self, _("Warning"), _("Failed to link character to scene."))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to link character: {}").format(str(e)))


def _(text):
    """Placeholder for translation function."""
    return text