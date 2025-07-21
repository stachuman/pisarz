"""
Custom Prompt Dialog - allows users to enter ad-hoc prompts with configurable context.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QSlider, QDoubleSpinBox, QFormLayout, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from typing import Dict, Any, Optional

from i18n import _


class CustomPromptDialog(QDialog):
    """Dialog for creating custom on-demand prompts."""
    
    # Signal emitted when user wants to execute the prompt
    execute_prompt = Signal(dict)  # prompt_config dict
    
    def __init__(self, scene_content: str = "", selected_text: str = "", parent=None):
        super().__init__(parent)
        self.scene_content = scene_content
        self.selected_text = selected_text
        self.setup_ui()
        self.update_context_preview()
        
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle(_("Custom Prompt"))
        self.setMinimumSize(600, 700)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Title
        title_label = QLabel(_("🎯 Custom Prompt Generator"))
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 10px 0;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Instruction input
        instruction_group = QGroupBox(_("Instruction"))
        instruction_layout = QVBoxLayout(instruction_group)
        
        self.instruction_edit = QTextEdit()
        self.instruction_edit.setPlaceholderText(_("Enter your custom instruction here...\nExample: 'Rewrite this scene in a more dramatic tone' or 'Add more dialogue between characters'"))
        self.instruction_edit.setMinimumHeight(120)
        self.instruction_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #007acc;
            }
        """)
        instruction_layout.addWidget(self.instruction_edit)
        layout.addWidget(instruction_group)
        
        # Context configuration
        context_group = QGroupBox(_("Context Configuration"))
        context_layout = QHBoxLayout(context_group)
        
        # Left column - checkboxes
        left_column = QVBoxLayout()
        
        self.include_scene_context_cb = QCheckBox(_("Include scene context"))
        self.include_scene_context_cb.setChecked(True)
        self.include_scene_context_cb.toggled.connect(self.update_context_preview)
        self.include_scene_context_cb.toggled.connect(self._on_scene_context_toggled)
        left_column.addWidget(self.include_scene_context_cb)
        
        self.include_characters_cb = QCheckBox(_("Include character list"))
        self.include_characters_cb.setChecked(True)
        self.include_characters_cb.toggled.connect(self.update_context_preview)
        left_column.addWidget(self.include_characters_cb)
        
        self.include_locations_cb = QCheckBox(_("Include location list"))  
        self.include_locations_cb.setChecked(True)
        self.include_locations_cb.toggled.connect(self.update_context_preview)
        left_column.addWidget(self.include_locations_cb)
        
        left_column.addStretch()
        
        # Right column - text portion and custom length
        right_column = QFormLayout()
        
        self.text_portion_combo = QComboBox()
        self.text_portion_combo.addItems([
            _("🎯 Selected text only"),
            _("📄 Full scene"),
            _("⬆️ Beginning of scene"),
            _("⬇️ End of scene"),
            _("🎚️ Custom length from end"),
            _("🎯 Selection + context")
        ])
        self.text_portion_combo.currentTextChanged.connect(self.update_context_preview)
        right_column.addRow(_("Text portion:"), self.text_portion_combo)
        
        self.custom_length_spin = QSpinBox()
        self.custom_length_spin.setRange(500, 50000)
        self.custom_length_spin.setValue(8000)
        self.custom_length_spin.setSuffix(_(" characters"))
        self.custom_length_spin.valueChanged.connect(self.update_context_preview)
        right_column.addRow(_("Custom length:"), self.custom_length_spin)
        
        # Add columns to main layout
        context_layout.addLayout(left_column)
        context_layout.addLayout(right_column)
        
        layout.addWidget(context_group)
        
        # LLM Parameters
        params_group = QGroupBox(_("LLM Parameters"))
        params_layout = QFormLayout(params_group)
        
        # Temperature
        temp_layout = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(1, 20)  # 0.1 to 2.0
        self.temperature_slider.setValue(8)  # 0.8 default
        self.temperature_label = QLabel("0.8")
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/10:.1f}")
        )
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        params_layout.addRow(_("Temperature:"), temp_layout)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 20000)
        self.max_tokens_spin.setValue(8000)
        params_layout.addRow(_("Max tokens:"), self.max_tokens_spin)
        
        # Repetition penalty
        rep_layout = QHBoxLayout()
        self.repetition_slider = QSlider(Qt.Orientation.Horizontal)
        self.repetition_slider.setRange(100, 150)  # 1.0 to 1.5
        self.repetition_slider.setValue(105)  # 1.05 default
        self.repetition_label = QLabel("1.05")
        self.repetition_slider.valueChanged.connect(
            lambda v: self.repetition_label.setText(f"{v/100:.2f}")
        )
        rep_layout.addWidget(self.repetition_slider)
        rep_layout.addWidget(self.repetition_label)
        params_layout.addRow(_("Repetition penalty:"), rep_layout)
        
        layout.addWidget(params_group)
        
        # Context preview
        preview_group = QGroupBox(_("Context Preview"))
        preview_layout = QVBoxLayout(preview_group)
        
        self.context_preview = QTextEdit()
        self.context_preview.setReadOnly(True)
        self.context_preview.setMaximumHeight(150)
        self.context_preview.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 9pt;
                color: #6c757d;
            }
        """)
        preview_layout.addWidget(self.context_preview)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton(_("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.execute_button = QPushButton(_("🚀 Execute Prompt"))
        self.execute_button.clicked.connect(self.execute_custom_prompt)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(self.execute_button)
        
        layout.addLayout(button_layout)
    
    def _on_scene_context_toggled(self, checked: bool):
        """Handle scene context checkbox toggle."""
        # Enable/disable text portion controls based on scene context setting
        self.text_portion_combo.setEnabled(checked)
        self.custom_length_spin.setEnabled(checked)
        
    def update_context_preview(self):
        """Update the context preview based on current settings."""
        try:
            # Check if scene context is enabled
            if not self.include_scene_context_cb.isChecked():
                self.context_preview.setPlainText(_("No scene context - instruction only"))
                return
            
            portion_text = self.text_portion_combo.currentText()
            context_text = ""
            
            # Clean HTML/CSS from content first
            clean_scene_content = self._clean_html_css(self.scene_content) if self.scene_content else ""
            clean_selected_text = self._clean_html_css(self.selected_text) if self.selected_text else ""
            
            # Use exact text matching instead of substring matching to fix selection bug
            if portion_text == _("🎯 Selected text only") and clean_selected_text:
                context_text = clean_selected_text
            elif portion_text == _("📄 Full scene"):
                context_text = clean_scene_content
            elif portion_text == _("⬆️ Beginning of scene"):
                length = self.custom_length_spin.value()
                context_text = clean_scene_content[:length]
                if len(clean_scene_content) > length:
                    context_text += "..."
            elif portion_text == _("⬇️ End of scene"):
                length = self.custom_length_spin.value()
                if len(clean_scene_content) > length:
                    context_text = "..." + clean_scene_content[-length:]
                else:
                    context_text = clean_scene_content
            elif portion_text == _("🎚️ Custom length from end"):
                length = self.custom_length_spin.value()
                context_text = clean_scene_content[-length:] if clean_scene_content else ""
            elif portion_text == _("🎯 Selection + context") and clean_selected_text:
                # Show selection plus some context
                context_text = f"SELECTED: {clean_selected_text}\n\nCONTEXT: {clean_scene_content[:2000]}..."
            else:
                context_text = clean_scene_content[:self.custom_length_spin.value()]
            
            # Show full preview without truncation
            final_preview = f"Preview ({len(context_text)} characters):\n\n{context_text}"
            self.context_preview.setPlainText(final_preview)
            
        except Exception as e:
            error_msg = f"Error generating preview: {e}"
            self.context_preview.setPlainText(error_msg)
    
    def _clean_html_css(self, content: str) -> str:
        """Clean HTML tags and CSS from content to produce plain text."""
        from core.utils.text_cleaner import clean_html_css
        return clean_html_css(content)
    
    def execute_custom_prompt(self):
        """Execute the custom prompt."""
        instruction = self.instruction_edit.toPlainText().strip()
        
        if not instruction:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, _("Warning"), _("Please enter an instruction."))
            return
        
        # Build configuration and store it in the dialog
        self.config = {
            "instruction": instruction,
            "text_portion": self.text_portion_combo.currentText(),
            "custom_length": self.custom_length_spin.value(),
            "include_characters": self.include_characters_cb.isChecked(),
            "include_locations": self.include_locations_cb.isChecked(),
            "include_scene_content": self.include_scene_context_cb.isChecked(),
            "temperature": self.temperature_slider.value() / 10.0,
            "max_tokens": self.max_tokens_spin.value(),
            "repetition_penalty": self.repetition_slider.value() / 100.0,
            "scene_content": self.scene_content,
            "selected_text": self.selected_text
        }
        
        # Accept dialog to close it
        self.accept()
    
    def get_config(self):
        """Get the configuration if dialog was accepted."""
        return getattr(self, 'config', None)