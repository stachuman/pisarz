"""Enhanced Task Button widget for LLM Assistant Panel."""

from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtCore import Signal

from i18n import _


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
        from ui.styles.llm_panel_styles import UIStyleManager
        UIStyleManager.apply_enhanced_task_button_style(self, 'normal')
        
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
            from ui.styles.llm_panel_styles import UIStyleManager
            UIStyleManager.apply_enhanced_task_button_style(self, 'executing')
        else:
            self.setText(self.task_name)
            # Restore original style properly
            from ui.styles.llm_panel_styles import UIStyleManager
            UIStyleManager.apply_enhanced_task_button_style(self, 'normal')