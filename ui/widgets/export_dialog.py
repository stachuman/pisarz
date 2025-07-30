"""
Export dialog for document and project data export.
Extends BaseDialog for consistent UI and integrates with export system.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QRadioButton, QCheckBox,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton, QLabel,
    QButtonGroup, QFileDialog, QMessageBox, QProgressDialog,
    QGroupBox, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from ui.base.base_dialog import BaseDialog
from controllers.app_project_controller import AppProjectController
from core.export import (
    ExportEngine, ExportDataManager, ExportScope, ExportConfig, 
    ExportResult, ExportScopeType, ExportFormat
)
from i18n import _


class ExportWorkerThread(QThread):
    """Worker thread for export operations to prevent UI blocking"""
    
    finished = Signal(object)  # ExportResult
    progress = Signal(str)     # Status message
    
    def __init__(self, data_manager: ExportDataManager, config: ExportConfig):
        super().__init__()
        self.data_manager = data_manager
        self.config = config
        self.export_engine = ExportEngine()
    
    def run(self):
        """Run export operation in background thread"""
        try:
            self.progress.emit(_("Preparing export data..."))
            
            # Perform the export
            result = self.export_engine.export_document(self.data_manager, self.config)
            
            self.finished.emit(result)
            
        except Exception as e:
            # Create error result
            from core.export.models import ExportResult
            error_result = ExportResult(
                success=False,
                error_message=str(e),
                format_used=self.config.format
            )
            self.finished.emit(error_result)


class ExportDialog(BaseDialog):
    """Export dialog extending BaseDialog for consistent UI"""
    
    # Signals
    exportStarted = Signal()
    exportCompleted = Signal(str)  # output_path
    exportFailed = Signal(str)     # error_message
    
    def __init__(self, project_controller: AppProjectController, parent=None):
        super().__init__(
            title=_("Export Document"),
            width=800,
            height=600,
            modal=True,
            parent=parent
        )
        
        self.project_controller = project_controller
        self.export_engine = ExportEngine()
        self.export_thread = None
        self.progress_dialog = None
        
        # UI state
        self.selected_format = ExportFormat.PDF
        self.selected_scope = ExportScopeType.ALL_SCENES
        self.selected_scene_ids = []
        
        # Validate project is loaded
        if not self.project_controller.has_current_project():
            QMessageBox.critical(self, _("Error"), _("No project is currently loaded"))
            self.reject()
            return
        
        self.setup_export_ui()
        self.load_project_data()
    
    def setup_export_ui(self):
        """Setup export dialog UI using BaseDialog methods"""
        
        # Main title
        title = self.create_section_title(_("Export Document"), 16)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_content_widget(title)
        
        # Create tab widget for different sections
        self.tabs = self.create_tab_widget()
        
        # Create tabs
        self.format_tab = self.create_format_selection()
        self.scope_tab = self.create_scope_selection()
        self.options_tab = self.create_output_options()
        
        # Add tabs
        self.tabs.addTab(self.format_tab, _("Format"))
        self.tabs.addTab(self.scope_tab, _("Content"))
        self.tabs.addTab(self.options_tab, _("Output"))
        
        self.add_content_widget(self.tabs)
        
        # Create buttons
        self.create_export_buttons()
    
    def create_format_selection(self) -> QWidget:
        """Create format selection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Format selection group
        format_group, format_layout = self.create_form_section(_("Export Format"))
        
        # Get supported formats from engine
        supported_formats = self.export_engine.get_supported_formats()
        format_info = self.export_engine.get_format_info()
        
        # Create radio button group for formats
        self.format_button_group = QButtonGroup()
        
        for i, export_format in enumerate(supported_formats):
            # Create radio button
            format_name = export_format.value.upper()
            radio_btn = QRadioButton(format_name)
            
            # Add description if available
            info = format_info.get(export_format, {})
            description = info.get('description', '')
            extension = info.get('extension', '')
            
            if description:
                tooltip_text = f"{description}\nFile extension: {extension}"
                radio_btn.setToolTip(tooltip_text)
            
            # Set default selection (PDF if available, otherwise first)
            if export_format == ExportFormat.PDF or i == 0:
                radio_btn.setChecked(True)
                self.selected_format = export_format
            
            # Connect signal
            radio_btn.toggled.connect(lambda checked, fmt=export_format: self.on_format_changed(fmt, checked))
            
            self.format_button_group.addButton(radio_btn, i)
            format_layout.addRow(radio_btn)
            
            # Add description label
            if description:
                desc_label = self.create_info_label(description, "muted")
                desc_label.setIndent(20)
                format_layout.addRow("", desc_label)
        
        layout.addWidget(format_group)
        layout.addStretch()
        
        return widget
    
    def create_scope_selection(self) -> QWidget:
        """Create export scope selection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scope selection group
        scope_group, scope_layout = self.create_form_section(_("What to Export"))
        
        # Create radio button group for scope
        self.scope_button_group = QButtonGroup()
        
        # All scenes option
        self.all_scenes_radio = QRadioButton(_("All Scenes"))
        self.all_scenes_radio.setChecked(True)
        self.all_scenes_radio.toggled.connect(lambda checked: self.on_scope_changed(ExportScopeType.ALL_SCENES, checked))
        self.scope_button_group.addButton(self.all_scenes_radio, 0)
        scope_layout.addRow(self.all_scenes_radio)
        
        # Selected scenes option
        self.selected_scenes_radio = QRadioButton(_("Selected Scenes"))
        self.selected_scenes_radio.toggled.connect(lambda checked: self.on_scope_changed(ExportScopeType.SELECTED_SCENES, checked))
        self.scope_button_group.addButton(self.selected_scenes_radio, 1)
        scope_layout.addRow(self.selected_scenes_radio)
        
        # Full project option
        self.full_project_radio = QRadioButton(_("Full Project (including characters and locations)"))
        self.full_project_radio.toggled.connect(lambda checked: self.on_scope_changed(ExportScopeType.FULL_PROJECT, checked))
        self.scope_button_group.addButton(self.full_project_radio, 2)
        scope_layout.addRow(self.full_project_radio)
        
        layout.addWidget(scope_group)
        
        # Scene selection list (shown when "Selected Scenes" is chosen)
        scenes_group, scenes_layout = self.create_form_section(_("Select Scenes"))
        
        self.scene_list = self.create_selection_list_widget(
            selection_changed_callback=self.on_scene_selection_changed
        )
        self.scene_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.scene_list.setVisible(False)  # Hidden by default
        
        scenes_layout.addRow(self.scene_list)
        layout.addWidget(scenes_group)
        
        # Additional content options
        content_group, content_layout = self.create_form_section(_("Additional Content"))
        
        self.include_metadata_cb = QCheckBox(_("Include project metadata"))
        self.include_metadata_cb.setChecked(True)
        content_layout.addRow(self.include_metadata_cb)
        
        self.include_characters_cb = QCheckBox(_("Include character information"))
        self.include_characters_cb.setChecked(True)
        content_layout.addRow(self.include_characters_cb)
        
        self.include_locations_cb = QCheckBox(_("Include location information"))
        self.include_locations_cb.setChecked(True)
        content_layout.addRow(self.include_locations_cb)
        
        layout.addWidget(content_group)
        layout.addStretch()
        
        return widget
    
    def create_output_options(self) -> QWidget:
        """Create output path and file options tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Output file group
        output_group, output_layout = self.create_form_section(_("Output File"))
        
        # File path selection
        path_layout = QHBoxLayout()
        
        self.path_input = self.create_line_input(_("Choose output file path..."))
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)
        
        self.browse_btn = self.create_custom_button(_("Browse..."), self.browse_output_path, "secondary")
        path_layout.addWidget(self.browse_btn)
        
        output_layout.addRow(_("Output Path:"), path_layout)
        
        # Filename preview
        self.filename_label = QLabel()
        self.filename_label.setStyleSheet(self.get_muted_text_style())
        output_layout.addRow(_("Filename:"), self.filename_label)
        
        layout.addWidget(output_group)
        
        # Template selection (future feature)
        template_group, template_layout = self.create_form_section(_("Template"))
        
        template_info = self.create_info_label(
            _("Document templates will be available in future versions."),
            "muted"
        )
        template_layout.addRow(template_info)
        
        layout.addWidget(template_group)
        layout.addStretch()
        
        return widget
    
    def create_export_buttons(self):
        """Create export and cancel buttons"""
        # Create standard buttons with preview option
        buttons = self.create_standard_buttons(
            save_text=_("Export"),
            save_callback=self.start_export,
            extra_buttons=[
                (_("Preview"), self.preview_export, "secondary")
            ]
        )
        
        self.export_btn = buttons['save']
        self.preview_btn = buttons.get('preview')
        self.cancel_btn = buttons['cancel']
    
    def load_project_data(self):
        """Load current project data for UI"""
        try:
            # Get current project info
            project_id, project_name = self.project_controller.get_current_project_info()
            
            if not project_id:
                return
            
            # Load scenes for selection list
            managers = self.project_controller.get_current_managers()
            scene_manager = managers.get('scene_manager')
            
            if scene_manager:
                scenes = scene_manager.get_scenes_by_project(project_id)
                self.populate_scene_list(scenes)
            
            # Set default output filename
            self.update_output_filename()
            
        except Exception as e:
            self.logger.error(f"Failed to load project data: {e}")
    
    def populate_scene_list(self, scenes: List[Dict[str, Any]]):
        """Populate scene list widget"""
        self.scene_list.clear()
        
        for scene in scenes:
            scene_id = scene.get('id')
            scene_title = scene.get('title', f'Scene {scene_id}')
            word_count = scene.get('word_count', 0)
            
            # Create list item with scene info
            item_text = f"{scene_title}"
            if word_count > 0:
                item_text += f" ({word_count:,} words)"
                
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, scene_id)
            
            self.scene_list.addItem(item)
    
    def on_format_changed(self, format_type: ExportFormat, checked: bool):
        """Handle format selection change"""
        if checked:
            self.selected_format = format_type
            self.update_output_filename()
    
    def on_scope_changed(self, scope_type: ExportScopeType, checked: bool):
        """Handle scope selection change"""
        if checked:
            self.selected_scope = scope_type
            
            # Show/hide scene list based on selection
            show_scene_list = (scope_type == ExportScopeType.SELECTED_SCENES)
            self.scene_list.setVisible(show_scene_list)
            
            # Update additional content checkboxes availability
            is_full_project = (scope_type == ExportScopeType.FULL_PROJECT)
            if is_full_project:
                self.include_characters_cb.setChecked(True)
                self.include_locations_cb.setChecked(True)
    
    def on_scene_selection_changed(self):
        """Handle scene selection in list"""
        selected_items = self.scene_list.selectedItems()
        self.selected_scene_ids = []
        
        for item in selected_items:
            scene_id = item.data(Qt.ItemDataRole.UserRole)
            if scene_id:
                self.selected_scene_ids.append(scene_id)
    
    def browse_output_path(self):
        """Open file dialog for output path selection"""
        try:
            # Get file extension for current format
            exporter = self.export_engine.get_exporter(self.selected_format)
            if not exporter:
                QMessageBox.warning(self, "Warning", "Selected format is not available")
                return
            
            extension = exporter.get_output_extension()
            format_name = self.selected_format.value.upper()
            
            # Prepare file dialog
            project_name = self.project_controller.get_project_name()
            default_filename = self.sanitize_filename(project_name or "export")
            
            file_filter = f"{format_name} Files (*{extension});;All Files (*.*)"
            
            # Show file dialog
            output_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Save Export As",
                f"{default_filename}{extension}",
                file_filter
            )
            
            if output_path:
                # Ensure correct extension based on selected format
                if not output_path.endswith(extension):
                    output_path = output_path + extension
                
                self.path_input.setText(output_path)
                self.update_filename_display()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file dialog: {str(e)}")
    
    def update_output_filename(self):
        """Update default output filename based on current settings"""
        try:
            project_name = self.project_controller.get_project_name()
            if not project_name:
                return
            
            # Get extension for current format
            exporter = self.export_engine.get_exporter(self.selected_format)
            if not exporter:
                return
                
            extension = exporter.get_output_extension()
            
            # Create default filename
            safe_name = self.sanitize_filename(project_name)
            filename = f"{safe_name}{extension}"
            
            self.filename_label.setText(filename)
            
            # Update existing path if it exists
            current_path = self.path_input.text()
            if current_path:
                # Replace extension in existing path
                path_obj = Path(current_path)
                new_path = path_obj.with_suffix(extension)
                self.path_input.setText(str(new_path))
            else:
                # Set default path
                default_path = str(Path.home() / "Documents" / filename)
                self.path_input.setText(default_path)
                
        except Exception as e:
            self.logger.error(f"Failed to update filename: {e}")
    
    def update_filename_display(self):
        """Update filename display based on current path"""
        path = self.path_input.text()
        if path:
            filename = Path(path).name
            self.filename_label.setText(filename)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem safety"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip(' .')
    
    def preview_export(self):
        """Show export preview (basic implementation)"""
        try:
            # Create export config for validation
            config = self.build_export_config()
            if not config:
                return
            
            # Show preview dialog with export summary
            preview_text = self.build_preview_text(config)
            
            # Create simple preview dialog
            preview_dialog = QMessageBox(self)
            preview_dialog.setWindowTitle(_("Export Preview"))
            preview_dialog.setText(_("Export Summary"))
            preview_dialog.setDetailedText(preview_text)
            preview_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            preview_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to generate preview: {}").format(str(e)))
    
    def build_preview_text(self, config: ExportConfig) -> str:
        """Build preview text for export configuration"""
        lines = []
        
        lines.append(f"Format: {config.format.value.upper()}")
        lines.append(f"Output: {config.output_path}")
        lines.append(f"Scope: {config.scope.scope_type.value.replace('_', ' ').title()}")
        
        if config.scope.scene_ids:
            lines.append(f"Selected Scenes: {len(config.scope.scene_ids)}")
        
        lines.append(f"Include Metadata: {'Yes' if config.scope.include_metadata else 'No'}")
        lines.append(f"Include Characters: {'Yes' if config.scope.include_characters else 'No'}")
        lines.append(f"Include Locations: {'Yes' if config.scope.include_locations else 'No'}")
        
        return "\n".join(lines)
    
    def start_export(self):
        """Validate inputs and start export process"""
        try:
            # Validate export configuration
            errors = self.validate_export_config()
            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.critical(self, _("Export Error"), error_msg)
                return
            
            # Build export configuration
            config = self.build_export_config()
            if not config:
                return
            
            # Create data manager
            data_manager = ExportDataManager(self.project_controller)
            
            # Start export in background thread
            self.export_thread = ExportWorkerThread(data_manager, config)
            self.export_thread.finished.connect(self.on_export_finished)
            self.export_thread.progress.connect(self.on_export_progress)
            
            # Show progress dialog
            self.progress_dialog = QProgressDialog(_("Exporting document..."), _("Cancel"), 0, 0, self)
            self.progress_dialog.setModal(True)
            self.progress_dialog.canceled.connect(self.cancel_export)
            self.progress_dialog.show()
            
            # Disable export button during export
            self.export_btn.setEnabled(False)
            
            # Start export
            self.exportStarted.emit()
            self.export_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to start export: {}").format(str(e)))
    
    def validate_export_config(self) -> List[str]:
        """Validate all export settings"""
        errors = []
        
        # Check output path
        if not self.path_input.text().strip():
            errors.append(_("Please specify an output file path"))
        else:
            output_path = Path(self.path_input.text().strip())
            output_dir = output_path.parent
            
            if not output_dir.exists():
                errors.append(_("Output directory does not exist: {}").format(str(output_dir)))
            elif not os.access(output_dir, os.W_OK):
                errors.append(_("Output directory is not writable: {}").format(str(output_dir)))
        
        # Check selected scenes if needed
        if self.selected_scope == ExportScopeType.SELECTED_SCENES:
            if not self.selected_scene_ids:
                errors.append(_("Please select at least one scene to export"))
        
        # Check format availability
        if not self.export_engine.get_exporter(self.selected_format):
            errors.append(_("Selected export format is not available"))
        
        return errors
    
    def build_export_config(self) -> Optional[ExportConfig]:
        """Build ExportConfig from dialog inputs"""
        try:
            # Build export scope
            scope = self.build_export_scope()
            if not scope:
                return None
            
            # Create export configuration
            config = ExportConfig(
                scope=scope,
                format=self.selected_format,
                output_path=self.path_input.text().strip()
            )
            
            return config
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to build export configuration: {}").format(str(e)))
            return None
    
    def build_export_scope(self) -> Optional[ExportScope]:
        """Build ExportScope from dialog inputs"""
        try:
            project_id = self.project_controller.get_project_id()
            if not project_id:
                QMessageBox.critical(self, _("Error"), _("No project loaded"))
                return None
            
            # Determine scene IDs based on scope
            scene_ids = None
            if self.selected_scope == ExportScopeType.SELECTED_SCENES:
                scene_ids = self.selected_scene_ids
            
            # Create export scope
            scope = ExportScope(
                project_id=project_id,
                scope_type=self.selected_scope,
                scene_ids=scene_ids,
                include_characters=self.include_characters_cb.isChecked(),
                include_locations=self.include_locations_cb.isChecked(),
                include_metadata=self.include_metadata_cb.isChecked()
            )
            
            return scope
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to build export scope: {}").format(str(e)))
            return None
    
    def on_export_progress(self, message: str):
        """Handle export progress updates"""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)
    
    def on_export_finished(self, result: ExportResult):
        """Handle export completion"""
        try:
            # Close progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            
            # Re-enable export button
            self.export_btn.setEnabled(True)
            
            # Handle result
            if result.success:
                # Show success message
                msg = _("Export completed successfully!")
                if result.output_path:
                    msg += f"\n\n{_('File saved to:')}\n{result.output_path}"
                if result.exported_items_count > 0:
                    msg += f"\n\n{_('Exported items:')}: {result.exported_items_count}"
                if result.file_size_bytes > 0:
                    msg += f"\n{_('File size:')}: {result.file_size_mb:.2f} MB"
                
                reply = QMessageBox.information(
                    self, 
                    _("Export Complete"), 
                    msg,
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open
                )
                
                # Open file if requested
                if reply == QMessageBox.StandardButton.Open and result.output_path:
                    self.open_exported_file(result.output_path)
                
                self.exportCompleted.emit(result.output_path or "")
                self.accept()  # Close dialog on success
                
            else:
                # Show error message
                error_msg = result.error_message or _("Export failed for unknown reason")
                QMessageBox.critical(self, _("Export Failed"), error_msg)
                self.exportFailed.emit(error_msg)
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Error handling export result: {}").format(str(e)))
        finally:
            # Clean up thread
            if self.export_thread:
                self.export_thread.quit()
                self.export_thread.wait()
                self.export_thread = None
    
    def cancel_export(self):
        """Cancel ongoing export operation"""
        if self.export_thread and self.export_thread.isRunning():
            self.export_thread.quit()
            self.export_thread.wait()
        
        if self.progress_dialog:
            self.progress_dialog.close()
            
        self.export_btn.setEnabled(True)
    
    def open_exported_file(self, file_path: str):
        """Open exported file with system default application"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux and others
                subprocess.run(["xdg-open", file_path])
                
        except Exception as e:
            QMessageBox.warning(
                self,
                _("Warning"),
                _("File exported successfully but could not be opened automatically.\n\nFile location: {}").format(file_path)
            )
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Cancel any running export
        if self.export_thread and self.export_thread.isRunning():
            self.cancel_export()
        
        super().closeEvent(event)