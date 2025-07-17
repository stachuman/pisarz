"""
Fixed llama.cpp provider using synchronous requests.
Connects to a local llama.cpp server for text generation.
"""

import json
import logging
import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional
from .base_provider import BaseLLMProvider
from ..settings import get_llm_settings
from .file_logger import get_llamacpp_file_logger
from i18n import _


class LlamaCppProvider(BaseLLMProvider):
    """Provider for llama.cpp local server using synchronous requests."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.settings_manager = get_llm_settings()
        self.file_logger = get_llamacpp_file_logger()
        self.base_url = ""
        
    def initialize(self) -> bool:
        """Initialize the llama.cpp provider."""
        try:
            self.logger.info("Initializing llama.cpp provider")
            
            # Get configuration from settings
            provider_config = self.settings_manager.get_provider_config('llamacpp')
            if not provider_config:
                self.logger.error(_("llama.cpp provider configuration not found"))
                return False
            
            # Build base URL
            host = provider_config.get_setting('host', 'localhost')
            port = provider_config.get_setting('port', 8080)
            self.base_url = f"http://{host}:{port}"
            
            # Validate configuration
            is_valid, message = self.settings_manager.validate_provider_config('llamacpp')
            if not is_valid:
                self.logger.error(_("llama.cpp configuration invalid: {}").format(message))
                return False
            
            self.logger.info(_("llama.cpp provider initialized with URL: {}").format(self.base_url))
            self._initialized = True
            return True
            
        except Exception as e:
            self.logger.error(_("Failed to initialize llama.cpp provider: {}").format(e))
            return False
    
    def is_available(self) -> bool:
        """Check if llama.cpp server is available."""
        if not self._initialized:
            return False
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Server availability check failed: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from llama.cpp server."""
        if not self._initialized:
            raise RuntimeError(_("llama.cpp provider not initialized"))
        
        def _get(name: str, default: Any) -> Any:
            return kwargs.pop(name, provider_config.get_setting(name, default))
        
        
        # Check server availability
        if not self.is_available():
            raise RuntimeError(_("llama.cpp server is not available"))
        
        # Get provider configuration
        provider_config = self.settings_manager.get_provider_config('llamacpp')
        
        # Build request payload
        payload = {
            'prompt': prompt,
            'n_predict': provider_config.get_setting('max_tokens', 4000),
            'temperature': provider_config.get_setting('temperature', 0.7),
            'top_p': provider_config.get_setting('top_p', 0.9),
            'top_k': provider_config.get_setting('top_k', 40),
            'repeat_penalty': provider_config.get_setting('repeat_penalty', 1.1),
            'seed': provider_config.get_setting('seed', -1),

            # No default stop tokens - let the model decide when to stop
        }

        stop_tokens = kwargs.pop("stop", provider_config.get_setting("stop", None))
        if stop_tokens:
            payload["stop"] = stop_tokens

        stream = bool(_get("stream", False))
        payload["stream"] = stream          

        # Add any additional parameters from kwargs
        # Map max_tokens to n_predict for llama.cpp compatibility
        if 'max_tokens' in kwargs:
            payload['n_predict'] = kwargs['max_tokens']
            kwargs = {k: v for k, v in kwargs.items() if k != 'max_tokens'}
        
        payload.update(kwargs)
        
        # Log detailed request information
        self.logger.info(f"=== LLAMA.CPP REQUEST ===")
        self.logger.info(f"URL: {self.base_url}/completion")
        self.logger.info(f"Prompt length: {len(prompt)} characters")
        self.logger.info(f"Prompt preview: {prompt[:200]}...")
        self.logger.info(f"Parameters: max_tokens={payload['n_predict']}, temp={payload['temperature']}")
        
        # Log full prompt if debug logging enabled
        self.logger.debug(f"=== FULL PROMPT ===\n{prompt}\n=== END PROMPT ===")
        
        # Send request
        timeout = provider_config.get_setting('timeout', 120)
        # Also check kwargs for timeout override
        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
            
        self.logger.info(f"Using timeout: {timeout} seconds")
        
        # Log request to file for easier inspection
        self.file_logger.log_request(prompt, payload, {"URL": f"{self.base_url}/completion"})
        
        try:
            if stream:
                text = self._generate_streaming(payload, timeout)
            else:
                text = self._generate_blocking(payload, timeout)
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(_("Request to llama.cpp server timed out")) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(_("Request to llama.cpp server failed: {}").format(exc)) from exc
        except Exception as exc:  # pragma: no cover
            self.logger.error(_("Error in llama.cpp generation: {}").format(exc))
            raise

        self._log_response(text)
        
        # Return raw response without any cleaning
        return text
                
     # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _generate_blocking(self, payload: Dict[str, Any], timeout: int) -> str:
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json; charset=utf-8',
            'Accept-Charset': 'utf-8'
        }
        
        # Ensure the payload is properly encoded
        import json
        payload_str = json.dumps(payload, ensure_ascii=False)
        
        r = requests.post(f"{self.base_url}/completion", 
                         data=payload_str.encode('utf-8'), 
                         timeout=timeout, 
                         headers=headers)
        if r.status_code != 200:
            raise RuntimeError(_("llama.cpp server error {}: {}").format(r.status_code, r.text))

        # Force UTF-8 encoding
        r.encoding = 'utf-8'
        
        # Get raw bytes and decode properly
        try:
            raw_bytes = r.content
            decoded_text = raw_bytes.decode('utf-8')
            data = json.loads(decoded_text)
        except UnicodeDecodeError:
            # Fallback to regular JSON parsing
            data = r.json()
        
        if "content" in data:
            return data["content"]
        if "choices" in data and data["choices"]:
            return data["choices"][0].get("text", "")
        return data.get("text", "")

    def _generate_streaming(self, payload: Dict[str, Any], timeout: int) -> str:
        """Collect content chunks from the llama.cpp SSE stream and return clean text."""
        url = f"{self.base_url}/completion"
        
        # Ensure proper encoding headers
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/plain; charset=utf-8',
            'Accept-Charset': 'utf-8'
        }
        
        # Ensure the payload is properly encoded
        import json
        payload_str = json.dumps(payload, ensure_ascii=False)
        
        with requests.post(url, 
                          data=payload_str.encode('utf-8'), 
                          stream=True, 
                          timeout=timeout, 
                          headers=headers) as r:
            if r.status_code != 200:
                raise RuntimeError(
                    _("llama.cpp server error {}: {}").format(r.status_code, r.text)
                )

            # Force UTF-8 encoding
            r.encoding = 'utf-8'
            
            pieces: list[str] = []
            for raw_line in r.iter_lines(decode_unicode=False, chunk_size=1024):
                if not raw_line:
                    # heartbeat / keep‑alive blank line
                    continue

                # Decode raw bytes to UTF-8 string
                try:
                    raw = raw_line.decode('utf-8')
                except UnicodeDecodeError:
                    # Skip malformed lines
                    continue

                # SSE lines look like:  "data: {...json...}"
                if raw.startswith("data:"):
                    raw = raw[5:].strip()

                # End‑of‑stream sentinel from llama.cpp
                if raw == "[DONE]":
                    break

                try:
                    chunk = json.loads(raw)
                except json.JSONDecodeError:
                    # If the server ever sends a plain‑text chunk, ignore it safely
                    self.logger.debug("Skipping non‑JSON SSE chunk: %s", raw[:120])
                    continue

                # Optional field "stop": true means model hit a stop condition
                if chunk.get("stop"):
                    break

                # /completion returns {"content": "..."}; /v1/chat/completions" returns choices
                if "content" in chunk:
                    pieces.append(chunk["content"])
                elif "choices" in chunk and chunk["choices"]:
                    pieces.append(chunk["choices"][0].get("delta", {}).get("content", ""))
                # else: silently ignore non‑content updates (timings, etc.)

            return "".join(pieces)
    
    def _log_response(self, text: str) -> None:
        self.logger.info("=== LLAMA.CPP RESPONSE ===")
        self.logger.info("Response length: %d chars", len(text))
        self.logger.info("Response preview: %s…", text[:200])
        self.file_logger.log_response(text, {"length": len(text)})
     
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        try:
            response = requests.get(f"{self.base_url}/props", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            self.logger.debug(f"Could not get model info: {e}")
            return {}
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get llama.cpp provider information."""
        info = super().get_provider_info()
        info.update({
            'type': 'llamacpp',
            'base_url': self.base_url,
            'supports_streaming': False,  # Disabled for now for simplicity
            'supports_system_prompt': True
        })
        
        # Add model info if available
        try:
            model_info = self.get_model_info()
            if model_info:
                info['model_info'] = model_info
        except:
            pass
        
        return info
    
    def cleanup(self):
        """Clean up provider resources."""
        # No session to clean up with requests
        super().cleanup()