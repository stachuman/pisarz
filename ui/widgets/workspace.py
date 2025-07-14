"""Workspace widget containing welcome screen, grid views and editor."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..styles.styles import INFO_TEXT_COLOR
from core.embedded_editor import EmbeddedRichTextWidget
from .scenes_grid_view import ScenesGridView


class Workspace(QWidget):
    """Obszar roboczy z ekranem powitalnym, widokami kafelków i edytorem."""
    
    saveRequested = Signal(str)             # content
    sceneSelectedFromGrid = Signal(int, str) # id, title - from grid view
    newSceneRequestedFromGrid = Signal(str) # title - from grid view
    focusModeRequested = Signal()           # focus mode toggle
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_editor = None
        self.scenes_grid_view = None
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja obszaru roboczego."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack widget dla różnych widoków
        self.workspace_stack = QStackedWidget()
        layout.addWidget(self.workspace_stack)
        
        # === WIDOK POWITALNY ===
        self._create_welcome_screen()
        
        # === WIDOK KAFELKÓW SCEN ===
        self.scenes_grid_view = ScenesGridView()
        self.scenes_grid_view.sceneSelected.connect(self.sceneSelectedFromGrid.emit)
        self.scenes_grid_view.newSceneRequested.connect(self.newSceneRequestedFromGrid.emit)
        self.workspace_stack.addWidget(self.scenes_grid_view)
        
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
        
    def show_scenes_grid(self, scenes):
        """Pokaż widok kafelków scen."""
        self.scenes_grid_view.load_scenes(scenes)
        self.workspace_stack.setCurrentIndex(1)
        
        
    def open_editor_for_scene(self, scene_content="<p>Zacznij pisać swoją scenę...</p>"):
        """Otwórz zintegrowany edytor RTF dla sceny."""
        # Usuń istniejący edytor jeśli jest (zachowaj welcome + grid views)
        while self.workspace_stack.count() > 2:
            old_editor = self.workspace_stack.widget(2)
            self.workspace_stack.removeWidget(old_editor)
            old_editor.setParent(None)
            
        # Stwórz nowy edytor
        self.current_editor = EmbeddedRichTextWidget()
        self.current_editor.set_content(scene_content)
        
        # Połącz sygnały
        self.current_editor.saveRequested.connect(self.saveRequested.emit)
        self.current_editor.focusModeRequested.connect(self.focusModeRequested.emit)
        
        # Dodaj do stack i pokaż
        self.workspace_stack.addWidget(self.current_editor)
        self.workspace_stack.setCurrentIndex(2)
        
    def get_editor_content(self):
        """Pobierz zawartość z aktualnego editora."""
        if self.current_editor:
            return self.current_editor.get_content()
        return ""