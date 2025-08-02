"""
Centralized file logging utilities for LLM providers.
Eliminates code duplication across providers.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from core.logging_config import get_logger
from i18n import _


class LLMFileLogger:
    """Centralized file logger for LLM providers."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name.lower()
        self.logger = get_logger(f"llm.{self.provider_name}_file_logger")
    
    def log_request(self, prompt: str, payload: Dict[str, Any], extra_info: Dict[str, Any] = None):
        """Log request details to file."""
        try:
            log_dir = Path("logs/llm_requests")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = log_dir / f"{self.provider_name}_request_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== {self.provider_name.upper()} REQUEST LOG ===\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                
                # Add provider-specific info
                if extra_info:
                    for key, value in extra_info.items():
                        f.write(f"{key}: {value}\n")
                
                f.write(f"Payload: {json.dumps(payload, indent=2)}\n")
                f.write(f"\n=== FULL PROMPT ===\n")
                f.write(prompt)
                f.write(f"\n=== END PROMPT ===\n")
                
        except Exception as e:
            self.logger.warning(_("Failed to {} file: {}").format("log request to", e))
    
    def log_response(self, generated_text: str, full_response: Dict[str, Any], stats: Dict[str, Any] = None):
        """Log response details to file."""
        try:
            log_dir = Path("logs/llm_requests")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = log_dir / f"{self.provider_name}_response_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== {self.provider_name.upper()} RESPONSE LOG ===\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Generated text length: {len(generated_text)} characters\n")
                
                # Add provider-specific stats
                if stats:
                    for key, value in stats.items():
                        f.write(f"{key}: {value}\n")
                
                f.write(f"\n=== GENERATED TEXT ===\n")
                f.write(generated_text)
                f.write(f"\n=== FULL RESPONSE ===\n")
                f.write(json.dumps(full_response, indent=2, ensure_ascii=False))
                f.write(f"\n=== END RESPONSE ===\n")
                
        except Exception as e:
            self.logger.warning(_("Failed to {} file: {}").format("log response to", e))


# Provider-specific file logger factories
def get_llamacpp_file_logger() -> LLMFileLogger:
    """Get file logger for llama.cpp provider."""
    return LLMFileLogger("llamacpp")

def get_ollama_file_logger() -> LLMFileLogger:
    """Get file logger for Ollama provider."""
    return LLMFileLogger("ollama")

def get_openai_file_logger() -> LLMFileLogger:
    """Get file logger for OpenAI provider."""
    return LLMFileLogger("openai")

def get_mock_file_logger() -> LLMFileLogger:
    """Get file logger for mock provider."""
    return LLMFileLogger("mock")

def get_openrouter_file_logger() -> LLMFileLogger:
    """Get file logger for OpenRouter provider."""
    return LLMFileLogger("openrouter")