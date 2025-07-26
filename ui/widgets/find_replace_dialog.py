"""Find/Replace dialog for scene editor."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QCheckBox, QFrame)

from ui.base.base_dialog import BaseDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from i18n import _


class FindReplaceDialog(BaseDialog):
    """Dialog for finding and replacing text in the scene editor."""
    
    # Signals
    findNext = Signal(str, bool, bool)        # text, match_case, whole_words
    findPrevious = Signal(str, bool, bool)    # text, match_case, whole_words
    replace = Signal(str, str, bool, bool)    # find_text, replace_text, match_case, whole_words
    replaceAll = Signal(str, str, bool, bool) # find_text, replace_text, match_case, whole_words
    
    def __init__(self, parent=None):
        super().__init__(
            title=_("Find and Replace"),
            width=400,
            height=200,
            modal=False,
            parent=parent
        )
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        # Current search state
        self.current_match = 0
        self.total_matches = 0
        
        self.setup_ui()
        self.setup_shortcuts()
        
    def setup_ui(self):
        """Setup the dialog UI."""
        # Find section
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel(_("Find:")))
        
        self.find_input = self.create_line_input(_("Enter text to find..."))
        self.find_input.textChanged.connect(self.on_find_text_changed)
        find_layout.addWidget(self.find_input)
        
        self.add_content_layout(find_layout)
        
        # Replace section
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel(_("Replace:")))
        
        self.replace_input = self.create_line_input(_("Enter replacement text..."))
        replace_layout.addWidget(self.replace_input)
        
        self.add_content_layout(replace_layout)
        
        # Options section
        options_layout = QHBoxLayout()
        
        self.match_case_cb = QCheckBox(_("Match case"))
        self.whole_words_cb = QCheckBox(_("Whole words"))
        
        options_layout.addWidget(self.match_case_cb)
        options_layout.addWidget(self.whole_words_cb)
        options_layout.addStretch()
        
        self.add_content_layout(options_layout)
        
        # Status section
        self.status_label = self.create_info_label(_("Ready"), "muted")
        self.add_content_widget(self.status_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #ccc;")
        self.add_content_widget(separator)
        
        # Find buttons
        self.find_next_btn = self.create_custom_button(_("Find Next"), self.on_find_next, "primary")
        self.find_next_btn.setEnabled(False)
        self.add_button(self.find_next_btn)
        
        self.find_prev_btn = self.create_custom_button(_("Find Previous"), self.on_find_previous, "secondary")
        self.find_prev_btn.setEnabled(False)
        self.add_button(self.find_prev_btn)
        
        self.add_button_stretch()
        
        # Replace buttons
        self.replace_btn = self.create_custom_button(_("Replace"), self.on_replace, "secondary")
        self.replace_btn.setEnabled(False)
        self.add_button(self.replace_btn)
        
        self.replace_all_btn = self.create_custom_button(_("Replace All"), self.on_replace_all, "secondary")
        self.replace_all_btn.setEnabled(False)
        self.add_button(self.replace_all_btn)
        
        self.add_button_stretch()
        
        # Close button
        self.close_btn = self.create_custom_button(_("Close"), self.close, "secondary")
        self.add_button(self.close_btn)
        
        # Set initial focus
        self.find_input.setFocus()
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Find Next - F3
        find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        find_next_shortcut.activated.connect(self.on_find_next)
        
        # Find Previous - Shift+F3
        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
        find_prev_shortcut.activated.connect(self.on_find_previous)
        
        # Replace - Ctrl+R
        replace_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        replace_shortcut.activated.connect(self.on_replace)
        
        # Replace All - Ctrl+Alt+R
        replace_all_shortcut = QShortcut(QKeySequence("Ctrl+Alt+R"), self)
        replace_all_shortcut.activated.connect(self.on_replace_all)
        
        # Close - Escape
        close_shortcut = QShortcut(QKeySequence("Escape"), self)
        close_shortcut.activated.connect(self.close)
        
        # Enter in find field = Find Next
        self.find_input.returnPressed.connect(self.on_find_next)
        
    def on_find_text_changed(self, text):
        """Handle find text changes."""
        has_text = bool(text.strip())
        self.find_next_btn.setEnabled(has_text)
        self.find_prev_btn.setEnabled(has_text)
        self.replace_btn.setEnabled(has_text)
        self.replace_all_btn.setEnabled(has_text)
        
        if not has_text:
            self.status_label.setText(_("Ready"))
            self.current_match = 0
            self.total_matches = 0
            
    def on_find_next(self):
        """Find next occurrence."""
        text = self.find_input.text().strip()
        if text:
            self.findNext.emit(text, self.match_case_cb.isChecked(), self.whole_words_cb.isChecked())
        else:
            self.status_label.setText(_("Enter text to find"))
            
    def on_find_previous(self):
        """Find previous occurrence."""
        text = self.find_input.text().strip()
        if text:
            self.findPrevious.emit(text, self.match_case_cb.isChecked(), self.whole_words_cb.isChecked())
        else:
            self.status_label.setText(_("Enter text to find"))
            
    def on_replace(self):
        """Replace current occurrence."""
        find_text = self.find_input.text().strip()
        replace_text = self.replace_input.text()
        if find_text:
            self.replace.emit(find_text, replace_text, self.match_case_cb.isChecked(), self.whole_words_cb.isChecked())
            
    def on_replace_all(self):
        """Replace all occurrences."""
        find_text = self.find_input.text().strip()
        replace_text = self.replace_input.text()
        if find_text:
            self.replaceAll.emit(find_text, replace_text, self.match_case_cb.isChecked(), self.whole_words_cb.isChecked())
            
    def set_find_text(self, text):
        """Set the find text and focus on it."""
        self.find_input.setText(text)
        self.find_input.selectAll()
        self.find_input.setFocus()
        
    def update_status(self, current_match, total_matches):
        """Update the status label with current match info."""
        self.current_match = current_match
        self.total_matches = total_matches
        
        if total_matches == 0:
            self.status_label.setText(_("No matches found"))
        else:
            self.status_label.setText(_("Match {} of {}").format(current_match, total_matches))
            
    def focus_find_input(self):
        """Focus the find input field."""
        self.find_input.setFocus()
        self.find_input.selectAll()