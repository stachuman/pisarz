"""Logging configuration for Pisarz application."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QSettings


class PisarzLoggingConfig:
    """Configuration manager for application logging."""
    
    def __init__(self):
        self.settings = QSettings()
        self.log_dir = Path.home() / ".pisarz" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_logging(self, 
                     log_level: str = "INFO",
                     max_file_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5,
                     console_logging: bool = True) -> logging.Logger:
        """
        Setup comprehensive logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            console_logging: Whether to enable console logging
            
        Returns:
            Configured logger instance
        """
        # Get log level from settings or use default
        level_str = self.settings.value("logging/level", log_level)
        level = getattr(logging, level_str.upper(), logging.INFO)
        
        # Configure root logger for pisarz
        logger = logging.getLogger("pisarz")
        logger.setLevel(level)
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Main application log (rotating file)
        main_log_file = self.log_dir / "pisarz.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_file, 
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(detailed_formatter)
        logger.addHandler(main_handler)
        
        # Error-only log (rotating file)
        error_log_file = self.log_dir / "pisarz_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        # Performance log for timing critical operations
        perf_log_file = self.log_dir / "pisarz_performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)
        
        # Add filter for performance logs
        class PerformanceFilter(logging.Filter):
            def filter(self, record):
                return hasattr(record, 'performance') and record.performance
        
        perf_handler.addFilter(PerformanceFilter())
        logger.addHandler(perf_handler)
        
        # Console handler for development
        if console_logging:
            console_handler = logging.StreamHandler()
            console_level = self.settings.value("logging/console_level", "WARNING")
            console_handler.setLevel(getattr(logging, console_level.upper(), logging.WARNING))
            console_handler.setFormatter(simple_formatter)
            logger.addHandler(console_handler)
        
        # Memory handler for critical errors (keeps last 100 critical errors in memory)
        memory_handler = logging.handlers.MemoryHandler(
            capacity=100,
            flushLevel=logging.CRITICAL,
            target=error_handler
        )
        memory_handler.setLevel(logging.ERROR)
        logger.addHandler(memory_handler)
        
        logger.propagate = False
        
        logger.info("Pisarz logging system initialized")
        logger.debug(f"Log directory: {self.log_dir}")
        logger.debug(f"Log level: {level_str}")
        
        return logger
    
    def get_module_logger(self, module_name: str) -> logging.Logger:
        """Get a logger for a specific module."""
        return logging.getLogger(f"pisarz.{module_name}")
    
    def log_performance(self, logger: logging.Logger, operation: str, duration: float, details: str = ""):
        """Log performance information."""
        extra = {'performance': True}
        message = f"PERFORMANCE: {operation} took {duration:.3f}s"
        if details:
            message += f" - {details}"
        logger.info(message, extra=extra)
    
    def set_log_level(self, level: str):
        """Update logging level and save to settings."""
        self.settings.setValue("logging/level", level.upper())
        logger = logging.getLogger("pisarz")
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.info(f"Log level changed to {level.upper()}")
    
    def set_console_log_level(self, level: str):
        """Update console logging level."""
        self.settings.setValue("logging/console_level", level.upper())
        logger = logging.getLogger("pisarz")
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(getattr(logging, level.upper(), logging.WARNING))
        logger.debug(f"Console log level changed to {level.upper()}")
    
    def get_log_stats(self) -> dict:
        """Get statistics about log files."""
        stats = {}
        for log_file in self.log_dir.glob("*.log"):
            try:
                file_size = log_file.stat().st_size
                with open(log_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                
                stats[log_file.name] = {
                    'size_bytes': file_size,
                    'size_mb': file_size / (1024 * 1024),
                    'line_count': line_count,
                    'modified': log_file.stat().st_mtime
                }
            except Exception as e:
                stats[log_file.name] = {'error': str(e)}
        
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days."""
        import time
        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
        
        cleaned_files = []
        for log_file in self.log_dir.glob("*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_files.append(log_file.name)
            except Exception as e:
                logger = self.get_module_logger("logging_config")
                logger.warning(f"Failed to clean up log file {log_file}: {e}")
        
        if cleaned_files:
            logger = self.get_module_logger("logging_config")
            logger.info(f"Cleaned up {len(cleaned_files)} old log files: {cleaned_files}")
        
        return cleaned_files
    
    def get_recent_errors(self, count: int = 50) -> list:
        """Get recent error messages from error log."""
        error_log_file = self.log_dir / "pisarz_errors.log"
        if not error_log_file.exists():
            return []
        
        try:
            with open(error_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Return last 'count' lines
            return lines[-count:] if lines else []
        except Exception as e:
            return [f"Error reading error log: {e}"]
    
    def export_logs(self, export_path: Path, include_debug: bool = False):
        """Export logs to a zip file for debugging."""
        import zipfile
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = export_path / f"pisarz_logs_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for log_file in self.log_dir.glob("*.log*"):
                # Skip debug logs if not requested
                if not include_debug and "debug" in log_file.name.lower():
                    continue
                
                if log_file.exists():
                    zipf.write(log_file, log_file.name)
        
        logger = self.get_module_logger("logging_config")
        logger.info(f"Logs exported to {zip_path}")
        return zip_path


# Global logging config instance
_logging_config = None


def get_logging_config() -> PisarzLoggingConfig:
    """Get the global logging configuration instance."""
    global _logging_config
    if _logging_config is None:
        _logging_config = PisarzLoggingConfig()
    return _logging_config


def setup_logging(**kwargs) -> logging.Logger:
    """Convenience function to setup logging."""
    return get_logging_config().setup_logging(**kwargs)


def get_logger(module_name: str = None) -> logging.Logger:
    """Convenience function to get a logger."""
    if module_name:
        return get_logging_config().get_module_logger(module_name)
    return logging.getLogger("pisarz")