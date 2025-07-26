"""Character management controller for the main application."""

from pathlib import Path
from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal

from core.database.character_repository import CharacterManager
from core.database.scene_repository import SceneManager
from ui.widgets import CharacterEditorDialog
from i18n import _


class AppCharacterController(QObject):
    """Handles character-related operations for the main application."""
    
    # Signals
    characterEditorOpened = Signal(int, str)  # character_id, character_name
    characterCreated = Signal(str)  # name
    characterSaved = Signal(dict)  # character_data
    charactersRefreshNeeded = Signal()
    statusMessage = Signal(str)  # message
    errorOccurred = Signal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_manager: Optional[CharacterManager] = None
        self.scene_manager: Optional[SceneManager] = None
        self.current_project_id: Optional[int] = None
        self.character_editor_windows: Dict[int, CharacterEditorDialog] = {}
        
    def set_managers(self, character_manager: CharacterManager, scene_manager: SceneManager, project_id: int):
        """Set the current managers and project ID."""
        self.character_manager = character_manager
        self.scene_manager = scene_manager
        self.current_project_id = project_id
        
    def open_character_editor(self, character_id: int, character_name: str, project_manager) -> bool:
        """Open character editor dialog."""
        if not self.character_manager or not self.scene_manager:
            return False
            
        try:
            # Check if window is already open for this character
            if character_id in self.character_editor_windows:
                window = self.character_editor_windows[character_id]
                window.raise_()
                window.activateWindow()
                return True
            
            # Get character data
            character_data = self.character_manager.get_character(character_id)
            if not character_data:
                self.errorOccurred.emit(_("Warning"), _("Character not found"))
                return False
                
            # Get linked scenes
            linked_scenes = self.character_manager.get_scenes_for_character(character_id)
            character_data['scenes'] = linked_scenes
            
            # Get all scenes in project for linking  
            project_data = self.character_manager.get_character(character_id)
            project_id = project_data.get('project_id') if project_data else None
            all_scenes = self.scene_manager.get_scenes_by_project(project_id) if project_id else []
            
            # Create and show dialog
            dialog = CharacterEditorDialog(character_data, all_scenes, self.parent())
            dialog.characterSaved.connect(self._on_character_saved)
            dialog.sceneLinked.connect(self._on_scene_linked)
            dialog.sceneUnlinked.connect(self._on_scene_unlinked)
            
            # Store reference and handle window closing
            self.character_editor_windows[character_id] = dialog
            dialog.finished.connect(lambda: self.character_editor_windows.pop(character_id, None))
            
            dialog.show()
            self.characterEditorOpened.emit(character_id, character_name)
            return True
            
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to open character: {}").format(e))
            return False
    
    def create_character(self, name: str, project_manager) -> bool:
        """Create a new character."""
        if not self.character_manager or not self.current_project_id:
            return False
            
        try:
            # Get project data
            project_data = project_manager.get_project_data(self.current_project_id)
            if not project_data:
                return False
                
            character_id = self.character_manager.create_character(self.current_project_id, name)
            
            # Open character editor for new character
            character_data = self.character_manager.get_character(character_id)
            if character_data:
                all_scenes = self.scene_manager.get_scenes_by_project(self.current_project_id)
                
                # Check if window is already open
                if character_id in self.character_editor_windows:
                    window = self.character_editor_windows[character_id]
                    window.raise_()
                    window.activateWindow()
                    return True
                
                dialog = CharacterEditorDialog(character_data, all_scenes, self.parent())
                dialog.characterSaved.connect(self._on_character_saved)
                dialog.sceneLinked.connect(self._on_scene_linked)
                dialog.sceneUnlinked.connect(self._on_scene_unlinked)
                
                # Store reference and handle window closing
                self.character_editor_windows[character_id] = dialog
                dialog.finished.connect(lambda: self.character_editor_windows.pop(character_id, None))
                
                dialog.show()
            
            self.characterCreated.emit(name)
            self.charactersRefreshNeeded.emit()
            self.statusMessage.emit(_("Created character: {}").format(name))
            return True
            
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to create character: {}").format(e))
            return False
    
    def _on_character_saved(self, character_data: dict):
        """Handle character saved signal."""
        if not self.character_manager:
            return
            
        try:
            # Extract linked scenes before processing
            linked_scenes = character_data.pop('linked_scenes', [])
            
            if 'id' in character_data:
                # Update existing character
                character_id = character_data['id']
                update_data = {k: v for k, v in character_data.items() if k != 'id'}
                self.character_manager.update_character(character_id, **update_data)
                
                # Handle scene links for existing character
                self._process_scene_links(character_id, linked_scenes)
                
            self.characterSaved.emit(character_data)
            self.charactersRefreshNeeded.emit()
            self.statusMessage.emit(_("Character saved successfully"))
            
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to save character: {}").format(e))
    
    def _on_scene_linked(self, character_id: int, scene_id: int, role: str, importance: str):
        """Handle scene linked to character."""
        if not self.character_manager:
            return
            
        try:
            success = self.character_manager.link_character_to_scene_with_role(character_id, scene_id, role)
            if success:
                self.statusMessage.emit(_("Scene linked to character"))
            else:
                self.errorOccurred.emit(_("Warning"), _("Failed to link scene"))
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to link scene: {}").format(e))
    
    def _on_scene_unlinked(self, character_id: int, scene_id: int):
        """Handle scene unlinked from character."""
        if not self.character_manager:
            return
            
        try:
            success = self.character_manager.unlink_character_from_scene(character_id, scene_id)
            if success:
                self.statusMessage.emit(_("Scene unlinked from character"))
            else:
                self.errorOccurred.emit(_("Warning"), _("Failed to unlink scene"))
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to unlink scene: {}").format(e))
    
    def _process_scene_links(self, character_id: int, linked_scenes: list):
        """Process scene links for a character."""
        if not self.character_manager:
            return
            
        for scene_data in linked_scenes:
            scene_id = scene_data.get('id')
            role = scene_data.get('role', '')
            
            if scene_id:
                try:
                    success = self.character_manager.link_character_to_scene_with_role(character_id, scene_id, role)
                    if not success:
                        self.errorOccurred.emit(_("Warning"), 
                                             _("Failed to link character {} to scene {}").format(character_id, scene_id))
                except Exception as e:
                    self.errorOccurred.emit(_("Warning"), 
                                         _("Failed to link character {} to scene {}: {}").format(character_id, scene_id, str(e)))
    
    def get_characters_list(self, project_id: int) -> list:
        """Get list of characters for project."""
        if not self.character_manager:
            return []
        try:
            return self.character_manager.get_characters(project_id)
        except Exception as e:
            self.errorOccurred.emit(_("Error"), _("Failed to load characters: {}").format(e))
            return []