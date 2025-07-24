"""
Location editor dialog for the Pisarz writing application.

Provides a comprehensive interface for creating and editing locations.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QTextEdit, QComboBox, QTabWidget,
                               QPushButton, QLabel, QMessageBox, QScrollArea, QWidget, QFrame,
                               QListWidget, QListWidgetItem, QInputDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from .scene_selector_dialog import SceneSelector
from i18n import _


class LocationEditorDialog(QDialog):
    """Dialog for creating and editing locations."""
    
    locationSaved = Signal(dict)  # location data
    sceneLinked = Signal(int, int, str, int)  # location_id, scene_id, role, importance
    sceneUnlinked = Signal(int, int)  # location_id, scene_id
    
    def __init__(self, location_manager, project_id, location=None, scenes_data=None, parent=None):
        super().__init__(parent)
        self.location_manager = location_manager
        self.project_id = project_id
        self.location = location  # None for new location
        self.scenes_data = scenes_data or []
        self.linked_scenes = []  # Will store linked scene data with roles
        self.is_editing = location is not None
        
        self.setWindowTitle(_("Edit Location") if self.is_editing else _("New Location"))
        
        # Make it non-modal and always on top
        self.setModal(False)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.resize(600, 500)
        
        self._setup_ui()
        self._connect_signals()
        
        if self.is_editing:
            self._populate_fields()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Title
        title = QLabel(_("Edit Location") if self.is_editing else _("Create New Location"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tab widget for different aspects of the location
        self.tab_widget = QTabWidget()
        
        # Basic Information Tab
        self._setup_basic_tab()
        
        # Details Tab
        self._setup_details_tab()
        
        # Story Role Tab
        self._setup_story_tab()
        
        # Scenes Tab (shows linked scenes)
        self._setup_scenes_tab()
        
        # Connections Tab (if editing)
        if self.is_editing:
            self._setup_connections_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton(_("Cancel"))
        self.save_button = QPushButton(_("Save"))
        self.save_button.setDefault(True)
        # Remove custom styling to use global professional theme
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _setup_basic_tab(self):
        """Set up the basic information tab."""
        widget = QWidget()
        layout = QFormLayout()
        layout.setSpacing(12)
        
        # Name (required)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(_("Enter location name..."))
        layout.addRow(_("Name *:"), self.name_input)
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.addItems([
            "",
            _("Indoor"),
            _("Outdoor"),
            _("Mixed"),
            _("Virtual")
        ])
        layout.addRow(_("Type:"), self.type_combo)
        
        # Atmosphere
        self.atmosphere_input = QLineEdit()
        self.atmosphere_input.setPlaceholderText(_("e.g., Cozy, Tense, Mysterious..."))
        layout.addRow(_("Atmosphere:"), self.atmosphere_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(_("Brief description of the location..."))
        self.description_input.setMaximumHeight(80)
        layout.addRow(_("Description:"), self.description_input)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, _("Basic Info"))
    
    def _setup_details_tab(self):
        """Set up the details tab."""
        widget = QWidget()
        layout = QFormLayout()
        layout.setSpacing(12)
        
        # Physical details
        self.details_input = QTextEdit()
        self.details_input.setPlaceholderText(_("Physical description, layout, important features..."))
        self.details_input.setMaximumHeight(120)
        layout.addRow(_("Physical Details:"), self.details_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(_("General notes, inspiration, references..."))
        self.notes_input.setMaximumHeight(120)
        layout.addRow(_("Notes:"), self.notes_input)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, _("Details"))
    
    def _setup_story_tab(self):
        """Set up the story role tab."""
        widget = QWidget()
        layout = QFormLayout()
        layout.setSpacing(12)
        
        # Story significance
        self.significance_input = QTextEdit()
        self.significance_input.setPlaceholderText(_("Why is this location important to your story? Symbolic meaning, recurring themes..."))
        self.significance_input.setMaximumHeight(120)
        layout.addRow(_("Story Significance:"), self.significance_input)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, _("Story Role"))
    
    def _setup_scenes_tab(self):
        """Set up the scenes tab showing location appearances."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scenes_group = QFrame()
        scenes_group.setFrameStyle(QFrame.StyledPanel)
        scenes_layout = QVBoxLayout(scenes_group)
        
        # Info and action buttons
        header_layout = QHBoxLayout()
        info_label = QLabel(_("This location appears in the following scenes:"))
        info_label.setFont(QFont("Arial", 9))
        info_label.setStyleSheet("color: #666;")
        header_layout.addWidget(info_label)
        
        header_layout.addStretch()
        
        # Add scene button
        self.add_scene_btn = QPushButton(_("Add Scene"))
        self.add_scene_btn.setToolTip(_("Link this location to additional scenes"))
        self.add_scene_btn.clicked.connect(self.add_scene_to_location)
        header_layout.addWidget(self.add_scene_btn)
        
        scenes_layout.addLayout(header_layout)
        
        # Scenes list
        self.linked_scenes_list = QListWidget()
        self.linked_scenes_list.setFont(QFont("Arial", 10))
        self.linked_scenes_list.itemClicked.connect(self.on_scene_item_clicked)
        scenes_layout.addWidget(self.linked_scenes_list)
        
        # Scene action buttons
        scene_buttons_layout = QHBoxLayout()
        
        self.edit_scene_role_btn = QPushButton(_("Edit Role"))
        self.edit_scene_role_btn.setEnabled(False)
        self.edit_scene_role_btn.clicked.connect(self.edit_scene_role)
        scene_buttons_layout.addWidget(self.edit_scene_role_btn)
        
        self.remove_scene_btn = QPushButton(_("Remove Scene"))
        self.remove_scene_btn.setEnabled(False)
        self.remove_scene_btn.clicked.connect(self.remove_scene_from_location)
        scene_buttons_layout.addWidget(self.remove_scene_btn)
        
        scene_buttons_layout.addStretch()
        scenes_layout.addLayout(scene_buttons_layout)
        
        layout.addWidget(scenes_group)
        self.tab_widget.addTab(widget, _("Scenes"))
    
    def _setup_connections_tab(self):
        """Set up the connections tab (only shown when editing)."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Scenes section
        scenes_frame = QFrame()
        scenes_frame.setFrameStyle(QFrame.StyledPanel)
        scenes_layout = QVBoxLayout()
        
        scenes_title = QLabel(_("Scenes at this location:"))
        scenes_title.setStyleSheet("font-weight: bold;")
        scenes_layout.addWidget(scenes_title)
        
        self.scenes_list = QLabel(_("Loading..."))
        self.scenes_list.setWordWrap(True)
        self.scenes_list.setStyleSheet("color: #666; margin: 8px;")
        scenes_layout.addWidget(self.scenes_list)
        
        scenes_frame.setLayout(scenes_layout)
        layout.addWidget(scenes_frame)
        
        # Characters section
        characters_frame = QFrame()
        characters_frame.setFrameStyle(QFrame.StyledPanel)
        characters_layout = QVBoxLayout()
        
        characters_title = QLabel(_("Characters associated with this location:"))
        characters_title.setStyleSheet("font-weight: bold;")
        characters_layout.addWidget(characters_title)
        
        self.characters_list = QLabel(_("Loading..."))
        self.characters_list.setWordWrap(True)
        self.characters_list.setStyleSheet("color: #666; margin: 8px;")
        characters_layout.addWidget(self.characters_list)
        
        characters_frame.setLayout(characters_layout)
        layout.addWidget(characters_frame)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, _("Connections"))
        
        # Load connection data
        if self.location:
            self._load_connections()
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.save_button.clicked.connect(self._save_location)
        self.cancel_button.clicked.connect(self.reject)
        self.name_input.textChanged.connect(self._validate_form)
    
    def _populate_fields(self):
        """Populate fields with existing location data."""
        if not self.location:
            return
        
        self.setWindowTitle(self.location.name or "Location")

        self.name_input.setText(self.location.name or "")
        self.type_combo.setCurrentText(self.location.type or "")
        self.atmosphere_input.setText(self.location.atmosphere or "")
        self.description_input.setPlainText(self.location.description or "")
        self.details_input.setPlainText(self.location.details or "")
        self.significance_input.setPlainText(self.location.significance or "")
        self.notes_input.setPlainText(self.location.notes or "")
        
        # Load linked scenes with roles/importance
        # Note: linked_scenes will be set by the controller after dialog creation
        # Don't load them here as they need to be fetched from database
    
    def _load_connections(self):
        """Load and display connection information."""
        if not self.location:
            return
        
        # Load scenes
        try:
            scenes = self.location_manager.get_location_scenes(self.location.id)
            if scenes:
                scene_texts = []
                for scene_data, role in scenes:
                    scene_name = scene_data.get('title', _('Untitled Scene'))
                    scene_texts.append(f"• {scene_name} ({role})")
                self.scenes_list.setText("\n".join(scene_texts))
            else:
                self.scenes_list.setText(_("No scenes at this location yet."))
        except Exception as e:
            self.scenes_list.setText(_("Error loading scenes."))
        
        # Load characters
        try:
            characters = self.location_manager.get_location_characters(self.location.id)
            if characters:
                character_texts = []
                for char_data, relationship, description in characters:
                    char_name = char_data.get('name', _('Unknown Character'))
                    if description:
                        character_texts.append(f"• {char_name} ({relationship}): {description}")
                    else:
                        character_texts.append(f"• {char_name} ({relationship})")
                self.characters_list.setText("\n".join(character_texts))
            else:
                self.characters_list.setText(_("No characters associated with this location yet."))
        except Exception as e:
            self.characters_list.setText(_("Error loading characters."))
    
    def _validate_form(self):
        """Validate the form and enable/disable save button."""
        name = self.name_input.text().strip()
        self.save_button.setEnabled(bool(name))
    
    def _save_location(self):
        """Save the location."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, _("Invalid Input"), _("Location name is required."))
            self.name_input.setFocus()
            return
        
        # Collect data
        location_data = {
            'name': name,
            'type': self.type_combo.currentText(),
            'atmosphere': self.atmosphere_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'details': self.details_input.toPlainText().strip(),
            'significance': self.significance_input.toPlainText().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }
        
        # Include ID if editing existing location
        if self.location and hasattr(self.location, 'id'):
            location_data['id'] = self.location.id
            
        # Store linked scenes for the signal, but don't save to database
        location_data_with_scenes = location_data.copy()
        location_data_with_scenes['linked_scenes'] = self.linked_scenes
        
        try:
            if self.is_editing:
                # Update existing location (without linked_scenes)
                success = self.location_manager.update_location(self.location.id, **location_data)
                operation = _("update")
            else:
                # Create new location
                location_id = self.location_manager.create_location(self.project_id, **location_data)
                success = location_id is not None
                operation = _("create")
            
            if success:
                self.locationSaved.emit(location_data_with_scenes)
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    _("Error"), 
                    _("Failed to {} location. Please try again.").format(operation)
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                _("Error"), 
                _("An error occurred while saving: {}").format(str(e))
            )
    
    def update_scenes_list(self):
        """Update the scenes list display."""
        self.linked_scenes_list.clear()
        
        for scene_data in self.linked_scenes:
            scene_title = scene_data.get('title', _('Untitled Scene'))
            role = scene_data.get('role', _('No role'))
            importance = scene_data.get('importance', 3)
            
            # Create display text
            display_text = f"{scene_title}"
            if role:
                display_text += f" ({role}"
                if importance != 3:  # Only show importance if not default
                    display_text += f", {_('Importance')}: {importance}"
                display_text += ")"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, scene_data)
            self.linked_scenes_list.addItem(item)
    
    def on_scene_item_clicked(self, item):
        """Handle click on scene item."""
        self.edit_scene_role_btn.setEnabled(True)
        self.remove_scene_btn.setEnabled(True)
    
    def add_scene_to_location(self):
        """Open scene selector dialog to add scenes."""
        if not self.scenes_data:
            QMessageBox.information(self, _("No Scenes"), 
                                  _("No scenes are available in this project."))
            return
            
        # Get already linked scene IDs
        linked_scene_ids = [scene.get('id') for scene in self.linked_scenes]
        
        # Open scene selector dialog
        dialog = SceneSelector(self.scenes_data, linked_scene_ids, self)
        dialog.scenesSelected.connect(self.on_scenes_selected)
        dialog.exec()
    
    def on_scenes_selected(self, selected_scenes):
        """Handle scenes selected from scene selector."""
        location_id = getattr(self.location, 'id', None) if self.location else None
        
        for scene_id, role, importance in selected_scenes:
            # Find scene data
            scene_data = None
            for scene in self.scenes_data:
                if scene['id'] == scene_id:
                    scene_data = scene.copy()
                    break
                    
            if scene_data:
                # Add role and importance
                scene_data['role'] = role
                scene_data['importance'] = importance
                
                # Add to linked scenes
                self.linked_scenes.append(scene_data)
                
                # Emit signal if we have location ID (editing existing location)
                if location_id:
                    self.sceneLinked.emit(location_id, scene_id, role, importance)
                    
        # Update display
        self.update_scenes_list()
    
    def edit_scene_role(self):
        """Edit the role of selected scene."""
        current_item = self.linked_scenes_list.currentItem()
        if not current_item:
            return
            
        scene_data = current_item.data(Qt.ItemDataRole.UserRole)
        current_role = scene_data.get('role', '')
        current_importance = scene_data.get('importance', 3)
        
        # Simple input dialog for role
        new_role, ok = QInputDialog.getText(
            self, _("Edit Role"), 
            _("Enter location's role in this scene:"),
            text=current_role
        )
        
        if ok and new_role.strip():
            # Update scene data
            scene_data['role'] = new_role.strip()
            
            # Update in linked_scenes list
            for i, scene in enumerate(self.linked_scenes):
                if scene.get('id') == scene_data.get('id'):
                    self.linked_scenes[i] = scene_data
                    break
                    
            # Update display
            self.update_scenes_list()
            
            # Emit signal if editing existing location
            location_id = getattr(self.location, 'id', None) if self.location else None
            if location_id:
                self.sceneLinked.emit(location_id, scene_data.get('id'), 
                                    new_role.strip(), current_importance)
    
    def remove_scene_from_location(self):
        """Remove selected scene from location."""
        current_item = self.linked_scenes_list.currentItem()
        if not current_item:
            return
            
        scene_data = current_item.data(Qt.ItemDataRole.UserRole)
        scene_title = scene_data.get('title', _('Untitled Scene'))
        
        # Confirm removal
        reply = QMessageBox.question(
            self, _("Remove Scene"),
            _("Remove '{}' from this location?").format(scene_title),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from linked_scenes
            self.linked_scenes = [s for s in self.linked_scenes if s.get('id') != scene_data.get('id')]
            
            # Update display
            self.update_scenes_list()
            
            # Disable buttons
            self.edit_scene_role_btn.setEnabled(False)
            self.remove_scene_btn.setEnabled(False)
            
            # Emit signal if editing existing location
            location_id = getattr(self.location, 'id', None) if self.location else None
            if location_id:
                self.sceneUnlinked.emit(location_id, scene_data.get('id'))