"""
OpenAI LLM Provider implementation.
Provides integration with OpenAI's GPT models via their API.
"""

import logging
import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.logging_config import get_logger
from .base_provider import BaseLLMProvider
from .file_logger import get_openai_file_logger
from i18n import _


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider for LLM operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = get_logger("llm.openai_provider")
        self.file_logger = get_openai_file_logger()
        self.settings_manager = None
        self.api_key: Optional[str] = None
        self.model: str = "gpt-4"
        self.base_url: str = "https://api.openai.com/v1"
        self.max_tokens: int = 512
        self.temperature: float = 0.7
        self.top_p: float = 1.0
        self.presence_penalty: float = 0.0
        self.frequency_penalty: float = 0.0
        self.timeout: int = 30
        self.session = requests.Session()
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the OpenAI provider with settings."""
        try:
            self.api_key = config.get('api_key', '')
            self.model = config.get('model', 'gpt-4')
            self.base_url = config.get('base_url', 'https://api.openai.com/v1')
            self.max_tokens = config.get('max_tokens', 512)
            self.temperature = config.get('temperature', 0.7)
            self.top_p = config.get('top_p', 1.0)
            self.presence_penalty = config.get('presence_penalty', 0.0)
            self.frequency_penalty = config.get('frequency_penalty', 0.0)
            self.timeout = config.get('timeout', 30)
            
            # Configure session headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'Pisarz-Writer/1.0'
            })
            
            self.logger.info(f"OpenAI provider configured for model: {self.model}")
            return True
            
        except Exception as e:
            self.logger.error(_("Error configuring OpenAI provider: {}").format(e))
            return False
    
    def initialize(self) -> bool:
        """Initialize the OpenAI provider."""
        try:
            self.logger.info("Initializing OpenAI provider")
            
            # Import here to avoid circular imports
            from ..settings import get_llm_settings
            self.settings_manager = get_llm_settings()
            
            # Get configuration from settings
            provider_config = self.settings_manager.get_provider_config('openai')
            if not provider_config:
                self.logger.error(_("OpenAI provider configuration not found"))
                return False
            
            # Load settings
            self.api_key = provider_config.get_setting('api_key', '')
            self.model = provider_config.get_setting('model', 'gpt-4')
            self.base_url = provider_config.get_setting('base_url', 'https://api.openai.com/v1')
            self.max_tokens = provider_config.get_setting('max_tokens', 512)
            self.temperature = provider_config.get_setting('temperature', 0.7)
            self.top_p = provider_config.get_setting('top_p', 1.0)
            self.presence_penalty = provider_config.get_setting('presence_penalty', 0.0)
            self.frequency_penalty = provider_config.get_setting('frequency_penalty', 0.0)
            self.timeout = provider_config.get_setting('timeout', 30)
            
            if not self.api_key:
                self.logger.error(_("OpenAI API key not configured"))
                return False
            
            # Configure session headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'Pisarz-Writer/1.0'
            })
            
            # Test connection by making a simple API call
            health_status = self.get_health_status()
            if health_status['status'] == 'healthy':
                self.logger.info(_("OpenAI provider initialized successfully"))
                return True
            else:
                self.logger.error(_("OpenAI provider initialization failed: {}").format(health_status['message']))
                return False
                
        except Exception as e:
            self.logger.error(_("Error initializing OpenAI provider: {}").format(e))
            return False
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available and configured."""
        try:
            # Check if API key is configured
            if not self.api_key or self.api_key == 'test-key-placeholder':
                return False
            
            # Check if basic configuration is valid
            if not self.model or not self.base_url:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking OpenAI availability: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI's API."""
        try:
            # Merge provider defaults with kwargs
            params = {
                'model': self.model,
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                'temperature': kwargs.get('temperature', self.temperature),
                'top_p': kwargs.get('top_p', self.top_p),
                'presence_penalty': kwargs.get('presence_penalty', self.presence_penalty),
                'frequency_penalty': kwargs.get('frequency_penalty', self.frequency_penalty)
            }
            
            # Build the request payload
            payload = {
                'model': params['model'],
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': params['max_tokens'],
                'temperature': params['temperature'],
                'top_p': params['top_p'],
                'presence_penalty': params['presence_penalty'],
                'frequency_penalty': params['frequency_penalty'],
                'stream': False
            }
            
            # Log detailed request information
            self.logger.info(f"=== OPENAI REQUEST ===")
            self.logger.info(f"URL: {self.base_url}/chat/completions")
            self.logger.info(f"Model: {params['model']}")
            self.logger.info(f"Prompt length: {len(prompt)} characters")
            self.logger.info(f"Prompt preview: {prompt[:200]}...")
            self.logger.info(f"Parameters: max_tokens={params['max_tokens']}, temp={params['temperature']}, "
                           f"top_p={params['top_p']}, presence_penalty={params['presence_penalty']}, "
                           f"frequency_penalty={params['frequency_penalty']}")
            self.logger.info(f"Timeout: {self.timeout} seconds")
            
            # Log full prompt if debug logging enabled
            self.logger.debug(f"=== FULL PROMPT ===\n{prompt}\n=== END PROMPT ===")
            
            # Log request to file
            self.file_logger.log_request(prompt, payload, {
                "Model": params['model'],
                "Base URL": self.base_url
            })
            
            # Make the API request
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    
                    self.logger.info(f"=== OPENAI RESPONSE ===")
                    self.logger.info(f"Response length: {len(content)} characters")
                    self.logger.info(f"Response preview: {content[:200]}...")
                    
                    # Log usage information if available
                    if 'usage' in data:
                        usage = data['usage']
                        self.logger.info(f"Token usage - Prompt: {usage.get('prompt_tokens', 0)}, "
                                       f"Completion: {usage.get('completion_tokens', 0)}, "
                                       f"Total: {usage.get('total_tokens', 0)}")
                    
                    # Log response to file
                    stats = {}
                    if 'usage' in data:
                        usage = data['usage']
                        stats = {
                            "Prompt tokens": usage.get('prompt_tokens', 0),
                            "Completion tokens": usage.get('completion_tokens', 0),
                            "Total tokens": usage.get('total_tokens', 0)
                        }
                    
                    if 'model' in data:
                        stats["Model used"] = data['model']
                    
                    if 'id' in data:
                        stats["Request ID"] = data['id']
                    
                    self.file_logger.log_response(content, data, stats)
                    
                    return content
                else:
                    self.logger.error("No choices returned from OpenAI API")
                    return ""
            else:
                error_msg = f"OpenAI API error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return ""
                
        except requests.exceptions.Timeout:
            self.logger.error("OpenAI API request timed out")
            return ""
        except requests.exceptions.RequestException as e:
            self.logger.error(f"OpenAI API request failed: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"Error generating text with OpenAI: {e}")
            return ""
    
    def get_health_status(self) -> Dict[str, Any]:
        """Check OpenAI API health and connectivity."""
        try:
            if not self.api_key:
                return {
                    'status': 'unhealthy',
                    'message': 'API key not configured',
                    'details': {}
                }
            
            # Test with a simple models list request
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get('data', []))
                
                # Check if our configured model is available
                available_models = [model['id'] for model in data.get('data', [])]
                model_available = self.model in available_models
                
                return {
                    'status': 'healthy',
                    'message': f'Connected to OpenAI API ({model_count} models available)',
                    'details': {
                        'model_configured': self.model,
                        'model_available': model_available,
                        'total_models': model_count,
                        'api_responsive': True
                    }
                }
            elif response.status_code == 401:
                return {
                    'status': 'unhealthy',
                    'message': 'Invalid API key',
                    'details': {'error_code': 401}
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': f'API error: {response.status_code}',
                    'details': {'error_code': response.status_code, 'error_text': response.text}
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'unhealthy',
                'message': 'Connection timeout',
                'details': {'timeout': self.timeout}
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'unhealthy',
                'message': f'Connection error: {str(e)}',
                'details': {'exception': str(e)}
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {str(e)}',
                'details': {'exception': str(e)}
            }
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available OpenAI models."""
        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model_data in data.get('data', []):
                    # Filter for GPT models that support chat completions
                    model_id = model_data.get('id', '')
                    if any(prefix in model_id for prefix in ['gpt-3.5', 'gpt-4']):
                        models.append({
                            'name': model_id,
                            'id': model_id,
                            'object': model_data.get('object', 'model'),
                            'created': model_data.get('created', 0),
                            'owned_by': model_data.get('owned_by', 'openai')
                        })
                
                # Sort by model name
                models.sort(key=lambda x: x['name'])
                return models
            else:
                self.logger.error(f"Failed to get OpenAI models: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting OpenAI models: {e}")
            return []
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.session:
                self.session.close()
            self.logger.debug("OpenAI provider cleaned up")
        except Exception as e:
            self.logger.error(f"Error during OpenAI provider cleanup: {e}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the OpenAI provider."""
        return {
            'name': 'OpenAI',
            'model': self.model,
            'base_url': self.base_url,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'presence_penalty': self.presence_penalty,
            'frequency_penalty': self.frequency_penalty,
            'timeout': self.timeout,
            'api_key_configured': bool(self.api_key)
        }
    
