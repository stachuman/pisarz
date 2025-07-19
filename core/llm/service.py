"""
Basic LLM service for Pisarz application.
Provides core functionality for AI-powered writing assistance.
"""

import logging
from typing import Dict, Any, Optional
from core.logging_config import get_logger
from .providers.base_provider import BaseLLMProvider
from .providers.mock_provider import MockLLMProvider
from .providers.llamacpp_provider import LlamaCppProvider
from .tasks.registry import TaskRegistry
from .settings import get_llm_settings
from .context.manager import ContextManager
from .templates.engine import TemplateEngine


class LLMService:
    """Main service for LLM operations."""
    
    def __init__(self):
        self.logger = get_logger("llm.service")
        self.provider: Optional[BaseLLMProvider] = None
        self.task_registry = TaskRegistry()
        self.settings_manager = get_llm_settings()
        self.context_manager = ContextManager()
        self.template_engine = TemplateEngine()
        self._initialized = False
        
    def initialize(self, provider_name: Optional[str] = None):
        """Initialize the LLM service with specified provider."""
        try:
            # Use current provider from settings if not specified
            if provider_name is None:
                provider_name = self.settings_manager.get_current_provider()
            
            self.logger.info(f"Initializing LLM service with provider: {provider_name}")
            
            # Validate provider configuration
            is_valid, message = self.settings_manager.validate_provider_config(provider_name)
            if not is_valid:
                self.logger.warning(f"Provider {provider_name} config invalid: {message}")
                if provider_name != "mock":
                    self.logger.info("Falling back to mock provider")
                    provider_name = "mock"
            
            # Create provider instance
            if provider_name == "mock":
                self.provider = MockLLMProvider()
            elif provider_name == "llamacpp":
                self.provider = LlamaCppProvider()
            elif provider_name == "ollama":
                from .providers.ollama_provider import OllamaProvider
                self.provider = OllamaProvider()
            elif provider_name == "openai":
                from .providers.openai_provider import OpenAIProvider
                self.provider = OpenAIProvider()
            else:
                self.logger.warning(f"Provider {provider_name} not yet implemented, using mock")
                self.provider = MockLLMProvider()
                provider_name = "mock"
            
            # Initialize the provider
            if not self.provider.initialize():
                self.logger.warning(f"Failed to initialize {provider_name} provider, falling back to mock")
                if provider_name != "mock":
                    # Fall back to mock provider
                    self.provider = MockLLMProvider()
                    if self.provider.initialize():
                        provider_name = "mock"
                        self.logger.info("Successfully initialized with mock provider fallback")
                    else:
                        self.logger.error("Even mock provider failed to initialize")
                        self._initialized = False
                        return
                else:
                    self.logger.error("Mock provider failed to initialize")
                    self._initialized = False
                    return
            
            # Update current provider in settings
            self.settings_manager.set_current_provider(provider_name)
            
            self._initialized = True
            self.logger.info(f"LLM service initialized successfully with {provider_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM service: {e}")
            # Don't raise - allow application to continue without LLM
            self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized and self.provider is not None
    
    def execute_task(self, task_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute a task with given context."""
        if not self.is_initialized():
            raise RuntimeError("LLM service not initialized")
        
        try:
            self.logger.info(f"Executing task: {task_id}")
            
            # Use enhanced template system for context building
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            
            # Use current context if none provided
            if context is None:
                context = self.context_manager.get_current_context()
                self.logger.debug("Using current context from context manager")
            
            # Build enhanced context based on template configuration
            enhanced_context = template_manager.build_enhanced_context(task_id, context)
            self.logger.debug("Enhanced context built using template configuration")
            
            # Generate prompt using enhanced template system
            prompt = self._generate_enhanced_prompt(task_id, enhanced_context)
            self.logger.debug(f"Generated prompt: {prompt[:200]}...")
            
            # Get template-specific LLM parameters
            llm_params = template_manager.get_template_llm_params(task_id)
            
            # Generate response with template-specific parameters
            raw_response = self.provider.generate(prompt, **llm_params)
            response = self._clean_response(raw_response)
            
            self.logger.info(f"Task {task_id} completed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {e}")
            raise
    
    def _clean_response(self, response: str) -> str:
        """Clean LLM response by removing think tags and formatting artifacts."""
        import re
        
        # Remove <think>...</think> blocks (case insensitive, multiline)
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any remaining think tag artifacts
        response = re.sub(r'</?think[^>]*>', '', response, flags=re.IGNORECASE)
        
        # Remove excessive whitespace and normalize line breaks
        response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
        response = response.strip()
        
        # If response is empty after cleaning, return a placeholder
        if not response:
            response = _("Generated response was empty after processing.")
        
        return response
    
    def _generate_enhanced_prompt(self, task_id: str, context: Dict[str, Any]) -> str:
        """
        Generate prompt using enhanced template system.
        
        Args:
            task_id: Task identifier
            context: Enhanced context variables
            
        Returns:
            Generated prompt string
        """
        try:
            from core.llm.templates import get_template_manager
            template_manager = get_template_manager()
            
            # Get template configuration
            template_config = template_manager.get_template(task_id)
            if not template_config:
                self.logger.warning(f"Enhanced template {task_id} not found, using fallback")
                return self._generate_prompt(task_id, context)
            
            # Use Jinja2 to render the template content
            from jinja2 import Template
            template = Template(template_config.template_content)
            prompt = template.render(context)
            
            self.logger.debug(f"Prompt generated using enhanced template {task_id}")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Failed to generate enhanced prompt for {task_id}: {e}")
            return self._generate_prompt(task_id, context)
    
    def _generate_prompt(self, task_id: str, context: Dict[str, Any]) -> str:
        """
        Generate prompt for task using legacy template engine (fallback).
        
        Args:
            task_id: Task identifier
            context: Context variables
            
        Returns:
            Generated prompt string
        """
        try:
            # Map task_id to template name
            template_name = f"{task_id}.j2"
            
            # Check if template exists
            if not self.template_engine.template_exists(template_name):
                self.logger.warning(f"Template {template_name} not found, using fallback")
                return self._generate_fallback_prompt(task_id, context)
            
            # Render template
            prompt = self.template_engine.render_template(template_name, context)
            
            self.logger.debug(f"Prompt generated using legacy template {template_name}")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Failed to generate prompt for {task_id}: {e}")
            return self._generate_fallback_prompt(task_id, context)
    
    def _generate_fallback_prompt(self, task_id: str, context: Dict[str, Any]) -> str:
        """
        Generate fallback prompt when template is not available.
        
        Args:
            task_id: Task identifier
            context: Context variables
            
        Returns:
            Fallback prompt string
        """
        try:
            # Get task definition from registry
            task_def = self.task_registry.get_task(task_id)
            if task_def:
                return task_def.build_prompt(context)
            
            # Ultimate fallback - basic prompt
            current_text = context.get('current_text', '')
            scene_summary = context.get('scene_summary', '')
            
            fallback_prompt = f"""Continue the following text naturally:

Scene Context: {scene_summary}

Current Text:
{current_text}

Please continue the text in a natural way:"""
            
            self.logger.debug(f"Using fallback prompt for {task_id}")
            return fallback_prompt
            
        except Exception as e:
            self.logger.error(f"Failed to generate fallback prompt: {e}")
            return "Please continue the text naturally."
    
    def get_available_tasks(self) -> list:
        """Get list of available tasks."""
        return self.task_registry.get_task_ids()
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific task."""
        task_def = self.task_registry.get_task(task_id)
        if not task_def:
            return None
        
        return {
            'id': task_def.id,
            'name': task_def.name,
            'description': task_def.description,
            'parameters': [param.to_dict() for param in task_def.parameters]
        }
    

    def get_service_info(self) -> Dict[str, Any]:
        """Get service status information."""
        return {
            'initialized': self.is_initialized(),
            'provider': self.provider.__class__.__name__ if self.provider else None,
            'available_tasks': len(self.task_registry.get_task_ids()),
            'available_templates': len(self.template_engine.list_templates()),
            'current_context': self.context_manager.get_context_summary()
        }
    
    def get_context_manager(self) -> ContextManager:
        """Get context manager instance."""
        return self.context_manager
    
    def get_template_engine(self) -> TemplateEngine:
        """Get template engine instance."""
        return self.template_engine
    
    def update_scene_context(self, scene_id: int, scene_title: str, scene_content: str):
        """Update current scene context."""
        self.context_manager.set_scene_context(scene_id, scene_title, scene_content)
    
    def update_project_context(self, project_name: str, project_path: Optional[str] = None):
        """Update current project context."""
        from pathlib import Path
        path = Path(project_path) if project_path else None
        self.context_manager.set_project_context(project_name, path)
    
    def update_text_selection(self, selected_text: str, current_text: str = ""):
        """Update current text selection context."""
        self.context_manager.set_text_selection(selected_text, current_text)
