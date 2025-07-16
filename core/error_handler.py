"""Unified error handling and logging system for Pisarz application."""

import logging
import traceback
from enum import Enum
from typing import Optional, Union, Callable
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import QObject, Signal

from i18n import _


class ErrorLevel(Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization."""
    DATABASE = "database"
    FILE_IO = "file_io"
    NETWORK = "network"
    VALIDATION = "validation"
    UI = "ui"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"


class ErrorHandler(QObject):
    """Centralized error handling and logging system."""
    
    # Signals for error notification
    errorOccurred = Signal(str, str, str)  # level, category, message
    
    def __init__(self):
        super().__init__()
        self._logger = None
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup centralized logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = Path.home() / ".pisarz" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self._logger = logging.getLogger("pisarz")
        self._logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_dir / "pisarz.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Error file handler for errors only
        error_handler = logging.FileHandler(log_dir / "pisarz_errors.log", encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self._logger.addHandler(file_handler)
        self._logger.addHandler(error_handler)
        self._logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
        
        self._logger.info("Logging system initialized")
    
    def handle_error(self, 
                    error: Union[Exception, str],
                    level: ErrorLevel = ErrorLevel.ERROR,
                    category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
                    context: str = "",
                    show_to_user: bool = True,
                    parent_widget: Optional[QWidget] = None,
                    custom_message: Optional[str] = None) -> str:
        """
        Handle an error with unified logging and user notification.
        
        Args:
            error: Exception object or error message string
            level: Severity level of the error
            category: Category for error organization
            context: Additional context information
            show_to_user: Whether to show error dialog to user
            parent_widget: Parent widget for error dialog
            custom_message: Custom user-friendly message
            
        Returns:
            Error ID for tracking
        """
        # Generate error details
        if isinstance(error, Exception):
            error_msg = str(error)
            error_type = type(error).__name__
            stack_trace = traceback.format_exc()
        else:
            error_msg = str(error)
            error_type = "Error"
            stack_trace = ""
        
        # Create full context message
        full_context = f"{context} - {error_type}: {error_msg}" if context else f"{error_type}: {error_msg}"
        
        # Log the error
        log_message = f"[{category.value.upper()}] {full_context}"
        if stack_trace:
            log_message += f"\nStack trace:\n{stack_trace}"
            
        if level == ErrorLevel.DEBUG:
            self._logger.debug(log_message)
        elif level == ErrorLevel.INFO:
            self._logger.info(log_message)
        elif level == ErrorLevel.WARNING:
            self._logger.warning(log_message)
        elif level == ErrorLevel.ERROR:
            self._logger.error(log_message)
        elif level == ErrorLevel.CRITICAL:
            self._logger.critical(log_message)
        
        # Emit signal for controllers
        self.errorOccurred.emit(level.value, category.value, error_msg)
        
        # Show to user if requested
        if show_to_user and level in [ErrorLevel.WARNING, ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
            self._show_error_to_user(error_msg, level, custom_message, parent_widget)
        
        # Return error ID for tracking
        return f"{category.value}_{level.value}_{hash(error_msg) % 10000}"
    
    def _show_error_to_user(self, 
                           error_msg: str, 
                           level: ErrorLevel, 
                           custom_message: Optional[str],
                           parent_widget: Optional[QWidget]):
        """Show error dialog to user."""
        # Determine user-friendly message
        if custom_message:
            user_message = custom_message
        else:
            user_message = self._get_user_friendly_message(error_msg, level)
        
        # Determine dialog type
        if level == ErrorLevel.WARNING:
            QMessageBox.warning(parent_widget, _("Warning"), user_message)
        elif level == ErrorLevel.ERROR:
            QMessageBox.critical(parent_widget, _("Error"), user_message)
        elif level == ErrorLevel.CRITICAL:
            QMessageBox.critical(parent_widget, _("Critical Error"), user_message)
    
    def _get_user_friendly_message(self, error_msg: str, level: ErrorLevel) -> str:
        """Convert technical error message to user-friendly message."""
        # Common error patterns and their user-friendly messages
        error_patterns = {
            "database is locked": _("The database is currently busy. Please try again in a moment."),
            "no such table": _("Database structure issue. Please restart the application."),
            "permission denied": _("Permission denied. Please check file permissions."),
            "file not found": _("Required file not found. Please check if the file exists."),
            "connection failed": _("Connection failed. Please check your network connection."),
            "invalid input": _("Invalid input provided. Please check your data."),
            "out of memory": _("Not enough memory available. Please close other applications."),
        }
        
        error_lower = error_msg.lower()
        for pattern, user_msg in error_patterns.items():
            if pattern in error_lower:
                return user_msg
        
        # Default messages based on level
        if level == ErrorLevel.WARNING:
            return _("A warning occurred. Please check your action and try again.")
        elif level == ErrorLevel.ERROR:
            return _("An error occurred while processing your request. Please try again.")
        elif level == ErrorLevel.CRITICAL:
            return _("A critical error occurred. Please restart the application.")
        
        return _("An unexpected error occurred.")
    
    def log_info(self, message: str, category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC):
        """Log an info message."""
        self.handle_error(message, ErrorLevel.INFO, category, show_to_user=False)
    
    def log_warning(self, message: str, category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC, 
                   show_to_user: bool = False, parent_widget: Optional[QWidget] = None):
        """Log a warning message."""
        self.handle_error(message, ErrorLevel.WARNING, category, show_to_user=show_to_user, 
                         parent_widget=parent_widget)
    
    def log_error(self, error: Union[Exception, str], category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
                 context: str = "", show_to_user: bool = True, parent_widget: Optional[QWidget] = None,
                 custom_message: Optional[str] = None):
        """Log an error message."""
        self.handle_error(error, ErrorLevel.ERROR, category, context, show_to_user, 
                         parent_widget, custom_message)
    
    def log_critical(self, error: Union[Exception, str], category: ErrorCategory = ErrorCategory.SYSTEM,
                    context: str = "", show_to_user: bool = True, parent_widget: Optional[QWidget] = None,
                    custom_message: Optional[str] = None):
        """Log a critical error message."""
        self.handle_error(error, ErrorLevel.CRITICAL, category, context, show_to_user, 
                         parent_widget, custom_message)
    
    def log_debug(self, message: str, category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC):
        """Log a debug message."""
        self.handle_error(message, ErrorLevel.DEBUG, category, show_to_user=False)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get logger instance for specific module."""
        if name:
            return logging.getLogger(f"pisarz.{name}")
        return self._logger
    
    def set_log_level(self, level: ErrorLevel):
        """Set the logging level."""
        log_levels = {
            ErrorLevel.DEBUG: logging.DEBUG,
            ErrorLevel.INFO: logging.INFO,
            ErrorLevel.WARNING: logging.WARNING,
            ErrorLevel.ERROR: logging.ERROR,
            ErrorLevel.CRITICAL: logging.CRITICAL
        }
        self._logger.setLevel(log_levels[level])
    
    def clear_logs(self):
        """Clear log files."""
        try:
            log_dir = Path.home() / ".pisarz" / "logs"
            for log_file in log_dir.glob("*.log"):
                log_file.unlink(missing_ok=True)
            self._logger.info("Log files cleared")
        except Exception as e:
            self._logger.error(f"Failed to clear log files: {e}")


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: Union[Exception, str], 
                level: ErrorLevel = ErrorLevel.ERROR,
                category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
                context: str = "",
                show_to_user: bool = True,
                parent_widget: Optional[QWidget] = None,
                custom_message: Optional[str] = None) -> str:
    """Convenience function for error handling."""
    return get_error_handler().handle_error(
        error, level, category, context, show_to_user, parent_widget, custom_message
    )


def get_logger(name: str = None) -> logging.Logger:
    """Convenience function to get logger."""
    return get_error_handler().get_logger(name)


# Decorator for automatic error handling
def handle_exceptions(category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
                     show_to_user: bool = True,
                     custom_message: Optional[str] = None,
                     return_value=None):
    """Decorator to automatically handle exceptions in methods."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Try to get parent widget from self
                parent_widget = None
                if args and hasattr(args[0], 'parent') and callable(args[0].parent):
                    parent_widget = args[0].parent()
                elif args and isinstance(args[0], QWidget):
                    parent_widget = args[0]
                
                handle_error(
                    e, ErrorLevel.ERROR, category, 
                    f"Error in {func.__name__}", show_to_user, 
                    parent_widget, custom_message
                )
                return return_value
        return wrapper
    return decorator