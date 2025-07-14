"""Embedded edytor RTF do integracji bezpośrednio w QML."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QToolBar, QComboBox, QPushButton, 
                              QFontComboBox, QLabel, QColorDialog, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QTimer, QObject, Slot, Property
from PySide6.QtGui import (QFont, QFontInfo, QTextCharFormat, QColor, QKeySequence, 
                          QTextCursor, QBrush, QAction)
from PySide6.QtQml import QmlElement
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickWidgets import QQuickWidget

QML_IMPORT_NAME = "Pisarz"
QML_IMPORT_MAJOR_VERSION = 1


class EmbeddedRichTextWidget(QWidget):
    """Edytor RTF do embeddowania w QML - bez głównego okna."""
    
    contentChanged = Signal()
    saveRequested = Signal(str)
    focusModeRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._content = ""
        self._has_changes = False
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Konfiguracja interfejsu jako widget (nie main window)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        self.setup_toolbar(layout)
        
        # Edytor tekstu
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        layout.addWidget(self.text_edit)
        
        # Ustaw domyślną czcionkę po utworzeniu toolbar (żeby combo box istniał)
        self._set_default_font()
        
    def setup_toolbar(self, main_layout):
        """Stworzenie toolbar jako widget (nie QMainWindow toolbar)."""
        # Container dla toolbar
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(5)
        
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
        self.bold_btn.setFixedSize(32, 32)
        self.bold_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
        """)
        toolbar_layout.addWidget(self.bold_btn)
        
        # Kursywa
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        font = QFont("Arial", 12)
        font.setItalic(True)
        self.italic_btn.setFont(font)
        self.italic_btn.setToolTip("Kursywa (Ctrl+I)")
        self.italic_btn.setFixedSize(32, 32)
        self.italic_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-style: italic;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
        """)
        toolbar_layout.addWidget(self.italic_btn)
        
        # Podkreślenie
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        font = QFont("Arial", 12)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.setToolTip("Podkreślenie (Ctrl+U)")
        self.underline_btn.setFixedSize(32, 32)
        self.underline_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-decoration: underline;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
        """)
        toolbar_layout.addWidget(self.underline_btn)
        
        # Separator
        separator2 = QWidget()
        separator2.setFixedWidth(10)
        toolbar_layout.addWidget(separator2)
        
        # === KOLOR TEKSTU ===
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setToolTip("Kolor tekstu")
        self.text_color_btn.setFixedSize(32, 32)
        self.text_color_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.text_color_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: 1px solid #dc3545;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
                border-color: #bd2130;
            }
        """)
        toolbar_layout.addWidget(self.text_color_btn)
        
        # Separator
        separator3 = QWidget()
        separator3.setFixedWidth(10)
        toolbar_layout.addWidget(separator3)
        
        # === WYRÓWNANIE ===
        # Wyrównanie do lewej
        self.align_left_btn = QPushButton("L")
        self.align_left_btn.setToolTip("Wyrównaj do lewej")
        self.align_left_btn.setFixedSize(32, 32)
        self.align_left_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.align_left_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        toolbar_layout.addWidget(self.align_left_btn)
        
        # Wyśrodkowanie
        self.align_center_btn = QPushButton("C")
        self.align_center_btn.setToolTip("Wyśrodkuj")
        self.align_center_btn.setFixedSize(32, 32)
        self.align_center_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.align_center_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        toolbar_layout.addWidget(self.align_center_btn)
        
        # Wyrównanie do prawej
        self.align_right_btn = QPushButton("R")
        self.align_right_btn.setToolTip("Wyrównaj do prawej")
        self.align_right_btn.setFixedSize(32, 32)
        self.align_right_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.align_right_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        toolbar_layout.addWidget(self.align_right_btn)
        
        # Separator
        separator4 = QWidget()
        separator4.setFixedWidth(10)
        toolbar_layout.addWidget(separator4)
        
        # === ZAPISZ ===
        self.save_btn = QPushButton("Zapisz")
        self.save_btn.setToolTip("Zapisz (Ctrl+S)")
        self.save_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: 1px solid #28a745;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
                border-color: #1e7e34;
            }
        """)
        toolbar_layout.addWidget(self.save_btn)
        
        # Separator
        separator5 = QWidget()
        separator5.setFixedWidth(10)
        toolbar_layout.addWidget(separator5)
        
        # === TRYB FOKUSU ===
        self.focus_mode_btn = QPushButton("Fokus")
        self.focus_mode_btn.setToolTip("Tryb fokusu pisania (F11)")
        self.focus_mode_btn.setFixedSize(70, 32)
        self.focus_mode_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.focus_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
        """)
        toolbar_layout.addWidget(self.focus_mode_btn)
        
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
        
        # Aktualizuj combo boxy - zablokuj sygnały aby uniknąć cyklicznych wywołań
        self.font_combo.blockSignals(True)
        current_font_family = format.font().family()
        index = self.font_combo.findText(current_font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        self.font_combo.blockSignals(False)
        
        if format.fontPointSize() > 0:
            self.font_size_combo.blockSignals(True)
            self.font_size_combo.setCurrentText(str(int(format.fontPointSize())))
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
        format = QTextCharFormat()
        format.setFontWeight(QFont.Weight.Bold if self.bold_btn.isChecked() else QFont.Weight.Normal)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def toggle_italic(self):
        """Przełączanie kursywy."""
        cursor = self.text_edit.textCursor()
        format = QTextCharFormat()
        format.setFontItalic(self.italic_btn.isChecked())
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Przywróć fokus do editora
        self.text_edit.setFocus()
            
    def toggle_underline(self):
        """Przełączanie podkreślenia."""
        cursor = self.text_edit.textCursor()
        format = QTextCharFormat()
        format.setFontUnderline(self.underline_btn.isChecked())
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
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


@QmlElement
class EmbeddedEditorBridge(QObject):
    """Bridge do embeddowania edytora RTF bezpośrednio w QML."""
    
    contentChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._widget = None
        self._content = ""
        self._has_changes = False
        
    def create_widget(self):
        """Stwórz widget edytora."""
        if not self._widget:
            self._widget = EmbeddedRichTextWidget()
            self._widget.contentChanged.connect(self._on_content_changed)
            self._widget.saveRequested.connect(self._on_save_requested)
        return self._widget
        
    def _on_content_changed(self):
        """Obsługa zmian zawartości."""
        if self._widget:
            self._content = self._widget.get_content()
            self._has_changes = True
            self.contentChanged.emit()
            
    def _on_save_requested(self, content):
        """Obsługa żądania zapisania."""
        self._content = content
        self._has_changes = False
        self.contentChanged.emit()
    
    @Property(str, notify=contentChanged)
    def content(self):
        """Pobierz zawartość."""
        return self._content
    
    @content.setter
    def content(self, value):
        """Ustaw zawartość."""
        if value != self._content:
            self._content = value
            if self._widget:
                self._widget.set_content(value)
            self._has_changes = False
            self.contentChanged.emit()
    
    @Slot(str)
    def setContent(self, content):
        """Ustaw zawartość z QML."""
        self.content = content
        
    @Slot(result=str)
    def getContent(self):
        """Pobierz zawartość dla QML."""
        if self._widget:
            return self._widget.get_content()
        return self._content
    
    @Slot(result=bool)
    def hasChanges(self):
        """Sprawdź czy są zmiany."""
        if self._widget:
            return self._widget.has_changes()
        return self._has_changes
    
    @Slot()
    def resetChanges(self):
        """Resetuj flagę zmian."""
        self._has_changes = False
        if self._widget:
            self._widget._has_changes = False