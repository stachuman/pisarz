"""
Ollama provider for local LLM inference.
Provides integration with Ollama API for running local language models.
"""

import json
import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from core.logging_config import get_logger
from .base_provider import BaseLLMProvider
from .file_logger import get_ollama_file_logger
from i18n import _


class OllamaProvider(BaseLLMProvider):
    """Provider for Ollama API."""
    
    def __init__(self):
        super().__init__()
        self.name = "ollama"
        self.logger = get_logger("llm.provider.ollama")
        self.file_logger = get_ollama_file_logger()
        
        # Connection settings
        self.host = "192.168.1.102"
        self.port = 11434
        self.timeout = 120  # 2 minutes
        self.model = ""
        
        # Generation parameters
        self.max_tokens = 512
        self.temperature = 0.7
        self.top_p = 0.9
        self.top_k = 40
        self.repeat_penalty = 1.1
        
        self._session = None
        self._available_models = []
    
    def configure(self, settings: Dict[str, Any]):
        """Configure the provider with settings."""
        try:
            self.host = settings.get('host', self.host)
            self.port = settings.get('port', self.port)
            self.timeout = settings.get('timeout', self.timeout)
            self.model = settings.get('model', self.model)
            
            # Generation parameters
            self.max_tokens = settings.get('max_tokens', self.max_tokens)
            self.temperature = settings.get('temperature', self.temperature)
            self.top_p = settings.get('top_p', self.top_p)
            self.top_k = settings.get('top_k', self.top_k)
            self.repeat_penalty = settings.get('repeat_penalty', self.repeat_penalty)
            
            self.logger.info(f"Ollama provider configured: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(_("Error configuring Ollama provider: {}").format(e))
            return False
    
    def initialize(self) -> bool:
        """Initialize the provider and check connection."""
        try:
            # Create session
            self._session = requests.Session()
            self._session.timeout = self.timeout
            
            # Test connection
            if not self._test_connection():
                return False
            
            # Load available models
            if not self._load_models():
                return False
            
            # Set default model if not specified
            if not self.model and self._available_models:
                self.model = self._available_models[0]['name']
                self.logger.info(f"Using default model: {self.model}")
            
            self.logger.info(_("Ollama provider initialized successfully"))
            return True
            
        except Exception as e:
            self.logger.error(_("Failed to initialize Ollama provider: {}").format(e))
            return False
    
    def _test_connection(self) -> bool:
        """Test connection to Ollama server."""
        try:
            base_url = f"http://{self.host}:{self.port}"
            
            # Test basic connectivity with tags endpoint
            response = self._session.get(
                urljoin(base_url, "/api/tags"),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(_("Ollama server connection successful"))
                return True
            else:
                self.logger.error(_("Ollama server returned status {}").format(response.status_code))
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(_("Failed to connect to Ollama server: {}").format(e))
            return False
    
    def _load_models(self) -> bool:
        """Load available models from Ollama."""
        try:
            base_url = f"http://{self.host}:{self.port}"
            
            response = self._session.get(
                urljoin(base_url, "/api/tags"),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self._available_models = data.get('models', [])
                
                model_names = [model['name'] for model in self._available_models]
                self.logger.info(f"Loaded {len(self._available_models)} models: {model_names}")
                return True
            else:
                self.logger.error(f"Failed to load models: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama."""
        if not self._session:
            raise RuntimeError("Provider not initialized")
        
        if not self.model:
            raise RuntimeError("No model specified")
        
        try:
            # Merge kwargs with instance settings
            params = self._build_generation_params(**kwargs)
            
            # Build request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,  # Use non-streaming for simplicity
                "options": params
            }
            
            # Log detailed request information
            self.logger.info(f"=== OLLAMA REQUEST ===")
            base_url = f"http://{self.host}:{self.port}"
            self.logger.info(f"URL: {urljoin(base_url, '/api/generate')}")
            self.logger.info(f"Model: {self.model}")
            self.logger.info(f"Prompt length: {len(prompt)} characters")
            self.logger.info(f"Prompt preview: {prompt[:200]}...")
            self.logger.info(f"Parameters: {params}")
            self.logger.info(f"Timeout: {self.timeout} seconds")
            
            # Log full prompt if debug logging enabled
            self.logger.debug(f"=== FULL PROMPT ===\n{prompt}\n=== END PROMPT ===")
            
            
            # Make request
            response = self._session.post(
                urljoin(base_url, "/api/generate"),
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get('response', '')
                
                self.logger.info(f"=== OLLAMA RESPONSE ===")
                self.logger.info(f"Response length: {len(generated_text)} characters")
                self.logger.info(f"Response preview: {generated_text[:200]}...")
                
                # Log generation stats
                if 'eval_count' in data and 'total_duration' in data:
                    eval_count = data['eval_count']
                    total_duration_ns = data['total_duration']
                    total_duration_s = total_duration_ns / 1_000_000_000
                    tokens_per_second = eval_count / total_duration_s if total_duration_s > 0 else 0
                    
                    self.logger.info(f"Generated {eval_count} tokens in {total_duration_s:.2f}s "
                                   f"({tokens_per_second:.2f} tokens/s)")
                
                # Log response to file
                stats = {}
                if 'eval_count' in data and 'total_duration' in data:
                    eval_count = data['eval_count']
                    total_duration_ns = data['total_duration']
                    total_duration_s = total_duration_ns / 1_000_000_000
                    tokens_per_second = eval_count / total_duration_s if total_duration_s > 0 else 0
                    stats = {
                        "Eval count": f"{eval_count} tokens",
                        "Total duration": f"{total_duration_s:.2f}s",
                        "Tokens/second": f"{tokens_per_second:.2f}"
                    }
                
                
                return generated_text
            else:
                error_msg = f"Ollama generation failed: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    pass
                
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = f"Ollama request timed out after {self.timeout} seconds"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama request failed: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Ollama generation error: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _build_generation_params(self, **kwargs) -> Dict[str, Any]:
        """Build generation parameters for Ollama."""
        # Start with instance defaults
        params = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
            "num_predict": self.max_tokens,
        }
        
        # Override with kwargs (map from common names to Ollama names)
        if 'temperature' in kwargs:
            params['temperature'] = kwargs['temperature']
        if 'top_p' in kwargs:
            params['top_p'] = kwargs['top_p']
        if 'top_k' in kwargs:
            params['top_k'] = kwargs['top_k']
        if 'repeat_penalty' in kwargs:
            params['repeat_penalty'] = kwargs['repeat_penalty']
        if 'max_tokens' in kwargs:
            params['num_predict'] = kwargs['max_tokens']
        
        # Add any custom parameters from kwargs
        custom_params = kwargs.get('custom_params', {})
        if isinstance(custom_params, dict):
            params.update(custom_params)
        
        return params
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._session is not None and bool(self._available_models)
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        return self._available_models.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model."""
        if not self.model:
            return {}
        
        for model in self._available_models:
            if model['name'] == self.model:
                return {
                    'name': model['name'],
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at', ''),
                    'digest': model.get('digest', ''),
                    'details': model.get('details', {})
                }
        
        return {'name': self.model}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status."""
        try:
            if not self._session:
                return {"status": "not_initialized", "message": "Provider not initialized"}
            
            # Test connection
            base_url = f"http://{self.host}:{self.port}"
            response = self._session.get(
                urljoin(base_url, "/api/tags"),
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "message": f"Connected to {self.host}:{self.port}",
                    "model": self.model,
                    "models_available": len(self._available_models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Server returned HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def cleanup(self):
        """Clean up resources."""
        if self._session:
            self._session.close()
            self._session = None
        
        self.logger.info("Ollama provider cleaned up")
    
