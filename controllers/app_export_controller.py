"""
Export controller following existing controller pattern.
Manages export operations and integrates with the main application.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QFileDialog

from .app_project_controller import AppProjectController
from core.export import (
    ExportEngine, ExportDataManager, ExportScope, ExportConfig,
    ExportScopeType, ExportFormat
)
from core.error_handler import get_error_handler, ErrorLevel, ErrorCategory
from ui.widgets.export_dialog import ExportDialog
from i18n import _


class AppExportController(QObject):
    """Export controller following existing controller pattern"""
    
    # Signals
    exportStarted = Signal(str)           # format
    exportCompleted = Signal(str, str)    # format, output_path
    exportFailed = Signal(str, str)       # format, error_message
    statusMessage = Signal(str)           # message
    errorOccurred = Signal(str, str)      # title, message
    
    def __init__(self, parent, project_controller: AppProjectController):
        super().__init__(parent)
        self.project_controller = project_controller
        self.export_engine = ExportEngine()
        self.error_handler = get_error_handler()
        self.logger = logging.getLogger(__name__)
        
        # Current export dialog
        self.export_dialog = None
    
    def show_export_dialog(self):
        """Show export dialog"""
        try:
            # Check if project is loaded
            if not self.project_controller.has_current_project():
                self.errorOccurred.emit(
                    "Export Error",
                    "Please load a project before exporting"
                )
                return
            
            # Create and show export dialog
            self.export_dialog = ExportDialog(self.project_controller, self.parent())
            
            # Connect dialog signals
            self.export_dialog.exportStarted.connect(self.on_dialog_export_started)
            self.export_dialog.exportCompleted.connect(self.on_dialog_export_completed)
            self.export_dialog.exportFailed.connect(self.on_dialog_export_failed)
            
            # Show dialog
            self.export_dialog.exec()
            
        except Exception as e:
            self.logger.error(f"Failed to show export dialog: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.UI,
                "Failed to show export dialog"
            )
            self.errorOccurred.emit("Error", f"Failed to open export dialog: {str(e)}")
    
    def quick_export_pdf(self):
        """Quick export current project to PDF"""
        self._quick_export(ExportFormat.PDF)
    
    def quick_export_txt(self):
        """Quick export current project to TXT"""
        self._quick_export(ExportFormat.TXT)
    
    def quick_export_scene_pdf(self, scene_id: int):
        """Quick export specific scene to PDF"""
        self._quick_export(ExportFormat.PDF, scene_ids=[scene_id])
    
    def quick_export_scene_txt(self, scene_id: int):
        """Quick export specific scene to TXT"""
        self._quick_export(ExportFormat.TXT, scene_ids=[scene_id])
    
    def _quick_export(self, format_type: ExportFormat, scene_ids: Optional[list] = None):
        """Perform quick export with minimal user interaction"""
        try:
            # Check if project is loaded
            if not self.project_controller.has_current_project():
                self.errorOccurred.emit(
                    "Export Error",
                    "Please load a project before exporting"
                )
                return
            
            # Check if format is supported
            if not self.export_engine.is_format_supported(format_type):
                self.errorOccurred.emit(
                    "Export Error",
                    f"Export format {format_type.value.upper()} is not available"
                )
                return
            
            # Get project info for filename
            project_name = self.project_controller.get_project_name()
            if not project_name:
                project_name = "export"
            
            # Get file extension
            exporter = self.export_engine.get_exporter(format_type)
            extension = exporter.get_output_extension()
            
            # Create default filename
            safe_name = self._sanitize_filename(project_name)
            if scene_ids and len(scene_ids) == 1:
                safe_name += f"_scene_{scene_ids[0]}"
            
            default_filename = f"{safe_name}{extension}"
            
            # Show file dialog
            format_name = format_type.value.upper()
            file_filter = f"{format_name} Files (*{extension});;All Files (*.*)"
            
            output_path, _ = QFileDialog.getSaveFileName(
                self.parent(),
                f"Quick Export to {format_name}",
                str(Path.home() / "Documents" / default_filename),
                file_filter
            )
            
            if not output_path:
                return  # User cancelled
            
            # Create export configuration
            config = self._create_quick_export_config(format_type, output_path, scene_ids)
            if not config:
                return
            
            # Perform export
            self.export_with_config(config)
            
        except Exception as e:
            self.logger.error(f"Quick export failed: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.EXPORT,
                f"Quick export to {format_type.value} failed"
            )
            self.errorOccurred.emit("Export Error", f"Quick export failed: {str(e)}")
    
    def _create_quick_export_config(self, format_type: ExportFormat, 
                                   output_path: str, scene_ids: Optional[list] = None) -> Optional[ExportConfig]:
        """Create export configuration for quick export"""
        try:
            project_id = self.project_controller.get_project_id()
            if not project_id:
                return None
            
            # Determine scope type
            if scene_ids:
                scope_type = ExportScopeType.CURRENT_SCENE if len(scene_ids) == 1 else ExportScopeType.SELECTED_SCENES
            else:
                scope_type = ExportScopeType.ALL_SCENES
            
            # Create export scope
            scope = ExportScope(
                project_id=project_id,
                scope_type=scope_type,
                scene_ids=scene_ids,
                include_characters=True,
                include_locations=True,
                include_metadata=True
            )
            
            # Create export config
            config = ExportConfig(
                scope=scope,
                format=format_type,
                output_path=output_path
            )
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to create export config: {e}")
            return None
    
    def export_with_config(self, config: ExportConfig):
        """Perform export with given configuration"""
        try:
            self.logger.info(f"Starting export to {config.format.value}")
            
            # Emit export started signal
            self.exportStarted.emit(config.format.value)
            self.statusMessage.emit(f"Exporting to {config.format.value.upper()}...")
            
            # Create data manager
            data_manager = ExportDataManager(self.project_controller)
            
            # Perform export
            result = self.export_engine.export_document(data_manager, config)
            
            # Handle result
            if result.success:
                self.logger.info(f"Export completed: {result.output_path}")
                self.exportCompleted.emit(config.format.value, result.output_path or "")
                
                success_msg = "Export completed successfully!"
                if result.output_path:
                    success_msg += f"\nFile saved to: {result.output_path}"
                
                self.statusMessage.emit("Export completed")
                
                # Show success message with option to open file
                reply = QMessageBox.information(
                    self.parent(),
                    "Export Complete",
                    success_msg,
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open
                )
                
                # Open file if requested
                if reply == QMessageBox.StandardButton.Open and result.output_path:
                    self._open_file(result.output_path)
                    
            else:
                error_msg = result.error_message or "Export failed for unknown reason"
                self.logger.error(f"Export failed: {error_msg}")
                self.exportFailed.emit(config.format.value, error_msg)
                self.statusMessage.emit("Export failed")
                
                QMessageBox.critical(
                    self.parent(),
                    "Export Failed",
                    error_msg
                )
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.EXPORT,
                f"Export to {config.format.value} failed"
            )
            
            self.exportFailed.emit(config.format.value, error_msg)
            self.statusMessage.emit("Export failed")
            
            QMessageBox.critical(
                self.parent(),
                "Export Error",
                f"Export failed: {str(e)}"
            )
    
    def get_supported_formats(self) -> list:
        """Get list of supported export formats"""
        try:
            formats = self.export_engine.get_supported_formats()
            return [fmt.value for fmt in formats]
        except Exception as e:
            self.logger.error(f"Failed to get supported formats: {e}")
            return []
    
    def is_format_supported(self, format_name: str) -> bool:
        """Check if export format is supported"""
        try:
            format_enum = ExportFormat(format_name.lower())
            return self.export_engine.is_format_supported(format_enum)
        except (ValueError, Exception):
            return False
    
    def get_export_info(self) -> dict:
        """Get information about export capabilities"""
        try:
            return {
                'supported_formats': self.get_supported_formats(),
                'engine_stats': self.export_engine.get_export_statistics(),
                'project_loaded': self.project_controller.has_current_project()
            }
        except Exception as e:
            self.logger.error(f"Failed to get export info: {e}")
            return {'supported_formats': [], 'engine_stats': {}, 'project_loaded': False}
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem safety"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip(' .')
    
    def _open_file(self, file_path: str):
        """Open file with system default application"""
        try:
            import subprocess
            import platform
            import os
            
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux and others
                subprocess.run(["xdg-open", file_path])
                
        except Exception as e:
            self.logger.warning(f"Failed to open file {file_path}: {e}")
            QMessageBox.information(
                self.parent(),
                "File Exported",
                f"File exported successfully to:\n{file_path}"
            )
    
    # Dialog event handlers
    def on_dialog_export_started(self):
        """Handle export started from dialog"""
        self.statusMessage.emit("Exporting document...")
    
    def on_dialog_export_completed(self, output_path: str):
        """Handle export completed from dialog"""
        self.statusMessage.emit("Export completed")
        
        # Extract format from output path extension
        extension = Path(output_path).suffix.lower()
        format_name = "unknown"
        if extension == ".pdf":
            format_name = "pdf"
        elif extension == ".txt":
            format_name = "txt"
        elif extension == ".html":
            format_name = "html"
        elif extension == ".docx":
            format_name = "docx"
        
        self.exportCompleted.emit(format_name, output_path)
    
    def on_dialog_export_failed(self, error_message: str):
        """Handle export failed from dialog"""
        self.statusMessage.emit("Export failed")
        self.exportFailed.emit("unknown", error_message)