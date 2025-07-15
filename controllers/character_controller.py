"""Character controller for managing character-related operations."""

from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from ui.widgets import CharacterEditorDialog
from i18n import _


class CharacterController(QObject):
    """Controller for managing character operations."""
    
    # Signals
    characterSelected = Signal(int, str)  # character_id, character_name
    characterCreated = Signal(int, str)  # character_id, character_name
    characterUpdated = Signal(int, dict)  # character_id, character_data
    charactersListUpdated = Signal(list)  # characters list
    characterAddedToScene = Signal(int, str)  # character_id, role
    characterRemovedFromScene = Signal(int)  # character_id
    error = Signal(str, str)  # title, message
    statusMessage = Signal(str)  # message
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.character_editor_windows = {}  # character_id -> window
        
    def select_character(self, character_id: int, character_name: str):
        """Select and show character editor."""
        character_manager = self.project_controller.current_character_manager
        if not character_manager:
            return
            
        try:
            # Close existing window if open
            if character_id in self.character_editor_windows:
                self.character_editor_windows[character_id].close()
                del self.character_editor_windows[character_id]
            
            project_id = self.project_controller.get_project_id()
            if project_id is None:
                return
                
            character_data = character_manager.get_character(character_id)
            if not character_data:
                self.error.emit(_("Error"), _("Character not found"))
                return
            
            # Create editor window
            editor = CharacterEditorDialog(
                character_data=character_data,
                character_manager=character_manager,
                location_manager=self.project_controller.current_location_manager,
                project_id=project_id
            )
            
            # Connect signals
            editor.characterSaved.connect(self._on_character_saved)
            editor.sceneLinked.connect(self._on_scene_linked)
            editor.sceneUnlinked.connect(self._on_scene_unlinked)
            
            # Show window
            editor.show()
            editor.raise_()
            editor.activateWindow()
            
            # Store reference
            self.character_editor_windows[character_id] = editor
            
            self.characterSelected.emit(character_id, character_name)
            self.statusMessage.emit(_("Editing character: {}").format(character_name))
            
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to open character editor: {}").format(e))
    
    def create_new_character(self, name: str):
        """Create a new character."""
        character_manager = self.project_controller.current_character_manager
        if not character_manager:
            return
            
        try:
            project_id = self.project_controller.get_project_id()
            if project_id is None:
                return
                
            character_data = {
                'name': name,
                'description': '',
                'notes': '',
                'importance': 'main',
                'is_protagonist': False,
                'is_antagonist': False,
                'project_id': project_id
            }
            
            character_id = character_manager.create_character(character_data)
            if character_id:
                self.characterCreated.emit(character_id, name)
                self._refresh_characters_data()
            else:
                self.error.emit(_("Error"), _("Failed to create character"))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to create character: {}").format(e))
    
    def _on_character_saved(self, character_data: Dict[str, Any]):
        """Handle character saved event."""
        try:
            character_id = character_data.get('id')
            if character_id:
                self.characterUpdated.emit(character_id, character_data)
                self._refresh_characters_data()
                
                # Process scene links if they exist
                if 'linked_scenes' in character_data:
                    self._process_scene_links(character_id, character_data['linked_scenes'])
                    
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to process character save: {}").format(e))
    
    def _on_scene_linked(self, character_id: int, scene_id: int, role: str, importance: str):
        """Handle scene linked to character event."""
        try:
            character_manager = self.project_controller.current_character_manager
            if character_manager:
                character_manager.link_character_to_scene(character_id, scene_id, role, importance)
                self.statusMessage.emit(_("Character linked to scene"))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to link character to scene: {}").format(e))
    
    def _on_scene_unlinked(self, character_id: int, scene_id: int):
        """Handle scene unlinked from character event."""
        try:
            character_manager = self.project_controller.current_character_manager
            if character_manager:
                character_manager.unlink_character_from_scene(character_id, scene_id)
                self.statusMessage.emit(_("Character unlinked from scene"))
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to unlink character from scene: {}").format(e))
    
    def _process_scene_links(self, character_id: int, linked_scenes: list):
        """Process scene links for a character."""
        try:
            character_manager = self.project_controller.current_character_manager
            if not character_manager:
                return
                
            # Get current links
            current_links = character_manager.get_character_scenes(character_id)
            current_scene_ids = {link['scene_id'] for link in current_links}
            
            # Process new links
            new_scene_ids = set()
            for scene_link in linked_scenes:
                scene_id = scene_link.get('scene_id')
                role = scene_link.get('role', 'character')
                importance = scene_link.get('importance', 'secondary')
                
                if scene_id:
                    new_scene_ids.add(scene_id)
                    if scene_id not in current_scene_ids:
                        # Link new scene
                        character_manager.link_character_to_scene(character_id, scene_id, role, importance)
            
            # Remove old links
            for scene_id in current_scene_ids - new_scene_ids:
                character_manager.unlink_character_from_scene(character_id, scene_id)
                
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to process scene links: {}").format(e))
    
    def add_character_to_scene(self, character_id: int, role: str):
        """Add character to current scene."""
        self.characterAddedToScene.emit(character_id, role)
    
    def remove_character_from_scene(self, character_id: int):
        """Remove character from current scene."""
        self.characterRemovedFromScene.emit(character_id)
    
    def get_characters_list(self) -> list:
        """Get the list of characters."""
        character_manager = self.project_controller.current_character_manager
        if not character_manager:
            return []
            
        try:
            project_id = self.project_controller.get_project_id()
            if project_id is None:
                return []
            return character_manager.get_characters(project_id)
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to load characters: {}").format(e))
            return []
    
    def _refresh_characters_data(self):
        """Refresh characters data."""
        try:
            characters = self.get_characters_list()
            self.charactersListUpdated.emit(characters)
        except Exception as e:
            self.error.emit(_("Error"), _("Failed to refresh characters: {}").format(e))
    
    def cleanup(self):
        """Clean up character editor windows."""
        for window in self.character_editor_windows.values():
            window.close()
        self.character_editor_windows.clear()