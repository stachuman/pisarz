"""Find/Replace manager for the embedded RTF editor."""

import re
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QBrush


class FindReplaceManager(QObject):
    """Manages find/replace operations for the RTF editor."""
    
    # Signals
    statusUpdated = Signal(int, int)  # current_match, total_matches
    
    def __init__(self, text_edit: QTextEdit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
        self.find_replace_dialog = None
        self.search_occurrences = []
        self.current_search_index = -1
        self.current_search_text = ""
        self.current_search_flags = {}
        
    def show_find_replace_dialog(self):
        """Show the Find/Replace dialog."""
        if self.find_replace_dialog is None:
            # Import here to avoid circular imports
            from ui.widgets.find_replace_dialog import FindReplaceDialog
            self.find_replace_dialog = FindReplaceDialog(self.text_edit)
            
            # Connect dialog signals
            self.find_replace_dialog.findNext.connect(self.on_find_next)
            self.find_replace_dialog.findPrevious.connect(self.on_find_previous)
            self.find_replace_dialog.replace.connect(self.on_replace)
            self.find_replace_dialog.replaceAll.connect(self.on_replace_all)
        
        # Get selected text if any
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            if selected_text:
                self.find_replace_dialog.set_find_text(selected_text)
        
        self.find_replace_dialog.show()
        self.find_replace_dialog.raise_()
        self.find_replace_dialog.focus_find_input()
    
    def find_text_in_document(self, search_text, match_case=False, whole_words=False):
        """Find all occurrences of text in the document."""
        if not search_text:
            return []
        
        plain_text = self.text_edit.toPlainText()
        occurrences = []
        
        # Prepare search pattern - be more careful with regex
        try:
            if whole_words:
                # Only use word boundaries if the text contains word characters
                if re.search(r'\w', search_text):
                    pattern = r'\b' + re.escape(search_text) + r'\b'
                else:
                    pattern = re.escape(search_text)
            else:
                pattern = re.escape(search_text)
        except re.error:
            # If regex fails, fall back to simple string search
            pattern = None
        
        flags = 0 if match_case else re.IGNORECASE
        
        try:
            if pattern:
                for match in re.finditer(pattern, plain_text, flags):
                    occurrences.append((match.start(), match.end()))
            else:
                # Pattern is None, use fallback immediately
                raise re.error("Pattern preparation failed")
        except (re.error, TypeError):
            # Fallback to simple string search if regex fails
            if match_case:
                search_in = plain_text
                search_for = search_text
            else:
                search_in = plain_text.lower()
                search_for = search_text.lower()
            
            start = 0
            while True:
                pos = search_in.find(search_for, start)
                if pos == -1:
                    break
                occurrences.append((pos, pos + len(search_text)))
                start = pos + 1
        
        return occurrences
    
    def update_search_occurrences(self, search_text, match_case=False, whole_words=False):
        """Update the search occurrences list."""
        self.current_search_text = search_text
        self.current_search_flags = {
            'match_case': match_case,
            'whole_words': whole_words
        }
        
        self.search_occurrences = self.find_text_in_document(search_text, match_case, whole_words)
        
        # Clear any existing highlights
        self._clear_search_highlight()
        
        # Highlight all occurrences
        if self.search_occurrences:
            self.highlight_all_occurrences()
        
        return len(self.search_occurrences)
    
    def highlight_all_occurrences(self):
        """Highlight all search occurrences."""
        cursor = self.text_edit.textCursor()
        
        for start_pos, end_pos in self.search_occurrences:
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
            
            # Apply highlighting
            format = QTextCharFormat()
            format.setBackground(QBrush(QColor(255, 255, 150, 100)))  # Light yellow
            cursor.mergeCharFormat(format)
    
    def highlight_current_occurrence(self):
        """Highlight the current occurrence with a different color."""
        if 0 <= self.current_search_index < len(self.search_occurrences):
            start_pos, end_pos = self.search_occurrences[self.current_search_index]
            
            cursor = self.text_edit.textCursor()
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
            
            # Apply current match highlighting
            format = QTextCharFormat()
            format.setBackground(QBrush(QColor(255, 200, 0, 150)))  # Darker yellow
            cursor.mergeCharFormat(format)
            
            # Set cursor position and ensure visibility
            self.text_edit.setTextCursor(cursor)
            self.text_edit.ensureCursorVisible()
    
    def on_find_next(self, search_text, match_case=False, whole_words=False):
        """Handle find next request from dialog."""
        if (search_text != self.current_search_text or 
            self.current_search_flags.get('match_case') != match_case or
            self.current_search_flags.get('whole_words') != whole_words):
            # New search or different options
            total_matches = self.update_search_occurrences(search_text, match_case, whole_words)
            self.current_search_index = 0 if total_matches > 0 else -1
        else:
            # Same search, move to next
            if self.search_occurrences:
                self.current_search_index = (self.current_search_index + 1) % len(self.search_occurrences)
        
        if self.search_occurrences:
            self.highlight_all_occurrences()
            self.highlight_current_occurrence()
            
            if self.find_replace_dialog:
                self.find_replace_dialog.update_status(
                    self.current_search_index + 1, 
                    len(self.search_occurrences)
                )
        elif self.find_replace_dialog:
            self.find_replace_dialog.update_status(0, 0)
        
        # Emit status update signal
        self.statusUpdated.emit(
            self.current_search_index + 1 if self.current_search_index >= 0 else 0,
            len(self.search_occurrences)
        )
    
    def on_find_previous(self, search_text, match_case=False, whole_words=False):
        """Handle find previous request from dialog."""
        if (search_text != self.current_search_text or 
            self.current_search_flags.get('match_case') != match_case or
            self.current_search_flags.get('whole_words') != whole_words):
            # New search or different options
            total_matches = self.update_search_occurrences(search_text, match_case, whole_words)
            self.current_search_index = total_matches - 1 if total_matches > 0 else -1
        else:
            # Same search, move to previous
            if self.search_occurrences:
                self.current_search_index = (self.current_search_index - 1) % len(self.search_occurrences)
        
        if self.search_occurrences:
            self.highlight_all_occurrences()
            self.highlight_current_occurrence()
            
            if self.find_replace_dialog:
                self.find_replace_dialog.update_status(
                    self.current_search_index + 1, 
                    len(self.search_occurrences)
                )
        elif self.find_replace_dialog:
            self.find_replace_dialog.update_status(0, 0)
        
        # Emit status update signal
        self.statusUpdated.emit(
            self.current_search_index + 1 if self.current_search_index >= 0 else 0,
            len(self.search_occurrences)
        )
    
    def find_next(self):
        """Find next occurrence using current search (keyboard shortcut)."""
        if self.current_search_text and self.search_occurrences:
            self.on_find_next(self.current_search_text, 
                            self.current_search_flags.get('match_case', False),
                            self.current_search_flags.get('whole_words', False))
        else:
            self.show_find_replace_dialog()
    
    def find_previous(self):
        """Find previous occurrence using current search (keyboard shortcut)."""
        if self.current_search_text and self.search_occurrences:
            self.on_find_previous(self.current_search_text, 
                                self.current_search_flags.get('match_case', False),
                                self.current_search_flags.get('whole_words', False))
        else:
            self.show_find_replace_dialog()
    
    def on_replace(self, find_text, replace_text, match_case=False, whole_words=False):
        """Handle replace current occurrence."""
        if not self.search_occurrences or self.current_search_index < 0:
            return
        
        # Get current occurrence position
        start_pos, end_pos = self.search_occurrences[self.current_search_index]
        
        # Replace the text
        cursor = self.text_edit.textCursor()
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(replace_text)
        
        # Update search occurrences after replacement
        self.update_search_occurrences(find_text, match_case, whole_words)
        
        # Update current index (stay at same position, or move to next if at end)
        if self.current_search_index >= len(self.search_occurrences):
            self.current_search_index = max(0, len(self.search_occurrences) - 1)
        
        # If no more occurrences, reset index
        if not self.search_occurrences:
            self.current_search_index = -1
        
        # Highlight updated occurrences
        if self.search_occurrences and self.current_search_index >= 0:
            self.highlight_all_occurrences()
            self.highlight_current_occurrence()
        
        # Update dialog status
        if self.find_replace_dialog:
            self.find_replace_dialog.update_status(
                self.current_search_index + 1 if self.current_search_index >= 0 else 0,
                len(self.search_occurrences)
            )
        
        # Emit status update signal
        self.statusUpdated.emit(
            self.current_search_index + 1 if self.current_search_index >= 0 else 0,
            len(self.search_occurrences)
        )
    
    def on_replace_all(self, find_text, replace_text, match_case=False, whole_words=False):
        """Handle replace all occurrences."""
        occurrences = self.find_text_in_document(find_text, match_case, whole_words)
        
        if not occurrences:
            return
        
        # Replace from end to beginning to maintain positions
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        
        try:
            for start_pos, end_pos in reversed(occurrences):
                cursor.setPosition(start_pos)
                cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(replace_text)
        finally:
            cursor.endEditBlock()
        
        # Clear search state
        self.search_occurrences = []
        self.current_search_index = -1
        self._clear_search_highlight()
        
        # Update dialog status
        if self.find_replace_dialog:
            self.find_replace_dialog.update_status(0, 0)
        
        # Emit status update signal
        self.statusUpdated.emit(0, 0)
    
    def find_and_highlight_text(self, search_text):
        """Find and highlight all occurrences of search text in the editor, positioning on first.
        
        This method integrates with the new Find/Replace system and is called when
        clicking on search results from the global search.
        """
        if not search_text:
            return False
        
        # Use the new search system
        total_matches = self.update_search_occurrences(search_text, match_case=False, whole_words=False)
        
        if total_matches == 0:
            return False
        
        # Set current index to first occurrence
        self.current_search_index = 0
        
        # Highlight all occurrences
        self.highlight_all_occurrences()
        self.highlight_current_occurrence()
        
        # Show the Find/Replace dialog if it's not already visible
        # This allows users to navigate between occurrences
        if self.find_replace_dialog is None or not self.find_replace_dialog.isVisible():
            self.show_find_replace_dialog()
            if self.find_replace_dialog:
                self.find_replace_dialog.set_find_text(search_text)
                self.find_replace_dialog.update_status(1, total_matches)
        
        # Emit status update signal
        self.statusUpdated.emit(1, total_matches)
        
        return True
    
    def _clear_search_highlight(self):
        """Clear search highlighting from the text."""
        # Clear highlighting by selecting all text and removing background formatting
        cursor = self.text_edit.textCursor()
        
        # Save current cursor position
        current_position = cursor.position()
        
        # Select all text to clear any background formatting
        cursor.select(QTextCursor.Document)
        
        # Clear background formatting
        format = QTextCharFormat()
        format.setBackground(QBrush())  # Clear background
        cursor.mergeCharFormat(format)
        
        # Restore cursor position and clear selection
        cursor.setPosition(current_position)
        self.text_edit.setTextCursor(cursor)
    
    def cleanup(self):
        """Clean up resources when the manager is destroyed."""
        if self.find_replace_dialog:
            self.find_replace_dialog.close()
            self.find_replace_dialog = None
        self.search_occurrences = []
        self.current_search_index = -1
        self.current_search_text = ""
        self.current_search_flags = {}