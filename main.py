#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                              QSplitter, QStatusBar, QMessageBox, QStackedWidget, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from core.project import ProjectManager
from core.scene import SceneManager
from core.character import CharacterManager
from core.location import LocationManager
from core.search import SearchManager
from ui.widgets import (ProjectsView, ProjectTreeView, Workspace, SettingsDialog,
                       CharactersGridView, CharacterEditorDialog)
from i18n import _


class PisarzApp(QMainWindow):
    """Główne okno aplikacji Pisarz."""
    
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.current_scene_manager = None
        self.current_character_manager = None
        self.current_location_manager = None
        self.current_search_manager = None
        self.current_project_path = None
        self.current_project_name = ""
        self.current_scene_id = None
        self.focus_mode = False
        
        # Non-modal editor windows
        self.character_editor_windows = {}  # character_id -> window
        self.location_editor_windows = {}   # location_id -> window
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.show_projects_view()
        
    def setup_ui(self) -> None:
        """Konfiguracja głównego interfejsu."""
        self.setWindowTitle(_("Pisarz - Writing Application"))
        self.setMinimumSize(1200, 800)
        
        # Widget centralny ze stack
        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)
        
        # === WIDOK PROJEKTÓW ===
        self.projects_view = ProjectsView()
        self.main_stack.addWidget(self.projects_view)
        
        # === WIDOK PROJEKTU (z nawigacją + workspace) ===
        self.project_widget = QWidget()
        project_layout = QHBoxLayout(self.project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter dla nawigacji i workspace
        splitter = QSplitter(Qt.Orientation.Horizontal)
        project_layout.addWidget(splitter)
        
        # Drzewko nawigacji w projekcie
        self.project_tree = ProjectTreeView()
        splitter.addWidget(self.project_tree)
        
        # Obszar roboczy
        self.workspace = Workspace()
        splitter.addWidget(self.workspace)
        
        # Proporcje splitter
        splitter.setSizes([300, 900])
        
        self.main_stack.addWidget(self.project_widget)
        
        # Pasek stanu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(_("Select project to start"))
        
    def setup_connections(self) -> None:
        """Konfiguracja połączeń sygnałów."""
        # Widok projektów
        self.projects_view.projectSelected.connect(self.on_project_selected)
        self.projects_view.newProjectRequested.connect(self.create_new_project)
        self.projects_view.settingsRequested.connect(self.show_settings)
        
        # Drzewko projektu
        self.project_tree.sceneSelected.connect(self.on_scene_selected)
        self.project_tree.characterSelected.connect(self.on_character_selected)
        self.project_tree.locationSelected.connect(self.on_location_selected)
        self.project_tree.categorySelected.connect(self.on_category_selected)
        self.project_tree.newSceneRequested.connect(self.create_new_scene)
        self.project_tree.newCharacterRequested.connect(self.create_new_character)
        self.project_tree.newLocationRequested.connect(self.create_new_location)
        self.project_tree.searchRequested.connect(self.on_search_requested)
        self.project_tree.backToProjectsRequested.connect(self.show_projects_view)
        
        # Workspace
        self.workspace.saveRequested.connect(self.save_scene_content)
        self.workspace.sceneSelectedFromGrid.connect(self.on_scene_selected)
        self.workspace.characterSelectedFromGrid.connect(self.on_character_selected)
        self.workspace.locationSelectedFromGrid.connect(self.on_location_selected)
        self.workspace.newCharacterRequestedFromGrid.connect(self.create_new_character)
        self.workspace.newLocationRequestedFromGrid.connect(self.create_new_location)
        self.workspace.newSceneRequestedFromGrid.connect(self.create_new_scene)
        self.workspace.sceneRenameRequestedFromGrid.connect(self.on_scene_rename_requested)
        self.workspace.focusModeRequested.connect(self.toggle_focus_mode)
        
        # Scene context panel signals
        self.workspace.characterAddedToScene.connect(self.on_character_added_to_scene)
        self.workspace.characterRemovedFromScene.connect(self.on_character_removed_from_scene)
        self.workspace.locationAddedToScene.connect(self.on_location_added_to_scene)
        self.workspace.locationRemovedFromScene.connect(self.on_location_removed_from_scene)
        self.workspace.newCharacterRequestedFromScene.connect(self.create_new_character)
        self.workspace.newLocationRequestedFromScene.connect(self.create_new_location)
        self.workspace.characterSelectedFromScene.connect(self.on_character_selected_from_scene)
        self.workspace.locationSelectedFromScene.connect(self.on_location_selected_from_scene)
        
        # Search signals
        self.workspace.searchRequested.connect(self.perform_search)
        self.workspace.searchResultSelected.connect(self.on_search_result_selected)
        
    def setup_shortcuts(self) -> None:
        """Konfiguracja skrótów klawiszowych."""
        # F11 - przełącz tryb fokusu
        self.focus_shortcut = QShortcut(QKeySequence("F11"), self)
        self.focus_shortcut.activated.connect(self.toggle_focus_mode)
        
        # Escape - wyjdź z trybu fokusu (tylko gdy jest aktywny)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.exit_focus_mode_if_active)
        
    def exit_focus_mode_if_active(self):
        """Wyjdź z trybu fokusu tylko jeśli jest aktywny."""
        if self.focus_mode:
            self.toggle_focus_mode()
        
    def show_projects_view(self) -> None:
        """Pokaż widok projektów."""
        try:
            projects = self.project_manager.list_projects()
            self.projects_view.load_projects(projects)
            self.main_stack.setCurrentIndex(0)
            self.status_bar.showMessage(_("Projects list ({} projects)").format(len(projects)))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load projects: {}").format(e))
            
    def on_project_selected(self, project_path: str, project_name: str) -> None:
        """Obsługa wyboru projektu - przejście do widoku projektu."""
        self.current_project_path = project_path
        self.current_project_name = project_name
        self.current_scene_id = None
        self.current_view_state = "welcome"
        self.current_category = None
        
        try:
            # Załaduj dane projektu
            self.current_scene_manager = SceneManager(Path(project_path))
            self.current_character_manager = CharacterManager(Path(project_path))
            self.current_location_manager = LocationManager(Path(project_path) / "pisarz.db")
            self.current_search_manager = SearchManager(Path(project_path) / "pisarz.db")
            
            project_data = self.project_manager.get_project_data(Path(project_path))
            project_id = project_data['id']
            
            scenes = self.current_scene_manager.list_scenes()
            characters = self.current_character_manager.get_characters(project_id)
            locations = self.current_location_manager.get_locations(project_id)
            
            # Zaktualizuj drzewko nawigacji
            self.project_tree.update_project_name(project_name)
            self.project_tree.load_scenes(scenes, preserve_selection=False)  # Nowy projekt, nie zachowuj selekcji
            self.project_tree.load_characters(characters, preserve_selection=False)
            
            # Convert location objects to dictionaries for display
            location_dicts = [loc.__dict__ for loc in locations]
            self.project_tree.load_locations(location_dicts, preserve_selection=False)
            
            # Pokaż ekran powitalny w workspace
            self.workspace.show_welcome()
            
            # Przełącz na widok projektu
            self.main_stack.setCurrentIndex(1)
            
            self.status_bar.showMessage(_("Project: {} ({} scenes)").format(project_name, len(scenes)))
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load projects: {}").format(e))
            self.show_projects_view()
            
    def on_category_selected(self, category: str) -> None:
        """Obsługa wyboru kategorii - pokaż widok kafelków."""
        if not self.current_scene_manager:
            return
            
        try:
            if category == "scenes":
                scenes = self.current_scene_manager.list_scenes()
                self.workspace.show_scenes_grid(scenes, self.current_character_manager, self.current_location_manager)
                self.status_bar.showMessage(_("Scenes view ({} scenes)").format(len(scenes)))
            elif category == "characters":
                if not self.current_character_manager:
                    return
                project_data = self.project_manager.get_project_data(Path(self.current_project_path))
                characters = self.current_character_manager.get_characters(project_data['id'])
                self.workspace.show_characters_grid(characters, self.current_location_manager)
                self.status_bar.showMessage(_("Characters view ({} characters)").format(len(characters)))
            elif category == "locations":
                if not self.current_location_manager:
                    return
                project_data = self.project_manager.get_project_data(Path(self.current_project_path))
                self.workspace.show_locations_grid(self.current_location_manager, project_data['id'])
                locations = self.current_location_manager.get_locations(project_data['id'])
                self.status_bar.showMessage(_("Locations view ({} locations)").format(len(locations)))
            elif category == "search":
                self.workspace.show_search_view()
                self.status_bar.showMessage(_("Search view - Enter text to search across your project"))
            else:
                self.workspace.show_welcome()
                self.status_bar.showMessage(_("View {} (function unavailable)").format(category))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load view: {}").format(e))
            
    def on_scene_selected(self, scene_id: int, scene_title: str) -> None:
        """Obsługa wyboru sceny."""
        self.current_scene_id = scene_id
        
        try:
            scene_data = self.current_scene_manager.get_scene(scene_id)
            content = scene_data.get("content_rtf", f"<p>{_('Start writing your scene...')}</p>") if scene_data else f"<p>{_('Scene loading error')}</p>"
            
            # Get project ID for managers
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            project_id = project_data['id'] if project_data else None
            
            # Open editor with context panel support
            self.workspace.open_editor_for_scene(
                content, 
                scene_id=scene_id,
                character_manager=self.current_character_manager,
                location_manager=self.current_location_manager,
                project_id=project_id
            )
            self.status_bar.showMessage(_("Editing scene: {}").format(scene_title))
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open scene: {}").format(e))
            
    def save_scene_content(self, content: str) -> None:
        """Zapisz zawartość sceny."""
        if not self.current_scene_manager or not self.current_scene_id:
            return
            
        try:
            success = self.current_scene_manager.update_scene(self.current_scene_id, content_rtf=content)
            if success:
                self.status_bar.showMessage(_("Scene saved successfully"))
                self._refresh_scenes_data()
            else:
                self.status_bar.showMessage(_("Failed to save scene"))
                QMessageBox.warning(self, _("Warning"), _("Failed to save scene"))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to save scene: {}").format(e))
            
    def _refresh_scenes_data(self):
        """Odśwież dane scen zachowując selekcję."""
        try:
            scenes = self.current_scene_manager.list_scenes()
            self.project_tree.load_scenes(scenes, preserve_selection=True)
            
            # Odśwież kafelki jeśli są widoczne
            if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
                self.workspace.scenes_grid_view.load_scenes(scenes)
                
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load view: {}").format(e))
            
    def _refresh_characters_data(self):
        """Odśwież dane postaci zachowując selekcję."""
        try:
            if not self.current_character_manager:
                return
                
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            characters = self.current_character_manager.get_characters(project_data['id'])
            self.project_tree.load_characters(characters, preserve_selection=True)
            
            # Odśwież kafelki jeśli są widoczne
            if hasattr(self.workspace, 'characters_grid_view') and self.workspace.characters_grid_view:
                self.workspace.characters_grid_view.set_location_manager(self.current_location_manager)
                self.workspace.characters_grid_view.load_characters(characters)
                
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load characters: {}").format(e))
    
    def _refresh_locations_data(self):
        """Odśwież dane lokacji zachowując selekcję."""
        try:
            if not self.current_location_manager:
                return
                
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            locations = self.current_location_manager.get_locations(project_data['id'])
            location_dicts = [loc.__dict__ for loc in locations]
            self.project_tree.load_locations(location_dicts, preserve_selection=True)
            
            # Odśwież kafelki jeśli są widoczne
            if hasattr(self.workspace, 'locations_grid_view') and self.workspace.locations_grid_view:
                self.workspace.locations_grid_view.refresh_locations()
                
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load locations: {}").format(e))
            
    def create_new_project(self, name: str) -> None:
        """Stwórz nowy projekt."""
        try:
            project_path = self.project_manager.create_project(name)
            self.show_projects_view()  # Odśwież listę projektów
            self.status_bar.showMessage(_("Created project: {}").format(name))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to create project: {}").format(e))
            
    def create_new_scene(self, title: str) -> None:
        """Stwórz nową scenę."""
        if not self.current_scene_manager:
            return
            
        try:
            scene_id = self.current_scene_manager.create_scene(title)
            self._refresh_scenes_data()
            self.status_bar.showMessage(_("Created scene: {}").format(title))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to create scene: {}").format(e))
    
    def on_scene_rename_requested(self, scene_id: int, new_title: str) -> None:
        """Handle scene rename request."""
        if not self.current_scene_manager:
            return
            
        try:
            success = self.current_scene_manager.update_scene(scene_id, title=new_title)
            if success:
                self._refresh_scenes_data()
                self.status_bar.showMessage(_("Scene renamed to: {}").format(new_title))
            else:
                QMessageBox.warning(self, _("Warning"), _("Failed to rename scene"))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to rename scene: {}").format(e))
            
    def on_character_selected(self, character_id, character_name):
        """Obsługa wyboru postaci - otwiera edytor postaci."""
        if not self.current_character_manager:
            return
            
        try:
            # Pobierz dane postaci
            character_data = self.current_character_manager.get_character(character_id)
            if not character_data:
                QMessageBox.warning(self, _("Warning"), _("Character not found"))
                return
                
            # Pobierz powiązane sceny
            linked_scenes = self.current_character_manager.get_scenes_for_character(character_id)
            character_data['scenes'] = linked_scenes
            
            # Pobierz wszystkie sceny w projekcie dla linkowania
            all_scenes = self.current_scene_manager.list_scenes()
            
            # Otwórz editor postaci (non-modal, always on top)
            character_id = character_data.get('id')
            
            # Check if window is already open for this character
            if character_id in self.character_editor_windows:
                window = self.character_editor_windows[character_id]
                window.raise_()
                window.activateWindow()
                return
            
            dialog = CharacterEditorDialog(character_data, all_scenes, self)
            dialog.characterSaved.connect(self._on_character_saved)
            dialog.sceneLinked.connect(self._on_scene_linked)
            dialog.sceneUnlinked.connect(self._on_scene_unlinked)
            
            # Store reference and handle window closing
            if character_id:
                self.character_editor_windows[character_id] = dialog
                dialog.finished.connect(lambda: self.character_editor_windows.pop(character_id, None))
            
            dialog.show()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open character: {}").format(e))
            
    def create_new_character(self, name):
        """Stwórz nową postać."""
        if not self.current_character_manager:
            return
            
        try:
            # Pobierz ID projektu
            if not self.current_project_path:
                return
                
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            if not project_data:
                return
                
            character_id = self.current_character_manager.create_character(
                project_data['id'], name
            )
            
            # Open character editor for new character to allow scene linking
            character_data = self.current_character_manager.get_character(character_id)
            if character_data:
                all_scenes = self.current_scene_manager.list_scenes()
                
                # Check if window is already open for this character
                if character_id in self.character_editor_windows:
                    window = self.character_editor_windows[character_id]
                    window.raise_()
                    window.activateWindow()
                    return
                
                dialog = CharacterEditorDialog(character_data, all_scenes, self)
                dialog.characterSaved.connect(self._on_character_saved)
                dialog.sceneLinked.connect(self._on_scene_linked)
                dialog.sceneUnlinked.connect(self._on_scene_unlinked)
                
                # Store reference and handle window closing
                self.character_editor_windows[character_id] = dialog
                dialog.finished.connect(lambda: self.character_editor_windows.pop(character_id, None))
                
                dialog.show()
            
            self._refresh_characters_data()
            self.status_bar.showMessage(_("Created character: {}").format(name))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to create character: {}").format(e))
            
    def _on_character_saved(self, character_data):
        """Obsługa zapisania postaci."""
        if not self.current_character_manager:
            return
            
        try:
            # Extract linked scenes before processing
            linked_scenes = character_data.pop('linked_scenes', [])
            
            if 'id' in character_data:
                # Aktualizuj istniejącą postać - usunięcie id z danych
                character_id = character_data['id']
                update_data = {k: v for k, v in character_data.items() if k != 'id'}
                self.current_character_manager.update_character(
                    character_id, **update_data
                )
                
                # Handle scene links for existing character
                self._process_scene_links(character_id, linked_scenes)
            else:
                # This shouldn't happen for editing, but handle just in case
                pass
                
            self._refresh_characters_data()
            self.status_bar.showMessage(_("Character saved successfully"))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to save character: {}").format(e))
            
    def _on_scene_linked(self, character_id, scene_id, role, importance):
        """Handle scene linked to character."""
        if not self.current_character_manager:
            return
            
        try:
            success = self.current_character_manager.link_character_to_scene_with_role(
                character_id, scene_id, role
            )
            if success:
                self.status_bar.showMessage(_("Scene linked to character"))
            else:
                QMessageBox.warning(self, _("Warning"), _("Failed to link scene"))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to link scene: {}").format(e))
            
    def _on_scene_unlinked(self, character_id, scene_id):
        """Handle scene unlinked from character."""
        if not self.current_character_manager:
            return
            
        try:
            success = self.current_character_manager.unlink_character_from_scene(
                character_id, scene_id
            )
            if success:
                self.status_bar.showMessage(_("Scene unlinked from character"))
            else:
                QMessageBox.warning(self, _("Warning"), _("Failed to unlink scene"))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to unlink scene: {}").format(e))
            
    def _process_scene_links(self, character_id, linked_scenes):
        """Process scene links for a character."""
        if not self.current_character_manager:
            return
            
        for scene_data in linked_scenes:
            scene_id = scene_data.get('id')
            role = scene_data.get('role', '')
            
            if scene_id:
                try:
                    success = self.current_character_manager.link_character_to_scene_with_role(
                        character_id, scene_id, role
                    )
                    if not success:
                        # This is already shown in the warning dialog below
                        pass
                except Exception as e:
                    QMessageBox.warning(self, _("Warning"), 
                                      _("Failed to link character {} to scene {}: {}").format(character_id, scene_id, str(e)))
    
    def on_location_selected(self, location_id, location_name):
        """Obsługa wyboru lokacji - otwiera edytor lokacji."""
        if not self.current_location_manager:
            return
            
        try:
            # Pobierz dane lokacji
            location = self.current_location_manager.get_location(location_id)
            if not location:
                QMessageBox.warning(self, _("Warning"), _("Location not found"))
                return
            
            # Otwórz editor lokacji (non-modal, always on top)
            from ui.widgets.location_editor_dialog import LocationEditorDialog
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            
            # Check if window is already open for this location
            if location_id in self.location_editor_windows:
                window = self.location_editor_windows[location_id]
                window.raise_()
                window.activateWindow()
                return
            
            dialog = LocationEditorDialog(
                self.current_location_manager, 
                project_data['id'], 
                location=location,
                parent=self
            )
            
            # Store reference and handle window closing
            self.location_editor_windows[location_id] = dialog
            dialog.finished.connect(lambda: self.location_editor_windows.pop(location_id, None))
            dialog.accepted.connect(lambda: (
                self._refresh_locations_data(),
                self.status_bar.showMessage(_("Location updated: {}").format(location_name))
            ))
            
            dialog.show()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open location: {}").format(e))
    
    def create_new_location(self, name):
        """Stwórz nową lokację."""
        if not self.current_location_manager:
            return
            
        try:
            # Pobierz ID projektu
            if not self.current_project_path:
                return
                
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            if not project_data:
                return
                
            # If name is empty (from signal without name), open dialog
            if not name or name.strip() == "":
                from ui.widgets.location_editor_dialog import LocationEditorDialog
                dialog = LocationEditorDialog(
                    self.current_location_manager, 
                    project_data['id'],
                    parent=self
                )
                
                # For new locations, we don't need to track by ID since ID doesn't exist yet
                dialog.accepted.connect(lambda: (
                    self._refresh_locations_data(),
                    self.status_bar.showMessage(_("Created new location"))
                ))
                
                dialog.show()
            else:
                # Create location with the provided name
                location_id = self.current_location_manager.create_location(
                    project_data['id'], name
                )
                
                if location_id:
                    self._refresh_locations_data()
                    self.status_bar.showMessage(_("Created location: {}").format(name))
                else:
                    QMessageBox.warning(self, _("Warning"), _("Failed to create location"))
                    
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to create location: {}").format(e))
    
    # Scene context panel handlers
    
    def on_character_added_to_scene(self, character_id, role):
        """Handle character added to scene from context panel."""
        self.status_bar.showMessage(_("Character linked to scene with role: {}").format(role))
        # The linking is already done in the context panel, just update UI if needed
        if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
            self.workspace.current_editor.refresh_context_panel()
    
    def on_character_removed_from_scene(self, character_id):
        """Handle character removed from scene."""
        self.status_bar.showMessage(_("Character unlinked from scene"))
        # The unlinking is already done in the context panel, just update UI if needed
        if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
            self.workspace.current_editor.refresh_context_panel()
    
    def on_location_added_to_scene(self, location_id, role):
        """Handle location added to scene from context panel."""
        self.status_bar.showMessage(_("Location linked to scene with role: {}").format(role))
        # The linking is already done in the context panel, just update UI if needed
        if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
            self.workspace.current_editor.refresh_context_panel()
    
    def on_location_removed_from_scene(self, location_id):
        """Handle location removed from scene."""
        self.status_bar.showMessage(_("Location unlinked from scene"))
        # The unlinking is already done in the context panel, just update UI if needed
        if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
            self.workspace.current_editor.refresh_context_panel()
    
    def on_character_selected_from_scene(self, character_id):
        """Handle character selected for editing from scene context panel."""
        # Get character name for the signal
        if self.current_character_manager:
            character = self.current_character_manager.get_character(character_id)
            if character:
                character_name = character.get('name', _('Unknown Character'))
                self.on_character_selected(character_id, character_name)
    
    def on_location_selected_from_scene(self, location_id):
        """Handle location selected for editing from scene context panel."""
        # Get location name for the signal
        if self.current_location_manager:
            location = self.current_location_manager.get_location(location_id)
            if location:
                self.on_location_selected(location_id, location.name)
    
    def on_search_requested(self):
        """Handle search category selection from tree."""
        if not self.current_search_manager:
            return
        self.workspace.show_search_view()
        self.status_bar.showMessage(_("Search view - Enter text to search across your project"))
    
    def perform_search(self, query, filter_type):
        """Perform search and display results."""
        if not self.current_search_manager or not query.strip():
            return
            
        try:
            # Get project ID
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            project_id = project_data['id'] if project_data else None
            
            if not project_id:
                return
            
            # Perform search based on filter type
            if filter_type == "scenes":
                results = self.current_search_manager.search_scenes(query, project_id, limit=50)
                from core.search import SearchResults
                search_results = SearchResults(query=query, results=results, total_count=len(results), search_time_ms=0.0)
            elif filter_type == "characters":
                results = self.current_search_manager.search_characters(query, project_id, limit=50)
                from core.search import SearchResults
                search_results = SearchResults(query=query, results=results, total_count=len(results), search_time_ms=0.0)
            elif filter_type == "locations":
                results = self.current_search_manager.search_locations(query, project_id, limit=50)
                from core.search import SearchResults
                search_results = SearchResults(query=query, results=results, total_count=len(results), search_time_ms=0.0)
            else:  # "all"
                search_results = self.current_search_manager.search_all(query, project_id, limit=100)
            
            # Load results into search view
            self.workspace.load_search_results(search_results)
            
            # Update status
            result_count = len(search_results.results) if hasattr(search_results, 'results') else len(search_results)
            self.status_bar.showMessage(_("Search completed - Found {} results for '{}'").format(result_count, query))
            
        except Exception as e:
            QMessageBox.critical(self, _("Search Error"), _("Failed to perform search: {}").format(e))
            self.status_bar.showMessage(_("Search failed"))
    
    def on_search_result_selected(self, result_type, result_id, title, search_query):
        """Handle selection of a search result."""
        try:
            if result_type == "scene":
                self.on_scene_selected_with_search(result_id, title, search_query)
            elif result_type == "character":
                self.on_character_selected(result_id, title)
            elif result_type == "location":
                self.on_location_selected(result_id, title)
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open search result: {}").format(e))
    
    def on_scene_selected_with_search(self, scene_id, scene_title, search_query):
        """Handle scene selection from search results with text highlighting."""
        self.current_scene_id = scene_id
        
        try:
            scene_data = self.current_scene_manager.get_scene(scene_id)
            content = scene_data.get("content_rtf", f"<p>{_('Start writing your scene...')}</p>") if scene_data else f"<p>{_('Scene loading error')}</p>"
            
            # Get project ID for managers
            project_data = self.project_manager.get_project_data(Path(self.current_project_path))
            project_id = project_data['id'] if project_data else None
            
            # Open editor with context panel support
            self.workspace.open_editor_for_scene(
                content, 
                scene_id=scene_id,
                character_manager=self.current_character_manager,
                location_manager=self.current_location_manager,
                project_id=project_id
            )
            
            # Find and highlight the search term in the editor
            if search_query and self.workspace.current_editor:
                self.workspace.current_editor.find_and_highlight_text(search_query)
            
            self.status_bar.showMessage(_("Editing scene: {} (search: '{}')").format(scene_title, search_query))
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open scene: {}").format(e))
            
    def show_settings(self):
        """Pokaż dialog ustawień."""
        dialog = SettingsDialog(self)
        dialog.themeChanged.connect(self.on_theme_changed)
        dialog.languageChanged.connect(self.on_language_changed)
        dialog.exec()
        
    def on_theme_changed(self, theme_name):
        """Obsługa zmiany motywu."""
        self.status_bar.showMessage(_("Applied theme: {}").format(theme_name))
        
        # Odśwież kafelki w widokach
        self.projects_view.refresh_theme()
        if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
            self.workspace.scenes_grid_view.refresh_theme()
            
        # Odśwież ikony w drzewku
        self.project_tree.refresh_icons()
        
        # Jeśli jesteśmy w trybie fokusu, odśwież style trybu fokusu
        if self.focus_mode:
            self._apply_focus_window_style()
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                self._apply_focus_mode_style()
                
    def on_language_changed(self, language_code):
        """Obsługa zmiany języka."""
        # Zapisz wybrany język do ustawień
        from PySide6.QtCore import QSettings
        settings = QSettings()
        settings.setValue("language", language_code)
        
        # Informacja o konieczności restartu
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            _("Language Changed"), 
            _("Language has been changed. Please restart the application to see changes.")
        )
        
    def toggle_focus_mode(self):
        """Przełącz tryb fokusu pisania."""
        self.focus_mode = not self.focus_mode
        
        if self.focus_mode:
            # Włącz tryb fokusu
            self.showFullScreen()
            self.status_bar.hide()
            
            # Ukryj nawigację po lewej stronie
            splitter = self.project_widget.findChild(QSplitter)
            if splitter:
                splitter.setSizes([0, 1200])  # Ukryj lewy panel całkowicie
                
            # Zastosuj styl zgodny z motywem do całego okna
            self._apply_focus_window_style()
                
            # Zastosuj styl do edytora
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                self._apply_focus_mode_style()
                
        else:
            # Wyłącz tryb fokusu
            self.showNormal()
            self.status_bar.show()
            
            # Przywróć nawigację
            splitter = self.project_widget.findChild(QSplitter)
            if splitter:
                splitter.setSizes([300, 900])  # Przywróć normalny podział
                
            # Przywróć normalny styl okna
            self._remove_focus_window_style()
                
            # Przywróć normalny styl edytora
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                self._remove_focus_mode_style()
    
    def _apply_focus_mode_style(self):
        """Zastosuj minimalistyczny styl w trybie fokusu."""
        editor = self.workspace.current_editor
        if not editor:
            return
            
        # Ukryj toolbar w trybie fokusu
        toolbar_widget = None
        for child in editor.findChildren(QWidget):
            if isinstance(child.layout(), QHBoxLayout) and child.findChild(QPushButton):
                toolbar_widget = child
                break
                
        if toolbar_widget:
            toolbar_widget.hide()
            
        # Pobierz kolory z aktualnego motywu
        from ui.styles.themes import ThemeManager
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        # Zastosuj minimalistyczny styl zgodny z motywem
        editor.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors["background"]};
                color: {colors["text"]};
                border: none;
                padding: 50px;
                font-size: 14pt;
                line-height: 1.6;
                selection-background-color: {colors["accent"]};
                selection-color: white;
            }}
        """)
        
    def _remove_focus_mode_style(self):
        """Usuń styl trybu fokusu."""
        editor = self.workspace.current_editor
        if not editor:
            return
            
        # Pokaż toolbar
        toolbar_widget = None
        for child in editor.findChildren(QWidget):
            if isinstance(child.layout(), QHBoxLayout) and child.findChild(QPushButton):
                toolbar_widget = child
                break
                
        if toolbar_widget:
            toolbar_widget.show()
            
        # Przywróć normalny styl
        editor.text_edit.setStyleSheet("")
        
    def _apply_focus_window_style(self):
        """Zastosuj styl okna w trybie fokusu."""
        from ui.styles.themes import ThemeManager
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        # Zastosuj tło zgodne z motywem
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
            }}
            QWidget {{
                background-color: {colors["background"]};
                color: {colors["text"]};
            }}
        """)
        
    def _remove_focus_window_style(self):
        """Usuń styl okna trybu fokusu."""
        # Przywróć domyślny styl
        self.setStyleSheet("")


def main():
    app = QApplication(sys.argv)
    
    # Konfiguracja aplikacji
    app.setApplicationName("Pisarz")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Pisarz")
    
    # Inicjalizacja i18n - ustaw język z ustawień systemowych lub domyślny
    import i18n
    from PySide6.QtCore import QSettings
    settings = QSettings()
    saved_language = settings.value("language", "en_US")
    i18n.set_language(saved_language)
    
    # Ustaw większą domyślną czcionkę dla całego interfejsu
    from PySide6.QtGui import QFont
    font = QFont()
    font.setPointSize(10)  # Zwiększ z domyślnej 8-9 do 10pt
    app.setFont(font)
    
    # Załaduj i zastosuj zapisany motyw
    from ui.styles.themes import ThemeManager
    theme_manager = ThemeManager()
    theme_manager.set_theme(theme_manager.get_current_theme())
    
    # Stwórz i pokaż główne okno
    window = PisarzApp()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())