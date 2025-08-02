"""
LLM Settings Management System.
Handles configuration for different LLM providers including llama.cpp.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from PySide6.QtCore import QSettings
from core.logging_config import get_logger
from pathlib import Path

GLOBAL_DB_PATH: Path = Path.home() / "pisarz_db" / "pisarz.db"

@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    display_name: str
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value with optional default."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        self.settings[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'enabled': self.enabled,
            'settings': self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMProviderConfig':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            display_name=data['display_name'],
            enabled=data.get('enabled', True),
            settings=data.get('settings', {})
        )


class LLMSettingsManager:
    """Manages LLM provider settings and configuration."""
    
    def __init__(self):
        self.logger = get_logger("llm.settings")
        self.settings = QSettings()
        self.providers: Dict[str, LLMProviderConfig] = {}
        self.global_settings = {
            'context_length_chars': 500  # Default context length in characters
        }
        self._initialize_default_providers()
        self._load_settings()
    
    def _initialize_default_providers(self):
        """Initialize default provider configurations."""
        # Mock provider for testing
        self.providers['mock'] = LLMProviderConfig(
            name='mock',
            display_name='Mock Provider (Testing)',
            enabled=True,
            settings={
                'response_delay': 0.5,
                'default_language': 'polish'
            }
        )
        
        # llama.cpp provider for local server
        self.providers['llamacpp'] = LLMProviderConfig(
            name='llamacpp',
            display_name='llama.cpp (Local Server)',
            enabled=True,
            settings={
                'host': 'localhost',
                'port': 8080,
                'model_path': '',
                'max_tokens': 10000,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
                'repeat_penalty': 1.1,
                'seed': -1,
                'threads': 4,
                'context_size': 2048,
                'batch_size': 512,
                'timeout': 120,
                'stream': True
            }
        )
        
        # OpenAI provider
        self.providers['openai'] = LLMProviderConfig(
            name='openai',
            display_name='OpenAI GPT',
            enabled=True,
            settings={
                'api_key': '',
                'model': 'gpt-4',
                'max_tokens': 10000,
                'temperature': 0.7,
                'top_p': 1.0,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0,
                'base_url': 'https://api.openai.com/v1',
                'timeout': 30
            }
        )
        
        # Anthropic provider (for future use)
        self.providers['anthropic'] = LLMProviderConfig(
            name='anthropic',
            display_name='Anthropic Claude',
            enabled=False,
            settings={
                'api_key': '',
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 512,
                'temperature': 0.7,
                'top_p': 1.0,
                'timeout': 30
            }
        )
        
        # Ollama provider for local models
        self.providers['ollama'] = LLMProviderConfig(
            name='ollama',
            display_name='Ollama (Local Models)',
            enabled=True,
            settings={
                'host': '192.168.1.102',
                'port': 11434,
                'model': 'tom_himanen/deepseek-r1-roo-cline-tools:70b',
                'max_tokens': 10000,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
                'repeat_penalty': 1.1,
                'timeout': 120
            }
        )
        
        # OpenRouter provider for multiple AI models
        self.providers['openrouter'] = LLMProviderConfig(
            name='openrouter',
            display_name='OpenRouter.ai (Multiple Models)',
            enabled=True,
            settings={
                'api_key': '',
                'model': 'openai/gpt-3.5-turbo',
                'max_tokens': 10000,
                'temperature': 0.7,
                'top_p': 1.0,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0,
                'base_url': 'https://openrouter.ai/api/v1',
                'timeout': 30,
                'site_url': '',
                'app_name': 'Pisarz-Writer'
            }
        )
    
    def _load_settings(self):
        """Load settings from QSettings."""
        try:
            # Load global settings
            global_settings = self.settings.value('llm/global', {})
            if isinstance(global_settings, dict) and global_settings:
                self.global_settings.update(global_settings)
            
            # Load current provider
            current_provider = self.settings.value('llm/current_provider', 'llamacpp')
            self.set_current_provider(current_provider)
            
            # Load provider configurations
            for provider_name in self.providers.keys():
                provider_settings = self.settings.value(f'llm/providers/{provider_name}', {})
                if isinstance(provider_settings, dict) and provider_settings:
                    self.providers[provider_name].settings.update(provider_settings)
                    
            self.logger.info(f"Loaded LLM settings, current provider: {current_provider}")
            
        except Exception as e:
            self.logger.error(f"Error loading LLM settings: {e}")
    
    def _save_settings(self):
        """Save settings to QSettings."""
        try:
            # Save global settings
            self.settings.setValue('llm/global', self.global_settings)
            
            # Save current provider
            self.settings.setValue('llm/current_provider', self.get_current_provider())
            
            # Save provider configurations
            for provider_name, provider in self.providers.items():
                self.settings.setValue(f'llm/providers/{provider_name}', provider.settings)
                
            self.logger.debug("LLM settings saved")
            
        except Exception as e:
            self.logger.error(f"Error saving LLM settings: {e}")
    
    def get_current_provider(self) -> str:
        """Get the currently selected provider name."""
        return self.settings.value('llm/current_provider', 'mock')
    
    def set_current_provider(self, provider_name: str):
        """Set the current provider."""
        if provider_name in self.providers:
            self.settings.setValue('llm/current_provider', provider_name)
            self.logger.info(f"Current LLM provider set to: {provider_name}")
        else:
            self.logger.warning(f"Unknown provider: {provider_name}")
    
    def get_provider_config(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """Get configuration for a specific provider."""
        return self.providers.get(provider_name)
    
    def get_current_provider_config(self) -> Optional[LLMProviderConfig]:
        """Get configuration for the current provider."""
        return self.get_provider_config(self.get_current_provider())
    
    def update_provider_setting(self, provider_name: str, key: str, value: Any):
        """Update a specific setting for a provider."""
        if provider_name in self.providers:
            self.providers[provider_name].set_setting(key, value)
            self._save_settings()
            self.logger.debug(f"Updated {provider_name}.{key} = {value}")
        else:
            self.logger.warning(f"Unknown provider: {provider_name}")
    
    def get_provider_setting(self, provider_name: str, key: str, default: Any = None) -> Any:
        """Get a specific setting for a provider."""
        provider = self.get_provider_config(provider_name)
        if provider:
            return provider.get_setting(key, default)
        return default
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())
    
    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names."""
        return [name for name, config in self.providers.items() if config.enabled]
    
    def enable_provider(self, provider_name: str, enabled: bool = True):
        """Enable or disable a provider."""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = enabled
            self._save_settings()
            self.logger.info(f"Provider {provider_name} {'enabled' if enabled else 'disabled'}")
    
    def get_provider_display_name(self, provider_name: str) -> str:
        """Get the display name for a provider."""
        provider = self.get_provider_config(provider_name)
        return provider.display_name if provider else provider_name
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting value."""
        return self.global_settings.get(key, default)
    
    def set_global_setting(self, key: str, value: Any):
        """Set a global setting value."""
        self.global_settings[key] = value
        self._save_settings()
    
    def get_context_length(self) -> int:
        """Get the configured context length in characters."""
        return self.get_global_setting('context_length_chars', 500)
    
    def set_context_length(self, length: int):
        """Set the context length in characters."""
        if length > 0:
            self.set_global_setting('context_length_chars', length)
    
    def validate_provider_config(self, provider_name: str) -> tuple[bool, str]:
        """Validate configuration for a provider."""
        provider = self.get_provider_config(provider_name)
        if not provider:
            return False, f"Provider {provider_name} not found"
        
        if not provider.enabled:
            return False, f"Provider {provider_name} is disabled"
        
        # Provider-specific validation
        if provider_name == 'llamacpp':
            return self._validate_llamacpp_config(provider)
        elif provider_name == 'openai':
            return self._validate_openai_config(provider)
        elif provider_name == 'anthropic':
            return self._validate_anthropic_config(provider)
        elif provider_name == 'ollama':
            return self._validate_ollama_config(provider)
        elif provider_name == 'mock':
            return True, "Mock provider is always valid"
        
        return True, "Configuration valid"
    
    def _validate_llamacpp_config(self, provider: LLMProviderConfig) -> tuple[bool, str]:
        """Validate llama.cpp configuration."""
        host = provider.get_setting('host', '')
        port = provider.get_setting('port', 0)
        
        if not host:
            return False, "Host is required for llama.cpp"
        
        if not isinstance(port, int) or port <= 0 or port > 65535:
            return False, "Port must be between 1 and 65535"
        
        max_tokens = provider.get_setting('max_tokens', 512)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return False, "Max tokens must be positive integer"
        
        temperature = provider.get_setting('temperature', 0.7)
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            return False, "Temperature must be between 0 and 2"
        
        return True, "llama.cpp configuration valid"
    
    def _validate_openai_config(self, provider: LLMProviderConfig) -> tuple[bool, str]:
        """Validate OpenAI configuration."""
        api_key = provider.get_setting('api_key', '')
        if not api_key:
            return False, "API key is required for OpenAI"
        
        model = provider.get_setting('model', '')
        if not model:
            return False, "Model is required for OpenAI"
        
        return True, "OpenAI configuration valid"
    
    def _validate_anthropic_config(self, provider: LLMProviderConfig) -> tuple[bool, str]:
        """Validate Anthropic configuration."""
        api_key = provider.get_setting('api_key', '')
        if not api_key:
            return False, "API key is required for Anthropic"
        
        model = provider.get_setting('model', '')
        if not model:
            return False, "Model is required for Anthropic"
        
        return True, "Anthropic configuration valid"
    
    def _validate_ollama_config(self, provider: LLMProviderConfig) -> tuple[bool, str]:
        """Validate Ollama configuration."""
        host = provider.get_setting('host', '')
        port = provider.get_setting('port', 0)
        
        if not host:
            return False, "Host is required for Ollama"
        
        if not isinstance(port, int) or port <= 0 or port > 65535:
            return False, "Port must be between 1 and 65535"
        
        model = provider.get_setting('model', '')
        if not model:
            return False, "Model is required for Ollama"
        
        max_tokens = provider.get_setting('max_tokens', 512)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return False, "Max tokens must be positive integer"
        
        temperature = provider.get_setting('temperature', 0.7)
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            return False, "Temperature must be between 0 and 2"
        
        return True, "Ollama configuration valid"
    
    def get_provider_url(self, provider_name: str) -> str:
        """Get the URL for a provider (useful for llamacpp and ollama)."""
        if provider_name == 'llamacpp':
            provider = self.get_provider_config(provider_name)
            if provider:
                host = provider.get_setting('host', 'localhost')
                port = provider.get_setting('port', 8080)
                return f"http://{host}:{port}"
        elif provider_name == 'ollama':
            provider = self.get_provider_config(provider_name)
            if provider:
                host = provider.get_setting('host', 'localhost')
                port = provider.get_setting('port', 11434)
                return f"http://{host}:{port}"
        
        return ""
    
    def export_settings(self) -> Dict[str, Any]:
        """Export settings to dictionary."""
        return {
            'current_provider': self.get_current_provider(),
            'providers': {
                name: config.to_dict() for name, config in self.providers.items()
            }
        }
    
    def import_settings(self, data: Dict[str, Any]):
        """Import settings from dictionary."""
        try:
            if 'current_provider' in data:
                self.set_current_provider(data['current_provider'])
            
            if 'providers' in data:
                for name, provider_data in data['providers'].items():
                    if name in self.providers:
                        self.providers[name] = LLMProviderConfig.from_dict(provider_data)
            
            self._save_settings()
            self.logger.info("LLM settings imported successfully")
            
        except Exception as e:
            self.logger.error(f"Error importing LLM settings: {e}")
            raise


# Global settings manager instance
_settings_manager = None


def get_llm_settings() -> LLMSettingsManager:
    """Get the global LLM settings manager."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = LLMSettingsManager()
    return _settings_manager