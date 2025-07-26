"""Template UI Manager for handling template-related UI operations."""

from typing import Optional
from PySide6.QtWidgets import QWidget, QComboBox, QMessageBox
from PySide6.QtCore import Qt, QObject, Signal

from core.logging_config import get_logger
from i18n import _


class TemplateUIManager(QObject):
    """Manages template-related UI operations and interactions."""
    
    template_saved = Signal(str)  # template_id
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = get_logger("ui.template_manager")
        self.parent_widget = parent
    
    def load_available_templates(self, task_combo: QComboBox):
        """Load available templates from template manager into dropdown."""
        try:
            from core.llm.templates import get_template_manager
            
            template_manager = get_template_manager()
            template_list = template_manager.get_template_list()
            
            # Remember current selection
            current_template_id = task_combo.currentData()
            
            # Clear existing templates (but keep edit templates option that will be added later)
            task_combo.clear()
            
            # Add custom prompt option first
            task_combo.addItem("🎯 " + _("Custom Prompt..."), "custom_prompt")
            task_combo.setItemData(
                task_combo.count() - 1,
                _("Create a custom prompt with configurable context and parameters"),
                Qt.ItemDataRole.ToolTipRole
            )
            
            # Add separator
            task_combo.insertSeparator(task_combo.count())
            
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
                
                task_combo.addItem(display_name, template_id)
                
                # Set tooltip with description
                if template_description:
                    task_combo.setItemData(
                        task_combo.count() - 1,
                        template_description,
                        Qt.ItemDataRole.ToolTipRole
                    )
            
            # Restore previous selection if it exists
            if current_template_id:
                for i in range(task_combo.count()):
                    if task_combo.itemData(i) == current_template_id:
                        task_combo.setCurrentIndex(i)
                        break
            else:
                # If no previous selection and we have templates, select the first real template (skip custom_prompt and separator)
                if len(template_list) > 0:
                    for i in range(task_combo.count()):
                        item_data = task_combo.itemData(i)
                        if item_data and item_data != "custom_prompt":
                            task_combo.setCurrentIndex(i)
                            self.logger.debug(f"Auto-selected first template: {item_data}")
                            break
            
            self.logger.info(f"Loaded {len(template_list)} templates into dropdown")
            
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            # Fallback to default option
            task_combo.addItem(_("📝 Continue Scene"), "continue_scene")
    
    def edit_selected_template(self, task_combo: QComboBox):
        """Edit the currently selected template."""
        try:
            selected_template_id = task_combo.currentData()
            if not selected_template_id:
                self._show_error(_("No Template Selected"), _("Please select a template to edit."))
                return
            
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            template_config = template_manager.get_template(selected_template_id)
            
            if not template_config:
                self._show_error(_("Template Not Found"), _("The selected template could not be found."))
                return
            
            # Open template editor with selected template
            from ui.widgets.template_editor_dialog import TemplateEditorDialog
            dialog = TemplateEditorDialog(template_config, self.parent_widget)
            
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
                    self._show_error(_("Save Error"), _("Failed to save template to file."))
            
        except Exception as e:
            self.logger.error(f"Error opening template editor: {e}")
            self._show_error(_("Error"), _("Failed to open template editor: {}").format(str(e)))
    
    def on_template_saved(self, template_id: str):
        """Handle template saved signal."""
        self.logger.info(f"Template saved: {template_id}")
        # Emit signal for parent to handle
        self.template_saved.emit(template_id)
    
    def refresh_templates(self, task_combo: QComboBox, status_callback=None):
        """Refresh templates from disk."""
        try:
            from core.llm.templates import get_template_manager
            
            # Refresh templates in the manager
            template_manager = get_template_manager()
            template_manager.refresh_templates()
            
            # Reload UI
            self.load_available_templates(task_combo)
            
            if status_callback:
                status_callback(_("✅ Templates refreshed"), "success")
            self.logger.info("Templates refreshed successfully")
            
        except Exception as e:
            self.logger.error(f"Error refreshing templates: {e}")
            if status_callback:
                status_callback(_("❌ Failed to refresh templates"), "error")
    
    def _show_error(self, title: str, message: str):
        """Show error message dialog."""
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, title, message)
        else:
            # Fallback to creating temporary widget
            temp_widget = QWidget()
            QMessageBox.critical(temp_widget, title, message)