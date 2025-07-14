"""
Character selector dialog for linking characters to scenes.

Provides a dialog for selecting existing characters to link to the current scene.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QPushButton, QLabel, QLineEdit,
                               QComboBox, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class CharacterSelectorDialog(QDialog):
    """Dialog for selecting characters to link to a scene."""
    
    # Signals
    character_selected = Signal(int, str)  # character_id, role
    
    def __init__(self, character_manager, project_id, already_linked_character_ids=None, parent=None):
        super().__init__(parent)
        self.character_manager = character_manager
        self.project_id = project_id
        self.already_linked_character_ids = set(already_linked_character_ids or [])
        self.available_characters = []
        
        self.setWindowTitle(_("Select Character"))
        self.setModal(True)
        self.resize(450, 400)
        
        self._setup_ui()
        self._connect_signals()
        self._load_characters()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Title
        title = QLabel(_("Select Character for Scene"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Search
        search_layout = QHBoxLayout()
        search_label = QLabel(_("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_("Filter characters by name..."))
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Available characters
        characters_group = QGroupBox(_("Available Characters"))
        characters_layout = QVBoxLayout()
        
        self.characters_list = QListWidget()
        self.characters_list.setMinimumHeight(200)
        characters_layout.addWidget(self.characters_list)
        
        characters_group.setLayout(characters_layout)
        layout.addWidget(characters_group)
        
        # Role selection
        role_group = QGroupBox(_("Character Role in Scene"))
        role_layout = QHBoxLayout()
        
        role_label = QLabel(_("Role:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            _("Protagonist"),
            _("Supporting Character"),
            _("Antagonist"),
            _("Minor Character"),
            _("Mentioned Only"),
            _("Narrator"),
            _("Cameo")
        ])
        self.role_combo.setCurrentText(_("Supporting Character"))
        
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
        self.select_button = QPushButton(_("Select Character"))
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
        self.search_input.textChanged.connect(self._filter_characters)
        self.characters_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.characters_list.itemDoubleClicked.connect(self._select_character)
        self.select_button.clicked.connect(self._select_character)
        self.cancel_button.clicked.connect(self.reject)
    
    def _load_characters(self):
        """Load available characters from the database."""
        try:
            all_characters = self.character_manager.get_characters(self.project_id)
            
            # Filter out already linked characters
            self.available_characters = [
                char for char in all_characters 
                if char.get('id') not in self.already_linked_character_ids
            ]
            
            self._populate_characters_list()
            self._update_info()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load characters: {}").format(str(e)))
            print(f"Error loading characters: {e}")
    
    def _populate_characters_list(self):
        """Populate the characters list widget."""
        self.characters_list.clear()
        
        if not self.available_characters:
            item = QListWidgetItem(_("No available characters"))
            item.setFlags(Qt.NoItemFlags)
            item.setData(Qt.UserRole, None)
            self.characters_list.addItem(item)
            return
        
        for character in self.available_characters:
            # Create display text
            display_text = character.get('name', _('Unknown Character'))
            if character.get('occupation'):
                display_text += f" ({character.get('occupation')})"
            if character.get('description'):
                preview = character.get('description', '').strip()[:50]
                if len(character.get('description', '')) > 50:
                    preview += "..."
                display_text += f"\n  {preview}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, character.get('id'))
            self.characters_list.addItem(item)
    
    def _filter_characters(self):
        """Filter characters based on search input."""
        search_text = self.search_input.text().lower()
        
        for i in range(self.characters_list.count()):
            item = self.characters_list.item(i)
            character_id = item.data(Qt.UserRole)
            
            if character_id is None:  # "No available characters" item
                item.setHidden(False)
                continue
            
            # Find the character data
            character = next((char for char in self.available_characters if char.get('id') == character_id), None)
            if not character:
                item.setHidden(True)
                continue
            
            # Check if search text matches
            if not search_text:
                item.setHidden(False)
            else:
                searchable_text = f"{character.get('name', '')} {character.get('occupation', '')} {character.get('description', '')}".lower()
                item.setHidden(search_text not in searchable_text)
    
    def _on_selection_changed(self):
        """Handle character selection changes."""
        selected_items = self.characters_list.selectedItems()
        has_valid_selection = (
            len(selected_items) > 0 and 
            selected_items[0].data(Qt.UserRole) is not None
        )
        self.select_button.setEnabled(has_valid_selection)
    
    def _update_info(self):
        """Update the info label."""
        total_available = len(self.available_characters)
        total_linked = len(self.already_linked_character_ids)
        
        if total_available == 0:
            if total_linked == 0:
                self.info_label.setText(_("No characters in project. Create characters first."))
            else:
                self.info_label.setText(_("All characters are already linked to this scene."))
        else:
            self.info_label.setText(_("{} character(s) available for linking").format(total_available))
    
    def _select_character(self):
        """Select the current character."""
        selected_items = self.characters_list.selectedItems()
        if not selected_items:
            return
        
        character_id = selected_items[0].data(Qt.UserRole)
        if character_id is None:
            return
        
        role = self.role_combo.currentText()
        self.character_selected.emit(character_id, role)
        self.accept()


def _(text):
    """Placeholder for translation function."""
    return text