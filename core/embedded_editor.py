"""Embedded edytor RTF do integracji bezpośrednio w QML."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QToolBar, QComboBox, QPushButton, 
                              QFontComboBox, QLabel, QColorDialog, QSizePolicy, QSplitter)
from PySide6.QtCore import Signal, Qt, QTimer, QObject, Slot, Property
from PySide6.QtGui import (QFont, QFontInfo, QTextCharFormat, QColor, QKeySequence, 
                          QTextCursor, QBrush, QShortcut)
import re
from .toolbar_manager import ToolbarManager
from .find_replace_manager import FindReplaceManager
from .context_panel_manager import ContextPanelManager
from .rtf_font_manager import RTFFontManager


class EmbeddedRichTextWidget(QWidget):
    """Embedded RTF editor widget for QtWidgets applications."""
    
    contentChanged = Signal()
    saveRequested = Signal(str)
    autoSaveRequested = Signal(str)     # Periodic auto-save signal
    focusModeRequested = Signal()
    contextPanelToggled = Signal(bool)  # New signal for context panel toggle
    aiAssistantToggled = Signal()       # New signal for AI assistant toggle
    narrativeContextToggled = Signal()  # New signal for narrative context toggle
    textSelectionChanged = Signal(str, str)  # selected_text, current_text
    
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
        self._last_saved_content = ""  # Przechowywanie ostatnio zapisanej zawartości
        
        # Initialize toolbar manager
        self.toolbar_manager = ToolbarManager(self)
        
        # Initialize find/replace manager (will be created after text_edit)
        self.find_replace_manager = None
        
        # Initialize context panel manager (will be created after splitter)
        self.context_panel_manager = None
        
        # Initialize font manager (will be created after text_edit)
        self.font_manager = None
        
        # Auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._periodic_auto_save)
        self.auto_save_timer.setSingleShot(False)
        self.auto_save_interval = 180000  # 3 minutes in milliseconds
        
        self.setup_ui()
        self.setup_connections()
        
        # Initial update of toolbar to reflect current format
        QTimer.singleShot(100, self.update_format_buttons)
        
        # Start auto-save timer
        self.auto_save_timer.start(self.auto_save_interval)
        
    def setup_ui(self):
        """Konfiguracja interfejsu jako widget (nie main window)."""
        # Set explicit styling to remove any default spacing
        self.setStyleSheet("EmbeddedRichTextWidget { margin: 0px; padding: 0px; border: none; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing between toolbar and editor
        
        # Toolbar
        toolbar_widget = self.toolbar_manager.create_toolbar()
        layout.addWidget(toolbar_widget)
        
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
        
        # Initialize find/replace manager after text_edit is created
        self.find_replace_manager = FindReplaceManager(self.text_edit, self)
        
        # Initialize context panel manager after splitter is created
        self.context_panel_manager = ContextPanelManager(self.splitter, self)
        
        # Initialize font manager after text_edit is created
        self.font_manager = RTFFontManager(self.text_edit, self)
        
        layout.addWidget(self.splitter)
        
        # Force layout update to prevent gaps
        self.updateGeometry()
        self.update()
        
        # Ustaw domyślną czcionkę po utworzeniu toolbar (żeby combo box istniał)
        self._set_default_font()
        
        
    def setup_connections(self):
        """Połączenie sygnałów z slotami."""
        # Zmiany tekstu
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.cursorPositionChanged.connect(self.update_format_buttons)
        self.text_edit.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self.text_edit.selectionChanged.connect(self._on_text_selection_changed)
        
        # Connect toolbar manager signals to font manager
        self.toolbar_manager.fontFamilyChanged.connect(self.font_manager.change_font_family)
        self.toolbar_manager.fontSizeChanged.connect(self.font_manager.change_font_size)
        self.toolbar_manager.boldToggled.connect(self.font_manager.toggle_bold)
        self.toolbar_manager.italicToggled.connect(self.font_manager.toggle_italic)
        self.toolbar_manager.underlineToggled.connect(self.font_manager.toggle_underline)
        self.toolbar_manager.textColorChanged.connect(self.font_manager.change_text_color_from_toolbar)
        self.toolbar_manager.alignmentChanged.connect(self.font_manager.set_alignment)
        self.toolbar_manager.saveRequested.connect(self.save_content)
        self.toolbar_manager.focusModeRequested.connect(self.focusModeRequested.emit)
        self.toolbar_manager.contextPanelToggled.connect(self.context_panel_manager.toggle_context_panel)
        self.toolbar_manager.aiAssistantToggled.connect(self.aiAssistantToggled.emit)
        self.toolbar_manager.narrativeContextToggled.connect(self.narrativeContextToggled.emit)
        
        # Connect context panel manager signals
        self.context_panel_manager.contextPanelToggled.connect(self.contextPanelToggled.emit)
        self.context_panel_manager.contextPanelToggled.connect(self.toolbar_manager.set_context_panel_state)
        self.context_panel_manager.characterAddedToScene.connect(self.characterAddedToScene.emit)
        self.context_panel_manager.characterRemovedFromScene.connect(self.characterRemovedFromScene.emit)
        self.context_panel_manager.locationAddedToScene.connect(self.locationAddedToScene.emit)
        self.context_panel_manager.locationRemovedFromScene.connect(self.locationRemovedFromScene.emit)
        self.context_panel_manager.newCharacterRequestedFromScene.connect(self.newCharacterRequestedFromScene.emit)
        self.context_panel_manager.newLocationRequestedFromScene.connect(self.newLocationRequestedFromScene.emit)
        self.context_panel_manager.characterSelectedFromScene.connect(self.characterSelectedFromScene.emit)
        self.context_panel_manager.locationSelectedFromScene.connect(self.locationSelectedFromScene.emit)
        
        # Set focus policy for toolbar controls
        self.toolbar_manager.set_font_focus_policy(Qt.FocusPolicy.StrongFocus)
        
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
        context_shortcut.activated.connect(self.context_panel_manager.toggle_context_panel)
        
        # Find/Replace shortcuts
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self.text_edit)
        find_shortcut.activated.connect(self.find_replace_manager.show_find_replace_dialog)
        
        find_next_shortcut = QShortcut(QKeySequence("F3"), self.text_edit)
        find_next_shortcut.activated.connect(self.find_replace_manager.find_next)
        
        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self.text_edit)
        find_prev_shortcut.activated.connect(self.find_replace_manager.find_previous)
        
    def on_text_changed(self):
        """Obsługa zmian w tekście."""
        current_content = self.text_edit.toHtml()
        self._content = current_content
        
        # Sprawdź czy zawartość rzeczywiście się zmieniła w porównaniu do ostatnio zapisanej
        if not self._has_changes and current_content != self._last_saved_content:
            self._has_changes = True
            self.contentChanged.emit()
            
    def update_format_buttons(self):
        """Aktualizacja stanu przycisków formatowania."""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        
        # Update toolbar state through toolbar manager
        self.toolbar_manager.update_format_state(format)
            
    def change_font_family(self, font_name):
        """Change font family."""
        self.font_manager.change_font_family(font_name)
            
    def change_font_size(self, size_text):
        """Change font size."""
        self.font_manager.change_font_size(size_text)
            
    def toggle_bold(self):
        """Toggle bold formatting."""
        self.font_manager.toggle_bold()
            
    def toggle_italic(self):
        """Toggle italic formatting."""
        self.font_manager.toggle_italic()
            
    def toggle_underline(self):
        """Toggle underline formatting."""
        self.font_manager.toggle_underline()
            
    def change_text_color(self):
        """Change text color."""
        self.font_manager.change_text_color()
        
    def change_text_color_from_toolbar(self, color):
        """Change text color from toolbar manager signal."""
        self.font_manager.change_text_color_from_toolbar(color)
            
    def set_alignment(self, alignment):
        """Set text alignment."""
        self.font_manager.set_alignment(alignment)
        
    def get_content(self):
        """Pobranie zawartości jako HTML."""
        return self.text_edit.toHtml()
        
    def set_content(self, content):
        """Ustawienie zawartości z HTML."""
        self.text_edit.setHtml(content)
        self._content = content
        self._last_saved_content = content  # Zapisz jako ostatnio zapisaną zawartość
        self._has_changes = False
        
        # Ustaw domyślną czcionkę dla nowego tekstu
        self._set_default_font()
        
        # Update toolbar to reflect current format
        QTimer.singleShot(50, self.update_format_buttons)
        
    def _set_default_font(self):
        """Set default font for editor and new text."""
        selected_font = self.font_manager.set_default_font()
        # Update toolbar to reflect the default font
        self.toolbar_manager.set_default_font(selected_font)
            
        
    def save_content(self):
        """Emisja sygnału zapisania - tylko jeśli zawartość się zmieniła."""
        content = self.get_content()
        
        # Sprawdź czy zawartość rzeczywiście się zmieniła
        if content == self._last_saved_content:
            return  # Nie zapisuj jeśli nic się nie zmieniło
        
        self.saveRequested.emit(content)
        self._last_saved_content = content  # Zaktualizuj ostatnio zapisaną zawartość
        self._has_changes = False
    
    def confirm_auto_save(self):
        """Confirm that auto-save was successful."""
        self._last_saved_content = self.get_content()  # Zaktualizuj ostatnio zapisaną zawartość
        self._has_changes = False
        
    def has_changes(self):
        """Sprawdzenie czy są niezapisane zmiany."""
        return self._has_changes
    
    def initialize_context_panel(self, character_manager, location_manager, project_id):
        """Initialize the context panel with managers."""
        self.context_panel_manager.initialize_context_panel(character_manager, location_manager, project_id)
    
    def set_scene_context(self, scene_id):
        """Set the current scene for the context panel."""
        self.context_panel_manager.set_scene_context(scene_id)
    
    def toggle_context_panel(self):
        """Toggle the visibility of the context panel."""
        self.context_panel_manager.toggle_context_panel()
    
    def _connect_context_panel_signals(self):
        """Connect context panel signals to handle character/location management."""
        # This method is now handled by the ContextPanelManager
        pass
    
    def refresh_context_panel(self):
        """Refresh the context panel data."""
        self.context_panel_manager.refresh_context_panel()
    
    def show_find_replace_dialog(self):
        """Show the Find/Replace dialog."""
        self.find_replace_manager.show_find_replace_dialog()
    
    def find_text_in_document(self, search_text, match_case=False, whole_words=False):
        """Find all occurrences of text in the document."""
        return self.find_replace_manager.find_text_in_document(search_text, match_case, whole_words)
    
    def update_search_occurrences(self, search_text, match_case=False, whole_words=False):
        """Update the search occurrences list."""
        return self.find_replace_manager.update_search_occurrences(search_text, match_case, whole_words)
    
    def highlight_all_occurrences(self):
        """Highlight all search occurrences."""
        self.find_replace_manager.highlight_all_occurrences()
    
    def highlight_current_occurrence(self):
        """Highlight the current occurrence with a different color."""
        self.find_replace_manager.highlight_current_occurrence()
    
    def on_find_next(self, search_text, match_case=False, whole_words=False):
        """Handle find next request from dialog."""
        self.find_replace_manager.on_find_next(search_text, match_case, whole_words)
    
    def on_find_previous(self, search_text, match_case=False, whole_words=False):
        """Handle find previous request from dialog."""
        self.find_replace_manager.on_find_previous(search_text, match_case, whole_words)
    
    def find_next(self):
        """Find next occurrence using current search (keyboard shortcut)."""
        self.find_replace_manager.find_next()
    
    def find_previous(self):
        """Find previous occurrence using current search (keyboard shortcut)."""
        self.find_replace_manager.find_previous()
    
    def on_replace(self, find_text, replace_text, match_case=False, whole_words=False):
        """Handle replace current occurrence."""
        self.find_replace_manager.on_replace(find_text, replace_text, match_case, whole_words)
    
    def on_replace_all(self, find_text, replace_text, match_case=False, whole_words=False):
        """Handle replace all occurrences."""
        self.find_replace_manager.on_replace_all(find_text, replace_text, match_case, whole_words)
    
    def find_and_highlight_text(self, search_text):
        """Find and highlight all occurrences of search text in the editor, positioning on first.
        
        This method integrates with the new Find/Replace system and is called when
        clicking on search results from the global search.
        """
        return self.find_replace_manager.find_and_highlight_text(search_text)
    
    def _clear_search_highlight(self):
        """Clear search highlighting from the text."""
        self.find_replace_manager._clear_search_highlight()
    
    def _periodic_auto_save(self):
        """Periodic auto-save functionality."""
        if self._has_changes:
            content = self.get_content()
            self.autoSaveRequested.emit(content)
            # Note: Don't set _has_changes to False here, as this is just a backup save
            # The actual save confirmation should come from the main application
    
    def set_auto_save_interval(self, milliseconds: int):
        """Set the auto-save interval in milliseconds."""
        self.auto_save_interval = milliseconds
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            self.auto_save_timer.start(self.auto_save_interval)
    
    def enable_auto_save(self, enabled: bool):
        """Enable or disable auto-save functionality."""
        if enabled:
            if not self.auto_save_timer.isActive():
                self.auto_save_timer.start(self.auto_save_interval)
        else:
            self.auto_save_timer.stop()
    
    def set_ai_assistant_state(self, visible: bool):
        """Set the AI assistant button state in the toolbar."""
        if self.toolbar_manager:
            self.toolbar_manager.set_ai_assistant_state(visible)
    
    def set_narrative_context_state(self, visible: bool):
        """Set the narrative context button state in the toolbar."""
        if self.toolbar_manager:
            self.toolbar_manager.set_narrative_context_state(visible)
    
    def _on_cursor_position_changed(self):
        """Handle cursor position changes."""
        try:
            # Get current text (paragraph around cursor)
            cursor = self.text_edit.textCursor()
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            current_text = cursor.selectedText()
            
            # Get selected text if any
            selected_text = self.text_edit.textCursor().selectedText()
            
            # Emit signal with current context
            self.textSelectionChanged.emit(selected_text, current_text)
            
        except Exception as e:
            # Log error but don't crash
            pass
    
    def _on_text_selection_changed(self):
        """Handle text selection changes."""
        try:
            # Get selected text
            selected_text = self.text_edit.textCursor().selectedText()
            
            # Get current text (paragraph around cursor)
            cursor = self.text_edit.textCursor()
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            current_text = cursor.selectedText()
            
            # Emit signal with current context
            self.textSelectionChanged.emit(selected_text, current_text)
            
        except Exception as e:
            # Log error but don't crash
            pass

    def cleanup(self):
        """Clean up resources when the editor is destroyed."""
        # Stop auto-save timer
        if self.auto_save_timer:
            self.auto_save_timer.stop()
        
        if self.find_replace_manager:
            self.find_replace_manager.cleanup()
        if self.context_panel_manager:
            self.context_panel_manager.cleanup()
        # Font manager doesn't need cleanup
