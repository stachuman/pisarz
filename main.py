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
                       LLMAssistantPanel, NarrativeContextPanel)
from services import LLMEventService, UIEventService, ProjectManagementService, SettingsService
from i18n import _


class PisarzApp(QMainWindow):
    """Główne okno aplikacji Pisarz."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize error handling and logging
        self.error_handler = get_error_handler()
        self.logger = setup_logging(log_level="DEBUG", console_logging=True)
        
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
        
        # Initialize services
        self.llm_event_service = LLMEventService(self)
        self.ui_event_service = UIEventService(self)
        self.project_management_service = ProjectManagementService(self)
        self.settings_service = SettingsService(self)
        
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
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        project_layout.addWidget(self.main_splitter)
        
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
        self.main_splitter.addWidget(top_widget)
        
        # LLM Assistant Panel (teraz na dole)
        self.llm_panel = LLMAssistantPanel(self)  # Pass self as parent
        self.llm_panel.setMinimumHeight(250)  # Minimum height for usability
        self.llm_panel.setVisible(False)  # Hidden by default
        self.main_splitter.addWidget(self.llm_panel)
        
        # Narrative Context Panel
        self.narrative_context_panel = NarrativeContextPanel()
        self.narrative_context_panel.setMinimumHeight(300)  # Minimum height for usability
        self.narrative_context_panel.setVisible(False)  # Hidden by default
        self.main_splitter.addWidget(self.narrative_context_panel)
        
        # Proporcje głównego splitteru (góra vs dół)
        # Initial setup: main area gets all space, panels get 0 (hidden)
        self.main_splitter.setSizes([1000, 0, 0])
        
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
        
        # Narrative Context toggle action
        self.narrative_context_action = QAction(_("Narrative Context"), self)
        self.narrative_context_action.setCheckable(True)
        self.narrative_context_action.setChecked(False)
        self.narrative_context_action.setShortcut(QKeySequence("Ctrl+Alt+N"))
        self.narrative_context_action.triggered.connect(self.toggle_narrative_context)
        tools_menu.addAction(self.narrative_context_action)
        
        # Templates action
        tools_menu.addSeparator()
        templates_action = QAction(_("Templates"), self)
        templates_action.setShortcut(QKeySequence("Ctrl+T"))
        templates_action.triggered.connect(self.show_templates)
        tools_menu.addAction(templates_action)
        
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
        
        # Update splitter sizes to properly show/hide the panel
        self._update_splitter_sizes()
        
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
    
    def _update_splitter_sizes(self):
        """Update splitter sizes based on panel visibility."""
        ai_visible = self.llm_panel.isVisible()
        narrative_visible = self.narrative_context_panel.isVisible()
        
        # Get current total height
        current_sizes = self.main_splitter.sizes()
        total_height = sum(current_sizes) if current_sizes else 1000
        
        # Define minimum sizes for panels
        ai_min_height = 250
        narrative_min_height = 300
        main_min_height = 400
        
        # Calculate sizes based on visibility
        if ai_visible and narrative_visible:
            # Both panels visible
            main_height = max(main_min_height, total_height - ai_min_height - narrative_min_height)
            ai_height = ai_min_height
            narrative_height = narrative_min_height
        elif ai_visible:
            # Only AI panel visible
            main_height = max(main_min_height, total_height - ai_min_height)
            ai_height = ai_min_height
            narrative_height = 0
        elif narrative_visible:
            # Only narrative panel visible
            main_height = max(main_min_height, total_height - narrative_min_height)
            ai_height = 0
            narrative_height = narrative_min_height
        else:
            # No panels visible
            main_height = total_height
            ai_height = 0
            narrative_height = 0
        
        # Set the new sizes
        self.main_splitter.setSizes([main_height, ai_height, narrative_height])
        
        self.logger.debug(f"Updated splitter sizes: main={main_height}, ai={ai_height}, narrative={narrative_height}")
    
    def toggle_narrative_context(self):
        """Toggle Narrative Context panel visibility."""
        is_visible = self.narrative_context_panel.isVisible()
        self.narrative_context_panel.setVisible(not is_visible)
        self.narrative_context_action.setChecked(not is_visible)
        
        # Update splitter sizes to properly show/hide the panel
        self._update_splitter_sizes()
        
        # Update button state in workspace
        self.workspace.set_narrative_context_state(not is_visible)
        
        # Update status message
        if not is_visible:
            self.status_bar.showMessage(_("Narrative Context panel opened"))
        else:
            self.status_bar.showMessage(_("Narrative Context panel closed"))
        
        self.logger.info(f"Narrative Context panel {'opened' if not is_visible else 'closed'}")
        
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
        
        # Context menu signals
        self.project_tree.generateContextRequested.connect(self.on_generate_context_requested)
        self.project_tree.editTemplateRequested.connect(self.on_edit_template_requested)
        self.project_tree.refreshContextRequested.connect(self.on_refresh_context_requested)
        self.project_tree.editContextRequested.connect(self.on_edit_context_requested)
        
        # LLM Assistant signals for context auto-save
        self.llm_panel.contextAutoSaved.connect(self.on_context_auto_saved)
        
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
        self.workspace.narrativeContextToggled.connect(self.toggle_narrative_context)
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
        self.settings_service.exit_focus_mode_if_active()
    
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
        
    def _on_project_data_loaded(self, project_id: int, project_name: str, managers_dict: dict):
        """Handle project data loaded signal."""
        # Set managers in controllers
        self.scene_controller.set_scene_manager(managers_dict['scene_manager'], project_id)
        self.character_controller.set_managers(
            managers_dict['character_manager'], 
            managers_dict['scene_manager'], 
            project_id
        )
        self.location_controller.set_managers(managers_dict['location_manager'], managers_dict['scene_manager'], project_id)
        self.search_controller.set_manager(managers_dict['search_manager'], project_id)
        
        # Show project view
        self.ui_controller.show_project_view(
            project_name, 
            managers_dict['scenes'], 
            managers_dict['characters'], 
            managers_dict['locations']
        )
        
        # Update LLM context with project info
        self.llm_controller.update_project_context(project_name, project_id)
        
        # Initialize narrative context panel with current project
        if hasattr(self, 'narrative_context_panel') and self.narrative_context_panel:
            self.narrative_context_panel.set_project(project_id, project_name)
        
        # Set up narrative context manager for project tree
        from core.database.narrative_context_repository import NarrativeContextManager
        try:
            narrative_manager = NarrativeContextManager()
            self.project_tree.set_narrative_context_manager(narrative_manager)
        except Exception as e:
            self.logger.warning(f"Failed to set up narrative context manager: {e}")
        
    def _on_project_created(self, project_name: str):
        """Handle project created signal."""
        self.show_projects_view()
        
    def _on_scene_opened(self, scene_id: int, scene_title: str, content: str):
        """Handle scene opened signal."""
        # Get project managers
        managers = self.project_controller.get_current_managers()
        project_id, _project_name = self.project_controller.get_current_project_info()
        
        if project_id:
            project_data = self.project_controller.get_project_data(project_id)
            
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
            
    def on_project_selected(self, project_id: int, project_name: str) -> None:
        """Obsługa wyboru projektu - przejście do widoku projektu."""
        
        # Auto-save current scene before switching projects
        current_scene_id = self.scene_controller.get_current_scene_id()
        if current_scene_id and self.workspace.current_editor:
            if self.workspace.current_editor.has_changes():
                content = self.workspace.current_editor.get_content()
                self.scene_controller.auto_save_current_scene(content)
        
        self.current_view_state = "welcome"
        self.current_category = None
        
        # Use project management service
        success = self.project_management_service.handle_project_selection(project_id, project_name)
        if not success:
            self.show_projects_view()
            
    def on_category_selected(self, category: str) -> None:
        """Obsługa wyboru kategorii - pokaż widok kafelków."""
        success = self.project_management_service.handle_category_selection(category)
        if success:
            # Get data and show the category view through UI controller
            managers = self.project_controller.get_current_managers()
            if not managers['scene_manager']:
                return
                
            project_id, _project_name = self.project_controller.get_current_project_info()
            if not project_id:
                return
            project_data = self.project_controller.get_project_data(project_id)

            
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
        
        # Use project management service for scene selection
        self.project_management_service.handle_scene_selection(scene_id, scene_title)
            
    def save_scene_content(self, content: str, is_auto_save: bool = False) -> None:
        """Zapisz zawartość sceny."""
        success = self.project_management_service.save_scene_content(content, is_auto_save)
        if success:
            # Update LLM panel with latest content
            current_scene_id = self.scene_controller.get_current_scene_id()
            if current_scene_id:
                self.llm_panel.set_scene_context(current_scene_id, content)
    
    def auto_save_scene_content(self, content: str) -> None:
        """Handle periodic auto-save."""
        success = self.project_management_service.save_scene_content(content, is_auto_save=True)
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
            
        project_id, _project_name = self.project_controller.get_current_project_info()
        if project_id:
            project_data = self.project_controller.get_project_data(project_id)
            characters = self.character_controller.get_characters_list(project_data['id'])
            self.ui_controller.refresh_characters_data(characters, managers['location_manager'])
    
    def _refresh_locations_data(self):
        """Odśwież dane lokacji zachowując selekcję."""
        project_id, _project_name = self.project_controller.get_current_project_info()
        if project_id:
            project_data = self.project_controller.get_project_data(project_id)
            locations = self.location_controller.get_locations_list(project_id)
            self.ui_controller.refresh_locations_data(locations)
            
    def create_new_project(self, name: str) -> None:
        """Stwórz nowy projekt."""
        self.project_management_service.create_new_project(name)
            
    def create_new_scene(self, title: str) -> None:
        """Stwórz nową scenę."""
        self.project_management_service.create_new_scene(title)
    
    def on_scene_rename_requested(self, scene_id: int, new_title: str) -> None:
        """Handle scene rename request."""
        self.project_management_service.handle_scene_rename(scene_id, new_title)
            
    def on_character_selected(self, character_id, character_name):
        """Obsługa wyboru postaci - otwiera edytor postaci."""
        self.ui_event_service.handle_character_selection(character_id, character_name)
            
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
        self.ui_event_service.handle_location_selection(location_id, location_name)
    
    def create_new_location(self, name):
        """Stwórz nową lokację."""
        self.location_controller.create_location(name, self.project_controller)
    
    # Scene context panel handlers
    
    def on_character_added_to_scene(self, character_id, role):
        """Handle character added to scene from context panel."""
        success = self.ui_event_service.handle_scene_character_addition(character_id, role)
        if success:
            self.status_bar.showMessage(_("Character linked to scene with role: {}").format(role))
    
    def on_character_removed_from_scene(self, character_id):
        """Handle character removed from scene."""
        success = self.ui_event_service.handle_scene_character_removal(character_id)
        if success:
            self.status_bar.showMessage(_("Character unlinked from scene"))
    
    def on_location_added_to_scene(self, location_id, role):
        """Handle location added to scene from context panel."""
        success = self.ui_event_service.handle_scene_location_addition(location_id, role)
        if success:
            self.status_bar.showMessage(_("Location linked to scene with role: {}").format(role))
    
    def on_location_removed_from_scene(self, location_id):
        """Handle location removed from scene."""
        success = self.ui_event_service.handle_scene_location_removal(location_id)
        if success:
            self.status_bar.showMessage(_("Location unlinked from scene"))
    
    def on_character_selected_from_scene(self, character_id):
        """Handle character selected for editing from scene context panel."""
        # Get character data using controller
        managers = self.project_controller.get_current_managers()
        if managers['character_manager']:
            character = managers['character_manager'].get_character(character_id)
            if character:
                character_name = character.get('name', _('Unknown Character'))
                self.ui_event_service.handle_character_selection(character_id, character_name)
    
    def on_location_selected_from_scene(self, location_id):
        """Handle location selected for editing from scene context panel."""
        # Get location data using controller
        location = self.location_controller.get_location(location_id)
        if location:
            self.ui_event_service.handle_location_selection(location_id, location.name)
    
    def on_search_requested(self):
        """Handle search category selection from tree."""
        self.ui_event_service.handle_search_request()
    
    def perform_search(self, query, filter_type):
        """Perform search and display results."""
        self.search_controller.perform_search(query, filter_type, self.project_controller)
    
    def on_search_result_selected(self, result_type, result_id, title, search_query):
        """Handle selection of a search result."""
        self.ui_event_service.handle_search_result_selection(result_type, result_id, title, search_query)
    
    def on_scene_selected_with_search(self, scene_id, scene_title, search_query):
        """Handle scene selection from search results with text highlighting."""
        success = self.project_management_service.handle_scene_selection_with_search(scene_id, scene_title, search_query)
        if success:
            self.status_bar.showMessage(_("Editing scene: {} (search: '{}')").format(scene_title, search_query))
            
    def show_settings(self):
        """Pokaż dialog ustawień."""
        self.settings_service.show_settings_dialog()
    
    def show_templates(self):
        """Show templates management dialog."""
        try:
            from ui.widgets.templates_list_dialog import TemplatesListDialog
            dialog = TemplatesListDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening templates dialog: {e}")
            QMessageBox.critical(self, _("Error"), _("Failed to open templates manager: {}").format(str(e)))
        
    def on_theme_changed(self, theme_name):
        """Obsługa zmiany motywu."""
        success = self.settings_service.handle_theme_change(theme_name)
        if success:
            self.status_bar.showMessage(_("Applied theme: {}").format(theme_name))
            # Odśwież kafelki w widokach
            self.projects_view.refresh_theme()
            if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
                self.workspace.scenes_grid_view.refresh_theme()
    
    def on_llm_settings_changed(self):
        """Handle LLM settings changes."""
        success = self.settings_service.handle_llm_settings_change()
        if success:
            self.status_bar.showMessage(_("LLM settings updated"))
    
    def on_text_selection_changed(self, selected_text: str, current_text: str):
        """Handle text selection changes from editor."""
        self.settings_service.handle_text_selection_change(selected_text, current_text)
    
    def show_project_properties(self):
        """Show project properties dialog."""
        self.settings_service.show_project_properties()
    
    def on_project_properties_saved(self, properties):
        """Handle project properties being saved."""
        success = self.settings_service.handle_project_properties_save(properties)
        if success:
            # Update the project title in the UI if it changed
            if 'title' in properties:
                _, current_project_name = self.project_controller.get_current_project_info()
                display_title = properties['title'] or current_project_name
                self.project_tree.update_project_name(display_title)
            
            # Odśwież ikony w drzewku
            self.project_tree.refresh_icons()
            
            # Jeśli jesteśmy w trybie fokusu, odśwież style trybu fokusu
            if hasattr(self.focus_controller, 'refresh_focus_mode_if_active'):
                self.focus_controller.refresh_focus_mode_if_active()
                
    def on_language_changed(self, language_code):
        """Obsługa zmiany języka."""
        self.settings_service.handle_language_change(language_code)
        
    def toggle_focus_mode(self):
        """Przełącz tryb fokusu pisania."""
        self.settings_service.toggle_focus_mode()
    
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
    
    def on_generate_context_requested(self, scene_id: int, template_name: str):
        """Handle request to generate narrative context using a template."""
        self.llm_event_service.handle_generate_context_request(scene_id, template_name)
    
    def on_edit_template_requested(self, template_name: str):
        """Handle request to edit a template."""
        try:
            from ui.widgets.template_editor_dialog import TemplateEditorDialog
            
            # Open template editor
            dialog = TemplateEditorDialog(template_name, self)
            dialog.exec()
            
            self.status_bar.showMessage(_("Template editor opened"))
            
        except Exception as e:
            from core.error_handler import ErrorCategory
            self.error_handler.log_error(e, ErrorCategory.UI,
                                       context=f"Opening template editor for {template_name}",
                                       show_to_user=True, parent_widget=self)
    
    def on_refresh_context_requested(self, scene_id: int):
        """Handle request to refresh narrative context for a scene."""
        self.llm_event_service.handle_refresh_context_request(scene_id)
    
    def on_edit_context_requested(self, scene_id: int):
        """Handle request to edit generated context for a scene."""
        try:
            # Get narrative context manager
            project_id, _project_name = self.project_controller.get_current_project_info()
            if not project_id:
                self.status_bar.showMessage(_("No project loaded"))
                return
            
            from core.database.narrative_context_repository import NarrativeContextManager
            narrative_manager = NarrativeContextManager()
            
            # Get existing context for the scene
            existing_context = narrative_manager.get_contexts_by_scene(scene_id) # get_context_for_scene(scene_id)
            
            if not existing_context:
                self.status_bar.showMessage(_("No context found for this scene"))
                return
            
            # Import the dialog class
            from ui.widgets.narrative_context_panel import NarrativeContextDialog
            
            if len(existing_context) == 1:
                # Single context entry - edit it directly
                context_entry = existing_context[0]
                dialog = NarrativeContextDialog(context_entry, self)
                
                if dialog.exec() == dialog.DialogCode.Accepted:
                    # Get updated data from dialog
                    updated_data = dialog.get_data()
                    
                    # Update the context entry
                    success = narrative_manager.update_narrative_context(
                        context_entry["id"],
                        title=updated_data["title"],
                        content=updated_data["content"],
                        metadata=updated_data.get("metadata")
                    )
                    
                    if success:
                        # Handle active/inactive state
                        if updated_data["is_active"] != context_entry.get("is_active", 1):
                            if updated_data["is_active"]:
                                narrative_manager.reactivate_context(context_entry["id"])
                            else:
                                narrative_manager.deactivate_context(context_entry["id"])
                        
                        # Refresh UI
                        self.on_context_auto_saved(scene_id)  # Refresh scene tree
                        if hasattr(self, 'narrative_context_panel') and self.narrative_context_panel:
                            self.narrative_context_panel.refresh_contexts()
                        
                        self.status_bar.showMessage(_("✓ Context updated successfully"))
                    else:
                        self.status_bar.showMessage(_("❌ Failed to update context"))
                        
            else:
                # Multiple context entries - show selection dialog first
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QLabel
                
                selection_dialog = QDialog(self)
                selection_dialog.setWindowTitle(_("Select Context to Edit"))
                selection_dialog.setModal(True)
                selection_dialog.resize(400, 300)
                
                layout = QVBoxLayout(selection_dialog)
                layout.addWidget(QLabel(_("Multiple contexts found for this scene. Select one to edit:")))
                
                context_list = QListWidget()
                for context in existing_context:
                    title = context.get("title", _("Untitled"))
                    context_type = context.get("context_type", "")
                    item_text = f"{title} ({context_type})"
                    context_list.addItem(item_text)
                    context_list.item(context_list.count() - 1).setData(1, context)  # Store context data
                
                layout.addWidget(context_list)
                
                buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
                buttons.accepted.connect(selection_dialog.accept)
                buttons.rejected.connect(selection_dialog.reject)
                layout.addWidget(buttons)
                
                if selection_dialog.exec() == QDialog.DialogCode.Accepted and context_list.currentItem():
                    selected_context = context_list.currentItem().data(1)
                    
                    # Open edit dialog for selected context
                    dialog = NarrativeContextDialog(selected_context, self)
                    
                    if dialog.exec() == dialog.DialogCode.Accepted:
                        # Get updated data from dialog
                        updated_data = dialog.get_data()
                        
                        # Update the context entry
                        success = narrative_manager.update_narrative_context(
                            selected_context["id"],
                            title=updated_data["title"],
                            content=updated_data["content"],
                            metadata=updated_data.get("metadata")
                        )
                        
                        if success:
                            # Handle active/inactive state
                            if updated_data["is_active"] != selected_context.get("is_active", 1):
                                if updated_data["is_active"]:
                                    narrative_manager.reactivate_context(selected_context["id"])
                                else:
                                    narrative_manager.deactivate_context(selected_context["id"])
                            
                            # Refresh UI
                            self.on_context_auto_saved(scene_id)  # Refresh scene tree
                            if hasattr(self, 'narrative_context_panel') and self.narrative_context_panel:
                                self.narrative_context_panel.refresh_contexts()
                            
                            self.status_bar.showMessage(_("✓ Context updated successfully"))
                        else:
                            self.status_bar.showMessage(_("❌ Failed to update context"))
            
        except Exception as e:
            from core.error_handler import ErrorCategory
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                       context=f"Editing context for scene {scene_id}",
                                       show_to_user=True, parent_widget=self)
    
    def on_context_auto_saved(self, scene_id: int):
        """Handle auto-saved context to refresh scene tree icons."""
        try:
            # Refresh the specific scene in the project tree
            managers = self.project_controller.get_current_managers()
            scene_manager = managers.get('scene_manager')
            if scene_manager:
                current_project_id, project_name = self.project_controller.get_current_project_info()
                if current_project_id:
                    from pathlib import Path
                    project_data = self.project_controller.get_project_data(current_project_id)
                    if project_data:
                        scenes = scene_manager.get_scenes_by_project(current_project_id)
                        self.project_tree.load_scenes(scenes)
            
            # Also refresh the narrative context panel
            if hasattr(self, 'narrative_context_panel') and self.narrative_context_panel:
                self.narrative_context_panel.refresh_contexts()
            
            self.status_bar.showMessage(_("✓ Context automatically saved and linked to scene"))
            self.logger.info(f"Context auto-saved for scene {scene_id}")
            
        except Exception as e:
            from core.error_handler import ErrorCategory
            self.error_handler.log_error(e, ErrorCategory.BUSINESS_LOGIC,
                                       context=f"Auto-saving context for scene {scene_id}",
                                       show_to_user=True, parent_widget=self)


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