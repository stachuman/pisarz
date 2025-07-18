"""Workspace widget containing welcome screen, grid views and editor."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..styles.styles import INFO_TEXT_COLOR
from core.embedded_editor import EmbeddedRichTextWidget
from .scenes_grid_view import ScenesGridView
from .characters_grid_view import CharactersGridView
from .locations_grid_view import LocationsGridView
from .search_view import SearchView


class Workspace(QWidget):
    """Obszar roboczy z ekranem powitalnym, widokami kafelków i edytorem."""
    
    saveRequested = Signal(str)             # content
    autoSaveRequested = Signal(str)         # content - periodic auto-save
    sceneSelectedFromGrid = Signal(int, str) # id, title - from grid view
    newSceneRequestedFromGrid = Signal(str) # title - from grid view
    sceneRenameRequestedFromGrid = Signal(int, str) # id, new_title - from grid view
    characterSelectedFromGrid = Signal(int, str) # id, name - from characters grid view
    newCharacterRequestedFromGrid = Signal(str) # name - from characters grid view
    characterEditRequestedFromGrid = Signal(int) # character_id - from characters grid view
    characterDeleteRequestedFromGrid = Signal(int) # character_id - from characters grid view
    locationSelectedFromGrid = Signal(int, str) # id, name - from locations grid view
    newLocationRequestedFromGrid = Signal(str) # name - from locations grid view
    focusModeRequested = Signal()           # focus mode toggle
    
    # Scene context panel signals
    characterAddedToScene = Signal(int, str)  # character_id, role
    characterRemovedFromScene = Signal(int)   # character_id
    locationAddedToScene = Signal(int, str)   # location_id, role
    locationRemovedFromScene = Signal(int)    # location_id
    newCharacterRequestedFromScene = Signal(str)  # name
    newLocationRequestedFromScene = Signal(str)   # name
    characterSelectedFromScene = Signal(int)     # character_id
    locationSelectedFromScene = Signal(int)      # location_id
    aiAssistantToggled = Signal()                # AI assistant toggle from editor
    narrativeContextToggled = Signal()           # Narrative context toggle from editor
    textSelectionChanged = Signal(str, str)      # selected_text, current_text from editor
    
    # Search view signals
    searchRequested = Signal(str, str)           # query, filter_type
    searchResultSelected = Signal(str, int, str, str) # result_type, id, title, search_query
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_editor = None
        self.scenes_grid_view = None
        self.characters_grid_view = None
        self.locations_grid_view = None
        self.search_view = None
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja obszaru roboczego."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # Remove any spacing between stacked widgets
        
        # Stack widget dla różnych widoków
        self.workspace_stack = QStackedWidget()
        self.workspace_stack.setContentsMargins(0, 0, 0, 0)
        self.workspace_stack.setStyleSheet("QStackedWidget { margin: 0px; padding: 0px; border: none; }")
        layout.addWidget(self.workspace_stack)
        
        # === WIDOK POWITALNY ===
        self._create_welcome_screen()
        
        # === WIDOK KAFELKÓW SCEN ===
        self.scenes_grid_view = ScenesGridView()
        self.scenes_grid_view.sceneSelected.connect(self.sceneSelectedFromGrid.emit)
        self.scenes_grid_view.newSceneRequested.connect(self.newSceneRequestedFromGrid.emit)
        self.scenes_grid_view.sceneRenameRequested.connect(self.sceneRenameRequestedFromGrid.emit)
        self.workspace_stack.addWidget(self.scenes_grid_view)
        
        # === WIDOK KAFELKÓW POSTACI ===
        self.characters_grid_view = CharactersGridView()
        self.characters_grid_view.characterSelected.connect(self.characterSelectedFromGrid.emit)
        self.characters_grid_view.newCharacterRequested.connect(self.newCharacterRequestedFromGrid.emit)
        self.characters_grid_view.characterEditRequested.connect(self.characterEditRequestedFromGrid.emit)
        self.characters_grid_view.characterDeleteRequested.connect(self.characterDeleteRequestedFromGrid.emit)
        self.workspace_stack.addWidget(self.characters_grid_view)
        
        # === WIDOK KAFELKÓW LOKACJI ===
        # Note: LocationsGridView requires location_manager and project_id to be set later
        self.locations_grid_view = None  # Will be initialized when needed
        
        # === WIDOK WYSZUKIWANIA ===
        self.search_view = SearchView()
        self.search_view.searchRequested.connect(self.searchRequested.emit)
        self.search_view.resultSelected.connect(self.searchResultSelected.emit)
        self.workspace_stack.addWidget(self.search_view)
        
    def _create_welcome_screen(self):
        """Stwórz ekran powitalny."""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_title = QLabel("Witaj w Pisarz")
        welcome_title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_title.setStyleSheet("color: #2c3e50;")
        welcome_layout.addWidget(welcome_title)
        
        welcome_text = QLabel("""
        Profesjonalna aplikacja do pisania z natywnym editorem RTF
        
        1. Wybierz lub stwórz projekt w lewym panelu
        2. Wybierz lub stwórz scenę dla swojego projektu  
        3. Edytor RTF zostanie automatycznie załadowany
        
        Funkcje editora:
        • Pełne formatowanie tekstu z toolbar
        • Wybór czcionki i rozmiar
        • Pogrubienie, kursywa, podkreślenie
        • Kolory tekstu i wyrównanie
        • Skróty klawiszowe (Ctrl+B/I/U/S)
        """)
        welcome_text.setFont(QFont("Arial", 12))
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_text.setStyleSheet(INFO_TEXT_COLOR)
        welcome_layout.addWidget(welcome_text)
        
        self.workspace_stack.addWidget(welcome_widget)
        
    def show_welcome(self):
        """Pokaż ekran powitalny."""
        self.workspace_stack.setCurrentIndex(0)
        
    def show_scenes_grid(self, scenes, character_manager=None, location_manager=None):
        """Pokaż widok kafelków scen."""
        if character_manager and location_manager:
            self.scenes_grid_view.set_managers(character_manager, location_manager)
        self.scenes_grid_view.load_scenes(scenes)
        self.workspace_stack.setCurrentIndex(1)
        
    def show_characters_grid(self, characters, location_manager=None):
        """Pokaż widok kafelków postaci."""
        if location_manager:
            self.characters_grid_view.set_location_manager(location_manager)
        self.characters_grid_view.load_characters(characters)
        self.workspace_stack.setCurrentIndex(2)
    
    def initialize_locations_grid(self, location_manager, project_id):
        """Initialize the locations grid view when needed."""
        if self.locations_grid_view is None:
            self.locations_grid_view = LocationsGridView(location_manager, project_id)
            self.locations_grid_view.location_selected.connect(self.locationSelectedFromGrid.emit)
            # Connect new location signal to our signal
            self.locations_grid_view.new_location_button.clicked.connect(
                lambda: self.newLocationRequestedFromGrid.emit("")
            )
            self.workspace_stack.addWidget(self.locations_grid_view)
    
    def show_locations_grid(self, location_manager=None, project_id=None):
        """Pokaż widok kafelków lokacji."""
        if location_manager and project_id:
            self.initialize_locations_grid(location_manager, project_id)
        
        if self.locations_grid_view:
            self.locations_grid_view.refresh_locations()
            # Find the index of locations grid view
            for i in range(self.workspace_stack.count()):
                if self.workspace_stack.widget(i) is self.locations_grid_view:
                    self.workspace_stack.setCurrentIndex(i)
                    break
    
    def show_search_view(self):
        """Pokaż widok wyszukiwania."""
        search_index = 3  # welcome(0) + scenes(1) + characters(2) + search(3)
        self.workspace_stack.setCurrentIndex(search_index)
        self.search_view.focus_search_input()  # Focus search input when shown
    
    def load_search_results(self, search_results):
        """Załaduj wyniki wyszukiwania do widoku."""
        if self.search_view:
            self.search_view.load_search_results(search_results)
        
    def open_editor_for_scene(self, scene_content="<p>Zacznij pisać swoją scenę...</p>", scene_id=None, 
                            character_manager=None, location_manager=None, project_id=None):
        """Otwórz zintegrowany edytor RTF dla sceny."""
        # Usuń istniejący edytor jeśli jest (zachowaj welcome + grid views)
        # Find current grid view count dynamically 
        base_views = 4  # welcome + scenes + characters + search
        if self.locations_grid_view:
            base_views += 1
        
        while self.workspace_stack.count() > base_views:
            old_editor = self.workspace_stack.widget(base_views)
            self.workspace_stack.removeWidget(old_editor)
            old_editor.setParent(None)
            
        # Stwórz nowy edytor
        self.current_editor = EmbeddedRichTextWidget()
        self.current_editor.set_content(scene_content)
        
        # Initialize context panel if managers are provided
        if character_manager and location_manager and project_id:
            self.current_editor.initialize_context_panel(character_manager, location_manager, project_id)
            
            # Set scene context if scene_id is provided
            if scene_id:
                self.current_editor.set_scene_context(scene_id)
        
        # Połącz sygnały
        self.current_editor.saveRequested.connect(self.saveRequested.emit)
        self.current_editor.autoSaveRequested.connect(self.autoSaveRequested.emit)
        self.current_editor.focusModeRequested.connect(self.focusModeRequested.emit)
        self.current_editor.aiAssistantToggled.connect(self.aiAssistantToggled.emit)
        self.current_editor.narrativeContextToggled.connect(self.narrativeContextToggled.emit)
        self.current_editor.textSelectionChanged.connect(self.textSelectionChanged.emit)
        
        # Connect context panel signals
        self.current_editor.characterAddedToScene.connect(self.characterAddedToScene.emit)
        self.current_editor.characterRemovedFromScene.connect(self.characterRemovedFromScene.emit)
        self.current_editor.locationAddedToScene.connect(self.locationAddedToScene.emit)
        self.current_editor.locationRemovedFromScene.connect(self.locationRemovedFromScene.emit)
        self.current_editor.newCharacterRequestedFromScene.connect(self.newCharacterRequestedFromScene.emit)
        self.current_editor.newLocationRequestedFromScene.connect(self.newLocationRequestedFromScene.emit)
        self.current_editor.characterSelectedFromScene.connect(self.characterSelectedFromScene.emit)
        self.current_editor.locationSelectedFromScene.connect(self.locationSelectedFromScene.emit)
        
        # Dodaj do stack i pokaż
        self.workspace_stack.addWidget(self.current_editor)
        self.workspace_stack.setCurrentIndex(self.workspace_stack.count() - 1)
        
    def get_editor_content(self):
        """Pobierz zawartość z aktualnego editora."""
        if self.current_editor:
            return self.current_editor.get_content()
        return ""
    
    def set_ai_assistant_state(self, visible: bool):
        """Set the AI assistant button state in the current editor."""
        if self.current_editor:
            self.current_editor.set_ai_assistant_state(visible)
    
    def set_narrative_context_state(self, visible: bool):
        """Set the narrative context button state in the current editor."""
        if self.current_editor:
            self.current_editor.set_narrative_context_state(visible)