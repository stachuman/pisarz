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
    QSpacerItem, QDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QSize
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QIcon

from core.logging_config import get_logger
from controllers.app_llm_controller import AppLLMController
from ui.widgets.enhanced_response_area import EnhancedResponseArea
from ui.widgets.enhanced_task_button import EnhancedTaskButton
from ui.managers.template_ui_manager import TemplateUIManager
from core.llm.custom_prompt_manager import CustomPromptManager
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


# EnhancedTaskButton moved to ui/widgets/enhanced_task_button.py
# EnhancedResponseArea moved to ui/widgets/enhanced_response_area.py


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
        
        # Template UI manager
        self.template_ui_manager = TemplateUIManager(self)
        
        # Custom prompt manager
        self.custom_prompt_manager = CustomPromptManager(self)
        
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
        
        # Create all sections
        self._create_header_controls(controls_layout)
        self._create_template_selection_controls(controls_layout)
        self._create_content_source_controls(controls_layout)
        self._create_action_controls(controls_layout)
        self._create_execution_controls(controls_layout)
        
        controls_layout.addStretch()
        return controls_widget
    
    def _create_header_controls(self, layout: QVBoxLayout):
        """Create header controls (title, status, progress)."""
        # Compact title
        title_label = QLabel(_("🤖 AI Assistant"))
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_additional_style(title_label, 'ai_assistant_title')
        layout.addWidget(title_label)
        
        # Status indicator
        self.status_label = QLabel(_("Ready"))
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_additional_style(self.status_label, 'ready_status')
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(4)
        layout.addWidget(self.progress_bar)
    
    def _create_template_selection_controls(self, layout: QVBoxLayout):
        """Create template selection controls (dropdown, refresh button)."""
        template_layout = QHBoxLayout()
        
        self.task_combo = QComboBox()
        self.template_ui_manager.load_available_templates(self.task_combo)
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_updated_control_section_style(self.task_combo, 'compact_task_combo')
        template_layout.addWidget(self.task_combo)
        
        # Refresh templates button
        self.refresh_templates_button = QPushButton("🔄")
        self.refresh_templates_button.setFixedSize(24, 24)
        self.refresh_templates_button.setToolTip(_("Refresh templates from disk"))
        self.refresh_templates_button.clicked.connect(self._refresh_templates)
        template_layout.addWidget(self.refresh_templates_button)
        
        layout.addLayout(template_layout)
    
    def _create_content_source_controls(self, layout: QVBoxLayout):
        """Create content source selection controls."""
        content_label = QLabel(_("Content Source:"))
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_updated_control_section_style(content_label, 'content_source_label')
        layout.addWidget(content_label)
        
        self.content_source_combo = QComboBox()
        self.content_source_combo.addItems([
            _("Selection (if any)"),
            _("Full Scene"),
            _("Scene Beginning"),
            _("Scene End"),
            _("Custom Length")
        ])
        self.content_source_combo.setCurrentIndex(0)  # Default to selection
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_updated_control_section_style(self.content_source_combo, 'compact_content_source_combo')
        self.content_source_combo.setToolTip(_("Choose what content to pass to the AI template"))
        layout.addWidget(self.content_source_combo)
    
    def _create_action_controls(self, layout: QVBoxLayout):
        """Create action controls (edit template button)."""
        self.edit_template_button = QPushButton(_("🛠️ Edit"))
        self.edit_template_button.setToolTip(_("Edit selected template"))
        self.edit_template_button.clicked.connect(self._edit_selected_template)
        layout.addWidget(self.edit_template_button)
    
    def _create_execution_controls(self, layout: QVBoxLayout):
        """Create execution controls (execute, streaming, stop buttons)."""
        # Execute buttons layout
        execute_layout = QHBoxLayout()
        
        # Execute button
        self.execute_button = QPushButton(_("Execute"))
        self.execute_button.clicked.connect(self.execute_selected_task)
        self.execute_button.setVisible(False)  # Hide regular execute button
        execute_layout.addWidget(self.execute_button)
        
        # Streaming Execute button
        self.execute_streaming_button = QPushButton(_("🔄 Execute"))
        self.execute_streaming_button.clicked.connect(self.execute_selected_task_streaming)
        execute_layout.addWidget(self.execute_streaming_button)
        
        layout.addLayout(execute_layout)
        
        # Stop button (initially hidden)
        self.stop_button = QPushButton(_("⏹️ Stop"))
        self.stop_button.clicked.connect(self.stop_streaming_task)
        self.stop_button.setVisible(False)
        layout.addWidget(self.stop_button)
        
        # Keep compatibility with old buttons
        self.continue_button = self.execute_button  # For backward compatibility
    
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
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_header_section_style(title_label, 'writing_assistant_title')
        header_layout.addWidget(title_label)
        
        # Status and progress section
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status indicator
        self.status_label = QLabel(_("Ready"))
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_header_section_style(self.status_label, 'header_status_label')
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(6)
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_header_section_style(self.progress_bar, 'header_progress_bar')
        
        header_layout.addWidget(status_widget)
        header_layout.addWidget(self.progress_bar)
        
        return header_widget
    
    def create_tasks_section(self) -> QWidget:
        """Create the tasks section with enhanced styling."""
        tasks_widget = QGroupBox(_("Writing Tasks"))
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_tasks_section_style(tasks_widget, 'tasks_group_box')
        
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
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_tasks_section_style(self.template_editor_btn, 'template_editor_button')
        self.template_editor_btn.clicked.connect(self._edit_selected_template)
        tasks_layout.addWidget(self.template_editor_btn)
        
        # Placeholder for future tasks with better styling
        future_tasks_label = QLabel(_("✨ More AI writing tasks coming soon..."))
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_tasks_section_style(future_tasks_label, 'future_tasks_placeholder')
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
        
        # Connect template UI manager signals
        self.template_ui_manager.template_saved.connect(self._on_template_saved)
    
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
        self.current_scene_content = content or ""
        self.additional_context = {}  # Reset additional context when scene changes
        self.logger.debug(f"Scene context set: ID={scene_id}, content length={len(self.current_scene_content)}")
        
        # Update status to show context is available
        if self.current_scene_content.strip():
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
        from core.llm.context_builder import ContextBuilder
        
        builder = ContextBuilder()
        content_source_selection = self.content_source_combo.currentIndex()
        
        return builder.build_context(
            current_scene_content=self.current_scene_content,
            current_scene_id=self.current_scene_id,
            additional_context=self.additional_context,
            content_source_selection=content_source_selection
        )
    
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
        
        # Use UIStyleManager for dynamic status styling
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_dynamic_status_style(self.status_label, status_type)
    
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
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_response_text_error_style(self.response_area.response_text)
        
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
    
    def _edit_selected_template(self):
        """Edit the currently selected template (wrapper method)."""
        self.template_ui_manager.edit_selected_template(self.task_combo)
    
    def _on_template_saved(self, template_id: str):
        """Handle template saved signal (wrapper method)."""
        self.logger.info(f"Template saved: {template_id}")
        # Refresh available templates
        self.template_ui_manager.load_available_templates(self.task_combo)
    
    def _refresh_templates(self):
        """Refresh templates from disk (wrapper method)."""
        self.template_ui_manager.refresh_templates(self.task_combo, self.update_status)
    
    def open_custom_prompt_dialog(self, streaming: bool = False):
        """Open custom prompt dialog (wrapper method)."""
        try:
            # Populate additional context with current scene data before opening dialog
            self._populate_additional_context()
            
            # Build context using the same logic as templates (respects content source selection)
            context = self.build_context()
            
            # Extract the relevant information from context
            scene_content = context.get('scene_content', '')
            selected_text = context.get('selected_text', '')
            
            # Use custom prompt manager to open dialog
            config = self.custom_prompt_manager.open_custom_prompt_dialog(
                scene_content, selected_text, self.build_context, streaming
            )
            
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
            
            # Use the LLM controller for custom prompts
            from controllers.app_llm_controller import get_llm_controller
            llm_controller = get_llm_controller()
            
            if not llm_controller:
                self.logger.error("LLM controller not available")
                return
            
            managers = main_window.project_controller.get_current_managers()
            
            context_data = llm_controller.prepare_custom_prompt_context(
                self.current_scene_id, managers, 
                include_characters=True, include_locations=True
            )
            
            self.set_additional_context(context_data)
            self.logger.debug(f"Additional context populated for scene {self.current_scene_id}")
            
        except Exception as e:
            self.logger.error(f"Error populating additional context: {e}")
    
    def execute_custom_prompt(self, config: dict, streaming: bool = False):
        """Execute a custom prompt configuration using CustomPromptManager."""
        try:
            # Create dynamic template configuration using manager
            template_config = self.custom_prompt_manager.create_dynamic_template_config(config)
            
            # Add template to manager temporarily
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            template_manager.add_template(template_config, save_to_file=False)
            
            # Build context using manager with HTML cleaning callback
            context = {
                'scene_content': config['scene_content'],
                'selected_text': config.get('selected_text', ''),
                'current_text': self.custom_prompt_manager.extract_custom_context(config, self._clean_html_css),
                'characters': self.additional_context.get('characters', []),
                'locations': self.additional_context.get('locations', []),
                'project_description': self.additional_context.get('project_description', ''),
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
    
    
    def _get_selected_content_source(self):
        """Get the selected content source from UI and convert to ContextSource enum."""
        from core.llm.context_builder import ContextBuilder
        
        builder = ContextBuilder()
        selected_index = self.content_source_combo.currentIndex()
        return builder._map_content_source_selection(selected_index)
    
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