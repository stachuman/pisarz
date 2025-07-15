"""Embedded edytor RTF do integracji bezpośrednio w QML."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QToolBar, QComboBox, QPushButton, 
                              QFontComboBox, QLabel, QColorDialog, QSizePolicy, QSplitter)
from PySide6.QtCore import Signal, Qt, QTimer, QObject, Slot, Property
from PySide6.QtGui import (QFont, QFontInfo, QTextCharFormat, QColor, QKeySequence, 
                          QTextCursor, QBrush, QShortcut)


class EmbeddedRichTextWidget(QWidget):
    """Embedded RTF editor widget for QtWidgets applications."""
    
    contentChanged = Signal()
    saveRequested = Signal(str)
    focusModeRequested = Signal()
    contextPanelToggled = Signal(bool)  # New signal for context panel toggle
    
    # Context panel signals
    characterAddedToScene = Signal(int, str)  # character_id, role
    characterRemovedFromScene = Signal(int)   # character_id
    locationAddedToScene = Signal(int, str)   # location_id, role
    locationRemovedFromScene = Signal(int)    # location_id
    newCharacterRequestedFromScene = Signal(str)  # name
    newLocationRequestedFromScene = Signal(str)   # name
    characterSelectedFromScene = Signal(int)     # character_id
    locationSelectedFromScene = Signal(int)      # location_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._content = ""
        self._has_changes = False
        self.context_panel = None
        self.context_panel_visible = False  # Start with panel hidden
        
        self.setup_ui()
        self.setup_connections()
        
        # Initial update of toolbar to reflect current format
        QTimer.singleShot(100, self.update_format_buttons)
        
    def setup_ui(self):
        """Konfiguracja interfejsu jako widget (nie main window)."""
        # Set explicit styling to remove any default spacing
        self.setStyleSheet("EmbeddedRichTextWidget { margin: 0px; padding: 0px; border: none; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing between toolbar and editor
        
        # Toolbar
        self.setup_toolbar(layout)
        
        # Splitter for editor and context panel
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setContentsMargins(0, 0, 0, 0)
        self.splitter.setHandleWidth(3)  # Minimize splitter handle width
        self.splitter.setStyleSheet("QSplitter { margin: 0px; padding: 0px; }")
        
        # Edytor tekstu
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setContentsMargins(0, 0, 0, 0)
        self.text_edit.setStyleSheet("QTextEdit { margin: 0px; padding: 8px; border: none; }")
        self.splitter.addWidget(self.text_edit)
        
        # Context panel (will be added later)
        self.context_panel = None
        
        layout.addWidget(self.splitter)
        
        # Force layout update to prevent gaps
        self.updateGeometry()
        self.update()
        
        # Ustaw domyślną czcionkę po utworzeniu toolbar (żeby combo box istniał)
        self._set_default_font()
        
    def setup_toolbar(self, main_layout):
        """Stworzenie toolbar jako widget (nie QMainWindow toolbar)."""
        # Container dla toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setFixedHeight(36)  # Fixed height instead of maximum
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(8, 2, 8, 2)  # Even smaller margins
        toolbar_layout.setSpacing(8)
        
        # === CZCIONKA ===
        # Rodzina czcionki
        font_label = QLabel("Czcionka:")
        toolbar_layout.addWidget(font_label)
        
        # Używamy zwykłego QComboBox zamiast QFontComboBox dla pełnej kontroli
        self.font_combo = QComboBox()
        self.font_combo.setEditable(False)
        # Ogranicz do tylko preferowanych czcionek do pisania
        self._setup_limited_font_list()
        self.font_combo.setMinimumWidth(130)
        self.font_combo.setMaximumWidth(150)
        toolbar_layout.addWidget(self.font_combo)
        
        # Rozmiar czcionki
        size_label = QLabel("Rozmiar:")
        toolbar_layout.addWidget(size_label)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.setEditable(True)
        sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36"]
        self.font_size_combo.addItems(sizes)
        self.font_size_combo.setCurrentText("12")
        self.font_size_combo.setMinimumWidth(50)
        self.font_size_combo.setMaximumWidth(70)
        toolbar_layout.addWidget(self.font_size_combo)
        
        # Separator
        separator1 = QWidget()
        separator1.setFixedWidth(10)
        toolbar_layout.addWidget(separator1)
        
        # === FORMATOWANIE ===
        # Pogrubienie
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.bold_btn.setToolTip("Pogrubienie (Ctrl+B)")
        self.bold_btn.setFixedSize(28, 28)
        toolbar_layout.addWidget(self.bold_btn)
        
        # Kursywa
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        font = QFont("Arial", 12)
        font.setItalic(True)
        self.italic_btn.setFont(font)
        self.italic_btn.setToolTip("Kursywa (Ctrl+I)")
        self.italic_btn.setFixedSize(28, 28)
        toolbar_layout.addWidget(self.italic_btn)
        
        # Podkreślenie
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        font = QFont("Arial", 12)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.setToolTip("Podkreślenie (Ctrl+U)")
        self.underline_btn.setFixedSize(28, 28)
        toolbar_layout.addWidget(self.underline_btn)
        
        # Separator
        separator2 = QWidget()
        separator2.setFixedWidth(10)
        toolbar_layout.addWidget(separator2)
        
        # === KOLOR TEKSTU ===
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setToolTip("Kolor tekstu")
        self.text_color_btn.setFixedSize(28, 28)
        self.text_color_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        toolbar_layout.addWidget(self.text_color_btn)
        
        # Separator
        separator3 = QWidget()
        separator3.setFixedWidth(10)
        toolbar_layout.addWidget(separator3)
        
        # === WYRÓWNANIE ===
        # Wyrównanie do lewej
        self.align_left_btn = QPushButton("◀")
        self.align_left_btn.setToolTip("Wyrównaj do lewej")
        self.align_left_btn.setFixedSize(28, 28)
        toolbar_layout.addWidget(self.align_left_btn)
        
        # Wyśrodkowanie
        self.align_center_btn = QPushButton("‖")
        self.align_center_btn.setToolTip("Wyśrodkuj")
        self.align_center_btn.setFixedSize(28, 28)
        toolbar_layout.addWidget(self.align_center_btn)
        
        # Wyrównanie do prawej
        self.align_right_btn = QPushButton("▶")
        self.align_right_btn.setToolTip("Wyrównaj do prawej")
        self.align_right_btn.setFixedSize(28, 28)
        toolbar_layout.addWidget(self.align_right_btn)
        
        # Separator
        separator4 = QWidget()
        separator4.setFixedWidth(10)
        toolbar_layout.addWidget(separator4)
        
        # === ZAPISZ ===
        self.save_btn = QPushButton("Zapisz")
        self.save_btn.setToolTip("Zapisz (Ctrl+S)")
        toolbar_layout.addWidget(self.save_btn)
        
        # Separator
        separator5 = QWidget()
        separator5.setFixedWidth(10)
        toolbar_layout.addWidget(separator5)
        
        # === TRYB FOKUSU ===
        self.focus_mode_btn = QPushButton("Fokus")
        self.focus_mode_btn.setToolTip("Tryb fokusu pisania (F11)")
        toolbar_layout.addWidget(self.focus_mode_btn)
        
        # Context Panel Toggle
        self.context_panel_btn = QPushButton("📝")
        self.context_panel_btn.setCheckable(True)
        self.context_panel_btn.setChecked(False)  # Start with panel hidden
        self.context_panel_btn.setToolTip("Toggle Scene Context Panel (Ctrl+E)")
        self.context_panel_btn.setFixedSize(32, 32)
        toolbar_layout.addWidget(self.context_panel_btn)
        
        # Elastyczny spacer
        toolbar_layout.addStretch()
        
        # Dodaj toolbar do głównego layout
        main_layout.addWidget(toolbar_widget)
        
    def setup_connections(self):
        """Połączenie sygnałów z slotami."""
        # Zmiany tekstu
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.cursorPositionChanged.connect(self.update_format_buttons)
        
        # Czcionka
        self.font_combo.currentTextChanged.connect(self.change_font_family)
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        
        # Ustawienia focus policy - zapobieganie utracie fokusu (ale pozwalamy na edycję)
        self.font_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.font_size_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Usuwam NoFocus policy - może to powodowało problem z wyświetlaniem
        # self.bold_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.italic_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.underline_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.text_color_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.align_left_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.align_center_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.align_right_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.save_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.focus_mode_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Formatowanie
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.underline_btn.clicked.connect(self.toggle_underline)
        
        # Kolor
        self.text_color_btn.clicked.connect(self.change_text_color)
        
        # Wyrównanie
        self.align_left_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        self.align_center_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignCenter))
        self.align_right_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        
        # Zapisz
        self.save_btn.clicked.connect(self.save_content)
        
        # Tryb fokusu
        self.focus_mode_btn.clicked.connect(self.focusModeRequested.emit)
        
        # Context panel toggle
        self.context_panel_btn.clicked.connect(self.toggle_context_panel)
        
        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for formatting."""
        
        # Bold - Ctrl+B
        bold_shortcut = QShortcut(QKeySequence("Ctrl+B"), self.text_edit)
        bold_shortcut.activated.connect(self.toggle_bold)
        
        # Italic - Ctrl+I
        italic_shortcut = QShortcut(QKeySequence("Ctrl+I"), self.text_edit)
        italic_shortcut.activated.connect(self.toggle_italic)
        
        # Underline - Ctrl+U
        underline_shortcut = QShortcut(QKeySequence("Ctrl+U"), self.text_edit)
        underline_shortcut.activated.connect(self.toggle_underline)
        
        # Save - Ctrl+S
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self.text_edit)
        save_shortcut.activated.connect(self.save_content)
        
        # Toggle Context Panel - Ctrl+E (for "Editor context")
        context_shortcut = QShortcut(QKeySequence("Ctrl+E"), self.text_edit)
        context_shortcut.activated.connect(self.toggle_context_panel)
        
    def on_text_changed(self):
        """Obsługa zmian w tekście."""
        self._content = self.text_edit.toHtml()
        if not self._has_changes:
            self._has_changes = True
            self.contentChanged.emit()
            
    def update_format_buttons(self):
        """Aktualizacja stanu przycisków formatowania."""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        
        # Aktualizuj stan przycisków
        self.bold_btn.setChecked(format.fontWeight() == QFont.Weight.Bold)
        self.italic_btn.setChecked(format.fontItalic())
        self.underline_btn.setChecked(format.fontUnderline())
        
        # Aktualizuj rodzinę czcionki - zablokuj sygnały aby uniknąć cyklicznych wywołań
        self.font_combo.blockSignals(True)
        current_font_family = format.font().family()
        if not current_font_family:
            # Fallback - pobierz czcionkę z editora
            current_font_family = self.text_edit.currentFont().family()
        
        index = self.font_combo.findText(current_font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        self.font_combo.blockSignals(False)
        
        # Aktualizuj rozmiar czcionki
        font_size = format.fontPointSize()
        if font_size <= 0:
            # Fallback - pobierz rozmiar z aktualnej czcionki editora
            font_size = self.text_edit.currentFont().pointSize()
        
        if font_size > 0:
            self.font_size_combo.blockSignals(True)
            self.font_size_combo.setCurrentText(str(int(font_size)))
            self.font_size_combo.blockSignals(False)
            
    def change_font_family(self, font_name):
        """Zmiana rodziny czcionki."""
        if not font_name:
            return
            
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            format = QTextCharFormat()
            format.setFontFamily(font_name)
            cursor.mergeCharFormat(format)
        else:
            font_obj = self.text_edit.currentFont()
            font_obj.setFamily(font_name)
            self.text_edit.setCurrentFont(font_obj)
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def change_font_size(self, size_text):
        """Zmiana rozmiaru czcionki."""
        try:
            size = int(size_text)
            
            # Walidacja zakresu rozmiaru fontu
            if size < 1 or size > 999:
                return
                
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                format = QTextCharFormat()
                format.setFontPointSize(size)
                cursor.mergeCharFormat(format)
            else:
                font = self.text_edit.currentFont()
                font.setPointSize(size)
                self.text_edit.setCurrentFont(font)
                
        except ValueError:
            # Ignoruj nieprawidłowe wartości
            return
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def toggle_bold(self):
        """Przełączanie pogrubienia."""
        cursor = self.text_edit.textCursor()
        current_format = cursor.charFormat()
        
        # Sprawdź aktualny stan pogrubienia
        is_bold = current_format.fontWeight() == QFont.Weight.Bold
        
        # Przełącz stan
        format = QTextCharFormat()
        format.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Aktualizuj przycisk
        self.bold_btn.setChecked(not is_bold)
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def toggle_italic(self):
        """Przełączanie kursywy."""
        cursor = self.text_edit.textCursor()
        current_format = cursor.charFormat()
        
        # Sprawdź aktualny stan kursywy
        is_italic = current_format.fontItalic()
        
        # Przełącz stan
        format = QTextCharFormat()
        format.setFontItalic(not is_italic)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Aktualizuj przycisk
        self.italic_btn.setChecked(not is_italic)
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def toggle_underline(self):
        """Przełączanie podkreślenia."""
        cursor = self.text_edit.textCursor()
        current_format = cursor.charFormat()
        
        # Sprawdź aktualny stan podkreślenia
        is_underline = current_format.fontUnderline()
        
        # Przełącz stan
        format = QTextCharFormat()
        format.setFontUnderline(not is_underline)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Aktualizuj przycisk
        self.underline_btn.setChecked(not is_underline)
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def change_text_color(self):
        """Zmiana koloru tekstu."""
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "Wybierz kolor tekstu")
        if color.isValid():
            cursor = self.text_edit.textCursor()
            format = QTextCharFormat()
            format.setForeground(QBrush(color))
            
            if cursor.hasSelection():
                cursor.mergeCharFormat(format)
            else:
                self.text_edit.mergeCurrentCharFormat(format)
                
            # Aktualizuj kolor przycisku
            self.text_color_btn.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; color: white; font-weight: bold; }}")
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def set_alignment(self, alignment):
        """Ustawienie wyrównania tekstu."""
        self.text_edit.setAlignment(alignment)
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
        
    def get_content(self):
        """Pobranie zawartości jako HTML."""
        return self.text_edit.toHtml()
        
    def set_content(self, content):
        """Ustawienie zawartości z HTML."""
        self.text_edit.setHtml(content)
        self._content = content
        self._has_changes = False
        
        # Ustaw domyślną czcionkę dla nowego tekstu
        self._set_default_font()
        
        # Update toolbar to reflect current format
        QTimer.singleShot(50, self.update_format_buttons)
        
    def _set_default_font(self):
        """Ustaw domyślną czcionkę dla edytora i nowego tekstu."""
        # Najlepsze czcionki do pisania książek dostępne w systemie (w kolejności preferencji)
        preferred_fonts = ["Georgia", "Times New Roman", "Nimbus Roman", "Bitstream Charter", 
                          "Liberation Serif", "URW Bookman", "C059", "DejaVu Serif"]
        selected_font = None
        
        for font_name in preferred_fonts:
            font = QFont(font_name, 12)
            if QFontInfo(font).family() == font_name:
                selected_font = font
                break
                
        if not selected_font:
            # Fallback na systemową czcionkę serif
            selected_font = QFont("serif", 12)
            
        # Ustaw czcionkę dla całego editora
        self.text_edit.setFont(selected_font)
        
        # Ustaw czcionkę jako aktualną (dla nowego tekstu)
        self.text_edit.setCurrentFont(selected_font)
        
        # Ustaw w combo box
        if hasattr(self, 'font_combo'):
            self.font_combo.blockSignals(True)
            font_family = selected_font.family()
            index = self.font_combo.findText(font_family)
            if index >= 0:
                self.font_combo.setCurrentIndex(index)
            self.font_combo.blockSignals(False)
            
    def _setup_limited_font_list(self):
        """Ogranicz combo box do tylko preferowanych czcionek."""
        preferred_fonts = ["Georgia", "Times New Roman", "Nimbus Roman", "Bitstream Charter", 
                          "Liberation Serif", "URW Bookman", "C059", "DejaVu Serif"]
        
        # Wyczyść domyślną listę
        self.font_combo.clear()
        
        # Dodaj tylko dostępne czcionki z naszej listy
        for font_name in preferred_fonts:
            font = QFont(font_name)
            if QFontInfo(font).family() == font_name:
                self.font_combo.addItem(font_name)
                
        # Jeśli żadna nie jest dostępna, dodaj fallback
        if self.font_combo.count() == 0:
            self.font_combo.addItem("serif")
        
    def save_content(self):
        """Emisja sygnału zapisania."""
        content = self.get_content()
        self.saveRequested.emit(content)
        self._has_changes = False
        
    def has_changes(self):
        """Sprawdzenie czy są niezapisane zmiany."""
        return self._has_changes
    
    def initialize_context_panel(self, character_manager, location_manager, project_id):
        """Initialize the context panel with managers."""
        from ui.widgets.scene_context_panel import SceneContextPanel
        
        if self.context_panel is None:
            self.context_panel = SceneContextPanel()
            self.context_panel.set_managers(character_manager, location_manager, project_id)
            self.splitter.addWidget(self.context_panel)
            
            # Set visibility based on current state
            self.context_panel.setVisible(self.context_panel_visible)
            
            # Set initial splitter sizes based on visibility
            if self.context_panel_visible:
                self.splitter.setSizes([800, 300])
            else:
                self.splitter.setSizes([1100, 0])
            
            # Connect context panel signals
            self._connect_context_panel_signals()
        else:
            # Update existing panel with new managers
            self.context_panel.set_managers(character_manager, location_manager, project_id)
    
    def set_scene_context(self, scene_id):
        """Set the current scene for the context panel."""
        if self.context_panel:
            self.context_panel.set_scene_id(scene_id)
    
    def toggle_context_panel(self):
        """Toggle the visibility of the context panel."""
        if self.context_panel:
            self.context_panel_visible = not self.context_panel_visible
            self.context_panel.setVisible(self.context_panel_visible)
            self.context_panel_btn.setChecked(self.context_panel_visible)
            self.contextPanelToggled.emit(self.context_panel_visible)
            
            # Adjust splitter sizes
            if self.context_panel_visible:
                self.splitter.setSizes([800, 300])
            else:
                self.splitter.setSizes([1100, 0])
    
    def _connect_context_panel_signals(self):
        """Connect context panel signals to handle character/location management."""
        if not self.context_panel:
            return
        
        # Pass through signals to main application
        self.context_panel.character_added.connect(self.characterAddedToScene.emit)
        self.context_panel.character_removed.connect(self.characterRemovedFromScene.emit)
        self.context_panel.location_added.connect(self.locationAddedToScene.emit)
        self.context_panel.location_removed.connect(self.locationRemovedFromScene.emit)
        self.context_panel.new_character_requested.connect(self.newCharacterRequestedFromScene.emit)
        self.context_panel.new_location_requested.connect(self.newLocationRequestedFromScene.emit)
        self.context_panel.character_selected.connect(self.characterSelectedFromScene.emit)
        self.context_panel.location_selected.connect(self.locationSelectedFromScene.emit)
    
    def refresh_context_panel(self):
        """Refresh the context panel data."""
        if self.context_panel:
            self.context_panel.refresh_context()
    
    def find_and_highlight_text(self, search_text):
        """Find and highlight the first occurrence of search text in the editor."""
        if not search_text:
            return False
        
        # Get the plain text content for searching
        plain_text = self.text_edit.toPlainText()
        
        # Find the first occurrence (case insensitive)
        index = plain_text.lower().find(search_text.lower())
        if index == -1:
            return False
        
        # Create a cursor and move it to the found position
        cursor = self.text_edit.textCursor()
        cursor.setPosition(index)
        cursor.setPosition(index + len(search_text), QTextCursor.MoveMode.KeepAnchor)
        
        # Set the cursor to select the found text
        self.text_edit.setTextCursor(cursor)
        
        # Ensure the found text is visible
        self.text_edit.ensureCursorVisible()
        
        # Apply temporary highlighting
        format = QTextCharFormat()
        format.setBackground(QBrush(QColor(255, 255, 0, 128)))  # Semi-transparent yellow
        cursor.mergeCharFormat(format)
        
        # Clear the highlighting after 2 seconds
        QTimer.singleShot(2000, self._clear_search_highlight)
        
        return True
    
    def _clear_search_highlight(self):
        """Clear search highlighting from the text."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            # Clear the background formatting
            format = QTextCharFormat()
            format.setBackground(QBrush())  # Clear background
            cursor.mergeCharFormat(format)
            # Move cursor to end of selection to deselect
            cursor.setPosition(cursor.selectionEnd())
            self.text_edit.setTextCursor(cursor)


