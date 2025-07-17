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
    QSpacerItem
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
                self.error.emit(self.task_id, "Task execution failed")
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
            # Restore original style
            self.__init__(self.task_id, self.task_name, self.task_description, self.parent())


class EnhancedResponseArea(QWidget):
    """Enhanced response area with better text handling and controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the enhanced response area."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Response label
        self.response_label = QLabel(_("AI Response"))
        self.response_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                color: #2c3e50;
                font-size: 12pt;
                padding: 4px 0px;
            }
        """)
        header_layout.addWidget(self.response_label)
        
        header_layout.addStretch()
        
        # Word count label
        self.word_count_label = QLabel("0 words")
        self.word_count_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 9pt;
                font-style: italic;
            }
        """)
        header_layout.addWidget(self.word_count_label)
        
        layout.addLayout(header_layout)
        
        # Enhanced text area
        self.response_text = QTextEdit()
        self.response_text.setPlaceholderText(_("AI responses will appear here...\n\nThis area is resizable - drag the splitter to adjust size."))
        self.response_text.setReadOnly(True)
        
        # Remove fixed height constraint and set better size policy
        self.response_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.response_text.setMinimumHeight(200)  # Minimum instead of maximum
        
        # Enhanced styling
        self.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                selection-background-color: #007acc;
                selection-color: white;
            }
            QTextEdit:focus {
                border-color: #007acc;
                background-color: #fafbfc;
            }
        """)
        
        # Connect text changes to update word count
        self.response_text.textChanged.connect(self.update_word_count)
        
        layout.addWidget(self.response_text)
        
        # Enhanced action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        # Copy button with icon
        self.copy_button = QPushButton(_("📋 Copy"))
        self.copy_button.setEnabled(False)
        self.copy_button.setToolTip(_("Copy response to clipboard"))
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        actions_layout.addWidget(self.copy_button)
        
        # Select All button
        self.select_all_button = QPushButton(_("📝 Select All"))
        self.select_all_button.setEnabled(False)
        self.select_all_button.setToolTip(_("Select all response text"))
        self.select_all_button.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
            QPushButton:pressed {
                background-color: #4c2a85;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        self.select_all_button.clicked.connect(self.select_all_text)
        actions_layout.addWidget(self.select_all_button)
        
        # Insert button (for inserting into document)
        self.insert_button = QPushButton(_("📄 Insert"))
        self.insert_button.setEnabled(False)
        self.insert_button.setToolTip(_("Insert response into current document"))
        self.insert_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        actions_layout.addWidget(self.insert_button)
        
        # Clear button
        self.clear_button = QPushButton(_("🗑️ Clear"))
        self.clear_button.setEnabled(False)
        self.clear_button.setToolTip(_("Clear response area"))
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
            }
        """)
        actions_layout.addWidget(self.clear_button)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
    
    def set_response(self, text: str):
        """Set response text and enable buttons."""
        self.response_text.setPlainText(text)
        self.copy_button.setEnabled(True)
        self.select_all_button.setEnabled(True)
        self.insert_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.update_word_count()
    
    def clear_response(self):
        """Clear response and disable buttons."""
        self.response_text.clear()
        self.copy_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.insert_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.update_word_count()
    
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("llm.assistant_panel")
        self.llm_controller: Optional[AppLLMController] = None
        self.task_thread: Optional[LLMTaskThread] = None
        self.current_scene_id: Optional[int] = None
        self.current_scene_content: str = ""
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the enhanced UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Header section
        header_widget = self.create_header_section()
        main_layout.addWidget(header_widget)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                border: 1px solid #adb5bd;
                border-radius: 2px;
                margin: 2px;
            }
            QSplitter::handle:hover {
                background-color: #007acc;
            }
        """)
        
        # Tasks section (top part of splitter)
        tasks_widget = self.create_tasks_section()
        splitter.addWidget(tasks_widget)
        
        # Response section (bottom part of splitter)
        self.response_area = EnhancedResponseArea()
        splitter.addWidget(self.response_area)
        
        # Set initial splitter proportions (30% tasks, 70% response)
        splitter.setSizes([200, 400])
        splitter.setCollapsible(0, False)  # Don't allow tasks section to collapse
        splitter.setCollapsible(1, False)  # Don't allow response section to collapse
        
        main_layout.addWidget(splitter)
        
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
    
    def set_llm_controller(self, controller: AppLLMController):
        """Set the LLM controller."""
        self.llm_controller = controller
        
        # Connect controller signals
        controller.llm_response_ready.connect(self.on_response_ready)
        controller.llm_error.connect(self.on_error)
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
        self.logger.debug(f"Scene context set: ID={scene_id}, content length={len(content)}")
        
        # Update status to show context is available
        if content.strip():
            self.update_status(_("Ready - Scene context loaded"), "success")
        else:
            self.update_status(_("Ready - No scene content"), "warning")
    
    def execute_task(self, task_id: str):
        """Execute an LLM task."""
        if not self.llm_controller:
            self.show_error(_("Error"), _("LLM controller not initialized"))
            return
        
        if not self.llm_controller.is_initialized():
            self.show_error(_("Error"), _("LLM system not initialized"))
            return
        
        # Build context from current scene
        context = self.build_context()
        
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
    
    def build_context(self) -> Dict[str, Any]:
        """Build context for LLM task from current scene."""
        # Extract text content (remove HTML tags for context)
        import re
        text_content = re.sub(r'<[^>]+>', '', self.current_scene_content)
        
        # Get last paragraph or selection as current text
        lines = text_content.split('\n')
        current_text = lines[-1] if lines else ""
        
        # Build scene summary (first 200 chars)
        scene_summary = text_content[:200] + "..." if len(text_content) > 200 else text_content
        
        context = {
            'current_text': current_text.strip(),
            'scene_summary': scene_summary.strip(),
            'scene_id': self.current_scene_id,
            'project_name': 'Current Project'  # TODO: Get actual project name
        }
        
        self.logger.debug(f"Built context: {context}")
        return context
    
    def set_task_executing(self, task_id: str, executing: bool):
        """Set task execution state."""
        if task_id == "continue_scene":
            self.continue_button.set_executing(executing)
    
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
        
        # Update response area
        self.response_area.set_response(response)
        
        # Reset task state
        self.set_task_executing(task_id, False)
        self.update_status(_("✅ Response ready"), "success")
        self.progress_bar.setVisible(False)
    
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