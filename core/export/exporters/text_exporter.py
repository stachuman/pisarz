"""
Text exporter - Export to plain text format.
Simple, clean text output with scene separators and optional metadata.
"""

import re
from typing import List
from datetime import datetime

from .base_exporter import BaseExporter
from ..models import ExportConfig, ExportResult, ExportData, ExportFormat
from ...utils.text_cleaner import clean_html_css


class TextExporter(BaseExporter):
    """Export to plain text format with clean formatting"""
    
    def get_supported_formats(self) -> List[ExportFormat]:
        """Return supported formats"""
        return [ExportFormat.TXT]
    
    def get_output_extension(self) -> str:
        """Return file extension"""
        return ".txt"
    
    def export(self, data: ExportData, config: ExportConfig) -> ExportResult:
        """
        Export scenes to plain text with scene separators.
        
        Args:
            data: ExportData with scenes and metadata
            config: ExportConfig with export parameters
            
        Returns:
            ExportResult with operation outcome
        """
        try:
            self.log_export_start(config, data)
            
            # Ensure output directory exists
            if not self.ensure_output_directory(config.output_path):
                return self.create_error_result(
                    "Failed to create output directory",
                    ExportFormat.TXT
                )
            
            # Build the text content
            content_parts = []
            
            # Add header if metadata should be included
            if config.scope.include_metadata:
                header = self._create_header(data.project_metadata)
                if header:
                    content_parts.append(header)
                    content_parts.append("\n" + "=" * 80 + "\n")
            
            # Add scenes
            for i, scene in enumerate(data.scenes):
                scene_text = self._format_scene(scene, i + 1)
                content_parts.append(scene_text)
                
                # Add separator between scenes (but not after the last one)
                if i < len(data.scenes) - 1:
                    content_parts.append("\n" + "-" * 40 + "\n")
            
            # Add character information if requested
            if config.scope.include_characters and data.characters:
                content_parts.append("\n\n" + "=" * 80)
                content_parts.append("\nCHARACTERS\n")
                content_parts.append("=" * 80 + "\n")
                
                for character in data.characters:
                    char_text = self._format_character(character)
                    content_parts.append(char_text)
            
            # Add location information if requested  
            if config.scope.include_locations and data.locations:
                content_parts.append("\n\n" + "=" * 80)
                content_parts.append("\nLOCATIONS\n")
                content_parts.append("=" * 80 + "\n")
                
                for location in data.locations:
                    loc_text = self._format_location(location)
                    content_parts.append(loc_text)
            
            # Join all content
            full_content = "".join(content_parts)
            
            # Write to file
            try:
                with open(config.output_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                # Create success result
                result = self.create_success_result(
                    config.output_path,
                    len(data.scenes),
                    format_used=ExportFormat.TXT
                )
                
                self.log_export_result(result)
                return result
                
            except IOError as e:
                error_msg = f"Failed to write text file: {str(e)}"
                self.logger.error(error_msg)
                return self.create_error_result(error_msg, ExportFormat.TXT)
            
        except Exception as e:
            error_msg = f"Text export failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return self.create_error_result(error_msg, ExportFormat.TXT)
    
    def _create_header(self, project_metadata: dict) -> str:
        """
        Create document header with project information.
        
        Args:
            project_metadata: Project metadata dictionary
            
        Returns:
            Formatted header string
        """
        header_parts = []
        
        # Title
        title = project_metadata.get('title') or project_metadata.get('name', 'Untitled')
        header_parts.append(title.upper())
        header_parts.append("=" * len(title))
        
        # Author
        author = project_metadata.get('author')
        if author:
            header_parts.append(f"by {author}")
        
        # Additional metadata
        metadata_items = []
        
        genre = project_metadata.get('genre')
        if genre:
            metadata_items.append(f"Genre: {genre}")
        
        status = project_metadata.get('status')
        if status:
            metadata_items.append(f"Status: {status.title()}")
        
        word_count = project_metadata.get('target_word_count')
        if word_count and word_count > 0:
            metadata_items.append(f"Target Words: {word_count:,}")
        
        if metadata_items:
            header_parts.append("")
            header_parts.extend(metadata_items)
        
        # Export timestamp
        header_parts.append("")
        header_parts.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(header_parts) + "\n"
    
    def _format_scene(self, scene: dict, scene_number: int) -> str:
        """
        Format a single scene for text output.
        
        Args:
            scene: Scene dictionary
            scene_number: Scene number for display
            
        Returns:
            Formatted scene text
        """
        scene_parts = []
        
        # Scene title
        title = scene.get('title', f'Scene {scene_number}')
        scene_parts.append(f"\n{title.upper()}")
        #scene_parts.append("-" * len(f"SCENE {scene_number}: {title}"))
        scene_parts.append("")
        
        # Scene content - try both content fields
        content = scene.get('content', '')
        content_rtf = scene.get('content_rtf', '')
        
        # Use RTF content if regular content is empty
        if not content and content_rtf:
            content = content_rtf
        
        if content:
            # Clean HTML/RTF content first if it contains HTML tags
            if '<' in content and '>' in content:
                cleaned_content = clean_html_css(content)
            else:
                cleaned_content = content
            
            # Then apply standard formatting
            formatted_content = self.format_content(cleaned_content)
            scene_parts.append(formatted_content)
        else:
            scene_parts.append("[No content]")
        
        # Scene notes (if any)
        notes = scene.get('notes', '').strip()
        if notes:
            scene_parts.append("")
            scene_parts.append("Notes:")
            scene_parts.append(self.format_content(notes))
        
        # Word count
        word_count = scene.get('word_count', 0)
        if word_count > 0:
            scene_parts.append("")
            scene_parts.append(f"[Word count: {word_count:,}]")
        
        return "\n".join(scene_parts) + "\n"
    
    def _format_character(self, character: dict) -> str:
        """
        Format character information for text output.
        
        Args:
            character: Character dictionary
            
        Returns:
            Formatted character text
        """
        char_parts = []
        
        # Character name
        name = character.get('name', 'Unknown Character')
        full_name = character.get('full_name', '')
        if full_name and full_name != name:
            char_parts.append(f"{name} ({full_name})")
        else:
            char_parts.append(name)
        
        char_parts.append("-" * len(char_parts[0]))
        
        # Basic info
        info_items = []
        age = character.get('age')
        if age:
            info_items.append(f"Age: {age}")
        
        gender = character.get('gender')
        if gender:
            info_items.append(f"Gender: {gender}")
        
        occupation = character.get('occupation')
        if occupation:
            info_items.append(f"Occupation: {occupation}")
        
        if info_items:
            char_parts.append(" | ".join(info_items))
            char_parts.append("")
        
        # Description
        description = character.get('description', '').strip()
        if description:
            char_parts.append("Description:")
            char_parts.append(self.format_content(description))
            char_parts.append("")
        
        # Personality
        personality = character.get('personality', '').strip()
        if personality:
            char_parts.append("Personality:")
            char_parts.append(self.format_content(personality))
            char_parts.append("")
        
        return "\n".join(char_parts) + "\n"
    
    def _format_location(self, location: dict) -> str:
        """
        Format location information for text output.
        
        Args:
            location: Location dictionary
            
        Returns:
            Formatted location text
        """
        loc_parts = []
        
        # Location name
        name = location.get('name', 'Unknown Location')
        loc_parts.append(name)
        loc_parts.append("-" * len(name))
        
        # Location type
        location_type = location.get('type')
        if location_type:
            loc_parts.append(f"Type: {location_type}")
            loc_parts.append("")
        
        # Description
        description = location.get('description', '').strip()
        if description:
            loc_parts.append("Description:")
            loc_parts.append(self.format_content(description))
            loc_parts.append("")
        
        # Atmosphere
        atmosphere = location.get('atmosphere', '').strip()
        if atmosphere:
            loc_parts.append("Atmosphere:")
            loc_parts.append(self.format_content(atmosphere))
            loc_parts.append("")
        
        return "\n".join(loc_parts) + "\n"