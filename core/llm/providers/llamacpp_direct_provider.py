"""
Direct llama.cpp provider using llama-cpp-python library.
This provider connects directly to the llama.cpp library for better performance.
"""

import logging
from typing import Dict, Any, Optional
from .base_provider import BaseLLMProvider
from ..settings import get_llm_settings
from .file_logger import get_llamacpp_file_logger
from i18n import _


class LlamaCppDirectProvider(BaseLLMProvider):
    """Provider for llama.cpp using direct library connection."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.settings_manager = get_llm_settings()
        self.file_logger = get_llamacpp_file_logger()
        self.llm = None
        
    def initialize(self) -> bool:
        """Initialize the llama.cpp provider."""
        try:
            self.logger.info("Initializing llama.cpp direct provider")
            
            # Import llama_cpp here to avoid import errors if not installed
            import llama_cpp
            
            # Get configuration from settings
            provider_config = self.settings_manager.get_provider_config('llamacpp')
            if not provider_config:
                self.logger.error(_("llama.cpp provider configuration not found"))
                return False
            
            # Get model path from config
            model_path = provider_config.get_setting('model_path', '')
            if not model_path:
                self.logger.error(_("Model path not specified in llama.cpp config"))
                return False
                
            # Initialize llama.cpp model
            self.llm = llama_cpp.Llama(
                model_path=model_path,
                n_ctx=provider_config.get_setting('context_size', 4096),
                n_threads=provider_config.get_setting('threads', 4),
                n_gpu_layers=provider_config.get_setting('gpu_layers', 0),
                verbose=False
            )
            
            self.logger.info(_("llama.cpp direct provider initialized with model: {}").format(model_path))
            self._initialized = True
            return True
            
        except ImportError:
            self.logger.error(_("llama-cpp-python library not installed. Run: pip install llama-cpp-python"))
            return False
        except Exception as e:
            self.logger.error(_("Failed to initialize llama.cpp direct provider: {}").format(e))
            return False
    
    def is_available(self) -> bool:
        """Check if llama.cpp provider is available."""
        return self._initialized and self.llm is not None
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from llama.cpp."""
        if not self.is_available():
            raise RuntimeError(_("llama.cpp direct provider not initialized"))
        
        # Get provider configuration
        provider_config = self.settings_manager.get_provider_config('llamacpp')
        
        # Extract parameters
        max_tokens = kwargs.get('max_tokens', provider_config.get_setting('max_tokens', 2000))
        temperature = kwargs.get('temperature', provider_config.get_setting('temperature', 0.7))
        top_p = kwargs.get('top_p', provider_config.get_setting('top_p', 0.9))
        top_k = kwargs.get('top_k', provider_config.get_setting('top_k', 40))
        repeat_penalty = kwargs.get('repeat_penalty', provider_config.get_setting('repeat_penalty', 1.1))
        
        # Log detailed request information
        self.logger.info(f"=== LLAMA.CPP DIRECT REQUEST ===")
        self.logger.info(f"Prompt length: {len(prompt)} characters")
        self.logger.info(f"Prompt preview: {prompt[:200]}...")
        self.logger.info(f"Parameters: max_tokens={max_tokens}, temp={temperature}")
        
        # Log full prompt if debug logging enabled
        self.logger.debug(f"=== FULL PROMPT ===\\n{prompt}\\n=== END PROMPT ===")
        
        # Log request to file
        self.file_logger.log_request(prompt, {
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'top_k': top_k,
            'repeat_penalty': repeat_penalty
        }, {"provider": "llamacpp_direct"})
        
        try:
            # Generate response
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=kwargs.get('stop', []),
                echo=False
            )
            
            # Extract text from response
            if isinstance(response, dict) and 'choices' in response:
                text = response['choices'][0]['text']
            else:
                text = str(response)
            
            self._log_response(text)
            
            # Return raw response without any cleaning
            return text
            
        except Exception as e:
            self.logger.error(_("Error in llama.cpp direct generation: {}").format(e))
            raise RuntimeError(_("Generation failed: {}").format(e))
    
    def _log_response(self, text: str) -> None:
        self.logger.info("=== LLAMA.CPP DIRECT RESPONSE ===")
        self.logger.info("Response length: %d chars", len(text))
        self.logger.info("Response preview: %s…", text[:200])
        self.file_logger.log_response(text, {"length": len(text)})
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get llama.cpp direct provider information."""
        info = super().get_provider_info()
        info.update({
            'type': 'llamacpp_direct',
            'supports_streaming': False,
            'supports_system_prompt': True,
            'library': 'llama-cpp-python'
        })
        return info
    
    def cleanup(self):
        """Clean up provider resources."""
        if self.llm:
            del self.llm
            self.llm = None
        super().cleanup()