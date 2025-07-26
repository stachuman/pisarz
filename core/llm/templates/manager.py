"""
Enhanced Template Manager for LLM operations.
Manages template storage, loading, and enhanced context building based on template configuration.
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import asdict

from core.logging_config import get_logger
from .config import (
    TemplateConfig, ContextSource, 
    create_default_template
)
import re


class EnhancedTemplateManager:
    """Manages enhanced LLM templates with configurable context building."""
    
    def __init__(self, templates_dir: Optional[Union[str, Path]] = None):
        self.logger = get_logger("llm.template_manager")
        
        # Template storage
        self.templates: Dict[str, TemplateConfig] = {}
        
        # Template directory
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Default to templates directory in user's config
            from PySide6.QtCore import QStandardPaths
            config_dir = QStandardPaths.writableLocation(QStandardPaths.ConfigLocation)
            self.templates_dir = Path(config_dir) / "Pisarz" / "templates"
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize with default templates
        self._initialize_default_templates()
        self._load_user_templates()
    
    def _initialize_default_templates(self):
        """Initialize default templates."""
        try:
            # Create default template
            default_template = create_default_template()
            self.templates[default_template.template_id] = default_template
            
            self.logger.info("Default templates initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing default templates: {e}")
    
    def _load_user_templates(self):
        """Load user templates from templates directory."""
        try:
            template_files = list(self.templates_dir.glob("*.yaml")) + list(self.templates_dir.glob("*.yml")) + list(self.templates_dir.glob("*.json"))
            
            for template_file in template_files:
                template_config = TemplateConfig.load_from_file(template_file)
                if template_config:
                    self.templates[template_config.template_id] = template_config
                    self.logger.debug(f"Loaded user template: {template_config.name}")
            
            self.logger.info(f"Loaded {len(template_files)} user templates")
            
        except Exception as e:
            self.logger.error(f"Error loading user templates: {e}")
    
    def get_template(self, template_id: str) -> Optional[TemplateConfig]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> Dict[str, TemplateConfig]:
        """Get all available templates."""
        return self.templates.copy()
    
    def get_templates_by_category(self, category: str) -> Dict[str, TemplateConfig]:
        """Get templates by category."""
        return {
            template_id: template 
            for template_id, template in self.templates.items()
            if template.category == category
        }
    
    def add_template(self, template_config: TemplateConfig, save_to_file: bool = True) -> bool:
        """Add a new template."""
        try:
            template_id = template_config.template_id
            
            # Validate template
            is_valid, errors = template_config.validate()
            if not is_valid:
                self.logger.error(f"Template validation failed: {errors}")
                return False
            
            # Add to memory
            self.templates[template_id] = template_config
            
            # Save to file if requested
            if save_to_file:
                filepath = self.templates_dir / f"{template_id}.yaml"
                if not template_config.save_to_file(filepath):
                    self.logger.error(f"Failed to save template to file: {filepath}")
                    return False
            
            self.logger.info(f"Template added: {template_config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding template: {e}")
            return False
    
    def remove_template(self, template_id: str, delete_file: bool = True) -> bool:
        """Remove a template."""
        try:
            if template_id not in self.templates:
                self.logger.warning(f"Template not found: {template_id}")
                return False
            
            # Remove from memory
            del self.templates[template_id]
            
            # Delete file if requested
            if delete_file:
                for ext in ['.yaml', '.yml', '.json']:
                    filepath = self.templates_dir / f"{template_id}{ext}"
                    if filepath.exists():
                        filepath.unlink()
                        self.logger.debug(f"Deleted template file: {filepath}")
                        break
            
            self.logger.info(f"Template removed: {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing template: {e}")
            return False
    
    def build_enhanced_context(self, template_id: str, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build enhanced context based on template configuration."""
        try:
            template = self.get_template(template_id)
            if not template:
                self.logger.error(f"Template not found: {template_id}")
                return scene_data
            
            # Use template directly (flattened structure)
            enhanced_context = scene_data.copy()
            
            # Get basic scene data
            scene_content = scene_data.get('scene_content', '')
            selected_text = scene_data.get('selected_text', '')
            current_text = scene_data.get('current_text', '')
            
            # Check if UI has provided a content_source override
            content_source_from_ui = scene_data.get('content_source')
            
            # Clean HTML tags and CSS if present
            import re
            clean_content = self._clean_html_css(scene_content)
            clean_selected_text = self._clean_html_css(selected_text) if selected_text else ''
            clean_current_text = self._clean_html_css(current_text) if current_text else ''
            
            # Build context based on configuration only if UI hasn't overridden content source
            if content_source_from_ui:
                # UI has selected specific content source - keep the context as is
                self.logger.debug(f"Using UI content source selection: {content_source_from_ui}")
                enhanced_context['current_text'] = current_text
                enhanced_context['selected_text'] = selected_text
                enhanced_context['has_selection'] = bool(selected_text.strip())
            else:
                # Use template configuration
                enhanced_context.update(self._build_selection_context(
                    template, clean_content, clean_selected_text, clean_current_text
                ))
            
            enhanced_context.update(self._build_scene_summary(
                template, clean_content, clean_selected_text
            ))
            
            enhanced_context.update(self._build_additional_context(
                template, scene_data, template.template_content
            ))
            
            # Add metadata
            enhanced_context['template_id'] = template_id
            enhanced_context['template_name'] = template.name
            
            self.logger.debug(f"Enhanced context built for template: {template_id}")
            return enhanced_context
            
        except Exception as e:
            self.logger.error(f"Error building enhanced context: {e}")
            return scene_data
    
    def _build_selection_context(self, config: TemplateConfig, scene_content: str, 
                                selected_text: str, current_text: str) -> Dict[str, Any]:
        """Build selection-related context."""
        context = {}
        
        # Handle text selection
        if config.use_selection and selected_text.strip():
            if config.selection_priority:
                context['current_text'] = selected_text.strip()
                context['has_selection'] = True
                context['selected_text'] = selected_text.strip()
            else:
                context['selected_text'] = selected_text.strip()
                context['has_selection'] = True
        else:
            context['has_selection'] = False
            context['selected_text'] = ''
            
            # Use configured context length if no selection
            if not context.get('current_text'):
                context['current_text'] = self._extract_context_text(
                    scene_content, config.default_context_length, config.word_boundary_trim
                )
        
        # Ensure current_text is set
        if 'current_text' not in context and current_text:
            context['current_text'] = current_text
        elif 'current_text' not in context:
            context['current_text'] = self._extract_context_text(
                scene_content, config.default_context_length, config.word_boundary_trim
            )
        
        return context
    
    def _build_scene_summary(self, config: TemplateConfig, scene_content: str, 
                           selected_text: str) -> Dict[str, Any]:
        """Build scene summary based on configuration."""
        context = {}
        
        summary_length = config.scene_summary_length
        source = config.scene_summary_source
        
        if source == ContextSource.SCENE_BEGINNING:
            summary = scene_content[:summary_length]
            if len(scene_content) > summary_length:
                summary += "..."
        elif source == ContextSource.SCENE_END:
            if len(scene_content) > summary_length:
                summary = "..." + scene_content[-summary_length:]
            else:
                summary = scene_content
        elif source == ContextSource.FULL_SCENE:
            summary = scene_content
        elif source == ContextSource.CUSTOM_LENGTH:
            # Use the configured length from the middle
            if len(scene_content) > summary_length:
                start = max(0, (len(scene_content) - summary_length) // 2)
                summary = scene_content[start:start + summary_length]
                if start > 0:
                    summary = "..." + summary
                if start + summary_length < len(scene_content):
                    summary += "..."
            else:
                summary = scene_content
        else:  # SELECTION or fallback
            if selected_text:
                # Provide broader context around selection
                summary = scene_content[:summary_length] if scene_content else selected_text
                if len(scene_content) > summary_length:
                    summary += "..."
            else:
                summary = scene_content[:summary_length]
                if len(scene_content) > summary_length:
                    summary += "..."
        
        # Avoid duplicate content
        if selected_text and summary == selected_text:
            # If summary is same as selection, provide broader context
            broader_length = min(config.max_context_chars, len(scene_content))
            summary = scene_content[:broader_length]
            if len(scene_content) > broader_length:
                summary += "..."
        
        context['scene_summary'] = summary.strip()
        return context
    
    def _build_additional_context(self, config: TemplateConfig, scene_data: Dict[str, Any], template_content: str) -> Dict[str, Any]:
        """Build additional context data based on template variables."""
        context = {}
        project_id = scene_data.get('project_id')
        
        # Parse template to detect used variables
        used_vars = self.get_template_variables(template_content)

        # Use ContextFormatterService for consistent formatting
        from services import ContextFormatterService
        formatter = ContextFormatterService()
        
        # Characters - populate if used in template
        if 'characters' in used_vars:
            characters = scene_data.get('characters', [])
            if isinstance(characters, list):
                context['characters'] = formatter.format_characters_list(characters)
            else:
                context['characters'] = []
        
        # Locations - populate if used in template
        if 'locations' in used_vars:
            locations = scene_data.get('locations', [])
            if isinstance(locations, list):
                context['locations'] = formatter.format_locations_list(locations)
            else:
                context['locations'] = []
                
        # Project info - populate if used in template
        if 'project_description' in used_vars:
            context['project_description'] = scene_data.get('project_description', '')
             
        # Narrative context - populate if used in template
        if 'narrative_context' in used_vars:
            if project_id:
                context['narrative_context'] = self._build_narrative_context(project_id)
            elif 'narrative_context' in scene_data:
                context['narrative_context'] = scene_data['narrative_context']
            else:
                context['narrative_context'] = ''
        
        return context
    
    def _extract_context_text(self, content: str, length: int, word_boundary: bool = True) -> str:
        """Extract context text of specified length."""
        if not content:
            return ""
        
        if len(content) <= length:
            return content.strip()
        
        # Take from the end of content, but respect the full length
        extracted = content[-length:].strip()
        original_length = len(extracted)
        
        # Only trim to word boundary if it would remove less than 20% of the content
        if word_boundary and extracted:
            space_index = extracted.find(' ')
            if space_index > 0:
                # Only trim if we're not losing too much content
                if space_index < (len(extracted) * 0.2):
                    extracted = extracted[space_index + 1:]
                    self.logger.debug(f"Context trimmed from {original_length} to {len(extracted)} chars due to word boundary")
                else:
                    self.logger.debug(f"Context kept at {original_length} chars (word boundary would remove too much)")
        
        self.logger.debug(f"Context extraction: requested={length}, content_length={len(content)}, extracted_length={len(extracted)}")
        return extracted
    
    def get_template_llm_params(self, template_id: str) -> Dict[str, Any]:
        """Get LLM parameters for a template."""
        template = self.get_template(template_id)
        if not template:
            return {}
        
        # Return LLM params from flattened structure
        params = {
            'max_tokens': template.max_tokens,
            'temperature': template.temperature,
            'top_p': template.top_p,
            'top_k': template.top_k,
            'repeat_penalty': template.repeat_penalty,
            'custom_params': template.custom_params
        }
        return params
    
    def get_template_ui_config(self, template_id: str) -> Dict[str, Any]:
        """Get UI configuration for a template."""
        template = self.get_template(template_id)
        if not template:
            return {}
        
        # Return UI config from flattened structure
        ui_config = {
            'show_context_preview': template.show_context_preview,
            'allow_context_editing': template.allow_context_editing,
            'preview_length': template.preview_length,
            'show_params_editor': template.show_params_editor,
            'auto_apply_selection': template.auto_apply_selection,
            'confirm_before_execution': template.confirm_before_execution
        }
        return ui_config
    
    def refresh_templates(self):
        """Refresh templates by reloading from disk."""
        self.logger.info("Refreshing templates from disk")
        # Clear existing user templates but keep defaults
        default_templates = {
            template_id: template 
            for template_id, template in self.templates.items()
            if template.author == "System"
        }
        self.templates = default_templates
        
        # Reload user templates
        self._load_user_templates()
        self.logger.info(f"Templates refreshed: {len(self.templates)} total templates loaded")
    
    def reload_template(self, template_id: str) -> bool:
        """Reload a specific template from disk."""
        try:
            # Find the template file
            template_files = (
                list(self.templates_dir.glob(f"{template_id}.yaml")) +
                list(self.templates_dir.glob(f"{template_id}.yml")) +
                list(self.templates_dir.glob(f"{template_id}.json"))
            )
            
            if not template_files:
                self.logger.warning(f"Template file not found for {template_id}")
                return False
            
            # Load the template
            template_file = template_files[0]
            template = self._load_template_file(template_file)
            if template:
                self.templates[template_id] = template
                self.logger.info(f"Template {template_id} reloaded successfully")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error reloading template {template_id}: {e}")
            return False
    
    def export_template(self, template_id: str, filepath: Union[str, Path]) -> bool:
        """Export template to file."""
        template = self.get_template(template_id)
        if not template:
            self.logger.error(f"Template not found for export: {template_id}")
            return False
        
        return template.save_to_file(filepath)
    
    def import_template(self, filepath: Union[str, Path]) -> Optional[str]:
        """Import template from file."""
        template_config = TemplateConfig.load_from_file(filepath)
        if not template_config:
            return None
        
        if self.add_template(template_config):
            return template_config.template_id
        
        return None
    
    def get_template_list(self) -> List[Dict[str, str]]:
        """Get simplified list of templates for UI display."""
        template_list = []
        
        for template_id, template in self.templates.items():
            template_list.append({
                'id': template_id,
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'version': template.version
            })
        
        return sorted(template_list, key=lambda x: x['name'])
    
    def get_template_variables(self, template_content: str) -> set:
        """Parse template content and return set of used variables."""
        if not template_content:
            return set()
            
        # Find {{ variable }} patterns
        variable_pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)'
        # Find {% if variable %} patterns  
        if_pattern = r'\{\%\s*if\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        
        variables = set()
        variables.update(re.findall(variable_pattern, template_content))
        variables.update(re.findall(if_pattern, template_content))
        
        return variables
    
    def refresh_templates(self):
        """Refresh templates by reloading from files."""
        self.logger.info("Refreshing templates...")
        
        # Clear current templates except defaults
        user_templates = {
            template_id: template 
            for template_id, template in self.templates.items()
            if template.author != "System"
        }
        
        # Reinitialize
        self._initialize_default_templates()
        self._load_user_templates()
        
        self.logger.info("Templates refreshed")
    
    def _clean_html_css(self, content: str) -> str:
        """
        Clean HTML tags and CSS from content to produce plain text.
        
        Args:
            content: Raw content that may contain HTML/CSS
            
        Returns:
            Cleaned plain text content
        """
        from core.utils.text_cleaner import clean_html_css
        return clean_html_css(content)
    
    def _build_narrative_context(self, project_id) -> str:
        """Build narrative context summary from project data."""
        try:
            from pathlib import Path
            from core.llm.context.narrative_context import NarrativeContextManager
            
            # Get narrative context manager
            manager = NarrativeContextManager(project_id)
            
            # Build context summary
            narrative_summary = manager.build_context_summary(max_length=1500)
            
            return narrative_summary if narrative_summary else ""
            
        except Exception as e:
            self.logger.error(f"Failed to build narrative context: {e}")
            return ""


# Global template manager instance
_template_manager = None


def get_template_manager() -> EnhancedTemplateManager:
    """Get the global template manager instance."""
    global _template_manager
    if _template_manager is None:
        # Use project templates directory
        from pathlib import Path
        project_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root
        templates_dir = project_dir / "templates"
        _template_manager = EnhancedTemplateManager(templates_dir)
    return _template_manager