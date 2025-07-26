"""
Templates List Dialog

Provides a dialog for viewing and managing all available templates.
Users can view, edit, delete, and create new templates from this interface.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QMessageBox, QGroupBox, QTextEdit,
    QSplitter, QFrame, QHeaderView, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QWidget, QFormLayout
)

from ui.base.base_dialog import BaseDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Optional, Dict, Any

from core.logging_config import get_logger
from core.llm.templates import get_template_manager, TemplateConfig
from i18n import _


class TemplatesListDialog(BaseDialog):
    """Dialog for managing templates list."""
    
    def __init__(self, parent=None):
        self.logger = get_logger("ui.templates_list")
        self.template_manager = get_template_manager()
        self.current_template = None
        
        super().__init__(
            title=_("Templates Manager"),
            width=1000,
            height=700,
            modal=True,
            parent=parent
        )
        
        self.setup_ui()
        self.refresh_templates_list()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Title
        title_label = QLabel(_("Templates Manager"))
        title_label.setFont(self.font_manager.get_font(14))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_content_widget(title_label)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Templates list
        left_panel = self.create_templates_list_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Template details
        right_panel = self.create_template_details_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([350, 650])
        self.add_content_widget(main_splitter)
        
        # Buttons using BaseDialog functionality
        # Left side buttons
        new_btn = self.create_custom_button(_("New Template"), self.create_new_template, "primary")
        self.add_button(new_btn)
        
        self.edit_btn = self.create_custom_button(_("Edit Template"), self.edit_selected_template, "secondary")
        self.add_button(self.edit_btn)
        
        self.delete_btn = self.create_custom_button(_("Delete Template"), self.delete_selected_template, "secondary")
        self.add_button(self.delete_btn)
        
        self.add_button_stretch()
        
        # Right side buttons
        refresh_btn = self.create_custom_button(_("Refresh"), self.refresh_templates_list, "secondary")
        self.add_button(refresh_btn)
        
        close_btn = self.create_custom_button(_("Close"), self.close, "secondary")
        close_btn.setDefault(True)
        self.add_button(close_btn)
        
        # Initially disable edit/delete buttons
        self.update_buttons_state()
        
    def create_templates_list_panel(self):
        """Create the templates list panel."""
        panel, layout = self.create_form_section(_("Available Templates"))
        
        # Templates list widget
        self.templates_list = QListWidget()
        self.templates_list.itemSelectionChanged.connect(self.on_template_selected)
        self.templates_list.itemDoubleClicked.connect(self.edit_selected_template)
        layout.addWidget(self.templates_list)
        
        # Template count label
        self.template_count_label = QLabel()
        layout.addWidget(self.template_count_label)
        
        return panel
        
    def create_template_details_panel(self):
        """Create the template details panel."""
        panel, layout = self.create_form_section(_("Template Details"))
        
        # Create form layout for template info
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Template info fields
        self.name_label = QLabel("-")
        self.name_label.setWordWrap(True)
        form_layout.addRow(_("Name:"), self.name_label)
        
        self.id_label = QLabel("-")
        form_layout.addRow(_("ID:"), self.id_label)
        
        self.version_label = QLabel("-")
        form_layout.addRow(_("Version:"), self.version_label)
        
        self.author_label = QLabel("-")
        form_layout.addRow(_("Author:"), self.author_label)
        
        self.category_label = QLabel("-")
        form_layout.addRow(_("Category:"), self.category_label)
        
        layout.addWidget(form_widget)
        
        # Description
        desc_label = QLabel(_("Description:"))
        layout.addWidget(desc_label)
        
        self.description_text = self.create_text_input(_("No description available"))
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)
        layout.addWidget(self.description_text)
        
        # Template content preview
        content_label = QLabel(_("Template Content (Preview):"))
        layout.addWidget(content_label)
        
        self.template_content_preview = self.create_text_input(_("No template selected"))
        self.template_content_preview.setReadOnly(True)
        self.template_content_preview.setFont(self.font_manager.get_font(9, family="Consolas"))
        layout.addWidget(self.template_content_preview)
        
        return panel
        
    def refresh_templates_list(self):
        """Refresh the templates list from template manager."""
        try:
            # Clear current list
            self.templates_list.clear()
            self.current_template = None
            
            # Get templates from manager
            templates = self.template_manager.get_template_list()
            
            # Sort templates by name
            templates.sort(key=lambda t: t.get('name', t.get('id', '')))
            
            # Add templates to list
            for template_info in templates:
                item = QListWidgetItem()
                template_id = template_info.get('id', 'unknown')
                template_name = template_info.get('name', template_id)
                item.setText(f"{template_name} ({template_id})")
                item.setData(Qt.ItemDataRole.UserRole, template_id)
                
                # Add tooltip with description
                description = template_info.get('description', '')
                if description:
                    item.setToolTip(f"{template_name}\n\n{description}")
                else:
                    item.setToolTip(template_name)
                    
                self.templates_list.addItem(item)
            
            # Update count
            count = len(templates)
            self.template_count_label.setText(_("Total templates: {}").format(count))
            
            # Clear details
            self.clear_template_details()
            self.update_buttons_state()
            
            self.logger.info(f"Templates list refreshed: {count} templates")
            
        except Exception as e:
            self.logger.error(f"Error refreshing templates list: {e}")
            QMessageBox.critical(self, _("Error"), _("Failed to refresh templates list: {}").format(str(e)))
            
    def on_template_selected(self):
        """Handle template selection."""
        selected_items = self.templates_list.selectedItems()
        if not selected_items:
            self.current_template = None
            self.clear_template_details()
            self.update_buttons_state()
            return
            
        item = selected_items[0]
        template_id = item.data(Qt.ItemDataRole.UserRole)
        
        try:
            # Get template from manager
            template_config = self.template_manager.get_template(template_id)
            if template_config:
                self.current_template = template_config
                self.display_template_details(template_config)
            else:
                self.current_template = None
                self.clear_template_details()
                
        except Exception as e:
            self.logger.error(f"Error loading template {template_id}: {e}")
            self.current_template = None
            self.clear_template_details()
            
        self.update_buttons_state()
        
    def display_template_details(self, template_config: TemplateConfig):
        """Display template details in the right panel."""
        try:
            # Update labels using flat attributes
            self.name_label.setText(template_config.name or "-")
            self.id_label.setText(template_config.template_id or "-")
            self.version_label.setText(template_config.version or "-")
            self.author_label.setText(template_config.author or "-")
            self.category_label.setText(template_config.category or "-")
            
            # Description
            description = template_config.description or _("No description available")
            self.description_text.setText(description)
            
            # Template content preview (first 500 characters)
            content = template_config.template_content or ""
            if len(content) > 500:
                preview = content[:500] + "\n\n..." + _("(Content truncated)")
            else:
                preview = content
                
            self.template_content_preview.setText(preview)
            
        except Exception as e:
            self.logger.error(f"Error displaying template details: {e}")
            self.clear_template_details()
            
    def clear_template_details(self):
        """Clear template details display."""
        self.name_label.setText("-")
        self.id_label.setText("-")
        self.version_label.setText("-")
        self.author_label.setText("-")
        self.category_label.setText("-")
        self.description_text.clear()
        self.template_content_preview.clear()
        
    def update_buttons_state(self):
        """Update button states based on selection."""
        has_selection = self.current_template is not None
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
    def create_new_template(self):
        """Create a new template."""
        try:
            from ui.widgets.template_editor_dialog import TemplateEditorDialog
            from core.llm.templates.config import create_default_template
            
            # Create default template
            new_template = create_default_template()
            new_template.template_id = "new_template"
            new_template.name = "New Template"
            
            # Open editor
            dialog = TemplateEditorDialog(new_template, self)
            dialog.template_saved.connect(self.on_template_saved)
            
            if dialog.exec():
                # Template was saved, refresh list
                self.refresh_templates_list()
                
        except Exception as e:
            self.logger.error(f"Error creating new template: {e}")
            QMessageBox.critical(self, _("Error"), _("Failed to create new template: {}").format(str(e)))
            
    def edit_selected_template(self):
        """Edit the selected template."""
        if not self.current_template:
            return
            
        try:
            from ui.widgets.template_editor_dialog import TemplateEditorDialog
            
            # Open editor with current template
            dialog = TemplateEditorDialog(self.current_template, self)
            dialog.template_saved.connect(self.on_template_saved)
            
            if dialog.exec():
                # Template was saved, refresh details
                self.on_template_selected()  # Refresh current template details
                
        except Exception as e:
            self.logger.error(f"Error editing template: {e}")
            QMessageBox.critical(self, _("Error"), _("Failed to edit template: {}").format(str(e)))
            
    def delete_selected_template(self):
        """Delete the selected template."""
        if not self.current_template:
            return
            
        template_name = self.current_template.name
        template_id = self.current_template.template_id
        
        # Confirmation dialog
        result = QMessageBox.question(
            self,
            _("Delete Template"),
            _("Are you sure you want to delete template '{}'?\n\nThis action cannot be undone.").format(template_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
            
        try:
            # Delete from template manager
            success = self.template_manager.remove_template(template_id)
            
            if success:
                QMessageBox.information(
                    self,
                    _("Success"),
                    _("Template '{}' deleted successfully.").format(template_name)
                )
                # Refresh list
                self.refresh_templates_list()
            else:
                QMessageBox.warning(
                    self,
                    _("Warning"),
                    _("Failed to delete template '{}'.").format(template_name)
                )
                
        except Exception as e:
            self.logger.error(f"Error deleting template {template_id}: {e}")
            QMessageBox.critical(self, _("Error"), _("Failed to delete template: {}").format(str(e)))
            
    def on_template_saved(self, template_id: str):
        """Handle template saved signal."""
        self.logger.info(f"Template saved: {template_id}")
        # Refresh the templates list to show changes
        self.refresh_templates_list()