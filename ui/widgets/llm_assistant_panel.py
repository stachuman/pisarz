"""
Enhanced LLM Assistant Panel - AI-powered writing assistance panel.
Provides context-aware text generation with improved user interface.
"""

import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QFrame, QSplitter, QProgressBar,
    QMessageBox, QApplication, QSizePolicy, QGroupBox, QToolButton,
    QSpacerItem, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QSize
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QIcon

from core.logging_config import get_logger
from controllers.app_llm_controller import AppLLMController
from i18n import _


class LLMTaskThread(QThread):
    """Thread for executing LLM tasks without blocking UI."""
    
    finished = Signal(str, str)  # task_id, response
    error = Signal(str, str)     # task_id, error_message
    
    def __init__(self, controller: AppLLMController, task_id: str, context: Dict[str, Any]):
        super().__init__()
        self.controller = controller
        self.task_id = task_id
        self.context = context
        self.logger = get_logger("llm.task_thread")
    
    def run(self):
        """Execute the LLM task in background thread."""
        try:
            self.logger.info(f"Starting LLM task: {self.task_id}")
            success = self.controller.execute_task(self.task_id, self.context)
            
            if not success:
                self.error.emit(self.task_id, _("Task execution failed"))
                return
                
            # The response will be emitted via controller signals
            
        except Exception as e:
            self.logger.error(f"Error in LLM task thread: {e}")
            self.error.emit(self.task_id, str(e))


class EnhancedTaskButton(QPushButton):
    """Enhanced button for LLM tasks with better visual feedback."""
    
    taskRequested = Signal(str)
    
    def __init__(self, task_id: str, task_name: str, task_description: str = "", parent=None):
        super().__init__(task_name, parent)
        self.task_id = task_id
        self.task_name = task_name
        self.task_description = task_description
        self.is_executing = False
        
        self.setMinimumHeight(45)
        self.setMaximumHeight(45)
        self.setToolTip(task_description)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Enhanced styling
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5cb85c, stop: 1 #449d44);
                color: white;
                border: 1px solid #419241;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 11pt;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6bc56b, stop: 1 #4cae4c);
                border-color: #52b852;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #449d44, stop: 1 #398a39);
                border-color: #357a35;
            }
            QPushButton:disabled {
                background: #e0e0e0;
                color: #888888;
                border-color: #cccccc;
            }
        """)
        
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Handle button click."""
        if not self.is_executing:
            self.taskRequested.emit(self.task_id)
    
    def set_executing(self, executing: bool):
        """Set button executing state with enhanced feedback."""
        self.is_executing = executing
        self.setEnabled(not executing)
        
        if executing:
            self.setText(f"{self.task_name}...")
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #f0ad4e, stop: 1 #ec971f);
                    color: white;
                    border: 1px solid #eb9316;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                }
            """)
        else:
            self.setText(self.task_name)
            # Restore original style properly
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #5cb85c, stop: 1 #449d44);
                    color: white;
                    border: 1px solid #419241;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                    text-align: center;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #6bc56b, stop: 1 #4cae4c);
                    border-color: #52b852;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #449d44, stop: 1 #398a39);
                    border-color: #357a35;
                }
                QPushButton:disabled {
                    background: #e0e0e0;
                    color: #888888;
                    border-color: #cccccc;
                }
            """)


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
        self.response_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                color: #2c3e50;
                font-size: 10pt;
                padding: 2px 0px;
            }
        """)
        header_layout.addWidget(self.response_label)
        
        header_layout.addStretch()
        
        self.word_count_label = QLabel("0 words")
        self.word_count_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 8pt;
                font-style: italic;
            }
        """)
        header_layout.addWidget(self.word_count_label)
        text_layout.addLayout(header_layout)
        
        # Text area
        self.response_text = QTextEdit()
        self.response_text.setPlaceholderText(_("AI responses will appear here..."))
        self.response_text.setReadOnly(True)
        self.response_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
                selection-background-color: #007acc;
                selection-color: white;
            }
            QTextEdit:focus {
                border-color: #007acc;
            }
        """)
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
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        actions_layout.addWidget(self.copy_button)
        
        # Select All button
        self.select_all_button = QPushButton(_("📝"))
        self.select_all_button.setEnabled(False)
        self.select_all_button.setToolTip(_("Select all response text"))
        self.select_all_button.setFixedSize(70, 30)
        self.select_all_button.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        self.select_all_button.clicked.connect(self.select_all_text)
        actions_layout.addWidget(self.select_all_button)
        
        # Insert button
        self.insert_button = QPushButton(_("📄"))
        self.insert_button.setEnabled(False)
        self.insert_button.setToolTip(_("Insert response into current document"))
        self.insert_button.setFixedSize(70, 30)
        self.insert_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        actions_layout.addWidget(self.insert_button)
        
        # Add to Narrative Context button
        self.add_to_narrative_button = QPushButton(_("📚"))
        self.add_to_narrative_button.setEnabled(False)
        self.add_to_narrative_button.setToolTip(_("Add response to Narrative Context"))
        self.add_to_narrative_button.setFixedSize(70, 30)
        self.add_to_narrative_button.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8680a;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        actions_layout.addWidget(self.add_to_narrative_button)
        
        # Clear button
        self.clear_button = QPushButton(_("🗑️"))
        self.clear_button.setEnabled(False)
        self.clear_button.setToolTip(_("Clear response area"))
        self.clear_button.setFixedSize(70, 30)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
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


class LLMAssistantPanel(QWidget):
    """Enhanced LLM Assistant Panel widget with improved interface."""
    
    # Signal for requesting text insertion into document
    insertTextRequested = Signal(str)
    
    # Signal for context auto-save completion
    contextAutoSaved = Signal(int)  # scene_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("llm.assistant_panel")
        self.llm_controller: Optional[AppLLMController] = None
        self.task_thread: Optional[LLMTaskThread] = None
        self.current_scene_id: Optional[int] = None
        self.current_scene_content: str = ""
        self.additional_context: Dict[str, Any] = {}
        
        # Auto-save context info
        self.auto_save_scene_id: Optional[int] = None
        self.auto_save_template_name: Optional[str] = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the compact horizontal UI components."""
        # Main horizontal layout for bottom placement
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        # Left section: Controls
        left_section = self.create_controls_section()
        main_layout.addWidget(left_section)
        
        # Center section: Response area
        self.response_area = EnhancedResponseArea()
        main_layout.addWidget(self.response_area)
        
        # Set stretch factors: controls take minimal space, response takes most
        main_layout.setStretchFactor(left_section, 0)
        main_layout.setStretchFactor(self.response_area, 1)
        
    def create_controls_section(self) -> QWidget:
        """Create compact controls section for horizontal layout."""
        controls_widget = QWidget()
        controls_widget.setFixedWidth(250)
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(8)
        
        # Compact title
        title_label = QLabel(_("🤖 AI Assistant"))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12pt;
                font-weight: bold;
                padding: 4px 8px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(title_label)
        
        # Status indicator
        self.status_label = QLabel(_("Ready"))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-size: 9pt;
                padding: 2px 6px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 3px;
            }
        """)
        controls_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(4)
        controls_layout.addWidget(self.progress_bar)
        
        # Task dropdown with refresh button
        template_layout = QHBoxLayout()
        
        from PySide6.QtWidgets import QComboBox
        self.task_combo = QComboBox()
        self._load_available_templates()
        self.task_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
        """)
        template_layout.addWidget(self.task_combo)
        
        # Refresh templates button
        self.refresh_templates_button = QPushButton("🔄")
        self.refresh_templates_button.setFixedSize(24, 24)
        self.refresh_templates_button.setToolTip(_("Refresh templates from disk"))
        self.refresh_templates_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #4e555b;
            }
        """)
        self.refresh_templates_button.clicked.connect(self.refresh_templates)
        template_layout.addWidget(self.refresh_templates_button)
        
        controls_layout.addLayout(template_layout)
        
        # Content source selection
        content_label = QLabel(_("Content Source:"))
        content_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 9pt;
                font-weight: bold;
                margin-top: 8px;
                margin-bottom: 2px;
            }
        """)
        controls_layout.addWidget(content_label)
        
        self.content_source_combo = QComboBox()
        self.content_source_combo.addItems([
            _("Selection (if any)"),
            _("Full Scene"),
            _("Scene Beginning"),
            _("Scene End"),
            _("Custom Length")
        ])
        self.content_source_combo.setCurrentIndex(0)  # Default to selection
        self.content_source_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 6px;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                background-color: white;
                font-size: 9pt;
            }
        """)
        self.content_source_combo.setToolTip(_("Choose what content to pass to the AI template"))
        controls_layout.addWidget(self.content_source_combo)
        
        # Edit template button
        self.edit_template_button = QPushButton(_("🛠️ Edit"))
        self.edit_template_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.edit_template_button.setToolTip(_("Edit selected template"))
        self.edit_template_button.clicked.connect(self.edit_selected_template)
        controls_layout.addWidget(self.edit_template_button)
        
        # Execute buttons layout
        execute_layout = QHBoxLayout()
        
        # Execute button
        self.execute_button = QPushButton(_("Execute"))
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.execute_button.clicked.connect(self.execute_selected_task)
        self.execute_button.setVisible(False)  # Hide regular execute button
        execute_layout.addWidget(self.execute_button)
        
        # Streaming Execute button
        self.execute_streaming_button = QPushButton(_("🔄 Execute"))
        self.execute_streaming_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.execute_streaming_button.clicked.connect(self.execute_selected_task_streaming)
        execute_layout.addWidget(self.execute_streaming_button)
        
        controls_layout.addLayout(execute_layout)
        
        # Stop button (initially hidden)
        self.stop_button = QPushButton(_("⏹️ Stop"))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.stop_button.clicked.connect(self.stop_streaming_task)
        self.stop_button.setVisible(False)
        controls_layout.addWidget(self.stop_button)
        
        # Keep compatibility with old buttons
        self.continue_button = self.execute_button  # For backward compatibility
        
        controls_layout.addStretch()
        return controls_widget
    
    def create_header_section(self) -> QWidget:
        """Create the header section with title and status."""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Title with modern styling
        title_label = QLabel(_("🤖 AI Writing Assistant"))
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Status and progress section
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status indicator
        self.status_label = QLabel(_("Ready"))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-size: 10pt;
                font-weight: 500;
                padding: 4px 8px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #e9ecef;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #007acc, stop: 1 #0056b3);
                border-radius: 3px;
            }
        """)
        
        header_layout.addWidget(status_widget)
        header_layout.addWidget(self.progress_bar)
        
        return header_widget
    
    def create_tasks_section(self) -> QWidget:
        """Create the tasks section with enhanced styling."""
        tasks_widget = QGroupBox(_("Writing Tasks"))
        tasks_widget.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: white;
            }
        """)
        
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(12, 20, 12, 12)
        tasks_layout.setSpacing(10)
        
        # Continue Scene button
        self.continue_button = EnhancedTaskButton(
            "continue_scene",
            _("📝 Continue Scene"),
            _("Continue writing the current scene based on context and selection")
        )
        self.continue_button.taskRequested.connect(self.execute_task)
        tasks_layout.addWidget(self.continue_button)
        
        # Template editor button
        self.template_editor_btn = QPushButton(_("🛠️ Edit Templates"))
        self.template_editor_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.template_editor_btn.clicked.connect(self.edit_selected_template)
        tasks_layout.addWidget(self.template_editor_btn)
        
        # Placeholder for future tasks with better styling
        future_tasks_label = QLabel(_("✨ More AI writing tasks coming soon..."))
        future_tasks_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 9pt;
                font-style: italic;
                text-align: center;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px dashed #dee2e6;
                border-radius: 6px;
            }
        """)
        future_tasks_label.setAlignment(Qt.AlignCenter)
        tasks_layout.addWidget(future_tasks_label)
        
        # Add some spacing
        tasks_layout.addStretch()
        
        return tasks_widget
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect response area buttons
        self.response_area.copy_button.clicked.connect(self.copy_response)
        self.response_area.clear_button.clicked.connect(self.clear_response)
        self.response_area.insert_button.clicked.connect(self.insert_response)
        self.response_area.add_to_narrative_button.clicked.connect(self.add_to_narrative_context)
    
    def set_llm_controller(self, controller: AppLLMController):
        """Set the LLM controller."""
        self.llm_controller = controller
        
        # Connect controller signals
        controller.llm_response_ready.connect(self.on_response_ready)
        controller.llm_response_chunk.connect(self.on_response_chunk)
        controller.llm_error.connect(self.on_error)
        controller.llm_cancelled.connect(self.on_cancelled)
        controller.llm_status_changed.connect(self.on_status_changed)
        
        # Initialize controller if not already done
        if not controller.is_initialized():
            try:
                controller.initialize()
                self.logger.info("LLM controller initialized successfully")
                self.update_status(_("Ready - LLM system online"), "success")
            except Exception as e:
                self.logger.error(f"Failed to initialize LLM controller: {e}")
                self.show_error(_("LLM Initialization Error"), str(e))
                self.update_status(_("LLM system offline"), "error")
    
    def set_scene_context(self, scene_id: int, content: str):
        """Set the current scene context."""
        self.current_scene_id = scene_id
        self.current_scene_content = content
        self.additional_context = {}  # Reset additional context when scene changes
        self.logger.debug(f"Scene context set: ID={scene_id}, content length={len(content)}")
        
        # Update status to show context is available
        if content.strip():
            self.update_status(_("Ready - Scene context loaded"), "success")
        else:
            self.update_status(_("Ready - No scene content"), "warning")
    
    def set_additional_context(self, context_data: dict):
        """Set additional context data (characters, locations, etc.)."""
        self.additional_context = context_data or {}
        self.logger.debug(f"Additional context set with {len(context_data)} keys")
    
    def set_auto_save_context_info(self, scene_id: int, template_name: str):
        """Set auto-save context info for automatic saving after task completion."""
        self.auto_save_scene_id = scene_id
        self.auto_save_template_name = template_name
        self.logger.info(f"Auto-save context info set: scene_id={scene_id}, template={template_name}")
        self.logger.info(f"Current auto-save state: scene_id={self.auto_save_scene_id}, template={self.auto_save_template_name}")
    
    def _prepare_task_execution(self, task_id: str) -> tuple[bool, dict]:
        """Prepare task execution with common validation and context building.
        
        Returns:
            tuple: (success, context) - success indicates if preparation was successful
        """
        self.logger.info(f"Preparing task execution with task_id='{task_id}', current auto-save: scene_id={self.auto_save_scene_id}, template={self.auto_save_template_name}")
        
        if not self.llm_controller:
            self.show_error(_("Error"), _("LLM controller not initialized"))
            return False, {}
        
        if not self.llm_controller.is_initialized():
            self.show_error(_("Error"), _("LLM system not initialized"))
            return False, {}
        
        # IMPORTANT: Populate additional context before building context
        self._populate_additional_context()
        
        # Build context from current scene
        context = self.build_context()
        
        return True, context
    
    def execute_task(self, task_id: str):
        """Execute an LLM task (non-streaming)."""
        success, context = self._prepare_task_execution(task_id)
        if not success:
            return
        
        # Update UI state
        self.set_task_executing(task_id, True)
        self.update_status(_("Processing AI request..."), "processing")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Execute task in background thread
        self.task_thread = LLMTaskThread(self.llm_controller, task_id, context)
        self.task_thread.finished.connect(self.on_task_finished)
        self.task_thread.error.connect(self.on_task_error)
        self.task_thread.start()
        
        self.logger.info(f"Started LLM task: {task_id}")
    
    def execute_task_streaming(self, task_id: str):
        """Execute an LLM task with streaming output."""
        success, context = self._prepare_task_execution(task_id)
        if not success:
            return
        
        # Update UI state for streaming
        self._is_streaming_task = True  # Mark as streaming task
        self.set_task_executing(task_id, True)
        self.update_status(_("🔄 Starting streaming..."), "processing")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear response area for new streaming content
        self.response_area.clear_response()
        
        # Execute streaming task directly (no thread needed as controller handles threading)
        success = self.llm_controller.execute_task_streaming(task_id, context)
        
        if not success:
            self.on_error(task_id, "Failed to start streaming task")
        
        self.logger.info(f"Started streaming LLM task: {task_id}")
    
    def execute_selected_task(self):
        """Execute the selected task from dropdown (using streaming as default)."""
        selected_data = self.task_combo.currentData()
        if selected_data == "custom_prompt":
            self.open_custom_prompt_dialog(streaming=True)
        elif selected_data:
            self.execute_task_streaming(selected_data)
        else:
            self.show_error(_("No Template Selected"), _("Please select a template to execute."))
    
    def execute_selected_task_streaming(self):
        """Execute the selected task from dropdown with streaming."""
        selected_data = self.task_combo.currentData()
        if selected_data == "custom_prompt":
            self.open_custom_prompt_dialog(streaming=True)
        elif selected_data:
            self.execute_task_streaming(selected_data)
        else:
            self.show_error(_("No Template Selected"), _("Please select a template to execute."))
    
    def stop_streaming_task(self):
        """Stop the currently running streaming task."""
        if not self.llm_controller:
            return
        
        self.logger.info("User requested to stop streaming task")
        success = self.llm_controller.stop_streaming()
        
        if success:
            self.update_status(_("⏹️ Stopping streaming..."), "warning")
        else:
            self.update_status(_("❌ No streaming task to stop"), "error")
    
    def _clean_html_css(self, content: str) -> str:
        """Clean HTML tags and CSS from content to produce plain text."""
        from core.utils.text_cleaner import clean_html_css
        return clean_html_css(content)

    def build_context(self) -> Dict[str, Any]:
        """Build context for LLM task from current scene."""
        # Extract text content (remove HTML tags and CSS for context)
        import re
        text_content = self._clean_html_css(self.current_scene_content)
        
        # Get user's content source selection
        content_source = self._get_selected_content_source()
        
        # Get current text selection from LLM service (updated via signals)
        selected_text = ""
        current_selection_text = ""
        
        try:
            from controllers.app_llm_controller import get_llm_controller
            llm_controller = get_llm_controller()
            if llm_controller and llm_controller.llm_service and llm_controller.llm_service.context_manager:
                # Get current selection from context manager
                selection_info = llm_controller.llm_service.context_manager.get_text_selection()
                if selection_info:
                    selected_text = selection_info.get('selected_text', '')
                    current_selection_text = selection_info.get('current_text', '')
                    if selected_text:
                        self.logger.debug(f"Using selected text: {selected_text[:50]}...")
        except Exception as e:
            self.logger.warning(f"Could not get text selection: {e}")
        
        # Apply content source selection to override template behavior
        from core.llm.templates.config import ContextSource
        from ui.widgets.ai_content_settings_widget import AIContentSettingsWidget
        
        # Store original selection state for logging
        original_selected_text = selected_text
        original_has_selection = bool(selected_text.strip())
        
        if content_source == ContextSource.SELECTION:
            # Use actual text selection from editor - keep what we got from context manager
            has_selection = bool(selected_text.strip())
        elif content_source == ContextSource.FULL_SCENE:
            # Use full scene as both selected and current text
            selected_text = text_content
            current_selection_text = text_content
            has_selection = True
        elif content_source == ContextSource.SCENE_BEGINNING:
            # Use configurable length for scene beginning
            beginning_length = AIContentSettingsWidget.get_scene_beginning_length_from_settings()
            scene_beginning = text_content[:beginning_length] if text_content else ""
            selected_text = scene_beginning
            current_selection_text = scene_beginning
            has_selection = bool(scene_beginning.strip())
        elif content_source == ContextSource.SCENE_END:
            # Use configurable length for scene end
            end_length = AIContentSettingsWidget.get_scene_end_length_from_settings()
            scene_end = text_content[-end_length:] if text_content else ""
            selected_text = scene_end
            current_selection_text = scene_end
            has_selection = bool(scene_end.strip())
        elif content_source == ContextSource.CUSTOM_LENGTH:
            # Use configurable custom length
            custom_length = AIContentSettingsWidget.get_custom_length_from_settings()
            custom_text = text_content[:custom_length] if text_content else ""
            selected_text = custom_text
            current_selection_text = custom_text
            has_selection = bool(custom_text.strip())
        
        # Build basic context - enhanced template manager will handle the rest
        context = {
            'scene_content': text_content,
            'selected_text': selected_text,
            'current_text': current_selection_text,
            'scene_summary': text_content,  # Full scene as summary
            'scene_id': self.current_scene_id,
            'project_name': self.additional_context.get('project_name', 'Current Project'),
            'has_selection': has_selection,
            'characters': self.additional_context.get('characters', []),
            'locations': self.additional_context.get('locations', []),
            'character_count': self.additional_context.get('character_count', 0),
            'location_count': self.additional_context.get('location_count', 0),
            'content_source': content_source.value
        }
        
        # Add any other additional context data
        for key, value in self.additional_context.items():
            if key not in context:  # Don't override existing keys
                context[key] = value
        
        self.logger.debug(f"Built context with {content_source.value}: {len(text_content)} chars, {len(context['characters'])} characters, {len(context['locations'])} locations")
        return context
    
    def set_task_executing(self, task_id: str, executing: bool):
        """Set task execution state."""
        self.execute_button.setEnabled(not executing)
        self.execute_streaming_button.setEnabled(not executing)
        
        if executing:
            self.execute_button.setText(_("Processing..."))
            self.execute_streaming_button.setText(_("🔄 Processing..."))
            # Show stop button only for streaming tasks
            if hasattr(self, '_is_streaming_task') and self._is_streaming_task:
                self.stop_button.setVisible(True)
        else:
            self.execute_button.setText(_("Execute"))
            self.execute_streaming_button.setText(_("🔄 Execute"))
            self.stop_button.setVisible(False)
            if hasattr(self, '_is_streaming_task'):
                self._is_streaming_task = False
    
    def update_status(self, message: str, status_type: str = "info"):
        """Update status with styling based on type."""
        self.status_label.setText(message)
        
        if status_type == "success":
            style = """
                QLabel {
                    color: #155724;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                }
            """
        elif status_type == "error":
            style = """
                QLabel {
                    color: #721c24;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                }
            """
        elif status_type == "warning":
            style = """
                QLabel {
                    color: #856404;
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                }
            """
        elif status_type == "processing":
            style = """
                QLabel {
                    color: #004085;
                    background-color: #cce7ff;
                    border: 1px solid #b8daff;
                }
            """
        else:  # info
            style = """
                QLabel {
                    color: #0c5460;
                    background-color: #d1ecf1;
                    border: 1px solid #bee5eb;
                }
            """
        
        self.status_label.setStyleSheet(style + """
            font-size: 10pt;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 4px;
        """)
    
    def on_response_ready(self, task_id: str, response: str):
        """Handle LLM response ready."""
        self.logger.info(f"Response ready for task: {task_id}")
        self.logger.info(f"Response length: {len(response)} characters")
        self.logger.info(f"Auto-save state when response ready: scene_id={self.auto_save_scene_id}, template={self.auto_save_template_name}")
        
        # Update response area (for non-streaming, or final response for streaming)
        self.response_area.set_response(response)
        
        # Auto-save to narrative context if context info is set
        self.logger.debug(f"Checking auto-save conditions: scene_id={self.auto_save_scene_id}, template={self.auto_save_template_name}")
        if self.auto_save_scene_id is not None and self.auto_save_template_name is not None:
            self.logger.info("Auto-save conditions met, starting auto-save process")
            self._auto_save_to_narrative_context(response)
        else:
            self.logger.warning(f"Auto-save conditions not met: scene_id={self.auto_save_scene_id}, template={self.auto_save_template_name}")
        
        # Reset task state
        self.set_task_executing(task_id, False)
        self.update_status(_("✅ Response ready"), "success")
        self.progress_bar.setVisible(False)
        
        self.logger.info(f"Task {task_id} completed. Final auto-save state: scene_id={self.auto_save_scene_id}, template={self.auto_save_template_name}")
    
    def on_response_chunk(self, task_id: str, chunk: str):
        """Handle streaming response chunk."""
        # Append chunk to response area in real-time
        self.response_area.append_chunk(chunk)
        self.update_status(_("🔄 Streaming response..."), "processing")
    
    def on_cancelled(self, task_id: str):
        """Handle LLM task cancellation."""
        self.logger.info(f"Task cancelled: {task_id}")
        
        # Add cancellation notice to response area
        current_text = self.response_area.response_text.toPlainText()
        if current_text:
            cancellation_notice = f"\n\n--- {_('Task cancelled by user')} ---"
            self.response_area.response_text.append(cancellation_notice)
        else:
            self.response_area.response_text.setPlainText(_("❌ Task cancelled by user"))
        
        # Reset task state
        self.set_task_executing(task_id, False)
        self.update_status(_("⏹️ Task cancelled"), "warning")
        self.progress_bar.setVisible(False)
        self.stop_button.setVisible(False)
    
    def on_error(self, task_id: str, error_message: str):
        """Handle LLM error."""
        self.logger.error(f"LLM error for task {task_id}: {error_message}")
        
        # Show error in response area
        error_text = f"{_('❌ Error occurred')}: {error_message}"
        self.response_area.response_text.setPlainText(error_text)
        
        # Style as error
        self.response_area.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8d7da;
                border: 2px solid #f5c6cb;
                border-radius: 8px;
                padding: 12px;
                color: #721c24;
                font-size: 11pt;
            }
        """)
        
        # Reset task state
        self.set_task_executing(task_id, False)
        self.update_status(_("❌ Error occurred"), "error")
        self.progress_bar.setVisible(False)
    
    def on_status_changed(self, status: str):
        """Handle LLM status change."""
        self.update_status(status)
    
    def on_task_finished(self, task_id: str, response: str):
        """Handle task thread finished."""
        # Response will be handled by controller signals
        pass
    
    def on_task_error(self, task_id: str, error_message: str):
        """Handle task thread error."""
        self.on_error(task_id, error_message)
    
    def _auto_save_to_narrative_context(self, response: str):
        """Automatically save response to narrative context with scene linkage."""
        try:
            self.logger.info(f"Starting auto-save: scene_id={self.auto_save_scene_id}, template={self.auto_save_template_name}")
            
            # Get the narrative context manager directly
            from PySide6.QtWidgets import QApplication
            from core.database.narrative_context_repository import NarrativeContextManager
            from pathlib import Path
            
            # Get main window for project path
            main_window = QApplication.instance().activeWindow()
            if not main_window:
                self.logger.error("No active window found for auto-save")
                return
                
            # Get project path from main window
            if not hasattr(main_window, 'project_controller'):
                self.logger.error("No project controller found for auto-save")
                return
                
            project_id, _project_name = main_window.project_controller.get_current_project_info()
            if not project_id:
                self.logger.error("No current project path for auto-save")
                return
                
            # Get narrative context manager directly
            context_manager = NarrativeContextManager()
            if not context_manager:
                self.logger.error("Failed to get narrative context manager for auto-save")
                return
            
            # Generate a title based on template name and first line of response
            template_title_map = {
                "scene_summary": _("Scene Summary"),
                "continue_with_context": _("Context Continuation"), 
                "expand_scene": _("Scene Expansion"),
                "dialogue_enhancement": _("Dialogue Enhancement"),
                "rewrite_scene": _("Scene Rewrite")
            }
            
            base_title = template_title_map.get(self.auto_save_template_name, _("AI Generated Context"))
            
            # Create more descriptive title with scene info
            scene_title = self.additional_context.get("scene_title", _("Scene"))
            full_title = f"{base_title}: {scene_title}"
            
            # Create the context entry with scene linkage, replacing any existing context of this type
            context_id = context_manager.replace_scene_context(
                scene_id=self.auto_save_scene_id,
                context_type=self.auto_save_template_name,
                title=full_title,
                content=response,
                metadata={
                    "auto_generated": True,
                    "template_name": self.auto_save_template_name,
                    "source": "llm_assistant_panel"
                }
            )
            
            if context_id:
                self.logger.info(f"Auto-saved context to database: scene_id={self.auto_save_scene_id}, context_id={context_id}")
                
                # Emit signal to refresh UI
                self.contextAutoSaved.emit(self.auto_save_scene_id)
                
                # Clear auto-save info to prevent duplicate saves
                self.auto_save_scene_id = None
                self.auto_save_template_name = None
                
                # Update status
                self.update_status(_("✅ Context automatically saved and linked"), "success")
            else:
                self.logger.error("Failed to auto-save context to database")
                
        except Exception as e:
            self.logger.error(f"Error during auto-save to narrative context: {e}")
    
    def copy_response(self):
        """Copy response to clipboard."""
        text = self.response_area.response_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.update_status(_("📋 Response copied to clipboard"), "success")
    
    def clear_response(self):
        """Clear the response area."""
        self.response_area.clear_response()
        self.update_status(_("Ready"), "success")
    
    def insert_response(self):
        """Insert response into the current document."""
        text = self.response_area.response_text.toPlainText()
        if text:
            self.insertTextRequested.emit(text)
            self.update_status(_("📄 Text insertion requested"), "success")
    
    def add_to_narrative_context(self):
        """Add response to Narrative Context."""
        text = self.response_area.response_text.toPlainText()
        if text:
            # Get the main window to access the narrative context panel
            from PySide6.QtWidgets import QApplication
            main_window = QApplication.instance().activeWindow()
            if hasattr(main_window, 'narrative_context_panel'):
                # Add the text as a new context entry with proper context type and scene linkage
                success = main_window.narrative_context_panel.add_context_from_text(
                    text, 
                    context_type=self.auto_save_template_name or "ai_response",
                    scene_id=self.current_scene_id
                )
                if success:
                    self.update_status(_("📚 Added to Narrative Context"), "success")
                    # Show the narrative context panel if it's hidden
                    if not main_window.narrative_context_panel.isVisible():
                        main_window.toggle_narrative_context()
                else:
                    self.update_status(_("❌ Failed to add to Narrative Context"), "error")
            else:
                self.update_status(_("❌ Narrative Context panel not available"), "error")
    
    def _load_available_templates(self):
        """Load available templates from template manager into dropdown."""
        try:
            from core.llm.templates import get_template_manager
            
            template_manager = get_template_manager()
            template_list = template_manager.get_template_list()
            
            # Remember current selection
            current_template_id = self.task_combo.currentData()
            
            # Clear existing templates (but keep edit templates option that will be added later)
            self.task_combo.clear()
            
            # Add custom prompt option first
            self.task_combo.addItem("🎯 " + _("Custom Prompt..."), "custom_prompt")
            self.task_combo.setItemData(
                self.task_combo.count() - 1,
                _("Create a custom prompt with configurable context and parameters"),
                Qt.ItemDataRole.ToolTipRole
            )
            
            # Add separator
            self.task_combo.insertSeparator(self.task_combo.count())
            
            # Add templates to dropdown
            for template_info in template_list:
                template_id = template_info['id']
                template_name = template_info['name']
                template_description = template_info['description']
                category = template_info.get('category', '')
                
                # Create display name with emoji based on category
                category_icons = {
                    'writing': '📝',
                    'dialogue': '💬', 
                    'editing': '✏️',
                    'scene': '🎬',
                    'character': '👤',
                    'summary': '📊'
                }
                
                icon = category_icons.get(category, '📄')
                display_name = f"{icon} {template_name}"
                
                self.task_combo.addItem(display_name, template_id)
                
                # Set tooltip with description
                if template_description:
                    self.task_combo.setItemData(
                        self.task_combo.count() - 1,
                        template_description,
                        Qt.ItemDataRole.ToolTipRole
                    )
            
            # Restore previous selection if it exists
            if current_template_id:
                for i in range(self.task_combo.count()):
                    if self.task_combo.itemData(i) == current_template_id:
                        self.task_combo.setCurrentIndex(i)
                        break
            else:
                # If no previous selection and we have templates, select the first real template (skip custom_prompt and separator)
                if len(template_list) > 0:
                    for i in range(self.task_combo.count()):
                        item_data = self.task_combo.itemData(i)
                        if item_data and item_data != "custom_prompt":
                            self.task_combo.setCurrentIndex(i)
                            self.logger.debug(f"Auto-selected first template: {item_data}")
                            break
            
            self.logger.info(f"Loaded {len(template_list)} templates into dropdown")
            
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            # Fallback to default option
            self.task_combo.addItem(_("📝 Continue Scene"), "continue_scene")
    
    def edit_selected_template(self):
        """Edit the currently selected template."""
        try:
            selected_template_id = self.task_combo.currentData()
            if not selected_template_id:
                self.show_error(_("No Template Selected"), _("Please select a template to edit."))
                return
            
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            template_config = template_manager.get_template(selected_template_id)
            
            if not template_config:
                self.show_error(_("Template Not Found"), _("The selected template could not be found."))
                return
            
            # Open template editor with selected template
            from ui.widgets.template_editor_dialog import TemplateEditorDialog
            dialog = TemplateEditorDialog(template_config, self)
            
            # Connect to template saved signal
            dialog.template_saved.connect(self.on_template_saved)
            
            # Show dialog
            if dialog.exec():
                # Get updated template config from dialog
                updated_template_config = dialog.get_template_config()
                
                # Save to template manager
                from core.llm.templates import get_template_manager
                template_manager = get_template_manager()
                success = template_manager.add_template(updated_template_config, save_to_file=True)
                
                if success:
                    self.logger.info(f"Template editor completed and saved for template: {selected_template_id}")
                else:
                    self.show_error(_("Save Error"), _("Failed to save template to file."))
            
        except Exception as e:
            self.logger.error(f"Error opening template editor: {e}")
            self.show_error(_("Error"), _("Failed to open template editor: {}").format(str(e)))
    
    def on_template_saved(self, template_id: str):
        """Handle template saved signal."""
        self.logger.info(f"Template saved: {template_id}")
        # Refresh available templates
        self._load_available_templates()
    
    def refresh_templates(self):
        """Refresh templates from disk."""
        try:
            from core.llm.templates import get_template_manager
            
            # Refresh templates in the manager
            template_manager = get_template_manager()
            template_manager.refresh_templates()
            
            # Reload UI
            self._load_available_templates()
            
            self.update_status(_("✅ Templates refreshed"), "success")
            self.logger.info("Templates refreshed successfully")
            
        except Exception as e:
            self.logger.error(f"Error refreshing templates: {e}")
            self.update_status(_("❌ Failed to refresh templates"), "error")
    
    def open_custom_prompt_dialog(self, streaming: bool = False):
        """Open custom prompt dialog."""
        try:
            from .custom_prompt_dialog import CustomPromptDialog
            
            # Populate additional context with current scene data before opening dialog
            self._populate_additional_context()
            
            # Build context using the same logic as templates (respects content source selection)
            context = self.build_context()
            
            # Extract the relevant information from context
            scene_content = context.get('scene_content', '')
            selected_text = context.get('selected_text', '')
            has_selection = context.get('has_selection', False)
            
            dialog = CustomPromptDialog(scene_content, selected_text, self)
            result = dialog.exec()
            
            # Check if dialog was accepted and get config
            if result == QDialog.DialogCode.Accepted:
                config = dialog.get_config()
                if config:
                    self.execute_custom_prompt(config, streaming)
            
        except Exception as e:
            self.logger.error(f"Error opening custom prompt dialog: {e}")
            self.show_error(_("Error"), _("Failed to open custom prompt dialog: {}").format(str(e)))
    
    def _populate_additional_context(self):
        """Populate additional context with current scene's characters and locations."""
        try:
            if not self.current_scene_id:
                self.logger.debug("No current scene ID, cannot populate additional context")
                return
            
            # Access main window to get managers - navigate up the widget hierarchy
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'project_controller'):
                main_window = main_window.parent()
            
            if not main_window or not hasattr(main_window, 'project_controller'):
                self.logger.debug("No main window or project controller found")
                return
            
            # Use the new LLM context service for custom prompts
            from services import LLMContextService
            llm_context_service = LLMContextService()
            
            managers = main_window.project_controller.get_current_managers()
            
            context_data = llm_context_service.prepare_custom_prompt_context(
                self.current_scene_id, managers, 
                include_characters=True, include_locations=True
            )
            
            self.set_additional_context(context_data)
            self.logger.debug(f"Additional context populated for scene {self.current_scene_id}")
            
        except Exception as e:
            self.logger.error(f"Error populating additional context: {e}")
    
    def execute_custom_prompt(self, config: dict, streaming: bool = False):
        """Execute a custom prompt configuration using regular LLM service path."""
        try:
            # Create dynamic template configuration
            template_config = self._create_dynamic_template_config(config)
            
            # Add template to manager temporarily
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            template_manager.add_template(template_config, save_to_file=False)
            
            # Build context in standard format
            context = {
                'scene_content': config['scene_content'],
                'selected_text': config.get('selected_text', ''),
                'current_text': self._extract_custom_context(config),  # Use existing extraction logic
                'characters': self.additional_context.get('characters', []),
                'locations': self.additional_context.get('locations', []),
                'project_name': self.additional_context.get('project_name', ''),
                'scene_title': self.additional_context.get('scene_title', ''),
                'scene_id': self.current_scene_id,
            }
            
            # Set up UI state (same as regular templates)
            self._current_task_id = "custom_prompt"
            self._is_streaming_task = streaming
            
            # Update UI state
            self.set_task_executing("custom_prompt", True)
            
            # Show progress bar
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Clear response area for new content
            self.response_area.clear_response()
            
            # Use regular LLM service execution path
            if streaming:
                success = self.llm_controller.execute_task_streaming("custom_prompt", context)
                if not success:
                    self.on_error("custom_prompt", "Failed to start custom prompt streaming")
            else:
                success = self.llm_controller.execute_task("custom_prompt", context)
                if not success:
                    self.on_error("custom_prompt", "Failed to start custom prompt execution")
                
        except Exception as e:
            self.logger.error(f"Error executing custom prompt: {e}")
            self.show_error(_("Error"), _("Failed to execute custom prompt: {}").format(str(e)))
    
    def _create_dynamic_template_config(self, config: dict):
        """Create a dynamic template configuration from custom prompt config."""
        from core.llm.templates.config import (
            EnhancedTemplateConfig, TemplateMetadata, ContextConfig, 
            LLMParams, UIConfig, ContextSource
        )
        
        # Create metadata
        metadata = TemplateMetadata(
            name="Custom Prompt",
            template_id="custom_prompt", 
            description="Dynamic custom prompt template",
            category="custom",
            author="User"
        )
        
        # Create context config based on custom prompt settings
        context_config = ContextConfig(
            include_characters=config.get('include_characters', False),
            include_locations=config.get('include_locations', False),
            include_scene_content=config.get('include_scene_content', True),  # Default true for compatibility
            use_selection=True,
            selection_priority=True,
            default_context_length=config.get('custom_length', 8000),
            scene_summary_length=config.get('custom_length', 8000),
            scene_summary_source=self._get_context_source_from_text_portion(config.get('text_portion', '')),
            max_context_chars=25000,
            word_boundary_trim=True
        )
        
        # Create LLM params from config
        llm_params = LLMParams(
            temperature=config.get('temperature', 0.75),
            max_tokens=config.get('max_tokens', 8000),
            repeat_penalty=config.get('repetition_penalty', 1.05)
        )
        
        # Create UI config
        ui_config = UIConfig(
            show_context_preview=True,
            allow_context_editing=False,
            show_params_editor=False,
            auto_apply_selection=True,
            confirm_before_execution=False
        )
        
        # Create template content using instruction as Jinja2 template
        template_content = self._build_template_content(config)
        
        return EnhancedTemplateConfig(
            metadata=metadata,
            context_config=context_config,
            llm_params=llm_params,
            ui_config=ui_config,
            template_content=template_content
        )
    
    def _get_context_source_from_text_portion(self, text_portion: str):
        """Convert text portion selection to ContextSource enum."""
        from core.llm.templates.config import ContextSource
        
        if _("🎯 Selected text only") in text_portion:
            return ContextSource.SELECTION
        elif _("📄 Full scene") in text_portion:
            return ContextSource.FULL_SCENE
        elif _("⬆️ Beginning of scene") in text_portion:
            return ContextSource.SCENE_BEGINNING
        elif _("⬇️ End of scene") in text_portion:
            return ContextSource.SCENE_END
        elif _("🎚️ Custom length from end") in text_portion:
            return ContextSource.CUSTOM_LENGTH
        else:
            return ContextSource.SELECTION
    
    def _build_template_content(self, config: dict) -> str:
        """Build Jinja2 template content from custom prompt config."""
        instruction = config.get('instruction', '')
        include_characters = config.get('include_characters', False)
        include_locations = config.get('include_locations', False)
        
        # Create template that conditionally includes scene content
        template_parts = [instruction]
        
        # Add conditional character section only if enabled
        if include_characters:
            template_parts.append("""
{% if characters and characters|length > 0 %}

Postacie w scenie:
{% for character in characters %}
- {{ character }}
{% endfor %}
{% endif %}""")
        
        # Add conditional location section only if enabled
        if include_locations:
            template_parts.append("""
{% if locations and locations|length > 0 %}

Lokalizacje:
{% for location in locations %}
- {{ location }}
{% endfor %}
{% endif %}""")
        
        # Add scene content section (controlled by include_scene_content in ContextConfig)
        template_parts.append("""
{% if current_text or selected_text %}

--- TEKST DO ANALIZY ---

{% if has_selection %}
{{ selected_text }}
{% else %}
{{ current_text }}
{% endif %}

{% if scene_summary and scene_summary != (selected_text if has_selection else current_text) %}

Dodatkowy kontekst sceny:
{{ scene_summary }}
{% endif %}
{% endif %}""")
        
        return "\n".join(template_parts)
    
    def _extract_custom_context(self, config: dict) -> str:
        """Extract context text based on custom prompt configuration."""
        scene_content = config['scene_content']
        selected_text = config.get('selected_text', '')
        text_portion = config['text_portion']
        custom_length = config['custom_length']
        
        # Clean HTML/CSS from scene content and selected text (reuse existing cleaning)
        clean_scene_content = self._clean_html_css(scene_content) if scene_content else ""
        clean_selected_text = self._clean_html_css(selected_text) if selected_text else ""
        
        self.logger.debug(f"Extracting custom context: portion='{text_portion}', scene_len={len(clean_scene_content)}, selected_len={len(clean_selected_text)}")
        
        # Use exact text matching instead of substring matching to fix selection bug
        if text_portion == _("🎯 Selected text only") and clean_selected_text:
            self.logger.debug("Using selected text only")
            return clean_selected_text
        elif text_portion == _("📄 Full scene"):
            self.logger.debug("Using full scene")
            return clean_scene_content
        elif text_portion == _("⬆️ Beginning of scene"):
            self.logger.debug(f"Using beginning of scene ({custom_length} chars)")
            result = clean_scene_content[:custom_length]
            if len(clean_scene_content) > custom_length:
                result += "..."
            return result
        elif text_portion == _("⬇️ End of scene"):
            self.logger.debug(f"Using end of scene ({custom_length} chars)")
            if len(clean_scene_content) > custom_length:
                return "..." + clean_scene_content[-custom_length:]
            return clean_scene_content
        elif text_portion == _("🎚️ Custom length from end"):
            self.logger.debug(f"Using custom length from end ({custom_length} chars)")
            return clean_scene_content[-custom_length:] if clean_scene_content else ""
        elif text_portion == _("🎯 Selection + context") and clean_selected_text:
            self.logger.debug("Using selection + context")
            # Return selection plus some context
            context_length = min(custom_length - len(clean_selected_text), len(clean_scene_content))
            context_part = clean_scene_content[:context_length]
            return f"{clean_selected_text}\n\n[Context: {context_part}]"
        else:
            self.logger.debug(f"Using fallback: first {custom_length} chars")
            return clean_scene_content[:custom_length]
    
    def _get_selected_content_source(self):
        """Get the selected content source from UI and convert to ContextSource enum."""
        from core.llm.templates.config import ContextSource
        
        selected_index = self.content_source_combo.currentIndex()
        content_source_map = {
            0: ContextSource.SELECTION,      # "Selection (if any)"
            1: ContextSource.FULL_SCENE,     # "Full Scene" 
            2: ContextSource.SCENE_BEGINNING, # "Scene Beginning"
            3: ContextSource.SCENE_END,      # "Scene End"
            4: ContextSource.CUSTOM_LENGTH   # "Custom Length"
        }
        
        return content_source_map.get(selected_index, ContextSource.SELECTION)
    
    def show_error(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def cleanup(self):
        """Clean up resources."""
        if self.task_thread and self.task_thread.isRunning():
            self.task_thread.terminate()
            self.task_thread.wait()
        
        if self.llm_controller:
            # Disconnect signals
            self.llm_controller.llm_response_ready.disconnect(self.on_response_ready)
            self.llm_controller.llm_error.disconnect(self.on_error)
            self.llm_controller.llm_status_changed.disconnect(self.on_status_changed)