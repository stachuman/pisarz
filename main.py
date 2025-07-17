#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QSplitter, QStatusBar, QMessageBox, QStackedWidget, QMenuBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QAction

from core.error_handler import get_error_handler, ErrorLevel, ErrorCategory
from core.logging_config import setup_logging

from controllers.app_project_controller import AppProjectController
from controllers.app_scene_controller import AppSceneController
from controllers.app_character_controller import AppCharacterController
from controllers.app_location_controller import AppLocationController
from controllers.app_search_controller import AppSearchController
from controllers.app_ui_controller import AppUIController
from controllers.app_focus_controller import AppFocusController
from controllers.app_llm_controller import AppLLMController
from ui.widgets import (ProjectsView, ProjectTreeView, Workspace, SettingsDialog,
                       CharactersGridView, CharacterEditorDialog, ProjectPropertiesDialog,
                       LLMAssistantPanel)
from i18n import _


class PisarzApp(QMainWindow):
    """Główne okno aplikacji Pisarz."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize error handling and logging
        self.error_handler = get_error_handler()
        self.logger = setup_logging()
        
        # Initialize controllers
        self.project_controller = AppProjectController(self)
        self.scene_controller = AppSceneController(self)
        self.character_controller = AppCharacterController(self)
        self.location_controller = AppLocationController(self)
        self.search_controller = AppSearchController(self)
        self.ui_controller = AppUIController(self, self)
        self.focus_controller = AppFocusController(self, self)
        self.llm_controller = AppLLMController(self)
        
        # Set global LLM controller instance
        from controllers.app_llm_controller import set_llm_controller
        set_llm_controller(self.llm_controller)
        
        # Initialize theme
        self.focus_controller.initialize_theme()
        
        # State variables
        self.current_view_state = "welcome"
        self.current_category = None
        
        # Non-modal editor windows
        self.location_editor_windows = {}   # location_id -> window
        
        self.setup_ui()
        self.setup_controllers()
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
        project_layout = QVBoxLayout(self.project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        
        # Główny splitter pionowy (góra: nawigacja+workspace, dół: AI assistant)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        project_layout.addWidget(main_splitter)
        
        # Górny widget zawierający nawigację i workspace
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter poziomy dla nawigacji i workspace
        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_layout.addWidget(horizontal_splitter)
        
        # Drzewko nawigacji w projekcie
        self.project_tree = ProjectTreeView()
        horizontal_splitter.addWidget(self.project_tree)
        
        # Obszar roboczy
        self.workspace = Workspace()
        horizontal_splitter.addWidget(self.workspace)
        
        # Proporcje splitter poziomego (nawigacja vs workspace)
        horizontal_splitter.setSizes([300, 900])
        
        # Dodaj górny widget do głównego splitteru
        main_splitter.addWidget(top_widget)
        
        # LLM Assistant Panel (teraz na dole)
        self.llm_panel = LLMAssistantPanel()
        self.llm_panel.setMaximumHeight(300)
        self.llm_panel.setVisible(False)  # Hidden by default
        main_splitter.addWidget(self.llm_panel)
        
        # Proporcje głównego splitteru (góra vs dół)
        main_splitter.setSizes([700, 300])
        
        self.main_stack.addWidget(self.project_widget)
        
        # Menu bar
        self.setup_menu_bar()
        
        # Pasek stanu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(_("Select project to start"))
        
    def setup_controllers(self) -> None:
        """Setup controller references and connections."""
        # Setup UI controller with components
        self.ui_controller.setup_ui_components(
            self.main_stack, self.projects_view, self.project_tree, 
            self.workspace, self.project_widget
        )
        
        # Setup focus controller with components
        self.focus_controller.setup_components(
            self.project_widget, self.workspace, self.status_bar, self.llm_panel
        )
        
        # Initialize LLM controller
        self.llm_controller.initialize()
        self.llm_panel.set_llm_controller(self.llm_controller)
        
        # Connect controller signals
        self._connect_controller_signals()
        
    def setup_menu_bar(self):
        """Setup the menu bar with AI Assistant toggle."""
        menubar = self.menuBar()
        
        # Tools menu
        tools_menu = menubar.addMenu(_("Tools"))
        
        # AI Assistant toggle action
        self.ai_assistant_action = QAction(_("AI Assistant"), self)
        self.ai_assistant_action.setCheckable(True)
        self.ai_assistant_action.setChecked(False)
        self.ai_assistant_action.setShortcut(QKeySequence("Ctrl+Alt+A"))
        self.ai_assistant_action.triggered.connect(self.toggle_ai_assistant)
        tools_menu.addAction(self.ai_assistant_action)
        
        # Settings action (if not already present)
        if not hasattr(self, 'settings_action'):
            tools_menu.addSeparator()
            settings_action = QAction(_("Settings"), self)
            settings_action.setShortcut(QKeySequence("Ctrl+,"))
            settings_action.triggered.connect(self.show_settings)
            tools_menu.addAction(settings_action)
    
    def toggle_ai_assistant(self):
        """Toggle AI Assistant panel visibility."""
        is_visible = self.llm_panel.isVisible()
        self.llm_panel.setVisible(not is_visible)
        self.ai_assistant_action.setChecked(not is_visible)
        
        # Update editor button state
        self.workspace.set_ai_assistant_state(not is_visible)
        
        # Notify focus controller about visibility change
        self.focus_controller.on_ai_assistant_visibility_changed(not is_visible)
        
        # Update status message
        if not is_visible:
            self.status_bar.showMessage(_("AI Assistant panel opened"))
        else:
            self.status_bar.showMessage(_("AI Assistant panel closed"))
        
        self.logger.info(f"AI Assistant panel {'opened' if not is_visible else 'closed'}")
        
    def _connect_controller_signals(self) -> None:
        """Connect signals from controllers."""
        # Project controller signals
        self.project_controller.projectDataLoaded.connect(self._on_project_data_loaded)
        self.project_controller.projectCreated.connect(self._on_project_created)
        self.project_controller.statusMessage.connect(self.status_bar.showMessage)
        self.project_controller.errorOccurred.connect(self._show_error_message)
        
        # Scene controller signals
        self.scene_controller.sceneOpened.connect(self._on_scene_opened)
        self.scene_controller.sceneSaved.connect(self._on_scene_saved)
        self.scene_controller.sceneCreated.connect(self._on_scene_created)
        self.scene_controller.sceneRenamed.connect(self._on_scene_renamed)
        self.scene_controller.scenesRefreshNeeded.connect(self._refresh_scenes_data)
        self.scene_controller.statusMessage.connect(self.status_bar.showMessage)
        self.scene_controller.errorOccurred.connect(self._show_error_message)
        
        # Character controller signals
        self.character_controller.characterCreated.connect(self._on_character_created)
        self.character_controller.charactersRefreshNeeded.connect(self._refresh_characters_data)
        self.character_controller.statusMessage.connect(self.status_bar.showMessage)
        self.character_controller.errorOccurred.connect(self._show_error_message)
        
        # Location controller signals
        self.location_controller.locationCreated.connect(self._on_location_created)
        self.location_controller.locationUpdated.connect(self._on_location_updated)
        self.location_controller.locationsRefreshNeeded.connect(self._refresh_locations_data)
        self.location_controller.statusMessage.connect(self.status_bar.showMessage)
        self.location_controller.errorOccurred.connect(self._show_error_message)
        
        # LLM assistant panel signals
        self.llm_panel.insertTextRequested.connect(self._on_insert_text_requested)
        
        # Search controller signals
        self.search_controller.searchResultsReady.connect(self._on_search_results_ready)
        self.search_controller.searchRequested.connect(self._on_search_requested)
        self.search_controller.statusMessage.connect(self.status_bar.showMessage)
        self.search_controller.errorOccurred.connect(self._show_error_message)
        
        # UI controller signals
        self.ui_controller.categorySelected.connect(self._on_category_selected)
        self.ui_controller.statusMessage.connect(self.status_bar.showMessage)
        self.ui_controller.errorOccurred.connect(self._show_error_message)
        
        # Focus controller signals
        self.focus_controller.statusMessage.connect(self.status_bar.showMessage)
        
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
        self.project_tree.projectPropertiesRequested.connect(self.show_project_properties)
        
        # Workspace
        self.workspace.saveRequested.connect(self.save_scene_content)
        self.workspace.autoSaveRequested.connect(self.auto_save_scene_content)
        self.workspace.sceneSelectedFromGrid.connect(self.on_scene_selected)
        self.workspace.characterSelectedFromGrid.connect(self.on_character_selected)
        self.workspace.locationSelectedFromGrid.connect(self.on_location_selected)
        self.workspace.newCharacterRequestedFromGrid.connect(self.create_new_character)
        self.workspace.newLocationRequestedFromGrid.connect(self.create_new_location)
        self.workspace.newSceneRequestedFromGrid.connect(self.create_new_scene)
        self.workspace.sceneRenameRequestedFromGrid.connect(self.on_scene_rename_requested)
        self.workspace.focusModeRequested.connect(self.toggle_focus_mode)
        self.workspace.aiAssistantToggled.connect(self.toggle_ai_assistant)
        self.workspace.textSelectionChanged.connect(self.on_text_selection_changed)
        
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
        self.focus_controller.exit_focus_mode_if_active()
    
    def closeEvent(self, event):
        """Handle application close event - auto-save current scene."""
        try:
            # Auto-save current scene before closing
            current_scene_id = self.scene_controller.get_current_scene_id()
            if current_scene_id and self.workspace.current_editor:
                if self.workspace.current_editor.has_changes():
                    content = self.workspace.current_editor.get_content()
                    success = self.scene_controller.save_scene_content(content, is_auto_save=True)
                    if success:
                        self.status_bar.showMessage(_("Auto-saved scene before closing"), 1000)
        except Exception as e:
            # Don't block application closing if auto-save fails
            self.error_handler.log_warning(f"Auto-save failed on close: {e}", 
                                         ErrorCategory.SYSTEM, show_to_user=False)
        
        # Accept the close event
        event.accept()
        
    # Controller signal handlers
    def _show_error_message(self, title: str, message: str):
        """Show error message dialog."""
        self.error_handler.log_error(message, ErrorCategory.UI, 
                                   context=f"UI Error: {title}", 
                                   show_to_user=True, parent_widget=self,
                                   custom_message=message)
        
    def _on_project_data_loaded(self, project_path: str, project_name: str, managers_dict: dict):
        """Handle project data loaded signal."""
        # Set managers in controllers
        self.scene_controller.set_scene_manager(managers_dict['scene_manager'])
        self.character_controller.set_managers(
            managers_dict['character_manager'], 
            managers_dict['scene_manager'], 
            project_path
        )
        self.location_controller.set_manager(managers_dict['location_manager'], project_path)
        self.search_controller.set_manager(managers_dict['search_manager'], project_path)
        
        # Show project view
        self.ui_controller.show_project_view(
            project_name, 
            managers_dict['scenes'], 
            managers_dict['characters'], 
            managers_dict['locations']
        )
        
        # Update LLM context with project info
        self.llm_controller.update_project_context(project_name, project_path)
        
    def _on_project_created(self, project_name: str):
        """Handle project created signal."""
        self.show_projects_view()
        
    def _on_scene_opened(self, scene_id: int, scene_title: str, content: str):
        """Handle scene opened signal."""
        # Get project managers
        managers = self.project_controller.get_current_managers()
        project_path, _ = self.project_controller.get_current_project_info()
        
        if project_path:
            project_data = self.project_controller.get_project_data(Path(project_path))
            project_id = project_data['id'] if project_data else None
            
            self.workspace.open_editor_for_scene(
                content, 
                scene_id=scene_id,
                character_manager=managers['character_manager'],
                location_manager=managers['location_manager'],
                project_id=project_id
            )
            
            # Update LLM panel with scene context
            self.llm_panel.set_scene_context(scene_id, content)
            
            # Update LLM controller with scene context
            self.llm_controller.update_scene_context(scene_id, scene_title, content)
            
    def _on_scene_saved(self, is_auto_save: bool):
        """Handle scene saved signal."""
        if not is_auto_save:
            self._refresh_scenes_data()
            
    def _on_scene_created(self, title: str):
        """Handle scene created signal."""
        pass  # Refresh handled by scenesRefreshNeeded signal
        
    def _on_scene_renamed(self, scene_id: int, new_title: str):
        """Handle scene renamed signal."""
        pass  # Refresh handled by scenesRefreshNeeded signal
        
    def _on_character_created(self, name: str):
        """Handle character created signal."""
        pass  # Refresh handled by charactersRefreshNeeded signal
        
    def _on_category_selected(self, category: str):
        """Handle category selected signal."""
        self.current_category = category
        
    def _on_location_created(self, name: str):
        """Handle location created signal."""
        pass  # Refresh handled by locationsRefreshNeeded signal
        
    def _on_location_updated(self, location_id: int, name: str):
        """Handle location updated signal."""
        pass  # Refresh handled by locationsRefreshNeeded signal
        
    def _on_search_requested(self):
        """Handle search requested signal."""
        pass  # UI already updated by controller
        
    def _on_search_results_ready(self, search_results):
        """Handle search results ready signal."""
        if hasattr(self.workspace, 'load_search_results'):
            self.workspace.load_search_results(search_results)
        
    def show_projects_view(self) -> None:
        """Pokaż widok projektów."""
        projects = self.project_controller.list_projects()
        self.ui_controller.show_projects_view(projects)
            
    def on_project_selected(self, project_path: str, project_name: str) -> None:
        """Obsługa wyboru projektu - przejście do widoku projektu."""
        
        # Auto-save current scene before switching projects
        current_scene_id = self.scene_controller.get_current_scene_id()
        if current_scene_id and self.workspace.current_editor:
            if self.workspace.current_editor.has_changes():
                content = self.workspace.current_editor.get_content()
                self.scene_controller.auto_save_current_scene(content)
        
        self.current_view_state = "welcome"
        self.current_category = None
        
        # Load project using controller
        success = self.project_controller.load_project(project_path, project_name)
        if not success:
            self.show_projects_view()
            
    def on_category_selected(self, category: str) -> None:
        """Obsługa wyboru kategorii - pokaż widok kafelków."""
        managers = self.project_controller.get_current_managers()
        if not managers['scene_manager']:
            return
            
        project_path, _ = self.project_controller.get_current_project_info()
        if not project_path:
            return
            
        project_data = self.project_controller.get_project_data(Path(project_path))
        project_id = project_data['id'] if project_data else None
        
        if category == "scenes":
            scenes = self.scene_controller.get_scenes_list()
            data_dict = {
                'scenes': scenes,
                'character_manager': managers['character_manager'],
                'location_manager': managers['location_manager']
            }
        elif category == "characters":
            characters = self.character_controller.get_characters_list(project_id) if project_id else []
            data_dict = {
                'characters': characters,
                'location_manager': managers['location_manager']
            }
        elif category == "locations":
            data_dict = {
                'location_manager': managers['location_manager'],
                'project_id': project_id
            }
        elif category == "search":
            data_dict = {}
        else:
            data_dict = {}
            
        self.ui_controller.show_category_view(category, data_dict)
            
    def on_scene_selected(self, scene_id: int, scene_title: str) -> None:
        """Obsługa wyboru sceny."""
        
        # Auto-save current scene before switching to a new one
        current_scene_id = self.scene_controller.get_current_scene_id()
        if current_scene_id and self.workspace.current_editor:
            if self.workspace.current_editor.has_changes():
                content = self.workspace.current_editor.get_content()
                success = self.scene_controller.auto_save_current_scene(content)
                if success and self.workspace.current_editor:
                    self.workspace.current_editor._has_changes = False
        
        # Open scene using controller
        self.scene_controller.open_scene(scene_id, scene_title)
            
    def save_scene_content(self, content: str, is_auto_save: bool = False) -> None:
        """Zapisz zawartość sceny."""
        self.scene_controller.save_scene_content(content, is_auto_save)
        
        # Update LLM panel with latest content
        current_scene_id = self.scene_controller.get_current_scene_id()
        if current_scene_id:
            self.llm_panel.set_scene_context(current_scene_id, content)
    
    def auto_save_scene_content(self, content: str) -> None:
        """Handle periodic auto-save."""
        success = self.scene_controller.auto_save_scene_content(content)
        if success and self.workspace.current_editor:
            self.workspace.current_editor.confirm_auto_save()
            
            # Update LLM panel with latest content
            current_scene_id = self.scene_controller.get_current_scene_id()
            if current_scene_id:
                self.llm_panel.set_scene_context(current_scene_id, content)
            
    def _refresh_scenes_data(self):
        """Odśwież dane scen zachowując selekcję."""
        scenes = self.scene_controller.get_scenes_list()
        self.ui_controller.refresh_scenes_data(scenes)
            
    def _refresh_characters_data(self):
        """Odśwież dane postaci zachowując selekcję."""
        managers = self.project_controller.get_current_managers()
        if not managers['character_manager']:
            return
            
        project_path, _ = self.project_controller.get_current_project_info()
        if project_path:
            project_data = self.project_controller.get_project_data(Path(project_path))
            characters = self.character_controller.get_characters_list(project_data['id'])
            self.ui_controller.refresh_characters_data(characters, managers['location_manager'])
    
    def _refresh_locations_data(self):
        """Odśwież dane lokacji zachowując selekcję."""
        project_path, _ = self.project_controller.get_current_project_info()
        if project_path:
            project_data = self.project_controller.get_project_data(Path(project_path))
            locations = self.location_controller.get_locations_list(project_data['id'])
            self.ui_controller.refresh_locations_data(locations)
            
    def create_new_project(self, name: str) -> None:
        """Stwórz nowy projekt."""
        self.project_controller.create_project(name)
            
    def create_new_scene(self, title: str) -> None:
        """Stwórz nową scenę."""
        self.scene_controller.create_scene(title)
    
    def on_scene_rename_requested(self, scene_id: int, new_title: str) -> None:
        """Handle scene rename request."""
        self.scene_controller.rename_scene(scene_id, new_title)
            
    def on_character_selected(self, character_id, character_name):
        """Obsługa wyboru postaci - otwiera edytor postaci."""
        self.character_controller.open_character_editor(character_id, character_name, self.project_controller)
            
    def create_new_character(self, name):
        """Stwórz nową postać."""
        self.character_controller.create_character(name, self.project_controller)
            
    def _on_character_saved(self, character_data):
        """Obsługa zapisania postaci."""
        managers = self.project_controller.get_current_managers()
        character_manager = managers['character_manager']
        if not character_manager:
            return
            
        try:
            # Extract linked scenes before processing
            linked_scenes = character_data.pop('linked_scenes', [])
            
            if 'id' in character_data:
                # Aktualizuj istniejącą postać - usunięcie id z danych
                character_id = character_data['id']
                update_data = {k: v for k, v in character_data.items() if k != 'id'}
                character_manager.update_character(
                    character_id, **update_data
                )
                
                # Handle scene links for existing character
                self._process_scene_links(character_id, linked_scenes, character_manager)
            else:
                # This shouldn't happen for editing, but handle just in case
                pass
                
            self._refresh_characters_data()
            self.status_bar.showMessage(_("Character saved successfully"))
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                       context="Saving character",
                                       show_to_user=True, parent_widget=self,
                                       custom_message=_("Failed to save character: {}").format(character_data.get('name', '')))
            
    def _on_scene_linked(self, character_id, scene_id, role, importance):
        """Handle scene linked to character."""
        managers = self.project_controller.get_current_managers()
        character_manager = managers['character_manager']
        if not character_manager:
            return
            
        try:
            success = character_manager.link_character_to_scene_with_role(
                character_id, scene_id, role
            )
            if success:
                self.status_bar.showMessage(_("Scene linked to character"))
            else:
                self.error_handler.log_warning("Failed to link scene to character", 
                                              ErrorCategory.BUSINESS_LOGIC,
                                              show_to_user=True, parent_widget=self)
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                       context=f"Linking scene {scene_id} to character {character_id}",
                                       show_to_user=True, parent_widget=self)
            
    def _on_scene_unlinked(self, character_id, scene_id):
        """Handle scene unlinked from character."""
        managers = self.project_controller.get_current_managers()
        character_manager = managers['character_manager']
        if not character_manager:
            return
            
        try:
            success = character_manager.unlink_character_from_scene(
                character_id, scene_id
            )
            if success:
                self.status_bar.showMessage(_("Scene unlinked from character"))
            else:
                self.error_handler.log_warning("Failed to unlink scene from character", 
                                              ErrorCategory.BUSINESS_LOGIC,
                                              show_to_user=True, parent_widget=self)
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                       context=f"Unlinking scene {scene_id} from character {character_id}",
                                       show_to_user=True, parent_widget=self)
            
    def _process_scene_links(self, character_id, linked_scenes, character_manager):
        """Process scene links for a character."""
        if not character_manager:
            return
            
        for scene_data in linked_scenes:
            scene_id = scene_data.get('id')
            role = scene_data.get('role', '')
            
            if scene_id:
                try:
                    success = character_manager.link_character_to_scene_with_role(
                        character_id, scene_id, role
                    )
                    if not success:
                        # This is already shown in the warning dialog below
                        pass
                except Exception as e:
                    self.error_handler.log_warning(f"Failed to link character {character_id} to scene {scene_id}: {e}", 
                                                  ErrorCategory.BUSINESS_LOGIC,
                                                  show_to_user=True, parent_widget=self)
    
    def on_location_selected(self, location_id, location_name):
        """Obsługa wyboru lokacji - otwiera edytor lokacji."""
        self.location_controller.open_location_editor(location_id, location_name, self.project_controller)
    
    def create_new_location(self, name):
        """Stwórz nową lokację."""
        self.location_controller.create_location(name, self.project_controller)
    
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
        # Get character data using controller
        managers = self.project_controller.get_current_managers()
        if managers['character_manager']:
            character = managers['character_manager'].get_character(character_id)
            if character:
                character_name = character.get('name', _('Unknown Character'))
                self.on_character_selected(character_id, character_name)
    
    def on_location_selected_from_scene(self, location_id):
        """Handle location selected for editing from scene context panel."""
        # Get location data using controller
        location = self.location_controller.get_location(location_id)
        if location:
            self.on_location_selected(location_id, location.name)
    
    def on_search_requested(self):
        """Handle search category selection from tree."""
        self.search_controller.show_search_view()
        if hasattr(self.workspace, 'show_search_view'):
            self.workspace.show_search_view()
    
    def perform_search(self, query, filter_type):
        """Perform search and display results."""
        self.search_controller.perform_search(query, filter_type, self.project_controller)
    
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
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                       context="Opening search result",
                                       show_to_user=True, parent_widget=self,
                                       custom_message=_("Failed to open search result"))
    
    def on_scene_selected_with_search(self, scene_id, scene_title, search_query):
        """Handle scene selection from search results with text highlighting."""
        try:
            managers = self.project_controller.get_current_managers()
            scene_manager = managers['scene_manager']
            if not scene_manager:
                return
                
            scene_data = scene_manager.get_scene(scene_id)
            content = scene_data.get("content_rtf", f"<p>{_('Start writing your scene...')}</p>") if scene_data else f"<p>{_('Scene loading error')}</p>"
            
            # Get project ID for managers
            project_path, project_name = self.project_controller.get_current_project_info()
            if project_path:
                project_data = self.project_controller.get_project_data(Path(project_path))
                project_id = project_data['id'] if project_data else None
            else:
                project_id = None
            
            # Open editor with context panel support
            self.workspace.open_editor_for_scene(
                content, 
                scene_id=scene_id,
                character_manager=managers['character_manager'],
                location_manager=managers['location_manager'],
                project_id=project_id
            )
            
            # Find and highlight the search term in the editor
            if search_query and self.workspace.current_editor:
                self.workspace.current_editor.find_and_highlight_text(search_query)
            
            self.status_bar.showMessage(_("Editing scene: {} (search: '{}')").format(scene_title, search_query))
            
        except Exception as e:
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                       context=f"Opening scene with search: {scene_title}",
                                       show_to_user=True, parent_widget=self,
                                       custom_message=_("Failed to open scene: {}").format(scene_title))
            
    def show_settings(self):
        """Pokaż dialog ustawień."""
        dialog = SettingsDialog(self)
        dialog.themeChanged.connect(self.on_theme_changed)
        dialog.languageChanged.connect(self.on_language_changed)
        dialog.llmSettingsChanged.connect(self.on_llm_settings_changed)
        dialog.exec()
        
    def on_theme_changed(self, theme_name):
        """Obsługa zmiany motywu."""
        self.status_bar.showMessage(_("Applied theme: {}").format(theme_name))
        
        # Odśwież kafelki w widokach
        self.projects_view.refresh_theme()
        if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
            self.workspace.scenes_grid_view.refresh_theme()
    
    def on_llm_settings_changed(self):
        """Handle LLM settings changes."""
        self.status_bar.showMessage(_("LLM settings updated"))
        
        # Notify the LLM controller about settings changes
        self.llm_controller.on_settings_changed()
    
    def on_text_selection_changed(self, selected_text: str, current_text: str):
        """Handle text selection changes from editor."""
        try:
            # Update LLM context with text selection
            self.llm_controller.update_text_selection(selected_text, current_text)
            
        except Exception as e:
            self.logger.error(f"Error handling text selection change: {e}")
    
    def show_project_properties(self):
        """Show project properties dialog."""
        project_path, _ = self.project_controller.get_current_project_info()
        if not project_path:
            return
            
        # Get current project data
        project_data = self.project_controller.get_project_data(Path(project_path))
        if not project_data:
            self.error_handler.log_warning("Could not load project data", 
                                          ErrorCategory.BUSINESS_LOGIC,
                                          show_to_user=True, parent_widget=self)
            return
            
        # Show the properties dialog
        dialog = ProjectPropertiesDialog(project_data, self)
        dialog.propertiesSaved.connect(self.on_project_properties_saved)
        dialog.exec()
    
    def on_project_properties_saved(self, properties):
        """Handle project properties being saved."""
        project_path, _ = self.project_controller.get_current_project_info()
        if not project_path:
            return
            
        # Update the project in the database
        success = self.project_controller.update_project_properties(
            Path(project_path), properties
        )
        
        if success:
            self.status_bar.showMessage(_("Project properties saved successfully"))
            
            # Update the project title in the UI if it changed
            if 'title' in properties:
                _, current_project_name = self.project_controller.get_current_project_info()
                display_title = properties['title'] or current_project_name
                self.project_tree.update_project_name(display_title)
        else:
            self.error_handler.log_error("Failed to save project properties", 
                                        ErrorCategory.BUSINESS_LOGIC,
                                        show_to_user=True, parent_widget=self)
            
        # Odśwież ikony w drzewku
        self.project_tree.refresh_icons()
        
        # Jeśli jesteśmy w trybie fokusu, odśwież style trybu fokusu
        # This is now handled by the focus controller
        if hasattr(self.focus_controller, 'refresh_focus_mode_if_active'):
            self.focus_controller.refresh_focus_mode_if_active()
                
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
        self.focus_controller.toggle_focus_mode()
        
        # Focus mode implementation is now in focus_controller
    
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
    
    def _on_insert_text_requested(self, text: str) -> None:
        """Handle text insertion request from LLM assistant."""
        try:
            # Get the current editor from workspace
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                editor = self.workspace.current_editor
                
                # Get the text widget from the editor
                text_widget = None
                if hasattr(editor, 'text_widget'):
                    text_widget = editor.text_widget
                elif hasattr(editor, 'text_edit'):
                    text_widget = editor.text_edit
                else:
                    # Search for QTextEdit in the editor
                    from PySide6.QtWidgets import QTextEdit
                    text_widgets = editor.findChildren(QTextEdit)
                    if text_widgets:
                        text_widget = text_widgets[0]
                
                if text_widget:
                    # Insert text at cursor position
                    cursor = text_widget.textCursor()
                    cursor.insertText(text)
                    text_widget.setTextCursor(cursor)
                    
                    # Set focus to the text widget
                    text_widget.setFocus()
                    
                    # Show success message
                    self.status_bar.showMessage(_("Text inserted successfully"))
                    
                    # Log the insertion
                    from core.logging_config import get_logger
                    logger = get_logger("main.text_insertion")
                    logger.info(f"Inserted {len(text)} characters into editor")
                else:
                    self.status_bar.showMessage(_("No text editor found"))
                    
            else:
                self.status_bar.showMessage(_("No editor active"))
                
        except Exception as e:
            error_msg = f"Error inserting text: {str(e)}"
            self.status_bar.showMessage(error_msg)
            from core.logging_config import get_logger
            logger = get_logger("main.text_insertion")
            logger.error(error_msg)


def main():
    app = QApplication(sys.argv)
    
    try:
        # Initialize logging first
        logger = setup_logging()
        error_handler = get_error_handler()
        
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
        
        logger.info("Pisarz application started successfully")
        return app.exec()
        
    except Exception as e:
        # Handle any critical startup errors
        error_handler = get_error_handler()
        error_handler.log_critical(e, ErrorCategory.SYSTEM,
                                 context="Application startup",
                                 show_to_user=True,
                                 custom_message="Failed to start Pisarz application")
        return 1


if __name__ == "__main__":
    sys.exit(main())