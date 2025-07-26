"""Enhanced Response Area widget for LLM Assistant Panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
    QLabel, QSizePolicy
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor

from i18n import _


class EnhancedResponseArea(QWidget):
    """Enhanced response area with better text handling and controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the enhanced response area with buttons on right."""
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Left side: Text area with header
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        # Compact header
        header_layout = QHBoxLayout()
        self.response_label = QLabel(_("AI Response"))
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_response_area_style(self.response_label, 'response_label')
        header_layout.addWidget(self.response_label)
        
        header_layout.addStretch()
        
        self.word_count_label = QLabel("0 words")
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_response_area_style(self.word_count_label, 'word_count_label')
        header_layout.addWidget(self.word_count_label)
        text_layout.addLayout(header_layout)
        
        # Text area
        self.response_text = QTextEdit()
        self.response_text.setPlaceholderText(_("AI responses will appear here..."))
        self.response_text.setReadOnly(True)
        self.response_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_response_area_style(self.response_text, 'response_text')
        self.response_text.textChanged.connect(self.update_word_count)
        text_layout.addWidget(self.response_text)
        
        main_layout.addWidget(text_widget)
        
        # Right side: Compact action buttons
        buttons_widget = QWidget()
        buttons_widget.setFixedWidth(80)
        actions_layout = QVBoxLayout(buttons_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(4)
        
        # Copy button
        self.copy_button = QPushButton(_("📋"))
        self.copy_button.setEnabled(False)
        self.copy_button.setToolTip(_("Copy response to clipboard"))
        self.copy_button.setFixedSize(70, 30)
        actions_layout.addWidget(self.copy_button)
        
        # Select All button
        self.select_all_button = QPushButton(_("📝"))
        self.select_all_button.setEnabled(False)
        self.select_all_button.setToolTip(_("Select all response text"))
        self.select_all_button.setFixedSize(70, 30)
        self.select_all_button.clicked.connect(self.select_all_text)
        actions_layout.addWidget(self.select_all_button)
        
        # Insert button
        self.insert_button = QPushButton(_("📄"))
        self.insert_button.setEnabled(False)
        self.insert_button.setToolTip(_("Insert response into current document"))
        self.insert_button.setFixedSize(70, 30)
        actions_layout.addWidget(self.insert_button)
        
        # Add to Narrative Context button
        self.add_to_narrative_button = QPushButton(_("📚"))
        self.add_to_narrative_button.setEnabled(False)
        self.add_to_narrative_button.setToolTip(_("Add response to Narrative Context"))
        self.add_to_narrative_button.setFixedSize(70, 30)
        actions_layout.addWidget(self.add_to_narrative_button)
        
        # Clear button
        self.clear_button = QPushButton(_("🗑️"))
        self.clear_button.setEnabled(False)
        self.clear_button.setToolTip(_("Clear response area"))
        self.clear_button.setFixedSize(70, 30)
        actions_layout.addWidget(self.clear_button)
        
        actions_layout.addStretch()
        main_layout.addWidget(buttons_widget)
    
    def set_response(self, text: str):
        """Set response text and enable buttons."""
        self.response_text.setPlainText(text)
        self.copy_button.setEnabled(True)
        self.select_all_button.setEnabled(True)
        self.insert_button.setEnabled(True)
        self.add_to_narrative_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.update_word_count()
    
    def clear_response(self):
        """Clear response and disable buttons."""
        self.response_text.clear()
        self.copy_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.insert_button.setEnabled(False)
        self.add_to_narrative_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.update_word_count()
    
    def append_chunk(self, chunk: str):
        """Append streaming chunk to response text."""
        # Move cursor to end and insert text
        cursor = self.response_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.response_text.setTextCursor(cursor)
        
        # Enable buttons on first chunk
        if self.response_text.toPlainText().strip():
            self.copy_button.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.insert_button.setEnabled(True)
            self.add_to_narrative_button.setEnabled(True)
            self.clear_button.setEnabled(True)
        
        # Update word count
        self.update_word_count()
        
        # Auto-scroll to bottom
        scrollbar = self.response_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def select_all_text(self):
        """Select all text in response area."""
        self.response_text.selectAll()
        self.response_text.setFocus()
    
    def update_word_count(self):
        """Update word count display."""
        text = self.response_text.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        char_count = len(text)
        self.word_count_label.setText(f"{word_count} words, {char_count} chars")