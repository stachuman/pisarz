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
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Optional, Dict, Any

from core.logging_config import get_logger
from core.llm.templates import get_template_manager, EnhancedTemplateConfig
from i18n import _


class TemplatesListDialog(QDialog):
    """Dialog for managing templates list."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("ui.templates_list")
        self.template_manager = get_template_manager()
        self.current_template = None
        
        self.setWindowTitle(_("Templates Manager"))
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self.setup_ui()
        self.refresh_templates_list()
        
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(_("Templates Manager"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Templates list
        left_panel = self.create_templates_list_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Template details
        right_panel = self.create_template_details_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([350, 650])
        
        # Button bar
        button_layout = QHBoxLayout()
        
        # Left side buttons
        new_btn = QPushButton(_("New Template"))
        new_btn.clicked.connect(self.create_new_template)
        button_layout.addWidget(new_btn)
        
        edit_btn = QPushButton(_("Edit Template"))
        edit_btn.clicked.connect(self.edit_selected_template)
        button_layout.addWidget(edit_btn)
        self.edit_btn = edit_btn
        
        delete_btn = QPushButton(_("Delete Template"))
        delete_btn.clicked.connect(self.delete_selected_template)
        button_layout.addWidget(delete_btn)
        self.delete_btn = delete_btn
        
        button_layout.addStretch()
        
        # Right side buttons
        refresh_btn = QPushButton(_("Refresh"))
        refresh_btn.clicked.connect(self.refresh_templates_list)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton(_("Close"))
        close_btn.clicked.connect(self.close)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Initially disable edit/delete buttons
        self.update_buttons_state()
        
    def create_templates_list_panel(self):
        """Create the templates list panel."""
        panel = QGroupBox(_("Available Templates"))
        layout = QVBoxLayout(panel)
        
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
        panel = QGroupBox(_("Template Details"))
        layout = QVBoxLayout(panel)
        
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
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)
        layout.addWidget(self.description_text)
        
        # Template content preview
        content_label = QLabel(_("Template Content (Preview):"))
        layout.addWidget(content_label)
        
        self.template_content_preview = QTextEdit()
        self.template_content_preview.setReadOnly(True)
        self.template_content_preview.setFont(QFont("Consolas", 9))
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
        
    def display_template_details(self, template_config: EnhancedTemplateConfig):
        """Display template details in the right panel."""
        try:
            metadata = template_config.metadata
            
            # Update labels
            self.name_label.setText(metadata.name or "-")
            self.id_label.setText(metadata.template_id or "-")
            self.version_label.setText(metadata.version or "-")
            self.author_label.setText(metadata.author or "-")
            self.category_label.setText(metadata.category or "-")
            
            # Description
            description = metadata.description or _("No description available")
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
            new_template.metadata.template_id = "new_template"
            new_template.metadata.name = "New Template"
            
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
            
        template_name = self.current_template.metadata.name
        template_id = self.current_template.metadata.template_id
        
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