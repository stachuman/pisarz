"""Character editor dialog for creating and editing characters."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QTextEdit, QPushButton, QGroupBox,
                              QMessageBox, QTabWidget, QWidget, QListWidget,
                              QListWidgetItem, QFrame, QSpinBox, QComboBox,
                              QCheckBox, QFormLayout, QScrollArea, QInputDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .scene_selector_dialog import SceneSelector
from i18n import _


class CharacterEditorDialog(QDialog):
    """Dialog for creating and editing character information."""
    
    characterSaved = Signal(dict)  # character data
    sceneLinked = Signal(int, int, str, int)  # character_id, scene_id, role, importance
    sceneUnlinked = Signal(int, int)  # character_id, scene_id
    
    def __init__(self, character_data=None, scenes_data=None, parent=None):
        super().__init__(parent)
        self.character_data = character_data or {}
        self.scenes_data = scenes_data or []
        self.linked_scenes = []  # Will store linked scene data with roles
        self.setup_ui()
        self.load_character_data()
        
    def setup_ui(self):
        """Setup the character editor dialog UI."""
        self.setWindowTitle(_("Character Editor"))
        self.setMinimumSize(500, 400)
        
        # Make it non-modal and always on top
        self.setModal(False)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Tab widget for different sections
        self.tabs = QTabWidget()
        
        # Basic Info Tab
        self.basic_tab = self.create_basic_tab()
        self.tabs.addTab(self.basic_tab, _("Basic Info"))
        
        # Development Tab
        self.development_tab = self.create_development_tab()
        self.tabs.addTab(self.development_tab, _("Development"))
        
        # Notes Tab
        self.notes_tab = self.create_notes_tab()
        self.tabs.addTab(self.notes_tab, _("Notes"))
        
        # Scenes Tab (shows linked scenes)
        self.scenes_tab = self.create_scenes_tab()
        self.tabs.addTab(self.scenes_tab, _("Scenes"))
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(_("Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton(_("Save"))
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_character)
        # Remove custom styling to use global professional theme
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
    def create_basic_tab(self):
        """Create the basic information tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout(tab)
        
        # === IDENTITY ===
        identity_group = QGroupBox(_("Identity"))
        identity_form = QFormLayout(identity_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(_("Enter character name..."))
        identity_form.addRow(_("Name") + "*:", self.name_edit)
        
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText(_("Full legal name"))
        identity_form.addRow(_("Full Name") + ":", self.full_name_edit)
        
        self.alias_edit = QLineEdit()
        self.alias_edit.setPlaceholderText(_("Nickname, pseudonym, title"))
        identity_form.addRow(_("Alias/Nickname") + ":", self.alias_edit)
        
        layout.addWidget(identity_group)
        
        # === DEMOGRAPHICS ===
        demo_group = QGroupBox(_("Demographics"))
        demo_form = QFormLayout(demo_group)
        
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 200)
        self.age_spin.setSpecialValueText(_("Unknown"))
        demo_form.addRow(_("Age") + ":", self.age_spin)
        
        self.gender_combo = QComboBox()
        self.gender_combo.setEditable(True)
        self.gender_combo.addItems([
            "", _("Male"), _("Female"), _("Non-binary"), _("Other")
        ])
        demo_form.addRow(_("Gender") + ":", self.gender_combo)
        
        self.occupation_edit = QLineEdit()
        self.occupation_edit.setPlaceholderText(_("Job, profession, role"))
        demo_form.addRow(_("Occupation") + ":", self.occupation_edit)
        
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText(_("Where they live or come from"))
        demo_form.addRow(_("Location") + ":", self.location_edit)
        
        layout.addWidget(demo_group)
        
        # === CHARACTER ROLE ===
        role_group = QGroupBox(_("Character Role"))
        role_layout = QVBoxLayout(role_group)
        
        importance_layout = QHBoxLayout()
        importance_layout.addWidget(QLabel(_("Importance") + ":"))
        self.importance_combo = QComboBox()
        self.importance_combo.addItems([
            _("Minor Character"),
            _("Supporting Character"), 
            _("Major Character"),
            _("Main Character"),
            _("Primary Character")
        ])
        importance_layout.addWidget(self.importance_combo)
        importance_layout.addStretch()
        role_layout.addLayout(importance_layout)
        
        flags_layout = QHBoxLayout()
        self.protagonist_check = QCheckBox(_("Protagonist"))
        self.antagonist_check = QCheckBox(_("Antagonist"))
        flags_layout.addWidget(self.protagonist_check)
        flags_layout.addWidget(self.antagonist_check)
        flags_layout.addStretch()
        role_layout.addLayout(flags_layout)
        
        layout.addWidget(role_group)
        
        # === BASIC DESCRIPTION ===
        desc_group = QGroupBox(_("Basic Description"))
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(_("Brief overview of the character..."))
        self.description_edit.setMaximumHeight(100)
        desc_layout.addWidget(self.description_edit)
        
        layout.addWidget(desc_group)
        
        # === APPEARANCE ===
        appearance_group = QGroupBox(_("Appearance"))
        appearance_layout = QVBoxLayout(appearance_group)
        
        self.appearance_edit = QTextEdit()
        self.appearance_edit.setPlaceholderText(_("Physical description, distinctive features, clothing style..."))
        self.appearance_edit.setMaximumHeight(80)
        appearance_layout.addWidget(self.appearance_edit)
        
        layout.addWidget(appearance_group)
        
        layout.addStretch()
        
        # Wrap in scroll area
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addWidget(scroll)
        return wrapper
        
    def create_notes_tab(self):
        """Create the notes tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        notes_group = QGroupBox(_("Character Notes"))
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(_("Additional notes about the character, development ideas, story arc..."))
        self.notes_edit.setFont(QFont("Arial", 10))
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        return tab
        
    def create_development_tab(self):
        """Create the character development tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout(tab)
        
        # === PERSONALITY ===
        personality_group = QGroupBox(_("Personality"))
        personality_layout = QVBoxLayout(personality_group)
        
        self.personality_edit = QTextEdit()
        self.personality_edit.setPlaceholderText(_("Character traits, quirks, habits, behavioral patterns..."))
        self.personality_edit.setMaximumHeight(100)
        personality_layout.addWidget(self.personality_edit)
        
        layout.addWidget(personality_group)
        
        # === BACKGROUND ===
        background_group = QGroupBox(_("Background"))
        background_layout = QVBoxLayout(background_group)
        
        self.background_edit = QTextEdit()
        self.background_edit.setPlaceholderText(_("Character history, upbringing, formative events, education..."))
        self.background_edit.setMaximumHeight(100)
        background_layout.addWidget(self.background_edit)
        
        layout.addWidget(background_group)
        
        # === GOALS ===
        goals_group = QGroupBox(_("Goals & Motivations"))
        goals_layout = QVBoxLayout(goals_group)
        
        self.goals_edit = QTextEdit()
        self.goals_edit.setPlaceholderText(_("What they want, their aspirations, driving forces..."))
        self.goals_edit.setMaximumHeight(80)
        goals_layout.addWidget(self.goals_edit)
        
        layout.addWidget(goals_group)
        
        # === CONFLICTS ===
        conflicts_group = QGroupBox(_("Conflicts & Challenges"))
        conflicts_layout = QVBoxLayout(conflicts_group)
        
        self.conflicts_edit = QTextEdit()
        self.conflicts_edit.setPlaceholderText(_("Internal conflicts, external obstacles, fears, weaknesses..."))
        self.conflicts_edit.setMaximumHeight(80)
        conflicts_layout.addWidget(self.conflicts_edit)
        
        layout.addWidget(conflicts_group)
        
        # === RELATIONSHIPS ===
        relationships_group = QGroupBox(_("Key Relationships"))
        relationships_layout = QVBoxLayout(relationships_group)
        
        self.relationships_edit = QTextEdit()
        self.relationships_edit.setPlaceholderText(_("Important connections with other characters, family, friends..."))
        self.relationships_edit.setMaximumHeight(80)
        relationships_layout.addWidget(self.relationships_edit)
        
        layout.addWidget(relationships_group)
        
        layout.addStretch()
        
        # Wrap in scroll area
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addWidget(scroll)
        return wrapper
        
    def create_scenes_tab(self):
        """Create the scenes tab showing character appearances."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scenes_group = QGroupBox(_("Scenes with this Character"))
        scenes_layout = QVBoxLayout(scenes_group)
        
        # Info and action buttons
        header_layout = QHBoxLayout()
        info_label = QLabel(_("This character appears in the following scenes:"))
        info_label.setFont(QFont("Arial", 9))
        info_label.setStyleSheet("color: #666;")
        header_layout.addWidget(info_label)
        
        header_layout.addStretch()
        
        # Add scene button
        self.add_scene_btn = QPushButton(_("Add Scene"))
        self.add_scene_btn.setToolTip(_("Link this character to additional scenes"))
        self.add_scene_btn.clicked.connect(self.add_scene_to_character)
        # Remove custom styling to use global professional theme
        header_layout.addWidget(self.add_scene_btn)
        
        scenes_layout.addLayout(header_layout)
        
        # Scenes list
        self.scenes_list = QListWidget()
        self.scenes_list.setFont(QFont("Arial", 10))
        self.scenes_list.itemClicked.connect(self.on_scene_item_clicked)
        scenes_layout.addWidget(self.scenes_list)
        
        # Scene action buttons
        scene_buttons_layout = QHBoxLayout()
        
        self.edit_scene_role_btn = QPushButton(_("Edit Role"))
        self.edit_scene_role_btn.setEnabled(False)
        self.edit_scene_role_btn.clicked.connect(self.edit_scene_role)
        # Remove custom styling to use global professional theme
        scene_buttons_layout.addWidget(self.edit_scene_role_btn)
        
        self.remove_scene_btn = QPushButton(_("Remove Scene"))
        self.remove_scene_btn.setEnabled(False)
        self.remove_scene_btn.clicked.connect(self.remove_scene_from_character)
        # Remove custom styling to use global professional theme
        scene_buttons_layout.addWidget(self.remove_scene_btn)
        
        scene_buttons_layout.addStretch()
        scenes_layout.addLayout(scene_buttons_layout)
        
        layout.addWidget(scenes_group)
        return tab
        
    def load_character_data(self):
        """Load existing character data into the form."""
        if not self.character_data:
            return
        
        # Basic Info Tab
        self.name_edit.setText(self.character_data.get('name', ''))
        self.full_name_edit.setText(self.character_data.get('full_name', ''))
        self.alias_edit.setText(self.character_data.get('alias', ''))
        
        # Demographics
        age = self.character_data.get('age')
        if age is not None:
            self.age_spin.setValue(age)
        
        gender = self.character_data.get('gender', '')
        index = self.gender_combo.findText(gender)
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)
        else:
            self.gender_combo.setCurrentText(gender)
            
        self.occupation_edit.setText(self.character_data.get('occupation', ''))
        self.location_edit.setText(self.character_data.get('location', ''))
        
        # Character Role
        importance = self.character_data.get('importance', 1)
        self.importance_combo.setCurrentIndex(importance - 1)  # importance 1-5 maps to index 0-4
        
        self.protagonist_check.setChecked(bool(self.character_data.get('is_protagonist', 0)))
        self.antagonist_check.setChecked(bool(self.character_data.get('is_antagonist', 0)))
        
        # Descriptions
        self.description_edit.setPlainText(self.character_data.get('description', ''))
        self.appearance_edit.setPlainText(self.character_data.get('appearance', ''))
        
        # Development Tab
        self.personality_edit.setPlainText(self.character_data.get('personality', ''))
        self.background_edit.setPlainText(self.character_data.get('background', ''))
        self.goals_edit.setPlainText(self.character_data.get('goals', ''))
        self.conflicts_edit.setPlainText(self.character_data.get('conflicts', ''))
        self.relationships_edit.setPlainText(self.character_data.get('relationships', ''))
        
        # Notes Tab
        self.notes_edit.setPlainText(self.character_data.get('notes', ''))
        
        # Load linked scenes with roles/importance
        self.linked_scenes = self.character_data.get('scenes', [])
        self.update_scenes_list()
            
    def save_character(self):
        """Save the character data."""
        # Validate input data
        validation_errors = self._validate_character_data()
        if validation_errors:
            QMessageBox.warning(
                self, 
                _("Validation Error"), 
                "\n".join(validation_errors)
            )
            return
        
        # Collect all character data (validation passed)
        name = self.name_edit.text().strip()
        character_data = {
            'name': name,
            'full_name': self.full_name_edit.text().strip(),
            'alias': self.alias_edit.text().strip(),
            'age': self.age_spin.value() if self.age_spin.value() > 0 else None,
            'gender': self.gender_combo.currentText().strip(),
            'occupation': self.occupation_edit.text().strip(),
            'location': self.location_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'appearance': self.appearance_edit.toPlainText().strip(),
            'personality': self.personality_edit.toPlainText().strip(),
            'background': self.background_edit.toPlainText().strip(),
            'goals': self.goals_edit.toPlainText().strip(),
            'conflicts': self.conflicts_edit.toPlainText().strip(),
            'relationships': self.relationships_edit.toPlainText().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'importance': self.importance_combo.currentIndex() + 1,  # index 0-4 maps to importance 1-5
            'is_protagonist': 1 if self.protagonist_check.isChecked() else 0,
            'is_antagonist': 1 if self.antagonist_check.isChecked() else 0
        }
        
        # Include ID if editing existing character
        if 'id' in self.character_data:
            character_data['id'] = self.character_data['id']
            
        # Include linked scenes for processing
        character_data['linked_scenes'] = self.linked_scenes
        
        self.characterSaved.emit(character_data)
        self.accept()
        
    def _validate_character_data(self):
        """Validate character data and return list of error messages."""
        errors = []
        
        # Required fields
        name = self.name_edit.text().strip()
        if not name:
            errors.append(_("Character name cannot be empty."))
        elif len(name) > 100:
            errors.append(_("Character name cannot be longer than 100 characters."))
            
        # Optional field length validation
        full_name = self.full_name_edit.text().strip()
        if len(full_name) > 150:
            errors.append(_("Full name cannot be longer than 150 characters."))
            
        alias = self.alias_edit.text().strip()
        if len(alias) > 100:
            errors.append(_("Alias cannot be longer than 100 characters."))
            
        # Age validation
        age = self.age_spin.value()
        if age < 0 or age > 200:
            errors.append(_("Age must be between 0 and 200."))
            
        # Text field length validation
        text_fields = [
            (self.occupation_edit.text().strip(), _("Occupation"), 100),
            (self.location_edit.text().strip(), _("Location"), 100),
            (self.gender_combo.currentText().strip(), _("Gender"), 50),
        ]
        
        for text, field_name, max_length in text_fields:
            if len(text) > max_length:
                errors.append(_("{} cannot be longer than {} characters.").format(field_name, max_length))
        
        # Text area validation
        text_areas = [
            (self.description_edit.toPlainText().strip(), _("Description"), 1000),
            (self.appearance_edit.toPlainText().strip(), _("Appearance"), 1000),
            (self.personality_edit.toPlainText().strip(), _("Personality"), 2000),
            (self.background_edit.toPlainText().strip(), _("Background"), 2000),
            (self.goals_edit.toPlainText().strip(), _("Goals & Motivations"), 1000),
            (self.conflicts_edit.toPlainText().strip(), _("Conflicts & Challenges"), 1000),
            (self.relationships_edit.toPlainText().strip(), _("Key Relationships"), 1000),
            (self.notes_edit.toPlainText().strip(), _("Notes"), 5000),
        ]
        
        for text, field_name, max_length in text_areas:
            if len(text) > max_length:
                errors.append(_("{} cannot be longer than {} characters.").format(field_name, max_length))
        
        return errors
        
    def update_scenes_list(self):
        """Update the scenes list display."""
        self.scenes_list.clear()
        
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
            self.scenes_list.addItem(item)
            
    def on_scene_item_clicked(self, item):
        """Handle click on scene item."""
        self.edit_scene_role_btn.setEnabled(True)
        self.remove_scene_btn.setEnabled(True)
        
    def add_scene_to_character(self):
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
        character_id = self.character_data.get('id')
        
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
                
                # Emit signal if we have character ID (editing existing character)
                if character_id:
                    self.sceneLinked.emit(character_id, scene_id, role, importance)
                    
        # Update display
        self.update_scenes_list()
        
    def edit_scene_role(self):
        """Edit the role of selected scene."""
        current_item = self.scenes_list.currentItem()
        if not current_item:
            return
            
        scene_data = current_item.data(Qt.ItemDataRole.UserRole)
        current_role = scene_data.get('role', '')
        current_importance = scene_data.get('importance', 3)
        
        # Simple input dialog for role
        new_role, ok = QInputDialog.getText(
            self, _("Edit Role"), 
            _("Enter character's role in this scene:"),
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
            
            # Emit signal if editing existing character
            character_id = self.character_data.get('id')
            if character_id:
                self.sceneLinked.emit(character_id, scene_data.get('id'), 
                                    new_role.strip(), current_importance)
                
    def remove_scene_from_character(self):
        """Remove selected scene from character."""
        current_item = self.scenes_list.currentItem()
        if not current_item:
            return
            
        scene_data = current_item.data(Qt.ItemDataRole.UserRole)
        scene_title = scene_data.get('title', _('Untitled Scene'))
        
        # Confirm removal
        reply = QMessageBox.question(
            self, _("Remove Scene"),
            _("Remove '{}' from this character?").format(scene_title),
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
            
            # Emit signal if editing existing character
            character_id = self.character_data.get('id')
            if character_id:
                self.sceneUnlinked.emit(character_id, scene_data.get('id'))
        
    def set_linked_scenes(self, scenes_data):
        """Set the scenes that this character appears in."""
        self.scenes_list.clear()
        for scene in scenes_data:
            item = QListWidgetItem(scene.get('title', _('Untitled Scene')))
            self.scenes_list.addItem(item)