"""
Enhanced template configuration system for LLM operations.
Provides comprehensive template definitions with context configuration,
LLM parameters, and UI settings.
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

from core.logging_config import get_logger


class TemplateVersion(Enum):
    """Template format versions."""
    V1_0 = "1.0"
    V2_0 = "2.0"  # Enhanced format with full configuration
    V3_0 = "3.0"  # Flat format without nested structures


class ContextSource(Enum):
    """Sources for context data."""
    SELECTION = "selection"
    SCENE_END = "scene_end"
    SCENE_BEGINNING = "scene_beginning"
    FULL_SCENE = "full_scene"
    CUSTOM_LENGTH = "custom_length"


@dataclass
class TemplateConfig:
    """Simplified unified template configuration."""
    # Metadata fields
    name: str
    template_id: str
    description: str = ""
    category: str = "writing"
    version: str = "1.0"
    author: str = "System"
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Template content
    template_content: str = ""
    
    # Context configuration
    use_selection: bool = True
    selection_priority: bool = True
    default_context_length: int = 500
    scene_summary_length: int = 500
    scene_summary_source: ContextSource = ContextSource.SCENE_BEGINNING
    max_context_chars: int = 2000
    word_boundary_trim: bool = True
    
    # LLM parameters
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    # UI configuration
    show_context_preview: bool = True
    allow_context_editing: bool = False
    preview_length: int = 100
    show_params_editor: bool = True
    auto_apply_selection: bool = True
    confirm_before_execution: bool = False
    
    # Format version
    format_version: TemplateVersion = TemplateVersion.V2_0
    
    def __post_init__(self):
        """Initialize logger after object creation."""
        self.logger = get_logger("llm.template_config")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['scene_summary_source'] = self.scene_summary_source.value
        result['format_version'] = self.format_version.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateConfig':
        """Create from dictionary with legacy format support."""
        # Handle legacy nested structure for existing template files
        if 'metadata' in data or 'context_config' in data or 'llm_params' in data or 'ui_config' in data:
            logger = get_logger("llm.template_config")
            logger.warning("Loading legacy template format. Consider updating template to new format.")
            
            # Extract from nested structure
            metadata = data.get('metadata', {})
            context_config = data.get('context_config', {})
            llm_params = data.get('llm_params', {})
            ui_config = data.get('ui_config', {})
            
            # Merge all fields into flat structure
            flat_data = {
                # Metadata fields
                'name': metadata.get('name', ''),
                'template_id': metadata.get('template_id', ''),
                'description': metadata.get('description', ''),
                'category': metadata.get('category', 'writing'),
                'version': metadata.get('version', '1.0'),
                'author': metadata.get('author', 'System'),
                'created_date': metadata.get('created_date'),
                'modified_date': metadata.get('modified_date'),
                'tags': metadata.get('tags', []),
                
                # Template content
                'template_content': data.get('template_content', ''),
                
                # Context config fields
                'use_selection': context_config.get('use_selection', True),
                'selection_priority': context_config.get('selection_priority', True),
                'default_context_length': context_config.get('default_context_length', 500),
                'scene_summary_length': context_config.get('scene_summary_length', 500),
                'scene_summary_source': ContextSource(context_config.get('scene_summary_source', 'scene_beginning')),
                'max_context_chars': context_config.get('max_context_chars', 2000),
                'word_boundary_trim': context_config.get('word_boundary_trim', True),
                
                # LLM params
                'max_tokens': llm_params.get('max_tokens', 512),
                'temperature': llm_params.get('temperature', 0.7),
                'top_p': llm_params.get('top_p', 0.9),
                'top_k': llm_params.get('top_k', 40),
                'repeat_penalty': llm_params.get('repeat_penalty', 1.1),
                'custom_params': llm_params.get('custom_params', {}),
                
                # UI config
                'show_context_preview': ui_config.get('show_context_preview', True),
                'allow_context_editing': ui_config.get('allow_context_editing', False),
                'preview_length': ui_config.get('preview_length', 100),
                'show_params_editor': ui_config.get('show_params_editor', True),
                'auto_apply_selection': ui_config.get('auto_apply_selection', True),
                'confirm_before_execution': ui_config.get('confirm_before_execution', False),
                
                # Format version
                'format_version': TemplateVersion(data.get('format_version', TemplateVersion.V2_0.value))
            }
        else:
            # New flat format
            flat_data = data.copy()
        
        # Convert string enums to proper enum types
        if 'scene_summary_source' in flat_data and isinstance(flat_data['scene_summary_source'], str):
            flat_data['scene_summary_source'] = ContextSource(flat_data['scene_summary_source'])
        if 'format_version' in flat_data and isinstance(flat_data['format_version'], str):
            flat_data['format_version'] = TemplateVersion(flat_data['format_version'])
        
        return cls(**flat_data)
    
    def save_to_file(self, filepath: Union[str, Path]) -> bool:
        """Save template configuration to file."""
        try:
            filepath = Path(filepath)
            data = self.to_dict()
            
            if filepath.suffix.lower() == '.json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif filepath.suffix.lower() in ['.yaml', '.yml']:
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                self.logger.error(f"Unsupported file format: {filepath.suffix}")
                return False
            
            self.logger.info(f"Template saved to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save template to {filepath}: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> Optional['TemplateConfig']:
        """Load template configuration from file."""
        logger = get_logger("llm.template_config")
        
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                logger.error(f"Template file not found: {filepath}")
                return None
            
            if filepath.suffix.lower() == '.json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif filepath.suffix.lower() in ['.yaml', '.yml']:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                logger.error(f"Unsupported file format: {filepath.suffix}")
                return None
            
            template_config = cls.from_dict(data)
            logger.info(f"Template loaded from: {filepath}")
            return template_config
            
        except Exception as e:
            logger.error(f"Failed to load template from {filepath}: {e}")
            return None
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate template configuration."""
        errors = []
        
        # Validate metadata fields
        if not self.name.strip():
            errors.append("Template name is required")
        if not self.template_id.strip():
            errors.append("Template ID is required")
        
        # Validate context config
        if self.default_context_length < 1:
            errors.append("Default context length must be positive")
        if self.scene_summary_length < 1:
            errors.append("Scene summary length must be positive")
        
        # Validate LLM params
        if self.max_tokens < 1:
            errors.append("Max tokens must be positive")
        if not (0.0 <= self.temperature <= 2.0):
            errors.append("Temperature must be between 0.0 and 2.0")
        if not (0.0 <= self.top_p <= 1.0):
            errors.append("Top-p must be between 0.0 and 1.0")
        
        # Validate template content
        if not self.template_content.strip():
            errors.append("Template content is required")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> str:
        """Get human-readable summary of template."""
        return (f"Template: {self.name} (ID: {self.template_id})\n"
                f"Category: {self.category}\n"
                f"Context Length: {self.default_context_length} chars\n"
                f"Max Tokens: {self.max_tokens}\n"
                f"Temperature: {self.temperature}")


def create_default_template() -> TemplateConfig:
    """Create a default template configuration using current LLM provider defaults."""
    from core.llm.settings import get_llm_settings
    
    # Get current LLM settings for defaults
    llm_settings = get_llm_settings()
    current_provider = llm_settings.get_current_provider_config()
    
    template_content = """{% if has_selection %}
Kontynuuj tę historię na podstawie zaznaczonego fragmentu:
"{{ selected_text }}"

{% if scene_summary and scene_summary != selected_text %}
Kontekst sceny:
{{ scene_summary }}
{% endif %}
{% else %}
Kontynuuj tę scenę:
{{ current_text }}

{% if scene_summary and scene_summary != current_text %}
Pełny kontekst sceny:
{{ scene_summary }}
{% endif %}
{% endif %}

{% if characters %}
Postacie w scenie: {{ characters|join(', ') }}
{% endif %}

{% if locations %}
Lokalizacje: {{ locations|join(', ') }}
{% endif %}

Kontynuuj pisanie w naturalny sposób, zachowując styl i ton tekstu."""
    
    # Create unified config with provider defaults
    config_data = {
        'name': "Continue Scene",
        'template_id': "continue_scene", 
        'description': "Continue writing the current scene based on context",
        'category': "writing",
        'template_content': template_content
    }
    
    # Add LLM provider defaults if available
    if current_provider:
        config_data.update({
            'max_tokens': current_provider.get_setting('max_tokens', 512),
            'temperature': current_provider.get_setting('temperature', 0.7),
            'top_p': current_provider.get_setting('top_p', 0.9),
            'top_k': current_provider.get_setting('top_k', 40),
            'repeat_penalty': current_provider.get_setting('repeat_penalty', 1.1)
        })
    
    return TemplateConfig(**config_data)


def create_template_from_provider_defaults(name: str, template_id: str, description: str, 
                                         category: str = "writing") -> TemplateConfig:
    """Create a new template using current LLM provider defaults."""
    from core.llm.settings import get_llm_settings
    
    # Get current LLM settings for defaults
    llm_settings = get_llm_settings()
    current_provider = llm_settings.get_current_provider_config()
    
    # Basic template content
    template_content = """{{ current_text }}

Kontynuuj naturalnie..."""
    
    # Create unified config
    config_data = {
        'name': name,
        'template_id': template_id,
        'description': description,
        'category': category,
        'template_content': template_content
    }
    
    # Add LLM provider defaults if available
    if current_provider:
        config_data.update({
            'max_tokens': current_provider.get_setting('max_tokens', 512),
            'temperature': current_provider.get_setting('temperature', 0.7),
            'top_p': current_provider.get_setting('top_p', 0.9),
            'top_k': current_provider.get_setting('top_k', 40),
            'repeat_penalty': current_provider.get_setting('repeat_penalty', 1.1)
        })
    
    return TemplateConfig(**config_data)


