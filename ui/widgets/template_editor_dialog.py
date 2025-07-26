"""
Template Editor Dialog for LLM operations.
Provides comprehensive template editing with tabbed interface.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QPushButton, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextOption

from typing import Optional, Dict, Any
from pathlib import Path

from core.logging_config import get_logger
from core.llm.templates.config import (
    TemplateConfig, ContextSource, 
    create_default_template, create_template_from_provider_defaults
)
from core.llm.settings import get_llm_settings
from ..base.base_dialog import BaseDialog
from i18n import _


class TemplateEditorDialog(BaseDialog):
    """Dialog for editing LLM template configurations."""
    
    template_saved = Signal(str)  # template_id
    
    def __init__(self, template_config: Optional[TemplateConfig] = None, parent=None):
        # Initialize with provided config or create default
        self.template_config = template_config or create_default_template()
        self.is_new_template = template_config is None
        
        # Set window properties
        title = _("New Template") if self.is_new_template else _("Edit Template")
        window_title = f"{title} - {self.template_config.name}"
        
        # Initialize BaseDialog
        super().__init__(title=window_title, width=900, height=700, modal=True, parent=parent)
        
        self.logger = get_logger("ui.template_editor")
        
        # Get LLM settings for reference values
        self.llm_settings = get_llm_settings()
        self.current_provider_config = self.llm_settings.get_current_provider_config()
        
        self.setup_ui()
        self.load_template_data()
        self.update_reference_values()
        
        # Size is already set in BaseDialog constructor
    
    def setup_ui(self):
        """Setup the user interface."""
        # Add title section
        title_label = self.create_section_title(_("Template Editor"), 16)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_content_widget(title_label)
        
        # Main content with tabs
        self.tab_widget = self.create_tab_widget()
        self.add_content_widget(self.tab_widget)
        
        # Setup tabs
        self.setup_llm_params_tab()
        self.setup_template_tab()
        self.setup_preview_tab()
        self.setup_metadata_tab()
        
        # Create custom buttons
        load_btn = self.create_custom_button(_("Load Template"), self.load_template_file, "secondary")
        save_as_btn = self.create_custom_button(_("Save as New Template"), self.save_as_new_template, "secondary")
        cancel_btn = self.create_custom_button(_("Cancel"), self.reject, "secondary")
        save_btn = self.create_custom_button(_("Save Template"), self.save_template, "primary")
        save_btn.setDefault(True)
        
        # Add buttons with stretch
        self.add_button_stretch()
        self.add_button(load_btn)
        self.add_button(save_as_btn)
        self.add_button(cancel_btn)
        self.add_button(save_btn)
    
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
    
    def setup_llm_params_tab(self):
        """Setup LLM parameters tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Reference settings info
        self.setup_reference_settings_info(layout)
        
        # Generation parameters group
        params_group = QGroupBox(_("Template LLM Parameters"))
        params_layout = QFormLayout(params_group)
        
        # Max tokens with reference
        tokens_layout, self.max_tokens_spin, self.max_tokens_ref_label = self.create_parameter_row(
            1, 100000, 512, 'max_tokens', self.update_character_estimate, lambda: self.use_default_parameter('max_tokens')
        )
        self.char_estimate_label = self.create_info_label(_("≈ 2048 characters"), "muted")
        tokens_layout.insertWidget(1, self.char_estimate_label)
        params_layout.addRow(_("Max Tokens:"), tokens_layout)
        
        # Temperature with reference
        temp_layout, self.temperature_spin, self.temperature_ref_label = self.create_double_parameter_row(
            0.0, 2.0, 0.1, 2, 0.7, 'temperature', lambda: self.use_default_parameter('temperature')
        )
        params_layout.addRow(_("Temperature:"), temp_layout)
        
        # Top P with reference
        topp_layout, self.top_p_spin, self.top_p_ref_label = self.create_double_parameter_row(
            0.0, 1.0, 0.1, 2, 0.9, 'top_p', lambda: self.use_default_parameter('top_p')
        )
        params_layout.addRow(_("Top P:"), topp_layout)
        
        # Top K with reference
        topk_layout, self.top_k_spin, self.top_k_ref_label = self.create_parameter_row(
            1, 100, 40, 'top_k', None, lambda: self.use_default_parameter('top_k')
        )
        params_layout.addRow(_("Top K:"), topk_layout)
        
        # Repeat penalty with reference
        penalty_layout, self.repeat_penalty_spin, self.repeat_penalty_ref_label = self.create_double_parameter_row(
            0.5, 2.0, 0.1, 2, 1.1, 'repeat_penalty', lambda: self.use_default_parameter('repeat_penalty')
        )
        params_layout.addRow(_("Repeat Penalty:"), penalty_layout)
        
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
    
    def setup_template_tab(self):
        """Setup template content editor tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Template editor
        editor_label = self.create_section_title(_("Template Content (Jinja2 Format)"), 10)
        layout.addWidget(editor_label)
        
        self.template_editor = QTextEdit()
        self.template_editor.setFont(self.font_manager.get_code_font(10))
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
        help_text.setStyleSheet(self.get_help_text_style())
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        
        self.tab_widget.addTab(widget, _("Template"))
    
    def setup_preview_tab(self):
        """Setup template preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        preview_btn = self.create_custom_button(_("Update Preview"), self.update_preview, "secondary")
        controls_layout.addWidget(preview_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Preview content
        preview_label = self.create_section_title(_("Template Preview"), 10)
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(self.font_manager.get_font(10))
        layout.addWidget(self.preview_text)
        
        self.tab_widget.addTab(widget, _("Preview"))
    
    def load_template_data(self):
        """Load template configuration data into UI."""
        try:
            # Metadata
            metadata_fields = [
                (self.name_edit, 'name'),
                (self.id_edit, 'template_id'),
                (self.version_edit, 'version'),
                (self.author_edit, 'author')
            ]
            for field, attr in metadata_fields:
                field.setText(getattr(self.template_config, attr, ''))
            
            self.description_edit.setPlainText(self.template_config.description)
            
            # Set category
            index = self.category_combo.findText(self.template_config.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            
            self.tags_edit.setText(", ".join(self.template_config.tags))
            
            # Context config - using defaults since UI was removed
            
            # LLM params
            llm_params = [
                (self.max_tokens_spin, 'max_tokens'),
                (self.temperature_spin, 'temperature'),
                (self.top_p_spin, 'top_p'),
                (self.top_k_spin, 'top_k'),
                (self.repeat_penalty_spin, 'repeat_penalty')
            ]
            for spin, attr in llm_params:
                spin.setValue(getattr(self.template_config, attr))
            
            if self.template_config.custom_params:
                import json
                self.custom_params_edit.setPlainText(
                    json.dumps(self.template_config.custom_params, indent=2, ensure_ascii=False)
                )
            
            # UI config - using defaults since UI was removed
            
            # Template content
            self.template_editor.setPlainText(self.template_config.template_content)
            
            # Update character estimate
            self.update_character_estimate()
            
            self.logger.debug("Template data loaded into UI")
            
        except Exception as e:
            self.logger.error(f"Error loading template data: {e}")
            QMessageBox.warning(self, _("Error"), _("Failed to load template data: {}").format(str(e)))
    
    def save_template_data(self) -> bool:
        """Save UI data back to template configuration."""
        try:
            # Metadata
            metadata_updates = [
                ('name', self.name_edit.text().strip()),
                ('template_id', self.id_edit.text().strip()),
                ('description', self.description_edit.toPlainText().strip()),
                ('category', self.category_combo.currentText()),
                ('version', self.version_edit.text().strip() or "1.0"),
                ('author', self.author_edit.text().strip() or "User")
            ]
            for attr, value in metadata_updates:
                setattr(self.template_config, attr, value)
            
            # Parse tags
            tags_text = self.tags_edit.text().strip()
            if tags_text:
                self.template_config.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            else:
                self.template_config.tags = []
            
            # Context config - keep defaults since UI was removed
            
            # LLM params
            llm_updates = [
                ('max_tokens', self.max_tokens_spin.value()),
                ('temperature', self.temperature_spin.value()),
                ('top_p', self.top_p_spin.value()),
                ('top_k', self.top_k_spin.value()),
                ('repeat_penalty', self.repeat_penalty_spin.value())
            ]
            for attr, value in llm_updates:
                setattr(self.template_config, attr, value)
            
            # Parse custom params
            custom_text = self.custom_params_edit.toPlainText().strip()
            if custom_text:
                import json
                try:
                    self.template_config.custom_params = json.loads(custom_text)
                except json.JSONDecodeError as e:
                    QMessageBox.warning(self, _("Error"), _("Invalid JSON in custom parameters: {}").format(str(e)))
                    return False
            else:
                self.template_config.custom_params = {}
            
            # UI config - keep defaults since UI was removed
            
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
        """Update template preview with real context data from current scene using exact same functions as real execution."""
        try:
            if not self.save_template_data():
                return
            
            # Get main window - same as real execution
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            main_window = None
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'project_controller') and hasattr(widget, 'llm_panel'):
                    main_window = widget
                    break
            
            # Use exactly the same build_context method as real LLM execution
            context_data = main_window.llm_panel.build_context()
            
            # Use the template manager to build enhanced context (full chain) - same as real execution
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            
            # Build enhanced context using the same chain as real execution
            enhanced_context = template_manager.build_enhanced_context(
                self.template_config.template_id, 
                context_data
            )
            
            # Render template using Jinja2 - same as real execution
            from jinja2 import Template, TemplateError
            template = Template(self.template_config.template_content)
            rendered = template.render(enhanced_context)
            
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
            
            template_config = TemplateConfig.load_from_file(filepath)
            if template_config:
                self.template_config = template_config
                self.load_template_data()
                QMessageBox.information(self, _("Success"), _("Template loaded successfully."))
            else:
                QMessageBox.critical(self, _("Error"), _("Failed to load template file."))
    
    def save_as_new_template(self):
        """Save current template as a new template with different ID."""
        if not self.save_template_data():
            return
        
        from PySide6.QtWidgets import QInputDialog
        
        # Get new template ID from user
        current_id = self.template_config.template_id
        new_id, ok = QInputDialog.getText(
            self,
            _("Save as New Template"),
            _("Enter new template ID:"),
            text=f"{current_id}_copy"
        )
        
        if not ok or not new_id.strip():
            return
        
        new_id = new_id.strip()
        
        # Check if template ID already exists
        try:
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            
            if template_manager.get_template(new_id):
                result = QMessageBox.question(
                    self,
                    _("Template Exists"),
                    _("Template ID '{}' already exists. Overwrite?").format(new_id),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if result != QMessageBox.StandardButton.Yes:
                    return
            
            # Create copy of current template with new ID
            import copy
            new_template = copy.deepcopy(self.template_config)
            new_template.template_id = new_id
            
            # Suggest new name based on ID
            if new_template.name:
                new_template.name = f"{new_template.name} (Copy)"
            else:
                new_template.name = new_id.replace('_', ' ').title()
            
            # Save new template to manager
            success = template_manager.add_template(new_template, save_to_file=True)
            
            if success:
                QMessageBox.information(
                    self,
                    _("Success"),
                    _("New template '{}' created successfully!\n\nTemplate ID: {}").format(
                        new_template.name,
                        new_id
                    )
                )
                # Emit signal to refresh template list
                self.template_saved.emit(new_id)
            else:
                QMessageBox.critical(self, _("Error"), _("Failed to create new template."))
                
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to create new template: {}").format(str(e)))
    
    def save_template(self):
        """Save template to file and template manager, then close dialog."""
        if not self.validate_template():
            return
            
        try:
            # Get template manager
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            
            # Save to template manager (which automatically saves to file)
            success = template_manager.add_template(self.template_config, save_to_file=True)
            
            if success:
                self.template_saved.emit(self.template_config.template_id)
                self.accept()
            else:
                QMessageBox.critical(self, _("Error"), _("Failed to save template."))
                
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to save template: {}").format(str(e)))
    
    def get_template_config(self) -> TemplateConfig:
        """Get the current template configuration."""
        return self.template_config
    
    def setup_reference_settings_info(self, layout):
        """Setup reference settings information display."""
        ref_group = QGroupBox(_("Current LLM Provider Reference"))
        ref_layout = QVBoxLayout(ref_group)
        
        provider_name = self.llm_settings.get_current_provider()
        provider_display = self.llm_settings.get_provider_display_name(provider_name)
        
        ref_info = self.create_section_title(_("Current Provider: {}").format(provider_display), 11)
        ref_layout.addWidget(ref_info)
        
        help_text = QLabel(_("Template parameters override provider defaults. Click 'Use Default' to apply current provider settings."))
        help_text.setStyleSheet(self.get_muted_text_style())
        help_text.setWordWrap(True)
        ref_layout.addWidget(help_text)
        
        layout.addWidget(ref_group)
    
    def update_character_estimate(self):
        """Update character estimate based on token count."""
        tokens = self.max_tokens_spin.value()
        # Estimate: 1 token ≈ 3-4 characters for most languages
        # Polish might be slightly different, but this is a good approximation
        estimated_chars = tokens * 4
        self.char_estimate_label.setText(_("≈ {} characters").format(estimated_chars))
    
    def use_default_parameter(self, param_name: str):
        """Apply default LLM parameter from current provider."""
        if not self.current_provider_config:
            QMessageBox.warning(self, _("Warning"), _("No provider configuration available"))
            return
        
        try:
            if param_name == 'max_tokens':
                default_value = self.current_provider_config.get_setting('max_tokens', 512)
                self.max_tokens_spin.setValue(default_value)
            elif param_name == 'temperature':
                default_value = self.current_provider_config.get_setting('temperature', 0.7)
                self.temperature_spin.setValue(default_value)
            elif param_name == 'top_p':
                default_value = self.current_provider_config.get_setting('top_p', 0.9)
                self.top_p_spin.setValue(default_value)
            elif param_name == 'top_k':
                default_value = self.current_provider_config.get_setting('top_k', 40)
                self.top_k_spin.setValue(default_value)
            elif param_name == 'repeat_penalty':
                default_value = self.current_provider_config.get_setting('repeat_penalty', 1.1)
                self.repeat_penalty_spin.setValue(default_value)
                
            self.logger.debug(f"Applied default {param_name}: {default_value}")
            
        except Exception as e:
            self.logger.error(f"Error applying default parameter {param_name}: {e}")
            QMessageBox.warning(self, _("Error"), _("Failed to apply default parameter"))
    
    def update_reference_values(self):
        """Update reference value labels with current provider settings."""
        if not self.current_provider_config:
            return
        
        try:
            # Update reference labels
            max_tokens_ref = self.current_provider_config.get_setting('max_tokens', 512)
            self.max_tokens_ref_label.setText(f"(default: {max_tokens_ref})")
            
            temperature_ref = self.current_provider_config.get_setting('temperature', 0.7)
            self.temperature_ref_label.setText(f"(default: {temperature_ref})")
            
            top_p_ref = self.current_provider_config.get_setting('top_p', 0.9)
            self.top_p_ref_label.setText(f"(default: {top_p_ref})")
            
            top_k_ref = self.current_provider_config.get_setting('top_k', 40)
            self.top_k_ref_label.setText(f"(default: {top_k_ref})")
            
            repeat_penalty_ref = self.current_provider_config.get_setting('repeat_penalty', 1.1)
            self.repeat_penalty_ref_label.setText(f"(default: {repeat_penalty_ref})")
            
        except Exception as e:
            self.logger.error(f"Error updating reference values: {e}")
    
    # Helper methods moved to BaseDialog