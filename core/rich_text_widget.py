"""QScintilla-based rich text editor manager for QML integration."""

from PySide6.QtCore import Signal, QObject, Slot, Property
from PySide6.QtQml import QmlElement
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QFontComboBox
from PySide6.QtGui import QFont
try:
    from PyQt5.Qsci import QsciScintilla, QsciLexerHTML
except ImportError:
    try:
        from qsci import QsciScintilla, QsciLexerHTML
    except ImportError:
        from QScintilla import QsciScintilla, QsciLexerHTML

QML_IMPORT_NAME = "Pisarz"
QML_IMPORT_MAJOR_VERSION = 1


class QScintillaWidget(QWidget):
    """QScintilla widget with toolbar."""
    
    textChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._content = ""
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Liberation Serif"))
        self.font_combo.currentFontChanged.connect(self.change_font_family)
        toolbar_layout.addWidget(self.font_combo)
        
        # Font size
        self.size_combo = QComboBox()
        self.size_combo.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36"])
        self.size_combo.setCurrentText("12")
        self.size_combo.currentTextChanged.connect(self.change_font_size)
        toolbar_layout.addWidget(self.size_combo)
        
        # Bold
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.bold_btn.clicked.connect(self.toggle_bold)
        toolbar_layout.addWidget(self.bold_btn)
        
        # Italic
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        font = QFont("Arial", 10)
        font.setItalic(True)
        self.italic_btn.setFont(font)
        self.italic_btn.clicked.connect(self.toggle_italic)
        toolbar_layout.addWidget(self.italic_btn)
        
        # Underline
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        font = QFont("Arial", 10)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.clicked.connect(self.toggle_underline)
        toolbar_layout.addWidget(self.underline_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Create editor
        self.editor = QsciScintilla()
        
        # Configure for rich text editing
        self.editor.setLexer(QsciLexerHTML())
        self.editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        self.editor.setAutoIndent(True)
        self.editor.setIndentationsUseTabs(False)
        self.editor.setIndentationWidth(2)
        self.editor.setTabWidth(2)
        
        # Enable folding
        self.editor.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        
        # Set font
        font = QFont("Liberation Serif", 12)
        self.editor.setFont(font)
        
        # Connect signals
        self.editor.textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.editor)
        
    def _on_text_changed(self):
        """Handle text change."""
        self._content = self.editor.text()
        self.textChanged.emit()
        
    def change_font_family(self, font):
        """Change font family."""
        if self.editor.hasSelectedText():
            self.wrap_selection_with_style(f'font-family: {font.family()}')
            
    def change_font_size(self, size):
        """Change font size."""
        if self.editor.hasSelectedText():
            self.wrap_selection_with_style(f'font-size: {size}px')
            
    def toggle_bold(self):
        """Toggle bold formatting."""
        if self.bold_btn.isChecked():
            self.wrap_selection_with_tag('strong')
        else:
            self.remove_tag_from_selection('strong')
            
    def toggle_italic(self):
        """Toggle italic formatting."""
        if self.italic_btn.isChecked():
            self.wrap_selection_with_tag('em')
        else:
            self.remove_tag_from_selection('em')
            
    def toggle_underline(self):
        """Toggle underline formatting."""
        if self.underline_btn.isChecked():
            self.wrap_selection_with_tag('u')
        else:
            self.remove_tag_from_selection('u')
            
    def wrap_selection_with_tag(self, tag):
        """Wrap selected text with HTML tag."""
        if self.editor.hasSelectedText():
            selected = self.editor.selectedText()
            replacement = f'<{tag}>{selected}</{tag}>'
            self.editor.replaceSelectedText(replacement)
            
    def wrap_selection_with_style(self, style):
        """Wrap selected text with span and style."""
        if self.editor.hasSelectedText():
            selected = self.editor.selectedText()
            replacement = f'<span style="{style}">{selected}</span>'
            self.editor.replaceSelectedText(replacement)
            
    def remove_tag_from_selection(self, tag):
        """Remove HTML tag from selection (simplified)."""
        if self.editor.hasSelectedText():
            selected = self.editor.selectedText()
            replacement = selected.replace(f'<{tag}>', '').replace(f'</{tag}>', '')
            self.editor.replaceSelectedText(replacement)

    def get_content(self):
        """Get editor content."""
        return self.editor.text()
        
    def set_content(self, content):
        """Set editor content."""
        self.editor.setText(content)


@QmlElement
class RichTextEditor(QObject):
    """QML interface for QScintilla editor."""
    
    textChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._widget = None
        self._content = ""
        
    def create_widget(self):
        """Create the widget instance."""
        if not self._widget:
            self._widget = QScintillaWidget()
            self._widget.textChanged.connect(self._on_text_changed)
        return self._widget
        
    def _on_text_changed(self):
        """Handle text change from widget."""
        if self._widget:
            self._content = self._widget.get_content()
            self.textChanged.emit()
    
    @Property(str, notify=textChanged)
    def content(self):
        """Get editor content."""
        return self._content
    
    @content.setter
    def content(self, value):
        """Set editor content."""
        if value != self._content:
            self._content = value
            if self._widget:
                self._widget.set_content(value)
            self.textChanged.emit()
    
    @Slot(str)
    def setContent(self, content):
        """Set content from QML."""
        self.content = content
        
    @Slot(result=str)
    def getContent(self):
        """Get content for QML."""
        if self._widget:
            return self._widget.get_content()
        return self._content