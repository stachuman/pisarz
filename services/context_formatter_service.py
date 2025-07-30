"""Service for formatting character and location context data for LLM prompts."""

import logging
from typing import Dict, List, Any
from core.logging_config import get_logger
from i18n import _


class ContextFormatterService:
    """Service for consistent formatting of character and location context data."""
    
    def __init__(self):
        self.logger = get_logger("services.context_formatter")
    
    def format_character_description(self, char_data: Dict[str, Any]) -> str:
        """
        Format a single character's data into a description string for LLM.
        
        Args:
            char_data: Dictionary containing character information
            
        Returns:
            Formatted character description string
        """
        if not isinstance(char_data, dict):
            return str(char_data)
        
        name = char_data.get('name', 'Nieznana postać')
        full_name = char_data.get('full_name', '').strip()
        alias = char_data.get('alias', '').strip()
        age = char_data.get('age')
        gender = char_data.get('gender', '').strip()
        occupation = char_data.get('occupation', '').strip()
        location = char_data.get('location', '').strip()
        description = char_data.get('description', '').strip()
        notes = char_data.get('notes', '').strip()
        role = char_data.get('role', '').strip()
        
        # Start with name and role
        char_desc = f"{name}"
        if role and role != "participant":
            char_desc += f" ({role})"
        
        # Add additional identity information
        identity_parts = []
        if full_name and full_name != name:
            identity_parts.append(_("full name: {}").format(full_name))
        if alias:
            identity_parts.append(_("alias: {}").format(alias))
        if age:
            identity_parts.append(_("age: {}").format(age))
        if gender:
            identity_parts.append(_("gender: {}").format(gender))
        if occupation:
            identity_parts.append(_("occupation: {}").format(occupation))
        if location:
            identity_parts.append(_("place: {}").format(location))
        
        if identity_parts:
            char_desc += f" [{', '.join(identity_parts)}]"
        
        # Add description
        if description:
            char_desc += f" - {description}"
        
        # Add notes
        if notes:
            notes_label = _("Notes: {}").format(notes)
            char_desc += f" | {notes_label}"
        
        return char_desc
    
    def format_location_description(self, loc_data: Dict[str, Any]) -> str:
        """
        Format a single location's data into a description string for LLM.
        
        Args:
            loc_data: Dictionary containing location information
            
        Returns:
            Formatted location description string
        """
        if not isinstance(loc_data, dict):
            return str(loc_data)
        
        name = loc_data.get('name', 'Nieznana lokalizacja')
        location_type = loc_data.get('type', '').strip()  # Note: field is 'type' not 'location_type'
        description = loc_data.get('description', '').strip()
        atmosphere = loc_data.get('atmosphere', '').strip()
        details = loc_data.get('details', '').strip()
        significance = loc_data.get('significance', '').strip()
        notes = loc_data.get('notes', '').strip()
        role = loc_data.get('role', '').strip()
        
        # Start with name and type/role
        loc_desc = f"{name}"
        if location_type:
            loc_desc += f" ({location_type})"
        elif role and role != "setting":
            loc_desc += f" ({role})"
        
        # Add description
        if description:
            loc_desc += f" - {description}"
        
        # Add atmospheric and detail information
        detail_parts = []
        if atmosphere:
            detail_parts.append(_("atmosphere: {}").format(atmosphere))
        if details:
            detail_parts.append(_("details: {}").format(details))
        if significance:
            detail_parts.append(_("significance: {}").format(significance))
        
        if detail_parts:
            loc_desc += f" [{', '.join(detail_parts)}]"
        
        # Add notes
        if notes:
            notes_label = _("Notes: {}").format(notes)
            loc_desc += f" | {notes_label}"
        
        return loc_desc
    
    def format_characters_list(self, characters: List[Any]) -> List[str]:
        """
        Format a list of characters into description strings for LLM.
        
        Args:
            characters: List of character data (dicts or other types)
            
        Returns:
            List of formatted character description strings
        """
        if not characters:
            return []
        
        character_descriptions = []
        for char in characters:
            formatted_desc = self.format_character_description(char)
            character_descriptions.append(formatted_desc)
        
        self.logger.debug(f"Formatted {len(character_descriptions)} character descriptions")
        return character_descriptions
    
    def format_locations_list(self, locations: List[Any]) -> List[str]:
        """
        Format a list of locations into description strings for LLM.
        
        Args:
            locations: List of location data (dicts or other types)
            
        Returns:
            List of formatted location description strings
        """
        if not locations:
            return []
        
        location_descriptions = []
        for loc in locations:
            formatted_desc = self.format_location_description(loc)
            location_descriptions.append(formatted_desc)
        
        self.logger.debug(f"Formatted {len(location_descriptions)} location descriptions")
        return location_descriptions
    
    def format_context_data(self, characters: List[Any] = None, locations: List[Any] = None) -> Dict[str, List[str]]:
        """
        Format both characters and locations data for LLM context.
        
        Args:
            characters: List of character data
            locations: List of location data
            
        Returns:
            Dictionary with formatted 'characters' and 'locations' lists
        """
        formatted_context = {}
        
        if characters is not None:
            formatted_context['characters'] = self.format_characters_list(characters)
        
        if locations is not None:
            formatted_context['locations'] = self.format_locations_list(locations)
        
        return formatted_context
    
    def format_scene_context_description(self, context_data: Dict[str, Any]) -> str:
        """
        Format a single scene context's data into a description string for LLM.
        
        Args:
            context_data: Dictionary containing scene context information
            
        Returns:
            Formatted scene context description string
        """
        if not isinstance(context_data, dict):
            return str(context_data)
        
        scene_title = context_data.get('scene_title', 'Untitled Scene')
        content = context_data.get('content', '').strip()
        has_content = context_data.get('has_content', False)
        scene_ord = context_data.get('scene_ord', 0)
        
        # Start with scene title and position
        context_desc = f"{scene_title}"
        
        # Add content if available
        if has_content and content:
            context_desc += f": {content}"
        else:
            context_desc += ": (no context available)"
        
        return context_desc
    
    def format_scene_contexts_list(self, scene_contexts: List[Any]) -> List[str]:
        """
        Format a list of scene contexts into description strings for LLM.
        
        Args:
            scene_contexts: List of scene context data (dicts or other types)
            
        Returns:
            List of formatted scene context description strings
        """
        if not scene_contexts:
            return []
        
        context_descriptions = []
        for context in scene_contexts:
            formatted_desc = self.format_scene_context_description(context)
            context_descriptions.append(formatted_desc)
        
        self.logger.debug(f"Formatted {len(context_descriptions)} scene context descriptions")
        return context_descriptions

