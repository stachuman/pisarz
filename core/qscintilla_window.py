"""Separate QScintilla editor window for rich text editing."""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QFontComboBox, QToolBar, QStatusBar
from PySide6.QtCore import Signal, QObject, Slot, QTimer
from PySide6.QtGui import QFont, QAction, QKeySequence, QCloseEvent


class QScintillaEditorWindow(QMainWindow):
    """Standalone QScintilla editor window with full rich text capabilities."""
    
    contentChanged = Signal()
    saveRequested = Signal(str)  # Emit content when save is requested
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._content = ""
        self._has_changes = False
        self.setup_ui()
        self.setup_actions()
        
    def setup_ui(self):
        """Setup the editor window UI."""
        self.setWindowTitle("Pisarz - Rich Text Editor (QScintilla)")
        self.setMinimumSize(800, 600)
        
        # Import QScintilla only when actually creating the widget
        try:
            from PyQt5.Qsci import QsciScintilla, QsciLexerHTML
        except ImportError:
            try:
                from qsci import QsciScintilla, QsciLexerHTML
            except ImportError:
                from QScintilla import QsciScintilla, QsciLexerHTML
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create toolbar
        self.setup_toolbar()
        
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
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def setup_toolbar(self):
        """Setup formatting toolbar."""
        toolbar = self.addToolBar("Formatting")
        
        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Liberation Serif"))
        self.font_combo.currentFontChanged.connect(self.change_font_family)
        toolbar.addWidget(self.font_combo)
        
        # Font size
        self.size_combo = QComboBox()
        self.size_combo.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36"])
        self.size_combo.setCurrentText("12")
        self.size_combo.currentTextChanged.connect(self.change_font_size)
        toolbar.addWidget(self.size_combo)
        
        toolbar.addSeparator()
        
        # Bold
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.bold_btn.setToolTip("Bold")
        toolbar.addWidget(self.bold_btn)
        
        # Italic
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        font = QFont("Arial", 10)
        font.setItalic(True)
        self.italic_btn.setFont(font)
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.italic_btn.setToolTip("Italic")
        toolbar.addWidget(self.italic_btn)
        
        # Underline
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        font = QFont("Arial", 10)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.clicked.connect(self.toggle_underline)
        self.underline_btn.setToolTip("Underline")
        toolbar.addWidget(self.underline_btn)
        
    def setup_actions(self):
        """Setup menu and keyboard actions."""
        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_content)
        self.addAction(save_action)
        
    def _on_text_changed(self):
        """Handle text change."""
        old_content = self._content
        self._content = self.editor.text()
        if old_content != self._content:
            self._has_changes = True
            self.status_bar.showMessage("Modified")
            self.contentChanged.emit()
        
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
        self._content = content
        self._has_changes = False
        self.status_bar.showMessage("Ready")
        
    def save_content(self):
        """Save current content."""
        self.saveRequested.emit(self.get_content())
        self._has_changes = False
        self.status_bar.showMessage("Saved")
        
    def has_changes(self):
        """Check if there are unsaved changes."""
        return self._has_changes
        
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        if self._has_changes:
            # Auto-save on close
            self.save_content()
        event.accept()