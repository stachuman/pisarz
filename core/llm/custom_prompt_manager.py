"""Custom Prompt Manager for handling custom prompt creation and execution."""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QDialog

from core.logging_config import get_logger
from core.llm.templates.config import TemplateConfig, ContextSource
from i18n import _


class CustomPromptManager:
    """Manages custom prompt creation, configuration, and execution."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        self.logger = get_logger("llm.custom_prompt_manager")
        self.parent_widget = parent
    
    def open_custom_prompt_dialog(self, scene_content: str, selected_text: str, 
                                 build_context_callback, streaming: bool = False):
        """Open custom prompt dialog and handle execution."""
        try:
            from ui.widgets.custom_prompt_dialog import CustomPromptDialog
            
            dialog = CustomPromptDialog(scene_content, selected_text, self.parent_widget)
            result = dialog.exec()
            
            # Check if dialog was accepted and get config
            if result == QDialog.DialogCode.Accepted:
                config = dialog.get_config()
                if config:
                    return config
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error opening custom prompt dialog: {e}")
            if self.parent_widget:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self.parent_widget, 
                    _("Error"), 
                    _("Failed to open custom prompt dialog: {}").format(str(e))
                )
            return None
    
    def create_dynamic_template_config(self, config: dict) -> TemplateConfig:
        """Create a dynamic template configuration from custom prompt config."""
        
        # Create template content using instruction as Jinja2 template
        template_content = self.build_template_content(config)
        
        # Create unified template config with all fields flattened
        return TemplateConfig(
            # Metadata fields
            name="Custom Prompt",
            template_id="custom_prompt", 
            description="Dynamic custom prompt template",
            category="custom",
            author="User",
            
            # Template content
            template_content=template_content,
            
            # Context configuration
            use_selection=True,
            selection_priority=True,
            default_context_length=config.get('custom_length', 8000),
            scene_summary_length=config.get('custom_length', 8000),
            scene_summary_source=self.get_context_source_from_text_portion(config.get('text_portion', '')),
            max_context_chars=25000,
            word_boundary_trim=True,
            
            # LLM parameters
            temperature=config.get('temperature', 0.75),
            max_tokens=config.get('max_tokens', 8000),
            repeat_penalty=config.get('repetition_penalty', 1.05),
            
            # UI configuration
            show_context_preview=True,
            allow_context_editing=False,
            show_params_editor=False,
            auto_apply_selection=True,
            confirm_before_execution=False
        )
    
    def get_context_source_from_text_portion(self, text_portion: str) -> ContextSource:
        """Convert text portion selection to ContextSource enum."""
        
        if _("🎯 Selected text only") in text_portion:
            return ContextSource.SELECTION
        elif _("📄 Full scene") in text_portion:
            return ContextSource.FULL_SCENE
        elif _("⬆️ Beginning of scene") in text_portion:
            return ContextSource.SCENE_BEGINNING
        elif _("⬇️ End of scene") in text_portion:
            return ContextSource.SCENE_END
        elif _("🎚️ Custom length from end") in text_portion:
            return ContextSource.CUSTOM_LENGTH
        else:
            return ContextSource.SELECTION
    
    def build_template_content(self, config: dict) -> str:
        """Build Jinja2 template content from custom prompt config."""
        instruction = config.get('instruction', '')
        include_characters = config.get('include_characters', False)
        include_locations = config.get('include_locations', False)
        include_project_description = config.get('include_project_description', False)
        
        # Create template that conditionally includes scene content
        template_parts = [instruction]
        
        # Add conditional character section only if enabled
        if include_characters:
            template_parts.append("""
{% if characters and characters|length > 0 %}

Postacie w scenie:
{% for character in characters %}
- {{ character }}
{% endfor %}
{% endif %}""")
        
        # Add conditional location section only if enabled
        if include_locations:
            template_parts.append("""
{% if locations and locations|length > 0 %}

Lokalizacje:
{% for location in locations %}
- {{ location }}
{% endfor %}
{% endif %}""")
        
        # Add conditional project description section only if enabled
        if include_project_description:
            template_parts.append("""
{% if project_description %}

Opis projektu:
{{ project_description }}
{% endif %}""")
        
        # Add scene content section (controlled by include_scene_content flag)
        if config.get('include_scene_content', True):
            template_parts.append("""
{% if current_text or selected_text %}

--- TEKST DO ANALIZY ---

{% if has_selection %}
{{ selected_text }}
{% else %}
{{ current_text }}
{% endif %}

{% if scene_summary and scene_summary != (selected_text if has_selection else current_text) %}

Dodatkowy kontekst sceny:
{{ scene_summary }}
{% endif %}
{% endif %}""")
        
        return "\n".join(template_parts)
    
    def extract_custom_context(self, config: dict, clean_html_css_callback) -> str:
        """Extract context text based on custom prompt configuration."""
        scene_content = config['scene_content']
        selected_text = config.get('selected_text', '')
        text_portion = config['text_portion']
        custom_length = config['custom_length']
        
        # Clean HTML/CSS from scene content and selected text (reuse existing cleaning)
        clean_scene_content = clean_html_css_callback(scene_content) if scene_content else ""
        clean_selected_text = clean_html_css_callback(selected_text) if selected_text else ""
        
        self.logger.debug(f"Extracting custom context: portion='{text_portion}', scene_len={len(clean_scene_content)}, selected_len={len(clean_selected_text)}")
        
        # Use exact text matching instead of substring matching to fix selection bug
        if text_portion == _("🎯 Selected text only") and clean_selected_text:
            self.logger.debug("Using selected text only")
            return clean_selected_text
        elif text_portion == _("📄 Full scene"):
            self.logger.debug("Using full scene")
            return clean_scene_content
        elif text_portion == _("⬆️ Beginning of scene"):
            self.logger.debug(f"Using beginning of scene ({custom_length} chars)")
            result = clean_scene_content[:custom_length]
            if len(clean_scene_content) > custom_length:
                result += "..."
            return result
        elif text_portion == _("⬇️ End of scene"):
            self.logger.debug(f"Using end of scene ({custom_length} chars)")
            if len(clean_scene_content) > custom_length:
                return "..." + clean_scene_content[-custom_length:]
            return clean_scene_content
        elif text_portion == _("🎚️ Custom length from end"):
            self.logger.debug(f"Using custom length from end ({custom_length} chars)")
            return clean_scene_content[-custom_length:] if clean_scene_content else ""
        elif text_portion == _("🎯 Selection + context") and clean_selected_text:
            self.logger.debug("Using selection + context")
            # Return selection plus some context
            context_length = min(custom_length - len(clean_selected_text), len(clean_scene_content))
            context_part = clean_scene_content[:context_length]
            return f"{clean_selected_text}\n\n[Context: {context_part}]"
        else:
            self.logger.debug(f"Using fallback: first {custom_length} chars")
            return clean_scene_content[:custom_length]
    
    def prepare_execution_context(self, config: dict, current_scene_id: Optional[int], 
                                 additional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for custom prompt execution."""
        return {
            'scene_content': config['scene_content'],
            'selected_text': config.get('selected_text', ''),
            'current_text': self.extract_custom_context(config, lambda x: x),  # Placeholder for clean callback
            'characters': additional_context.get('characters', []),
            'locations': additional_context.get('locations', []),
            'project_description': additional_context.get('project_description', ''),
            'project_name': additional_context.get('project_name', ''),
            'scene_title': additional_context.get('scene_title', ''),
            'scene_id': current_scene_id,
        }