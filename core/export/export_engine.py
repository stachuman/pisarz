"""
Core Export Engine - Plugin-based export system.
Manages exporter registration and orchestrates export operations.
"""

import logging
import time
from typing import Dict, List, Optional, Any

from .models import ExportConfig, ExportResult, ExportFormat, ExportData
from .exporters.base_exporter import BaseExporter
from .export_data_manager import ExportDataManager
from ..error_handler import get_error_handler, ErrorLevel, ErrorCategory


class ExportEngine:
    """
    Plugin-based export engine with exporter registration.
    Coordinates between data managers and format-specific exporters.
    """
    
    def __init__(self):
        """Initialize export engine with error handling and logging"""
        self.exporters: Dict[ExportFormat, BaseExporter] = {}
        self.error_handler = get_error_handler()
        self.logger = logging.getLogger(__name__)
        
        # Register default exporters
        self._register_default_exporters()
    
    def register_exporter(self, format_type: ExportFormat, exporter: BaseExporter):
        """
        Register an exporter for a specific format.
        
        Args:
            format_type: ExportFormat enum value
            exporter: BaseExporter implementation
        """
        try:
            # Validate that exporter supports the format
            if format_type not in exporter.get_supported_formats():
                raise ValueError(f"Exporter {exporter.__class__.__name__} does not support format {format_type.value}")
            
            self.exporters[format_type] = exporter
            
        except Exception as e:
            self.logger.error(f"Failed to register exporter: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.SYSTEM,
                f"Failed to register exporter for format {format_type.value}"
            )
    
    def get_supported_formats(self) -> List[ExportFormat]:
        """
        Get all supported export formats.
        
        Returns:
            List of ExportFormat enums for registered exporters
        """
        return list(self.exporters.keys())
    
    def get_exporter(self, format_type: ExportFormat) -> Optional[BaseExporter]:
        """
        Get exporter for a specific format.
        
        Args:
            format_type: ExportFormat to get exporter for
            
        Returns:
            BaseExporter instance, or None if not found
        """
        return self.exporters.get(format_type)
    
    def is_format_supported(self, format_type: ExportFormat) -> bool:
        """
        Check if a format is supported.
        
        Args:
            format_type: ExportFormat to check
            
        Returns:
            True if format is supported, False otherwise
        """
        return format_type in self.exporters
    
    def export_document(self, data_manager: ExportDataManager, 
                       config: ExportConfig) -> ExportResult:
        """
        Main export method - orchestrates the entire export process.
        
        Args:
            data_manager: ExportDataManager instance for data access
            config: ExportConfig with export parameters
            
        Returns:
            ExportResult with operation outcome
        """
        start_time = time.time()
        
        try:
            
            # Validate configuration
            config_errors = self.validate_export_config(config)
            if config_errors:
                error_msg = f"Invalid export configuration: {'; '.join(config_errors)}"
                self.logger.error(error_msg)
                return ExportResult(
                    success=False,
                    error_message=error_msg,
                    format_used=config.format,
                    duration_seconds=time.time() - start_time
                )
            
            # Get the appropriate exporter
            exporter = self.get_exporter(config.format)
            if not exporter:
                error_msg = f"No exporter available for format {config.format.value}"
                self.logger.error(error_msg)
                return ExportResult(
                    success=False,
                    error_message=error_msg,
                    format_used=config.format,
                    duration_seconds=time.time() - start_time
                )
            
            # Get export data
            export_data = data_manager.get_export_data(config.scope)
            if not export_data:
                error_msg = "Failed to retrieve export data"
                self.logger.error(error_msg)
                return ExportResult(
                    success=False,
                    error_message=error_msg,
                    format_used=config.format,
                    duration_seconds=time.time() - start_time
                )
            
            # Validate export data
            data_errors = exporter.validate_data(export_data)
            if data_errors:
                error_msg = f"Invalid export data: {'; '.join(data_errors)}"
                self.logger.error(error_msg)
                return ExportResult(
                    success=False,
                    error_message=error_msg,
                    format_used=config.format,
                    duration_seconds=time.time() - start_time
                )
            
            # Validate exporter-specific configuration
            exporter_config_errors = exporter.validate_config(config)
            if exporter_config_errors:
                error_msg = f"Invalid exporter configuration: {'; '.join(exporter_config_errors)}"
                self.logger.error(error_msg)
                return ExportResult(
                    success=False,
                    error_message=error_msg,
                    format_used=config.format,
                    duration_seconds=time.time() - start_time
                )
            
            # Log export start
            exporter.log_export_start(config, export_data)
            
            # Perform the export
            result = exporter.export(export_data, config)
            
            # Update result with timing
            result.duration_seconds = time.time() - start_time
            result.format_used = config.format
            
            # Log the result
            exporter.log_export_result(result)
            
            if not result.success:
                self.logger.error(f"Export failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Unexpected error during export: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.SYSTEM,
                f"Export failed for format {config.format.value}"
            )
            
            return ExportResult(
                success=False,
                error_message=error_msg,
                format_used=config.format,
                duration_seconds=duration
            )
    
    def validate_export_config(self, config: ExportConfig) -> List[str]:
        """
        Validate export configuration.
        
        Args:
            config: ExportConfig to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            if not config:
                errors.append("Export configuration is required")
                return errors
            
            if not config.format:
                errors.append("Export format is required")
            elif not self.is_format_supported(config.format):
                errors.append(f"Export format {config.format.value} is not supported")
            
            if not config.output_path:
                errors.append("Output path is required")
            
            if not config.scope:
                errors.append("Export scope is required")
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def get_format_info(self) -> Dict[ExportFormat, Dict[str, str]]:
        """
        Get information about all supported formats.
        
        Returns:
            Dictionary mapping formats to their info (extension, description)
        """
        format_info = {}
        
        for format_type, exporter in self.exporters.items():
            try:
                format_info[format_type] = {
                    'extension': exporter.get_output_extension(),
                    'exporter_class': exporter.__class__.__name__,
                    'description': self._get_format_description(format_type)
                }
            except Exception as e:
                self.logger.warning(f"Failed to get info for format {format_type.value}: {e}")
        
        return format_info
    
    def _register_default_exporters(self):
        """Register built-in exporters"""
        try:
            # Import and register text exporter
            from .exporters.text_exporter import TextExporter
            text_exporter = TextExporter()
            self.register_exporter(ExportFormat.TXT, text_exporter)
            
            # Import and register PDF exporter
            from .exporters.pdf_exporter import PDFExporter
            pdf_exporter = PDFExporter()
            self.register_exporter(ExportFormat.PDF, pdf_exporter)
            
            
        except ImportError as e:
            self.logger.warning(f"Some exporters not available due to missing dependencies: {e}")
        except Exception as e:
            self.logger.error(f"Failed to register default exporters: {e}")
    
    def _get_format_description(self, format_type: ExportFormat) -> str:
        """
        Get human-readable description for export format.
        
        Args:
            format_type: ExportFormat enum
            
        Returns:
            Description string
        """
        descriptions = {
            ExportFormat.PDF: "Portable Document Format - Professional document with formatting",
            ExportFormat.TXT: "Plain Text - Simple text format without formatting", 
            ExportFormat.HTML: "HTML Document - Web page format with styling",
            ExportFormat.DOCX: "Microsoft Word Document - Editable document format",
            ExportFormat.JSON: "JSON Data - Structured data export for backup/import"
        }
        
        return descriptions.get(format_type, f"Export to {format_type.value.upper()} format")
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the export engine.
        
        Returns:
            Dictionary with engine statistics
        """
        return {
            'registered_exporters': len(self.exporters),
            'supported_formats': [fmt.value for fmt in self.get_supported_formats()],
            'exporter_classes': [exp.__class__.__name__ for exp in self.exporters.values()]
        }