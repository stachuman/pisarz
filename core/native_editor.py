"""Natywny edytor Qt Widgets z QTextEdit i profesjonalnym toolbar."""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QToolBar, QComboBox, QPushButton, 
                              QFontComboBox, QSpinBox, QLabel, QStatusBar,
                              QColorDialog, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import (QFont, QTextCharFormat, QColor, QKeySequence, 
                          QTextCursor, QIcon, QPixmap, QPainter, QBrush, QAction)


class NativeRichTextEditor(QMainWindow):
    """Profesjonalny edytor tekstu używający natywnych komponentów Qt."""
    
    contentChanged = Signal()
    saveRequested = Signal(str)
    
    def __init__(self, scene_title="", parent=None):
        super().__init__(parent)
        self.scene_title = scene_title
        self._content = ""
        self._has_changes = False
        
        self.setup_ui()
        self.setup_toolbar()
        self.setup_actions()
        self.setup_connections()
        
    def setup_ui(self):
        """Konfiguracja głównego interfejsu."""
        self.setWindowTitle(f"Pisarz - Edytor RTF: {self.scene_title}")
        self.setMinimumSize(900, 700)
        
        # Widget centralny
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Edytor tekstu
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setFont(QFont("Liberation Serif", 12))
        layout.addWidget(self.text_edit)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Gotowy")
        
    def setup_toolbar(self):
        """Stworzenie profesjonalnego toolbar z formatowaniem."""
        # Główny toolbar
        toolbar = self.addToolBar("Formatowanie")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # === CZCIONKA ===
        # Rodzina czcionki
        font_label = QLabel("Czcionka:")
        toolbar.addWidget(font_label)
        
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Liberation Serif"))
        self.font_combo.setMinimumWidth(150)
        toolbar.addWidget(self.font_combo)
        
        # Rozmiar czcionki
        size_label = QLabel("Rozmiar:")
        toolbar.addWidget(size_label)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.setEditable(True)
        sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]
        self.font_size_combo.addItems(sizes)
        self.font_size_combo.setCurrentText("12")
        self.font_size_combo.setMinimumWidth(60)
        toolbar.addWidget(self.font_size_combo)
        
        toolbar.addSeparator()
        
        # === FORMATOWANIE ===
        # Pogrubienie
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.bold_btn.setToolTip("Pogrubienie (Ctrl+B)")
        self.bold_btn.setMinimumSize(30, 30)
        toolbar.addWidget(self.bold_btn)
        
        # Kursywa
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        font = QFont("Arial", 10)
        font.setItalic(True)
        self.italic_btn.setFont(font)
        self.italic_btn.setToolTip("Kursywa (Ctrl+I)")
        self.italic_btn.setMinimumSize(30, 30)
        toolbar.addWidget(self.italic_btn)
        
        # Podkreślenie
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        font = QFont("Arial", 10)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.setToolTip("Podkreślenie (Ctrl+U)")
        self.underline_btn.setMinimumSize(30, 30)
        toolbar.addWidget(self.underline_btn)
        
        toolbar.addSeparator()
        
        # === KOLOR TEKSTU ===
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setToolTip("Kolor tekstu")
        self.text_color_btn.setMinimumSize(30, 30)
        self.text_color_btn.setStyleSheet("QPushButton { background-color: black; color: white; font-weight: bold; }")
        toolbar.addWidget(self.text_color_btn)
        
        toolbar.addSeparator()
        
        # === WYRÓWNANIE ===
        # Wyrównanie do lewej
        self.align_left_btn = QPushButton("⇤")
        self.align_left_btn.setToolTip("Wyrównaj do lewej (Ctrl+L)")
        self.align_left_btn.setMinimumSize(30, 30)
        toolbar.addWidget(self.align_left_btn)
        
        # Wyśrodkowanie
        self.align_center_btn = QPushButton("▣")
        self.align_center_btn.setToolTip("Wyśrodkuj (Ctrl+E)")
        self.align_center_btn.setMinimumSize(30, 30)
        toolbar.addWidget(self.align_center_btn)
        
        # Wyrównanie do prawej
        self.align_right_btn = QPushButton("⇥")
        self.align_right_btn.setToolTip("Wyrównaj do prawej (Ctrl+R)")
        self.align_right_btn.setMinimumSize(30, 30)
        toolbar.addWidget(self.align_right_btn)
        
        # Wyjustowanie
        self.align_justify_btn = QPushButton("≡")
        self.align_justify_btn.setToolTip("Wyjustuj (Ctrl+J)")
        self.align_justify_btn.setMinimumSize(30, 30)
        toolbar.addWidget(self.align_justify_btn)
        
        toolbar.addSeparator()
        
        # === AKCJE ===
        # Zapisz
        self.save_btn = QPushButton("Zapisz")
        self.save_btn.setToolTip("Zapisz (Ctrl+S)")
        toolbar.addWidget(self.save_btn)
        
        # Elastyczny spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
    def setup_actions(self):
        """Konfiguracja akcji i skrótów klawiszowych."""
        # Akcja zapisz
        save_action = QAction("&Zapisz", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_content)
        self.addAction(save_action)
        
        # Formatowanie - skróty
        bold_action = QAction("Pogrubienie", self)
        bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        bold_action.triggered.connect(self.toggle_bold)
        self.addAction(bold_action)
        
        italic_action = QAction("Kursywa", self)
        italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        italic_action.triggered.connect(self.toggle_italic)
        self.addAction(italic_action)
        
        underline_action = QAction("Podkreślenie", self)
        underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        underline_action.triggered.connect(self.toggle_underline)
        self.addAction(underline_action)
        
    def setup_connections(self):
        """Połączenie sygnałów z slotami."""
        # Zmiany tekstu
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.cursorPositionChanged.connect(self.update_format_buttons)
        
        # Czcionka
        self.font_combo.currentFontChanged.connect(self.change_font_family)
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        
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
        self.align_justify_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignJustify))
        
        # Zapisz
        self.save_btn.clicked.connect(self.save_content)
        
    def on_text_changed(self):
        """Obsługa zmian w tekście."""
        self._content = self.text_edit.toHtml()
        if not self._has_changes:
            self._has_changes = True
            self.status_bar.showMessage("Zmodyfikowany")
            self.contentChanged.emit()
            
    def update_format_buttons(self):
        """Aktualizacja stanu przycisków formatowania based on cursor position."""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        
        # Aktualizuj stan przycisków
        self.bold_btn.setChecked(format.fontWeight() == QFont.Weight.Bold)
        self.italic_btn.setChecked(format.fontItalic())
        self.underline_btn.setChecked(format.fontUnderline())
        
        # Aktualizuj combo boxy
        self.font_combo.setCurrentFont(format.font())
        if format.fontPointSize() > 0:
            self.font_size_combo.setCurrentText(str(int(format.fontPointSize())))
            
    def change_font_family(self, font):
        """Zmiana rodziny czcionki."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            format = QTextCharFormat()
            format.setFontFamily(font.family())
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.setCurrentFont(font)
            
    def change_font_size(self, size_text):
        """Zmiana rozmiaru czcionki."""
        try:
            size = int(size_text)
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
            pass
            
    def toggle_bold(self):
        """Przełączanie pogrubienia."""
        cursor = self.text_edit.textCursor()
        format = QTextCharFormat()
        format.setFontWeight(QFont.Weight.Bold if self.bold_btn.isChecked() else QFont.Weight.Normal)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
            
    def toggle_italic(self):
        """Przełączanie kursywy."""
        cursor = self.text_edit.textCursor()
        format = QTextCharFormat()
        format.setFontItalic(self.italic_btn.isChecked())
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
            
    def toggle_underline(self):
        """Przełączanie podkreślenia."""
        cursor = self.text_edit.textCursor()
        format = QTextCharFormat()
        format.setFontUnderline(self.underline_btn.isChecked())
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
            
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
            
    def set_alignment(self, alignment):
        """Ustawienie wyrównania tekstu."""
        self.text_edit.setAlignment(alignment)
        
    def get_content(self):
        """Pobranie zawartości jako HTML."""
        return self.text_edit.toHtml()
        
    def set_content(self, content):
        """Ustawienie zawartości z HTML."""
        self.text_edit.setHtml(content)
        self._content = content
        self._has_changes = False
        self.status_bar.showMessage("Zawartość załadowana")
        
    def save_content(self):
        """Emisja sygnału zapisania."""
        content = self.get_content()
        self.saveRequested.emit(content)
        self._has_changes = False
        self.status_bar.showMessage("Zapisano")
        
    def has_changes(self):
        """Sprawdzenie czy są niezapisane zmiany."""
        return self._has_changes
        
    def closeEvent(self, event):
        """Obsługa zamknięcia okna."""
        if self._has_changes:
            # Auto-zapisz przy zamykaniu
            self.save_content()
        event.accept()