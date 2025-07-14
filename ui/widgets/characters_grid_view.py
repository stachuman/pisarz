"""Characters grid view widget for displaying and managing characters."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QScrollArea, QFrame, QGridLayout,
                              QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .character_card import CharacterCard
from ..styles.styles import HEADER_COLOR, NEW_SCENE_BUTTON_STYLE
from i18n import _


class CharactersGridView(QWidget):
    """Grid view for managing characters in a project."""
    
    characterSelected = Signal(int, str)  # character_id, name
    newCharacterRequested = Signal(str)   # name
    characterEditRequested = Signal(int)  # character_id
    characterDeleteRequested = Signal(int)  # character_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.characters = []
        self.location_manager = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the characters grid view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(_("📝 Characters"))
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet(HEADER_COLOR)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # New Character button
        self.new_character_btn = QPushButton(_("New Character"))
        self.new_character_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.new_character_btn.setStyleSheet(NEW_SCENE_BUTTON_STYLE)
        self.new_character_btn.clicked.connect(self.create_new_character)
        header_layout.addWidget(self.new_character_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        self.subtitle_label = QLabel(_("Click on character to edit it or create new character."))
        self.subtitle_label.setFont(QFont("Arial", 10))
        self.subtitle_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.subtitle_label)
        
        # Scroll area for characters
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Characters container
        self.characters_widget = QWidget()
        self.characters_layout = QGridLayout(self.characters_widget)
        self.characters_layout.setSpacing(15)
        self.characters_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.characters_widget)
        layout.addWidget(self.scroll_area)
        
        # Empty state
        self.empty_label = QLabel(_("You don't have any characters yet.\\nCreate first character to start!"))
        self.empty_label.setFont(QFont("Arial", 12))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #999; padding: 40px;")
        layout.addWidget(self.empty_label)
        
        self.update_empty_state()
    
    def set_location_manager(self, location_manager):
        """Set the location manager for character cards."""
        self.location_manager = location_manager
        
    def load_characters(self, characters_data):
        """Load characters data and display cards."""
        self.characters = characters_data
        self.clear_characters()
        
        if not self.characters:
            self.update_empty_state()
            return
            
        # Create character cards
        cols = 3  # 3 characters per row
        for i, character in enumerate(self.characters):
            row = i // cols
            col = i % cols
            
            card = CharacterCard(
                character_id=character['id'],
                name=character['name'],
                description=character.get('description', ''),
                location_manager=self.location_manager
            )
            card.clicked.connect(self.characterSelected.emit)
            card.edit_requested.connect(self.characterEditRequested.emit)
            card.delete_requested.connect(self.characterDeleteRequested.emit)
            
            self.characters_layout.addWidget(card, row, col)
            
        self.update_empty_state()
        
    def clear_characters(self):
        """Clear all character cards from the grid."""
        while self.characters_layout.count():
            child = self.characters_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                
    def update_empty_state(self):
        """Show/hide empty state based on characters count."""
        has_characters = len(self.characters) > 0
        self.scroll_area.setVisible(has_characters)
        self.empty_label.setVisible(not has_characters)
        
        # Update title with count
        count_text = _("Characters view ({} characters)").format(len(self.characters))
        self.title_label.setText(f"📝 {count_text}")
        
    def create_new_character(self):
        """Show dialog to create a new character."""
        name, ok = QInputDialog.getText(
            self, 
            _("New Character"), 
            _("Character name:"),
            text=_("Untitled")
        )
        
        if ok and name.strip():
            self.newCharacterRequested.emit(name.strip())
        elif ok:
            QMessageBox.warning(
                self, 
                _("Warning"), 
                _("Character name cannot be empty.")
            )