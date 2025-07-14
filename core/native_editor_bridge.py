"""Bridge dla natywnego editora Qt Widgets do integracji z QML."""

from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "Pisarz"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class NativeEditorBridge(QObject):
    """Bridge do expose natywnego editora RTF dla QML."""
    
    contentChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor_window = None
        self._content = ""
        self._has_changes = False
        
    def _ensure_editor_window(self, scene_title=""):
        """Stwórz okno editora jeśli nie istnieje."""
        if not self._editor_window:
            try:
                from core.native_editor import NativeRichTextEditor
                self._editor_window = NativeRichTextEditor(scene_title)
                self._editor_window.contentChanged.connect(self._on_content_changed)
                self._editor_window.saveRequested.connect(self._on_save_requested)
                return True
            except Exception as e:
                print(f"Błąd tworzenia natywnego editora: {e}")
                return False
        return True
            
    def _on_content_changed(self):
        """Obsługa zmian zawartości z okna editora."""
        if self._editor_window:
            new_content = self._editor_window.get_content()
            if new_content != self._content:
                self._content = new_content
                self._has_changes = True
                self.contentChanged.emit()
                
    def _on_save_requested(self, content):
        """Obsługa żądania zapisania z okna editora."""
        self._content = content
        self._has_changes = False
        self.contentChanged.emit()
    
    @Property(str, notify=contentChanged)
    def content(self):
        """Pobierz aktualną zawartość."""
        return self._content
    
    @content.setter
    def content(self, value):
        """Ustaw zawartość."""
        if value != self._content:
            self._content = value
            if self._editor_window:
                self._editor_window.set_content(value)
            self._has_changes = False
            self.contentChanged.emit()
    
    @Slot(str)
    def setContent(self, content):
        """Ustaw zawartość z QML."""
        self.content = content
        
    @Slot(result=str)
    def getContent(self):
        """Pobierz zawartość dla QML."""
        if self._editor_window:
            return self._editor_window.get_content()
        return self._content
    
    @Slot(result=bool)
    def hasChanges(self):
        """Sprawdź czy edytor ma niezapisane zmiany."""
        if self._editor_window:
            return self._editor_window.has_changes()
        return self._has_changes
    
    @Slot()
    def resetChanges(self):
        """Resetuj flagę zmian."""
        self._has_changes = False
        if self._editor_window:
            self._editor_window._has_changes = False
    
    @Slot(str)
    def openEditor(self, scene_title):
        """Otwórz okno natywnego editora RTF."""
        if self._ensure_editor_window(scene_title):
            self._editor_window.setWindowTitle(f"Pisarz - Edytor RTF: {scene_title}")
            self._editor_window.show()
            self._editor_window.raise_()
            self._editor_window.activateWindow()
        else:
            print("Nie udało się utworzyć okna natywnego editora")
    
    @Slot()
    def closeEditor(self):
        """Zamknij okno editora."""
        if self._editor_window:
            self._editor_window.close()
            self._editor_window = None