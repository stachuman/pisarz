"""Characters grid view widget for displaying and managing characters."""

from PySide6.QtWidgets import QInputDialog, QMessageBox
from PySide6.QtCore import Signal

from .character_card import CharacterCard
from ..base.base_grid_view import BaseGridView
from i18n import _


class CharactersGridView(BaseGridView):
    """Grid view for managing characters in a project."""
    
    characterSelected = Signal(int, str)  # character_id, name
    newCharacterRequested = Signal(str)   # name
    characterEditRequested = Signal(int)  # character_id
    characterDeleteRequested = Signal(int)  # character_id
    
    def __init__(self, parent=None):
        super().__init__(title=_("Characters"), icon="📝", parent=parent)
        self.characters = []
        self.location_manager = None
        self.setup_connections()
        
    def setup_connections(self):
        """Setup signal connections."""
        self.newItemRequested.connect(self.newCharacterRequested.emit)
    
    def set_location_manager(self, location_manager):
        """Set the location manager for character cards."""
        self.location_manager = location_manager
        
    def load_characters(self, characters_data):
        """Load characters data and display cards."""
        self.characters = characters_data
        self.load_items(characters_data)
        
    def get_item_search_text(self, item):
        """Get searchable text for a character."""
        return f"{item['name']} {item.get('description', '')}"
        
    def create_item_card(self, item):
        """Create a character card for an item."""
        card = CharacterCard(
            character_id=item['id'],
            name=item['name'],
            description=item.get('description', ''),
            location_manager=self.location_manager
        )
        card.clicked.connect(self.characterSelected.emit)
        card.edit_requested.connect(self.characterEditRequested.emit)
        card.delete_requested.connect(self.characterDeleteRequested.emit)
        return card
        
    def clear_characters(self):
        """Clear all character cards from the grid."""
        self.clear_grid()
        
    def update_empty_state(self):
        """Show/hide empty state based on characters count."""
        # This is now handled by the base class
        pass