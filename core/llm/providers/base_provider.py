"""
Base provider class for LLM operations.
Defines the interface that all LLM providers must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.logging_config import get_logger


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = get_logger(f"llm.provider.{self.__class__.__name__.lower()}")
        self.config = config or {}
        self._initialized = False
    
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