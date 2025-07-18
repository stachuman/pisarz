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


class ContextSource(Enum):
    """Sources for context data."""
    SELECTION = "selection"
    SCENE_END = "scene_end"
    SCENE_BEGINNING = "scene_beginning"
    FULL_SCENE = "full_scene"
    CUSTOM_LENGTH = "custom_length"


@dataclass
class ContextConfig:
    """Configuration for context extraction."""
    use_selection: bool = True
    selection_priority: bool = True
    default_context_length: int = 500
    scene_summary_length: int = 500  # Default, can be overridden by template
    scene_summary_source: ContextSource = ContextSource.SCENE_BEGINNING
    include_characters: bool = True
    include_locations: bool = True
    include_project_info: bool = False
    max_context_chars: int = 2000
    word_boundary_trim: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['scene_summary_source'] = self.scene_summary_source.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextConfig':
        """Create from dictionary."""
        if 'scene_summary_source' in data:
            data['scene_summary_source'] = ContextSource(data['scene_summary_source'])
        return cls(**data)


@dataclass
class LLMParams:
    """LLM generation parameters."""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMParams':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class UIConfig:
    """UI behavior configuration."""
    show_context_preview: bool = True
    allow_context_editing: bool = False
    preview_length: int = 100
    show_params_editor: bool = True
    auto_apply_selection: bool = True
    confirm_before_execution: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TemplateMetadata:
    """Template metadata information."""
    name: str
    template_id: str
    description: str
    category: str = "writing"
    version: str = "1.0"
    author: str = "System"
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateMetadata':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class EnhancedTemplateConfig:
    """Complete enhanced template configuration."""
    metadata: TemplateMetadata
    context_config: ContextConfig
    llm_params: LLMParams
    ui_config: UIConfig
    template_content: str
    format_version: TemplateVersion = TemplateVersion.V2_0
    
    def __post_init__(self):
        """Initialize logger after object creation."""
        self.logger = get_logger("llm.template_config")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'metadata': self.metadata.to_dict(),
            'context_config': self.context_config.to_dict(),
            'llm_params': self.llm_params.to_dict(),
            'ui_config': self.ui_config.to_dict(),
            'template_content': self.template_content,
            'format_version': self.format_version.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedTemplateConfig':
        """Create from dictionary."""
        return cls(
            metadata=TemplateMetadata.from_dict(data.get('metadata', {})),
            context_config=ContextConfig.from_dict(data.get('context_config', {})),
            llm_params=LLMParams.from_dict(data.get('llm_params', {})),
            ui_config=UIConfig.from_dict(data.get('ui_config', {})),
            template_content=data.get('template_content', ''),
            format_version=TemplateVersion(data.get('format_version', TemplateVersion.V2_0.value))
        )
    
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
    def load_from_file(cls, filepath: Union[str, Path]) -> Optional['EnhancedTemplateConfig']:
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
        
        # Validate metadata
        if not self.metadata.name.strip():
            errors.append("Template name is required")
        if not self.metadata.template_id.strip():
            errors.append("Template ID is required")
        
        # Validate context config
        if self.context_config.default_context_length < 1:
            errors.append("Default context length must be positive")
        if self.context_config.scene_summary_length < 1:
            errors.append("Scene summary length must be positive")
        
        # Validate LLM params
        if self.llm_params.max_tokens < 1:
            errors.append("Max tokens must be positive")
        if not (0.0 <= self.llm_params.temperature <= 2.0):
            errors.append("Temperature must be between 0.0 and 2.0")
        if not (0.0 <= self.llm_params.top_p <= 1.0):
            errors.append("Top-p must be between 0.0 and 1.0")
        
        # Validate template content
        if not self.template_content.strip():
            errors.append("Template content is required")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> str:
        """Get human-readable summary of template."""
        return (f"Template: {self.metadata.name} (ID: {self.metadata.template_id})\n"
                f"Category: {self.metadata.category}\n"
                f"Context Length: {self.context_config.default_context_length} chars\n"
                f"Max Tokens: {self.llm_params.max_tokens}\n"
                f"Temperature: {self.llm_params.temperature}")


def create_default_template() -> EnhancedTemplateConfig:
    """Create a default template configuration using current LLM provider defaults."""
    from core.llm.settings import get_llm_settings
    
    # Get current LLM settings for defaults
    llm_settings = get_llm_settings()
    current_provider = llm_settings.get_current_provider_config()
    
    metadata = TemplateMetadata(
        name="Continue Scene",
        template_id="continue_scene",
        description="Continue writing the current scene based on context",
        category="writing"
    )
    
    context_config = ContextConfig()
    
    # Create LLM params using provider defaults
    if current_provider:
        llm_params = LLMParams(
            max_tokens=current_provider.get_setting('max_tokens', 512),
            temperature=current_provider.get_setting('temperature', 0.7),
            top_p=current_provider.get_setting('top_p', 0.9),
            top_k=current_provider.get_setting('top_k', 40),
            repeat_penalty=current_provider.get_setting('repeat_penalty', 1.1)
        )
    else:
        llm_params = LLMParams()
    
    ui_config = UIConfig()
    
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
    
    return EnhancedTemplateConfig(
        metadata=metadata,
        context_config=context_config,
        llm_params=llm_params,
        ui_config=ui_config,
        template_content=template_content
    )


def create_template_from_provider_defaults(name: str, template_id: str, description: str, 
                                         category: str = "writing") -> EnhancedTemplateConfig:
    """Create a new template using current LLM provider defaults."""
    from core.llm.settings import get_llm_settings
    
    # Get current LLM settings for defaults
    llm_settings = get_llm_settings()
    current_provider = llm_settings.get_current_provider_config()
    
    metadata = TemplateMetadata(
        name=name,
        template_id=template_id,
        description=description,
        category=category
    )
    
    context_config = ContextConfig()
    
    # Create LLM params using provider defaults
    if current_provider:
        llm_params = LLMParams(
            max_tokens=current_provider.get_setting('max_tokens', 512),
            temperature=current_provider.get_setting('temperature', 0.7),
            top_p=current_provider.get_setting('top_p', 0.9),
            top_k=current_provider.get_setting('top_k', 40),
            repeat_penalty=current_provider.get_setting('repeat_penalty', 1.1)
        )
    else:
        llm_params = LLMParams()
    
    ui_config = UIConfig()
    
    # Basic template content
    template_content = """{{ current_text }}

Kontynuuj naturalnie..."""
    
    return EnhancedTemplateConfig(
        metadata=metadata,
        context_config=context_config,
        llm_params=llm_params,
        ui_config=ui_config,
        template_content=template_content
    )