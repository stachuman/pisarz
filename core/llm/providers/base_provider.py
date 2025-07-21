"""
Base provider class for LLM operations.
Defines the interface that all LLM providers must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.logging_config import get_logger
from i18n import _


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = get_logger(f"llm.provider.{self.__class__.__name__.lower()}")
        self.config = config or {}
        self._initialized = False
        self.settings_manager = None
    
    def _get_provider_name(self) -> str:
        """Get the provider name for configuration lookup."""
        # Default implementation - providers can override
        return self.__class__.__name__.replace('Provider', '').lower()
    
    def _load_settings_manager(self):
        """Load settings manager, handling circular imports."""
        if not self.settings_manager:
            # Import here to avoid circular imports
            from ..settings import get_llm_settings
            self.settings_manager = get_llm_settings()
    
    def _get_provider_config(self):
        """Get provider configuration from settings manager."""
        self._load_settings_manager()
        provider_name = self._get_provider_name()
        return self.settings_manager.get_provider_config(provider_name)
    
    def _validate_provider_config(self) -> tuple[bool, str]:
        """Validate provider configuration."""
        provider_name = self._get_provider_name()
        return self.settings_manager.validate_provider_config(provider_name)
    
    def initialize_with_common_pattern(self) -> bool:
        """Common initialization pattern used by all providers."""
        try:
            provider_name = self._get_provider_name()
            self.logger.info(f"Initializing {provider_name} provider")
            
            # Get configuration from settings
            provider_config = self._get_provider_config()
            if not provider_config:
                self.logger.error(_(f"{provider_name.title()} provider configuration not found"))
                return False
            
            # Let subclass load specific settings
            if not self._load_provider_settings(provider_config):
                return False
            
            # Validate configuration if provider implements validation
            is_valid, message = self._validate_provider_config()
            if not is_valid:
                self.logger.error(_(f"{provider_name.title()} configuration invalid: {message}"))
                return False
            
            # Mark as initialized before health check since health check may depend on it
            self._initialized = True
            
            # Test connection/availability
            health_status = self.get_health_status()
            if health_status['status'] == 'healthy':
                self.logger.info(_(f"{provider_name.title()} provider initialized successfully"))
                return True
            else:
                self.logger.error(_(f"{provider_name.title()} provider initialization failed: {health_status['message']}"))
                self._initialized = False  # Reset if health check fails
                return False
                
        except Exception as e:
            provider_name = self._get_provider_name()
            self.logger.error(_(f"Error initializing {provider_name} provider: {e}"))
            self._initialized = False
            return False
    
    def _load_provider_settings(self, provider_config) -> bool:
        """Load provider-specific settings. Override in subclasses."""
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status. Override in subclasses."""
        return {
            'status': 'healthy' if self.is_available() else 'unhealthy',
            'message': 'Provider available' if self.is_available() else 'Provider not available'
        }
    
    def log_request_details(self, provider_name: str, url: str, prompt: str, params: Dict[str, Any], timeout: int = None):
        """Log detailed request information in a standardized format."""
        self.logger.info(f"=== {provider_name.upper()} REQUEST ===")
        self.logger.info(f"URL: {url}")
        self.logger.info(f"Prompt length: {len(prompt)} characters")
        self.logger.info(f"Prompt preview: {prompt[:200]}...")
        self.logger.info(f"Parameters: {params}")
        if timeout:
            self.logger.info(f"Timeout: {timeout} seconds")
        
        # Log full prompt if debug logging enabled
        self.logger.debug(f"=== FULL PROMPT ===\n{prompt}\n=== END PROMPT ===")
    
    def log_response_details(self, provider_name: str, content: str, status_code: int = None):
        """Log detailed response information in a standardized format."""
        self.logger.info(f"=== {provider_name.upper()} RESPONSE ===")
        if status_code:
            self.logger.info(f"Status Code: {status_code}")
        self.logger.info(f"Response length: {len(content)} characters")
        self.logger.info(f"Response preview: {content[:200]}...")
        
        # Log full response if debug logging enabled
        self.logger.debug(f"=== FULL RESPONSE ===\n{content}\n=== END RESPONSE ===")
    
    def handle_request_exception(self, provider_name: str, exception: Exception, operation: str = "request") -> str:
        """Handle common request exceptions with standardized logging."""
        import requests
        
        if isinstance(exception, requests.exceptions.Timeout):
            error_msg = f"{provider_name} API request timed out"
            self.logger.error(error_msg)
        elif isinstance(exception, requests.exceptions.RequestException):
            error_msg = f"{provider_name} API {operation} failed: {exception}"
            self.logger.error(error_msg)
        else:
            error_msg = f"Error during {provider_name} {operation}: {exception}"
            self.logger.error(error_msg)
        
        return ""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the provider. Returns True if successful."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'name': self.__class__.__name__,
            'initialized': self._initialized,
            'available': self.is_available(),
            'config_keys': list(self.config.keys()) if self.config else []
        }
    
    def validate_config(self) -> bool:
        """Validate provider configuration."""
        return True
    
    def cleanup(self):
        """Clean up provider resources."""
        pass