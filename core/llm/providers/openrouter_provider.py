"""
OpenRouter LLM Provider implementation.
Provides integration with OpenRouter.ai's API for accessing multiple AI models.
"""

import logging
import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.logging_config import get_logger
from .base_provider import BaseLLMProvider
from .file_logger import get_openrouter_file_logger
from i18n import _


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter.ai provider for accessing multiple AI models."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.file_logger = get_openrouter_file_logger()
        self.api_key: Optional[str] = None
        self.model: str = "openai/gpt-3.5-turbo"
        self.base_url: str = "https://openrouter.ai/api/v1"
        self.max_tokens: int = 512
        self.temperature: float = 0.7
        self.top_p: float = 1.0
        self.presence_penalty: float = 0.0
        self.frequency_penalty: float = 0.0
        self.timeout: int = 30
        self.session = requests.Session()
        self.site_url: Optional[str] = None
        self.app_name: Optional[str] = None
    
    def _get_provider_name(self) -> str:
        """Get the provider name for configuration lookup."""
        return 'openrouter'
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the OpenRouter provider with settings."""
        try:
            self.api_key = config.get('api_key', '')
            self.model = config.get('model', 'openai/gpt-3.5-turbo')
            self.base_url = config.get('base_url', 'https://openrouter.ai/api/v1')
            self.max_tokens = config.get('max_tokens', 512)
            self.temperature = config.get('temperature', 0.7)
            self.top_p = config.get('top_p', 1.0)
            self.presence_penalty = config.get('presence_penalty', 0.0)
            self.frequency_penalty = config.get('frequency_penalty', 0.0)
            self.timeout = config.get('timeout', 30)
            self.site_url = config.get('site_url', None)
            self.app_name = config.get('app_name', 'Pisarz-Writer')
            
            # Configure session headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Add optional headers for usage tracking
            if self.site_url:
                headers['HTTP-Referer'] = self.site_url
            if self.app_name:
                headers['X-Title'] = self.app_name
            
            self.session.headers.update(headers)
            
            self.logger.info(f"OpenRouter provider configured for model: {self.model}")
            return True
            
        except Exception as e:
            self.logger.error(_("Error configuring OpenRouter provider: {}").format(e))
            return False
    
    def _load_provider_settings(self, provider_config) -> bool:
        """Load OpenRouter-specific settings from configuration."""
        try:
            # Load settings
            self.api_key = provider_config.get_setting('api_key', '')
            self.model = provider_config.get_setting('model', 'openai/gpt-3.5-turbo')
            self.base_url = provider_config.get_setting('base_url', 'https://openrouter.ai/api/v1')
            self.max_tokens = provider_config.get_setting('max_tokens', 512)
            self.temperature = provider_config.get_setting('temperature', 0.7)
            self.top_p = provider_config.get_setting('top_p', 1.0)
            self.presence_penalty = provider_config.get_setting('presence_penalty', 0.0)
            self.frequency_penalty = provider_config.get_setting('frequency_penalty', 0.0)
            self.timeout = provider_config.get_setting('timeout', 30)
            self.site_url = provider_config.get_setting('site_url', None)
            self.app_name = provider_config.get_setting('app_name', 'Pisarz-Writer')
            
            if not self.api_key:
                self.logger.error(_("OpenRouter API key not configured"))
                return False
            
            # Configure session headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Add optional headers for usage tracking
            if self.site_url:
                headers['HTTP-Referer'] = self.site_url
            if self.app_name:
                headers['X-Title'] = self.app_name
            
            self.session.headers.update(headers)
            
            return True
            
        except Exception as e:
            self.logger.error(_("Error loading OpenRouter settings: {}").format(e))
            return False
    
    def initialize(self) -> bool:
        """Initialize the OpenRouter provider using common pattern."""
        return self.initialize_with_common_pattern()
    
    def is_available(self) -> bool:
        """Check if OpenRouter provider is available and configured."""
        try:
            # Check if API key is configured
            if not self.api_key or self.api_key == 'test-key-placeholder':
                return False
            
            # Check if basic configuration is valid
            if not self.model or not self.base_url:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking OpenRouter availability: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenRouter's API."""
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
            
            # Log detailed request information using base class utility
            request_params = {
                'model': params['model'],
                'max_tokens': params['max_tokens'],
                'temperature': params['temperature'],
                'top_p': params['top_p'],
                'presence_penalty': params['presence_penalty'],
                'frequency_penalty': params['frequency_penalty']
            }
            self.log_request_details("OpenRouter", f"{self.base_url}/chat/completions", prompt, request_params, self.timeout)
            
            
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
                    
                    # Log response using base class utility
                    self.log_response_details("OpenRouter", content, response.status_code)
                    
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
                    
                    
                    return content
                else:
                    self.logger.error("No choices returned from OpenRouter API")
                    return ""
            else:
                error_msg = f"OpenRouter API error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return ""
                
        except Exception as e:
            return self.handle_request_exception("OpenRouter", e, "text generation")
    
    def generate_streaming(self, prompt: str, chunk_callback, **kwargs) -> str:
        """Generate text using OpenRouter's API with streaming support."""
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
            
            # Build the request payload with streaming enabled
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
                'stream': True  # Enable streaming
            }
            
            # Log detailed request information
            self.logger.info(f"=== OPENROUTER STREAMING REQUEST ===")
            self.logger.info(f"URL: {self.base_url}/chat/completions")
            self.logger.info(f"Model: {params['model']}")
            self.logger.info(f"Prompt length: {len(prompt)} characters")
            self.logger.info(f"Streaming: True")
            
            
            # Make the streaming API request
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                full_content = ""
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            
                            if data_str.strip() == '[DONE]':
                                break
                                
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    
                                    if content:
                                        full_content += content
                                        # Call the chunk callback with the new content
                                        if chunk_callback:
                                            chunk_callback(content)
                                            
                            except json.JSONDecodeError:
                                # Skip invalid JSON lines
                                continue
                
                self.logger.info(f"=== OPENROUTER STREAMING RESPONSE ===")
                self.logger.info(f"Total response length: {len(full_content)} characters")
                
                
                return full_content
            else:
                error_msg = f"OpenRouter API streaming error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return ""
                
        except Exception as e:
            return self.handle_request_exception("OpenRouter", e, "streaming generation")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Check OpenRouter API health and connectivity."""
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
                    'message': f'Connected to OpenRouter API ({model_count} models available)',
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
        """Get list of available OpenRouter models."""
        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model_data in data.get('data', []):
                    models.append({
                        'name': model_data.get('id', ''),
                        'id': model_data.get('id', ''),
                        'context_length': model_data.get('context_length', 0),
                        'pricing': model_data.get('pricing', {}),
                        'top_provider': model_data.get('top_provider', {}),
                        'per_request_limits': model_data.get('per_request_limits', {})
                    })
                
                # Sort by model name
                models.sort(key=lambda x: x['name'])
                return models
            else:
                self.logger.error(f"Failed to get OpenRouter models: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting OpenRouter models: {e}")
            return []
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.session:
                self.session.close()
            self.logger.debug("OpenRouter provider cleaned up")
        except Exception as e:
            self.logger.error(f"Error during OpenRouter provider cleanup: {e}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the OpenRouter provider."""
        return {
            'name': 'OpenRouter',
            'model': self.model,
            'base_url': self.base_url,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'presence_penalty': self.presence_penalty,
            'frequency_penalty': self.frequency_penalty,
            'timeout': self.timeout,
            'api_key_configured': bool(self.api_key),
            'site_url': self.site_url,
            'app_name': self.app_name
        }
    