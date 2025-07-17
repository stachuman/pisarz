"""
Template Editor Dialog for LLM operations.
Provides comprehensive template editing with tabbed interface.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QSplitter, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextOption

from typing import Optional, Dict, Any
from pathlib import Path

from core.logging_config import get_logger
from core.llm.templates.config import (
    EnhancedTemplateConfig, TemplateMetadata, ContextConfig, 
    LLMParams, UIConfig, ContextSource, create_default_template
)
from i18n import _


class TemplateEditorDialog(QDialog):
    """Dialog for editing LLM template configurations."""
    
    template_saved = Signal(str)  # template_id
    
    def __init__(self, template_config: Optional[EnhancedTemplateConfig] = None, parent=None):
        super().__init__(parent)
        self.logger = get_logger("ui.template_editor")
        
        # Initialize with provided config or create default
        self.template_config = template_config or create_default_template()
        self.is_new_template = template_config is None
        
        self.setup_ui()
        self.load_template_data()
        
        # Set window properties
        title = _("New Template") if self.is_new_template else _("Edit Template")
        self.setWindowTitle(f"{title} - {self.template_config.metadata.name}")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel(_("Template Editor"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Main content with tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self.setup_metadata_tab()
        self.setup_context_tab()
        self.setup_llm_params_tab()
        self.setup_ui_config_tab()
        self.setup_template_tab()
        self.setup_preview_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Load/Save buttons
        load_btn = QPushButton(_("Load Template"))
        load_btn.clicked.connect(self.load_template_file)
        button_layout.addWidget(load_btn)
        
        save_file_btn = QPushButton(_("Save to File"))
        save_file_btn.clicked.connect(self.save_template_file)
        button_layout.addWidget(save_file_btn)
        
        # Standard dialog buttons
        cancel_btn = QPushButton(_("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton(_("Save Template"))
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_template)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def setup_metadata_tab(self):
        """Setup metadata configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Basic info group
        basic_group = QGroupBox(_("Basic Information"))
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(_("Enter template name"))
        basic_layout.addRow(_("Name:"), self.name_edit)
        
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText(_("unique_template_id"))
        basic_layout.addRow(_("Template ID:"), self.id_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText(_("Describe what this template does"))
        basic_layout.addRow(_("Description:"), self.description_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "writing", "editing", "analysis", "creative", "technical", "custom"
        ])
        basic_layout.addRow(_("Category:"), self.category_combo)
        
        layout.addWidget(basic_group)
        
        # Additional info group
        additional_group = QGroupBox(_("Additional Information"))
        additional_layout = QFormLayout(additional_group)
        
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("1.0")
        additional_layout.addRow(_("Version:"), self.version_edit)
        
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText(_("Author name"))
        additional_layout.addRow(_("Author:"), self.author_edit)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText(_("tag1, tag2, tag3"))
        additional_layout.addRow(_("Tags:"), self.tags_edit)
        
        layout.addWidget(additional_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, _("Metadata"))
    
    def setup_context_tab(self):
        """Setup context configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Selection group
        selection_group = QGroupBox(_("Text Selection"))
        selection_layout = QFormLayout(selection_group)
        
        self.use_selection_cb = QCheckBox()
        self.use_selection_cb.setChecked(True)
        selection_layout.addRow(_("Use Selected Text:"), self.use_selection_cb)
        
        self.selection_priority_cb = QCheckBox()
        self.selection_priority_cb.setChecked(True)
        selection_layout.addRow(_("Selection Priority:"), self.selection_priority_cb)
        
        layout.addWidget(selection_group)
        
        # Context length group
        context_group = QGroupBox(_("Context Configuration"))
        context_layout = QFormLayout(context_group)
        
        self.default_context_spin = QSpinBox()
        self.default_context_spin.setRange(50, 5000)
        self.default_context_spin.setValue(500)
        self.default_context_spin.setSuffix(" " + _("characters"))
        context_layout.addRow(_("Default Context Length:"), self.default_context_spin)
        
        self.scene_summary_spin = QSpinBox()
        self.scene_summary_spin.setRange(50, 2000)
        self.scene_summary_spin.setValue(300)
        self.scene_summary_spin.setSuffix(" " + _("characters"))
        context_layout.addRow(_("Scene Summary Length:"), self.scene_summary_spin)
        
        self.summary_source_combo = QComboBox()
        for source in ContextSource:
            self.summary_source_combo.addItem(source.value, source)
        context_layout.addRow(_("Summary Source:"), self.summary_source_combo)
        
        self.max_context_spin = QSpinBox()
        self.max_context_spin.setRange(100, 10000)
        self.max_context_spin.setValue(2000)
        self.max_context_spin.setSuffix(" " + _("characters"))
        context_layout.addRow(_("Max Context Length:"), self.max_context_spin)
        
        layout.addWidget(context_group)
        
        # Additional data group
        additional_group = QGroupBox(_("Additional Data"))
        additional_layout = QFormLayout(additional_group)
        
        self.include_characters_cb = QCheckBox()
        self.include_characters_cb.setChecked(True)
        additional_layout.addRow(_("Include Characters:"), self.include_characters_cb)
        
        self.include_locations_cb = QCheckBox()
        self.include_locations_cb.setChecked(True)
        additional_layout.addRow(_("Include Locations:"), self.include_locations_cb)
        
        self.include_project_cb = QCheckBox()
        additional_layout.addRow(_("Include Project Info:"), self.include_project_cb)
        
        self.word_boundary_cb = QCheckBox()
        self.word_boundary_cb.setChecked(True)
        additional_layout.addRow(_("Trim at Word Boundaries:"), self.word_boundary_cb)
        
        layout.addWidget(additional_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, _("Context"))
    
    def setup_llm_params_tab(self):
        """Setup LLM parameters tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Generation parameters group
        params_group = QGroupBox(_("Generation Parameters"))
        params_layout = QFormLayout(params_group)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 4096)
        self.max_tokens_spin.setValue(512)
        params_layout.addRow(_("Max Tokens:"), self.max_tokens_spin)
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setDecimals(2)
        self.temperature_spin.setValue(0.7)
        params_layout.addRow(_("Temperature:"), self.temperature_spin)
        
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setDecimals(2)
        self.top_p_spin.setValue(0.9)
        params_layout.addRow(_("Top P:"), self.top_p_spin)
        
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 100)
        self.top_k_spin.setValue(40)
        params_layout.addRow(_("Top K:"), self.top_k_spin)
        
        self.repeat_penalty_spin = QDoubleSpinBox()
        self.repeat_penalty_spin.setRange(0.5, 2.0)
        self.repeat_penalty_spin.setSingleStep(0.1)
        self.repeat_penalty_spin.setDecimals(2)
        self.repeat_penalty_spin.setValue(1.1)
        params_layout.addRow(_("Repeat Penalty:"), self.repeat_penalty_spin)
        
        layout.addWidget(params_group)
        
        # Custom parameters group
        custom_group = QGroupBox(_("Custom Parameters"))
        custom_layout = QVBoxLayout(custom_group)
        
        self.custom_params_edit = QTextEdit()
        self.custom_params_edit.setMaximumHeight(120)
        self.custom_params_edit.setPlaceholderText(_(
            "Enter custom parameters as JSON:\n"
            "{\n"
            "  \"creativity_level\": \"medium\",\n"
            "  \"style\": \"formal\"\n"
            "}"
        ))
        custom_layout.addWidget(self.custom_params_edit)
        
        layout.addWidget(custom_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, _("LLM Parameters"))
    
    def setup_ui_config_tab(self):
        """Setup UI configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # UI behavior group
        ui_group = QGroupBox(_("UI Behavior"))
        ui_layout = QFormLayout(ui_group)
        
        self.show_context_preview_cb = QCheckBox()
        self.show_context_preview_cb.setChecked(True)
        ui_layout.addRow(_("Show Context Preview:"), self.show_context_preview_cb)
        
        self.allow_context_editing_cb = QCheckBox()
        ui_layout.addRow(_("Allow Context Editing:"), self.allow_context_editing_cb)
        
        self.preview_length_spin = QSpinBox()
        self.preview_length_spin.setRange(50, 500)
        self.preview_length_spin.setValue(100)
        self.preview_length_spin.setSuffix(" " + _("characters"))
        ui_layout.addRow(_("Preview Length:"), self.preview_length_spin)
        
        self.show_params_editor_cb = QCheckBox()
        self.show_params_editor_cb.setChecked(True)
        ui_layout.addRow(_("Show Parameters Editor:"), self.show_params_editor_cb)
        
        self.auto_apply_selection_cb = QCheckBox()
        self.auto_apply_selection_cb.setChecked(True)
        ui_layout.addRow(_("Auto Apply Selection:"), self.auto_apply_selection_cb)
        
        self.confirm_execution_cb = QCheckBox()
        ui_layout.addRow(_("Confirm Before Execution:"), self.confirm_execution_cb)
        
        layout.addWidget(ui_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, _("UI Settings"))
    
    def setup_template_tab(self):
        """Setup template content editor tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Template editor
        editor_label = QLabel(_("Template Content (Jinja2 Format):"))
        editor_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(editor_label)
        
        self.template_editor = QTextEdit()
        self.template_editor.setFont(QFont("Consolas, Monaco, monospace", 10))
        self.template_editor.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.template_editor.setPlaceholderText(_(
            "Enter your Jinja2 template here. Available variables:\n"
            "- {{ current_text }} - Current text for continuation\n"
            "- {{ selected_text }} - Selected text (if any)\n"
            "- {{ scene_summary }} - Scene summary/context\n"
            "- {{ has_selection }} - Boolean, true if text is selected\n"
            "- {{ characters }} - List of characters in scene\n"
            "- {{ locations }} - List of locations in scene\n"
            "- {{ project_name }} - Project name\n"
            "- {{ scene_id }} - Current scene ID"
        ))
        layout.addWidget(self.template_editor)
        
        # Help section
        help_group = QGroupBox(_("Template Help"))
        help_layout = QVBoxLayout(help_group)
        
        help_text = QLabel(_(
            "Use Jinja2 syntax for dynamic templates:\n"
            "• {% if condition %} ... {% endif %} - Conditional blocks\n"
            "• {{ variable }} - Variable insertion\n"
            "• {{ list|join(', ') }} - Join list items\n"
            "• {% for item in list %} ... {% endfor %} - Loops"
        ))
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666666; padding: 5px;")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        
        self.tab_widget.addTab(widget, _("Template"))
    
    def setup_preview_tab(self):
        """Setup template preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        preview_btn = QPushButton(_("Update Preview"))
        preview_btn.clicked.connect(self.update_preview)
        controls_layout.addWidget(preview_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Preview content
        preview_label = QLabel(_("Template Preview:"))
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Arial", 10))
        layout.addWidget(self.preview_text)
        
        self.tab_widget.addTab(widget, _("Preview"))
    
    def load_template_data(self):
        """Load template configuration data into UI."""
        try:
            # Metadata
            self.name_edit.setText(self.template_config.metadata.name)
            self.id_edit.setText(self.template_config.metadata.template_id)
            self.description_edit.setPlainText(self.template_config.metadata.description)
            
            # Find and set category
            index = self.category_combo.findText(self.template_config.metadata.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            
            self.version_edit.setText(self.template_config.metadata.version)
            self.author_edit.setText(self.template_config.metadata.author)
            self.tags_edit.setText(", ".join(self.template_config.metadata.tags))
            
            # Context config
            context = self.template_config.context_config
            self.use_selection_cb.setChecked(context.use_selection)
            self.selection_priority_cb.setChecked(context.selection_priority)
            self.default_context_spin.setValue(context.default_context_length)
            self.scene_summary_spin.setValue(context.scene_summary_length)
            
            # Find and set summary source
            for i in range(self.summary_source_combo.count()):
                if self.summary_source_combo.itemData(i) == context.scene_summary_source:
                    self.summary_source_combo.setCurrentIndex(i)
                    break
            
            self.max_context_spin.setValue(context.max_context_chars)
            self.include_characters_cb.setChecked(context.include_characters)
            self.include_locations_cb.setChecked(context.include_locations)
            self.include_project_cb.setChecked(context.include_project_info)
            self.word_boundary_cb.setChecked(context.word_boundary_trim)
            
            # LLM params
            params = self.template_config.llm_params
            self.max_tokens_spin.setValue(params.max_tokens)
            self.temperature_spin.setValue(params.temperature)
            self.top_p_spin.setValue(params.top_p)
            self.top_k_spin.setValue(params.top_k)
            self.repeat_penalty_spin.setValue(params.repeat_penalty)
            
            if params.custom_params:
                import json
                self.custom_params_edit.setPlainText(
                    json.dumps(params.custom_params, indent=2, ensure_ascii=False)
                )
            
            # UI config
            ui = self.template_config.ui_config
            self.show_context_preview_cb.setChecked(ui.show_context_preview)
            self.allow_context_editing_cb.setChecked(ui.allow_context_editing)
            self.preview_length_spin.setValue(ui.preview_length)
            self.show_params_editor_cb.setChecked(ui.show_params_editor)
            self.auto_apply_selection_cb.setChecked(ui.auto_apply_selection)
            self.confirm_execution_cb.setChecked(ui.confirm_before_execution)
            
            # Template content
            self.template_editor.setPlainText(self.template_config.template_content)
            
            self.logger.debug("Template data loaded into UI")
            
        except Exception as e:
            self.logger.error(f"Error loading template data: {e}")
            QMessageBox.warning(self, _("Error"), _("Failed to load template data: {}").format(str(e)))
    
    def save_template_data(self) -> bool:
        """Save UI data back to template configuration."""
        try:
            # Metadata
            self.template_config.metadata.name = self.name_edit.text().strip()
            self.template_config.metadata.template_id = self.id_edit.text().strip()
            self.template_config.metadata.description = self.description_edit.toPlainText().strip()
            self.template_config.metadata.category = self.category_combo.currentText()
            self.template_config.metadata.version = self.version_edit.text().strip() or "1.0"
            self.template_config.metadata.author = self.author_edit.text().strip() or "User"
            
            # Parse tags
            tags_text = self.tags_edit.text().strip()
            if tags_text:
                self.template_config.metadata.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            else:
                self.template_config.metadata.tags = []
            
            # Context config
            context = self.template_config.context_config
            context.use_selection = self.use_selection_cb.isChecked()
            context.selection_priority = self.selection_priority_cb.isChecked()
            context.default_context_length = self.default_context_spin.value()
            context.scene_summary_length = self.scene_summary_spin.value()
            context.scene_summary_source = self.summary_source_combo.currentData()
            context.max_context_chars = self.max_context_spin.value()
            context.include_characters = self.include_characters_cb.isChecked()
            context.include_locations = self.include_locations_cb.isChecked()
            context.include_project_info = self.include_project_cb.isChecked()
            context.word_boundary_trim = self.word_boundary_cb.isChecked()
            
            # LLM params
            params = self.template_config.llm_params
            params.max_tokens = self.max_tokens_spin.value()
            params.temperature = self.temperature_spin.value()
            params.top_p = self.top_p_spin.value()
            params.top_k = self.top_k_spin.value()
            params.repeat_penalty = self.repeat_penalty_spin.value()
            
            # Parse custom params
            custom_text = self.custom_params_edit.toPlainText().strip()
            if custom_text:
                import json
                try:
                    params.custom_params = json.loads(custom_text)
                except json.JSONDecodeError as e:
                    QMessageBox.warning(self, _("Error"), _("Invalid JSON in custom parameters: {}").format(str(e)))
                    return False
            else:
                params.custom_params = {}
            
            # UI config
            ui = self.template_config.ui_config
            ui.show_context_preview = self.show_context_preview_cb.isChecked()
            ui.allow_context_editing = self.allow_context_editing_cb.isChecked()
            ui.preview_length = self.preview_length_spin.value()
            ui.show_params_editor = self.show_params_editor_cb.isChecked()
            ui.auto_apply_selection = self.auto_apply_selection_cb.isChecked()
            ui.confirm_before_execution = self.confirm_execution_cb.isChecked()
            
            # Template content
            self.template_config.template_content = self.template_editor.toPlainText()
            
            self.logger.debug("Template data saved from UI")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving template data: {e}")
            QMessageBox.critical(self, _("Error"), _("Failed to save template data: {}").format(str(e)))
            return False
    
    def validate_template(self) -> bool:
        """Validate current template configuration."""
        if not self.save_template_data():
            return False
        
        is_valid, errors = self.template_config.validate()
        
        if not is_valid:
            error_text = "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(
                self, 
                _("Validation Error"), 
                _("Template validation failed:\n\n{}").format(error_text)
            )
            return False
        
        return True
    
    def update_preview(self):
        """Update template preview with sample data."""
        try:
            if not self.save_template_data():
                return
            
            # Create sample context
            sample_context = {
                'current_text': "Przykładowy tekst do kontynuacji...",
                'selected_text': "zaznaczony fragment",
                'scene_summary': "To jest przykładowe podsumowanie sceny z kontekstem.",
                'has_selection': True,
                'characters': ["Jan", "Anna", "Marek"],
                'locations': ["Kawiarnia", "Park"],
                'project_name': "Mój Projekt",
                'scene_id': "scene_001"
            }
            
            # Try to render template
            from jinja2 import Template, TemplateError
            
            try:
                template = Template(self.template_config.template_content)
                rendered = template.render(sample_context)
                self.preview_text.setPlainText(rendered)
                self.preview_text.setStyleSheet("color: black;")
                
            except TemplateError as e:
                error_text = f"Template Error: {str(e)}"
                self.preview_text.setPlainText(error_text)
                self.preview_text.setStyleSheet("color: red;")
                
        except Exception as e:
            self.logger.error(f"Error updating preview: {e}")
            self.preview_text.setPlainText(f"Preview Error: {str(e)}")
            self.preview_text.setStyleSheet("color: red;")
    
    def load_template_file(self):
        """Load template from file."""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter(_("Template Files (*.json *.yaml *.yml)"))
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec():
            filepath = Path(file_dialog.selectedFiles()[0])
            
            template_config = EnhancedTemplateConfig.load_from_file(filepath)
            if template_config:
                self.template_config = template_config
                self.load_template_data()
                QMessageBox.information(self, _("Success"), _("Template loaded successfully."))
            else:
                QMessageBox.critical(self, _("Error"), _("Failed to load template file."))
    
    def save_template_file(self):
        """Save template to file."""
        if not self.save_template_data():
            return
        
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter(_("Template Files (*.json *.yaml *.yml)"))
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setDefaultSuffix("yaml")
        
        suggested_name = f"{self.template_config.metadata.template_id}.yaml"
        file_dialog.selectFile(suggested_name)
        
        if file_dialog.exec():
            filepath = Path(file_dialog.selectedFiles()[0])
            
            if self.template_config.save_to_file(filepath):
                QMessageBox.information(self, _("Success"), _("Template saved to file successfully."))
            else:
                QMessageBox.critical(self, _("Error"), _("Failed to save template to file."))
    
    def save_template(self):
        """Save template and close dialog."""
        if self.validate_template():
            self.template_saved.emit(self.template_config.metadata.template_id)
            self.accept()
    
    def get_template_config(self) -> EnhancedTemplateConfig:
        """Get the current template configuration."""
        return self.template_config