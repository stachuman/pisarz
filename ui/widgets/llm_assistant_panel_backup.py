"""
LLM Assistant Panel - AI-powered writing assistance panel.
Provides context-aware text generation and improvement suggestions.
"""

import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QFrame, QSplitter, QProgressBar,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

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


class TaskButton(QPushButton):
    """Custom button for LLM tasks."""
    
    taskRequested = Signal(str)
    
    def __init__(self, task_id: str, task_name: str, task_description: str = "", parent=None):
        super().__init__(task_name, parent)
        self.task_id = task_id
        self.task_name = task_name
        self.task_description = task_description
        self.is_executing = False
        
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setToolTip(task_description)
        
        # Style the button
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Handle button click."""
        if not self.is_executing:
            self.taskRequested.emit(self.task_id)
    
    def set_executing(self, executing: bool):
        """Set button executing state."""
        self.is_executing = executing
        self.setEnabled(not executing)
        
        if executing:
            self.setText(f"{self.task_name}...")
        else:
            self.setText(self.task_name)


class LLMAssistantPanel(QWidget):
    """Main LLM Assistant Panel widget."""
    
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
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel(_("AI Assistant"))
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Status indicator
        self.status_label = QLabel(_("Ready"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 9pt;
                padding: 4px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Task buttons section
        tasks_frame = QFrame()
        tasks_frame.setFrameStyle(QFrame.Box)
        tasks_frame.setLineWidth(1)
        tasks_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        tasks_layout = QVBoxLayout(tasks_frame)
        tasks_layout.setContentsMargins(8, 8, 8, 8)
        tasks_layout.setSpacing(6)
        
        # Tasks label
        tasks_label = QLabel(_("Writing Tasks"))
        tasks_label.setStyleSheet("font-weight: bold; color: #333333;")
        tasks_layout.addWidget(tasks_label)
        
        # Continue Scene button
        self.continue_button = TaskButton(
            "continue_scene",
            _("Continue Scene"),
            _("Continue writing the current scene based on context")
        )
        self.continue_button.taskRequested.connect(self.execute_task)
        tasks_layout.addWidget(self.continue_button)
        
        # Placeholder for future buttons
        placeholder_label = QLabel(_("More tasks coming in Phase 6..."))
        placeholder_label.setStyleSheet("color: #888888; font-size: 8pt; font-style: italic;")
        placeholder_label.setAlignment(Qt.AlignCenter)
        tasks_layout.addWidget(placeholder_label)
        
        layout.addWidget(tasks_frame)
        
        # Response display area
        response_frame = QFrame()
        response_frame.setFrameStyle(QFrame.Box)
        response_frame.setLineWidth(1)
        response_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 6px;
            }
        """)
        
        response_layout = QVBoxLayout(response_frame)
        response_layout.setContentsMargins(8, 8, 8, 8)
        response_layout.setSpacing(6)
        
        # Response label
        response_label = QLabel(_("AI Response"))
        response_label.setStyleSheet("font-weight: bold; color: #333333;")
        response_layout.addWidget(response_label)
        
        # Response text area
        self.response_text = QTextEdit()
        self.response_text.setPlaceholderText(_("AI responses will appear here..."))
        self.response_text.setReadOnly(True)
        self.response_text.setMaximumHeight(300)
        self.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
                line-height: 1.4;
            }
        """)
        response_layout.addWidget(self.response_text)
        
        # Response actions
        actions_layout = QHBoxLayout()
        
        self.copy_button = QPushButton(_("Copy"))
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_response)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        actions_layout.addWidget(self.copy_button)
        
        self.clear_button = QPushButton(_("Clear"))
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_response)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        actions_layout.addWidget(self.clear_button)
        
        actions_layout.addStretch()
        response_layout.addLayout(actions_layout)
        
        layout.addWidget(response_frame)
        
        # Stretch to push everything to top
        layout.addStretch()
        
    def setup_connections(self):
        """Setup signal connections."""
        # Will be connected when controller is set
        pass
    
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
            except Exception as e:
                self.logger.error(f"Failed to initialize LLM controller: {e}")
                self.show_error(_("LLM Initialization Error"), str(e))
    
    def set_scene_context(self, scene_id: int, content: str):
        """Set the current scene context."""
        self.current_scene_id = scene_id
        self.current_scene_content = content
        self.logger.debug(f"Scene context set: ID={scene_id}, content length={len(content)}")
    
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
        self.status_label.setText(_("Processing..."))
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
    
    def on_response_ready(self, task_id: str, response: str):
        """Handle LLM response ready."""
        self.logger.info(f"Response ready for task: {task_id}")
        
        # Update UI
        self.response_text.setPlainText(response)
        self.copy_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        # Reset task state
        self.set_task_executing(task_id, False)
        self.status_label.setText(_("Response ready"))
        self.progress_bar.setVisible(False)
    
    def on_error(self, task_id: str, error_message: str):
        """Handle LLM error."""
        self.logger.error(f"LLM error for task {task_id}: {error_message}")
        
        # Show error in response area
        self.response_text.setPlainText(f"{_('Error')}: {error_message}")
        self.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                padding: 8px;
                color: #721c24;
            }
        """)
        
        # Reset task state
        self.set_task_executing(task_id, False)
        self.status_label.setText(_("Error occurred"))
        self.progress_bar.setVisible(False)
    
    def on_status_changed(self, status: str):
        """Handle LLM status change."""
        self.status_label.setText(status)
    
    def on_task_finished(self, task_id: str, response: str):
        """Handle task thread finished."""
        # Response will be handled by controller signals
        pass
    
    def on_task_error(self, task_id: str, error_message: str):
        """Handle task thread error."""
        self.on_error(task_id, error_message)
    
    def copy_response(self):
        """Copy response to clipboard."""
        text = self.response_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_label.setText(_("Response copied to clipboard"))
    
    def clear_response(self):
        """Clear the response area."""
        self.response_text.clear()
        self.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
                line-height: 1.4;
            }
        """)
        self.copy_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.status_label.setText(_("Ready"))
    
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