"""Bridge for QScintilla editor window to QML integration."""

from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtQml import QmlElement
from .qscintilla_window import QScintillaEditorWindow

QML_IMPORT_NAME = "Pisarz"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class EditorBridge(QObject):
    """Bridge to expose QScintilla editor window functionality to QML."""
    
    contentChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor_window = None
        self._content = ""
        self._has_changes = False
        
    def _ensure_editor_window(self):
        """Create editor window if it doesn't exist."""
        if not self._editor_window:
            try:
                self._editor_window = QScintillaEditorWindow()
                self._editor_window.contentChanged.connect(self._on_content_changed)
                self._editor_window.saveRequested.connect(self._on_save_requested)
            except Exception as e:
                print(f"Error creating QScintilla window: {e}")
                return False
        return True
            
    def _on_content_changed(self):
        """Handle content changes from editor window."""
        if self._editor_window:
            new_content = self._editor_window.get_content()
            if new_content != self._content:
                self._content = new_content
                self._has_changes = True
                self.contentChanged.emit()
                
    def _on_save_requested(self, content):
        """Handle save request from editor window."""
        self._content = content
        self._has_changes = False
        self.contentChanged.emit()
    
    @Property(str, notify=contentChanged)
    def content(self):
        """Get current content."""
        return self._content
    
    @content.setter
    def content(self, value):
        """Set content."""
        if value != self._content:
            self._content = value
            if self._editor_window:
                self._editor_window.set_content(value)
            self._has_changes = False
            self.contentChanged.emit()
    
    @Slot(str)
    def setContent(self, content):
        """Set content from QML."""
        self.content = content
        
    @Slot(result=str)
    def getContent(self):
        """Get content for QML."""
        if self._editor_window:
            return self._editor_window.get_content()
        return self._content
    
    @Slot(result=bool)
    def hasChanges(self):
        """Check if editor has unsaved changes."""
        if self._editor_window:
            return self._editor_window.has_changes()
        return self._has_changes
    
    @Slot()
    def resetChanges(self):
        """Reset changes flag."""
        self._has_changes = False
        if self._editor_window:
            self._editor_window._has_changes = False
    
    @Slot()
    def openEditor(self):
        """Open the QScintilla editor window."""
        if self._ensure_editor_window():
            self._editor_window.show()
            self._editor_window.raise_()
            self._editor_window.activateWindow()
        else:
            print("Failed to create QScintilla editor window")