"""
Base exporter abstract class following the repository pattern.
Provides common functionality and interface for all export formats.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any

from ..models import ExportConfig, ExportResult, ExportData, ExportFormat
from ...error_handler import get_error_handler, ErrorLevel, ErrorCategory


class BaseExporter(ABC):
    """
    Abstract base class for all exporters following repository pattern.
    Provides common functionality and consistent interface.
    """
    
    def __init__(self):
        """Initialize base exporter with logging and error handling"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.error_handler = get_error_handler()
    
    @abstractmethod
    def get_supported_formats(self) -> List[ExportFormat]:
        """
        Return list of supported export formats.
        
        Returns:
            List of ExportFormat enums this exporter supports
        """
        pass
    
    @abstractmethod
    def export(self, data: ExportData, config: ExportConfig) -> ExportResult:
        """
        Perform the export operation.
        
        Args:
            data: ExportData container with all data to export
            config: ExportConfig with export parameters
            
        Returns:
            ExportResult with operation outcome
        """
        pass
    
    @abstractmethod
    def get_output_extension(self) -> str:
        """
        Return file extension for this exporter (including dot).
        
        Returns:
            File extension string (e.g., ".pdf", ".txt")
        """
        pass
    
    def validate_config(self, config: ExportConfig) -> List[str]:
        """
        Validate export configuration for this exporter.
        
        Args:
            config: ExportConfig to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            # Check if format is supported
            if config.format not in self.get_supported_formats():
                errors.append(f"Format {config.format.value} not supported by {self.__class__.__name__}")
            
            # Check output path
            if not config.output_path:
                errors.append("Output path is required")
            else:
                # Check if output directory exists and is writable
                output_path = Path(config.output_path)
                output_dir = output_path.parent
                
                if not output_dir.exists():
                    errors.append(f"Output directory does not exist: {output_dir}")
                elif not os.access(output_dir, os.W_OK):
                    errors.append(f"Output directory is not writable: {output_dir}")
                
                # Check file extension matches exporter
                expected_ext = self.get_output_extension()
                if not config.output_path.endswith(expected_ext):
                    errors.append(f"Output path should end with {expected_ext}")
            
            # Validate scope
            if not config.scope:
                errors.append("Export scope is required")
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def validate_data(self, data: ExportData) -> List[str]:
        """
        Validate export data for this exporter.
        
        Args:
            data: ExportData to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            if not data:
                errors.append("Export data is required")
                return errors
            
            if not data.project_metadata:
                errors.append("Project metadata is required")
            
            if not data.scenes:
                errors.append("At least one scene is required for export")
            
            # Check for required scene fields
            for i, scene in enumerate(data.scenes):
                if not isinstance(scene, dict):
                    errors.append(f"Scene {i} must be a dictionary")
                    continue
                
                if 'title' not in scene:
                    errors.append(f"Scene {i} missing required field: title")
                
                if 'content' not in scene:
                    errors.append(f"Scene {i} missing required field: content")
            
        except Exception as e:
            errors.append(f"Data validation error: {str(e)}")
        
        return errors
    
    def create_success_result(self, output_path: str, exported_count: int, 
                            file_size: int = 0, duration: float = 0.0,
                            format_used: ExportFormat = None) -> ExportResult:
        """
        Create a success ExportResult.
        
        Args:
            output_path: Path to the exported file
            exported_count: Number of items exported
            file_size: File size in bytes
            duration: Export duration in seconds
            format_used: Format that was used for export
            
        Returns:
            ExportResult indicating success
        """
        # Get actual file size if not provided
        if file_size == 0 and os.path.exists(output_path):
            try:
                file_size = os.path.getsize(output_path)
            except OSError:
                pass  # Keep file_size as 0 if we can't get it
        
        return ExportResult(
            success=True,
            output_path=output_path,
            exported_items_count=exported_count,
            file_size_bytes=file_size,
            duration_seconds=duration,
            format_used=format_used
        )
    
    def create_error_result(self, error_message: str, 
                          format_used: ExportFormat = None,
                          duration: float = 0.0) -> ExportResult:
        """
        Create an error ExportResult.
        
        Args:
            error_message: Error description
            format_used: Format that was attempted
            duration: Time spent before error
            
        Returns:
            ExportResult indicating failure
        """
        return ExportResult(
            success=False,
            error_message=error_message,
            format_used=format_used,
            duration_seconds=duration
        )
    
    def ensure_output_directory(self, output_path: str) -> bool:
        """
        Ensure the output directory exists.
        
        Args:
            output_path: Full path to output file
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {e}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Ensure it's not empty
        if not filename:
            filename = "export"
        
        return filename
    
    def format_content(self, content: str) -> str:
        """
        Format content for export by cleaning up markup and formatting.
        
        Args:
            content: Raw content from scene
            
        Returns:
            Formatted content suitable for export
        """
        if not content:
            return ""
        
        # Basic RTF cleanup if content contains RTF markup
        if content.startswith('{\\rtf'):
            # This is a basic RTF cleanup - could be enhanced with proper RTF parser
            # For now, just remove common RTF tags
            import re
            
            # Remove RTF control sequences
            content = re.sub(r'\\[a-z]+\d*\s?', '', content)
            content = re.sub(r'[{}]', '', content)
            
            # Clean up extra whitespace
            content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def get_template_path(self, template_name: str) -> Path:
        """
        Get path to export template file.
        
        Args:
            template_name: Name of template
            
        Returns:
            Path to template file
        """
        # Templates will be in core/export/templates/
        templates_dir = Path(__file__).parent.parent / "templates"
        return templates_dir / template_name
    
    def log_export_start(self, config: ExportConfig, data: ExportData):
        """Log export operation start"""
        self.logger.info(
            f"Starting {config.format.value.upper()} export: "
            f"{len(data.scenes)} scenes, {len(data.characters)} characters, "
            f"{len(data.locations)} locations to {config.output_path}"
        )
    
    def log_export_result(self, result: ExportResult):
        """Log export operation result"""
        if result.success:
            self.logger.info(
                f"Export completed successfully: {result.exported_items_count} items, "
                f"{result.file_size_mb:.2f}MB, {result.duration_seconds:.2f}s"
            )
        else:
            self.logger.error(f"Export failed: {result.error_message}")