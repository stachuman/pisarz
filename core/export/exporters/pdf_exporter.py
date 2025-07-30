"""
PDF exporter - Export to PDF format using ReportLab.
Professional PDF generation with formatting, styles, and page management.
"""

from typing import List, Dict, Any
from datetime import datetime
import os

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Create dummy classes to prevent NameError during class definition
    class ParagraphStyle:
        pass
    class SimpleDocTemplate:
        pass
    class Paragraph:
        pass
    class Spacer:
        pass
    class PageBreak:
        pass
    class Table:
        pass
    class TableStyle:
        pass

from .base_exporter import BaseExporter
from ..models import ExportConfig, ExportResult, ExportData, ExportFormat


class PDFExporter(BaseExporter):
    """Export to PDF format using ReportLab with professional formatting"""
    
    def __init__(self):
        super().__init__()
        if not REPORTLAB_AVAILABLE:
            self.logger.warning("ReportLab not available - PDF export will not work")
        else:
            self._register_unicode_fonts()
    
    def get_supported_formats(self) -> List[ExportFormat]:
        """Return supported formats"""
        return [ExportFormat.PDF]
    
    def get_output_extension(self) -> str:
        """Return file extension"""
        return ".pdf"
    
    def validate_config(self, config: ExportConfig) -> List[str]:
        """Validate PDF-specific configuration"""
        errors = super().validate_config(config)
        
        if not REPORTLAB_AVAILABLE:
            errors.append("ReportLab library not available - cannot export to PDF")
        
        return errors
    
    def export(self, data: ExportData, config: ExportConfig) -> ExportResult:
        """
        Export scenes to PDF with professional formatting.
        
        Args:
            data: ExportData with scenes and metadata
            config: ExportConfig with export parameters
            
        Returns:
            ExportResult with operation outcome
        """
        if not REPORTLAB_AVAILABLE:
            return self.create_error_result(
                "ReportLab library not available",
                ExportFormat.PDF
            )
        
        try:
            self.log_export_start(config, data)
            
            # Ensure output directory exists
            if not self.ensure_output_directory(config.output_path):
                return self.create_error_result(
                    "Failed to create output directory",
                    ExportFormat.PDF
                )
            
            # Create PDF document
            doc = SimpleDocTemplate(
                config.output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build document content
            story = []
            styles = self._create_styles()
            
            # Add title page if metadata should be included
            if config.scope.include_metadata:
                title_elements = self._create_title_page(data.project_metadata, styles)
                story.extend(title_elements)
                story.append(PageBreak())
            
            # Add scenes
            for i, scene in enumerate(data.scenes):
                scene_elements = self._format_scene(scene, i + 1, styles)
                story.extend(scene_elements)
                
                # Add page break between scenes (but not after the last one)
                if i < len(data.scenes) - 1:
                    story.append(PageBreak())
            
            # Add character information if requested
            if config.scope.include_characters and data.characters:
                story.append(PageBreak())
                char_elements = self._create_characters_section(data.characters, styles)
                story.extend(char_elements)
            
            # Add location information if requested
            if config.scope.include_locations and data.locations:
                story.append(PageBreak())
                loc_elements = self._create_locations_section(data.locations, styles)
                story.extend(loc_elements)
            
            # Build PDF
            try:
                doc.build(story)
                
                # Create success result
                result = self.create_success_result(
                    config.output_path,
                    len(data.scenes),
                    format_used=ExportFormat.PDF
                )
                
                self.log_export_result(result)
                return result
                
            except Exception as e:
                error_msg = f"Failed to build PDF document: {str(e)}"
                self.logger.error(error_msg)
                return self.create_error_result(error_msg, ExportFormat.PDF)
            
        except Exception as e:
            error_msg = f"PDF export failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return self.create_error_result(error_msg, ExportFormat.PDF)
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """
        Create PDF paragraph styles with Unicode font support.
        
        Returns:
            Dictionary of paragraph styles
        """
        base_styles = getSampleStyleSheet()
        styles = {}
        
        # Choose appropriate fonts based on availability
        if hasattr(self, 'unicode_fonts_available') and self.unicode_fonts_available:
            title_font = 'DejaVuSans-Bold'
            heading_font = 'DejaVuSans-Bold'
            body_font = 'DejaVuSerif'
            italic_font = 'DejaVuSerif-Italic'
        else:
            # Fallback to ReportLab's built-in fonts (limited Unicode support)
            title_font = 'Helvetica-Bold'
            heading_font = 'Helvetica-Bold'
            body_font = 'Times-Roman'
            italic_font = 'Times-Italic'
            self.logger.warning("Using fallback fonts - Polish characters may not display properly")
        
        # Title style
        styles['title'] = ParagraphStyle(
            'CustomTitle',
            parent=base_styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName=title_font
        )
        
        # Author style
        styles['author'] = ParagraphStyle(
            'Author',
            parent=base_styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=italic_font
        )
        
        # Metadata style
        styles['metadata'] = ParagraphStyle(
            'Metadata',
            parent=base_styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        # Scene title style
        styles['scene_title'] = ParagraphStyle(
            'SceneTitle',
            parent=base_styles['Heading1'],
            fontSize=16,
            spaceAfter=18,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName=heading_font
        )
        
        # Scene content style
        styles['scene_content'] = ParagraphStyle(
            'SceneContent',
            parent=base_styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName=body_font,
            leading=16
        )
        
        # Section header style
        styles['section_header'] = ParagraphStyle(
            'SectionHeader',
            parent=base_styles['Heading1'],
            fontSize=18,
            spaceAfter=24,
            spaceBefore=12,
            alignment=TA_CENTER,
            fontName=heading_font
        )
        
        # Character name style
        styles['character_name'] = ParagraphStyle(
            'CharacterName',
            parent=base_styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=16,
            fontName=heading_font
        )
        
        # Description style
        styles['description'] = ParagraphStyle(
            'Description',
            parent=base_styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName=body_font
        )
        
        # Notes style
        styles['notes'] = ParagraphStyle(
            'Notes',
            parent=base_styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_LEFT,
            fontName=italic_font,
            textColor=colors.grey,
            leftIndent=20
        )
        
        return styles
    
    def _create_title_page(self, project_metadata: dict, styles: Dict[str, ParagraphStyle]) -> List:
        """
        Create title page with project information.
        
        Args:
            project_metadata: Project metadata dictionary
            styles: Dictionary of paragraph styles
            
        Returns:
            List of ReportLab flowables for title page
        """
        elements = []
        
        # Add some space at top
        elements.append(Spacer(1, 2*inch))
        
        # Title
        title = project_metadata.get('title') or project_metadata.get('name', 'Untitled')
        elements.append(Paragraph(title, styles['title']))
        
        # Author
        author = project_metadata.get('author')
        if author:
            elements.append(Paragraph(f"by {author}", styles['author']))
        
        # Add space
        elements.append(Spacer(1, inch))
        
        # Metadata table
        metadata_data = []
        
        genre = project_metadata.get('genre')
        if genre:
            metadata_data.append(['Genre:', genre])
        
        status = project_metadata.get('status')
        if status:
            metadata_data.append(['Status:', status.title()])
        
        word_count = project_metadata.get('target_word_count')
        if word_count and word_count > 0:
            metadata_data.append(['Target Words:', f"{word_count:,}"])
        
        language = project_metadata.get('language')
        if language:
            metadata_data.append(['Language:', language.upper()])
        
        # Export timestamp
        metadata_data.append(['Exported:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        if metadata_data:
            table = Table(metadata_data, colWidths=[1.5*inch, 3*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
        
        return elements
    
    def _format_scene(self, scene: dict, scene_number: int, styles: Dict[str, ParagraphStyle]) -> List:
        """
        Format a single scene as ReportLab flowables.
        
        Args:
            scene: Scene dictionary
            scene_number: Scene number for display
            styles: Dictionary of paragraph styles
            
        Returns:
            List of ReportLab flowables
        """
        elements = []
        
        # Scene title
        title = scene.get('title', f'Scene {scene_number}')
        scene_title_text = f"{title}"
        elements.append(Paragraph(scene_title_text, styles['scene_title']))
        
        # Scene content - try both content fields
        content = scene.get('content', '')
        content_rtf = scene.get('content_rtf', '')
        
        # Use RTF content if regular content is empty
        if not content and content_rtf:
            content = content_rtf
        
        if content:
            # For PDF, let's use clean text instead of trying to preserve HTML
            # This is more reliable and avoids ReportLab HTML parsing issues
            if '<' in content and '>' in content:
                # Clean HTML content to plain text
                from ...utils.text_cleaner import clean_html_css
                cleaned_content = clean_html_css(content)
            else:
                cleaned_content = content
            
            # Format the clean content
            formatted_content = self.format_content(cleaned_content)
            paragraphs = formatted_content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    elements.append(Paragraph(paragraph.strip(), styles['scene_content']))
        else:
            elements.append(Paragraph("[No content]", styles['notes']))
        
        # Scene notes (if any)
        notes = scene.get('notes', '').strip()
        if notes:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("<b>Notes:</b>", styles['description']))
            formatted_notes = self.format_content(notes)
            elements.append(Paragraph(formatted_notes, styles['notes']))
        
        return elements
    
    def _create_characters_section(self, characters: List[dict], styles: Dict[str, ParagraphStyle]) -> List:
        """
        Create characters section.
        
        Args:
            characters: List of character dictionaries
            styles: Dictionary of paragraph styles
            
        Returns:
            List of ReportLab flowables
        """
        elements = []
        
        # Section header
        elements.append(Paragraph("Characters", styles['section_header']))
        
        for character in characters:
            # Character name
            name = character.get('name', 'Unknown Character')
            full_name = character.get('full_name', '')
            if full_name and full_name != name:
                char_title = f"{name} ({full_name})"
            else:
                char_title = name
            
            elements.append(Paragraph(char_title, styles['character_name']))
            
            # Basic info
            info_parts = []
            age = character.get('age')
            if age:
                info_parts.append(f"Age: {age}")
            
            gender = character.get('gender')
            if gender:
                info_parts.append(f"Gender: {gender}")
            
            occupation = character.get('occupation')
            if occupation:
                info_parts.append(f"Occupation: {occupation}")
            
            if info_parts:
                elements.append(Paragraph(" | ".join(info_parts), styles['description']))
            
            # Description
            description = character.get('description', '').strip()
            if description:
                formatted_desc = self.format_content(description)
                elements.append(Paragraph(f"<b>Description:</b> {formatted_desc}", styles['description']))
            
            # Add space between characters
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_locations_section(self, locations: List[dict], styles: Dict[str, ParagraphStyle]) -> List:
        """
        Create locations section.
        
        Args:
            locations: List of location dictionaries
            styles: Dictionary of paragraph styles
            
        Returns:
            List of ReportLab flowables
        """
        elements = []
        
        # Section header
        elements.append(Paragraph("Locations", styles['section_header']))
        
        for location in locations:
            # Location name
            name = location.get('name', 'Unknown Location')
            elements.append(Paragraph(name, styles['character_name']))
            
            # Location type
            location_type = location.get('type')
            if location_type:
                elements.append(Paragraph(f"<b>Type:</b> {location_type}", styles['description']))
            
            # Description
            description = location.get('description', '').strip()
            if description:
                formatted_desc = self.format_content(description)
                elements.append(Paragraph(f"<b>Description:</b> {formatted_desc}", styles['description']))
            
            # Atmosphere
            atmosphere = location.get('atmosphere', '').strip()
            if atmosphere:
                formatted_atm = self.format_content(atmosphere)
                elements.append(Paragraph(f"<b>Atmosphere:</b> {formatted_atm}", styles['description']))
            
            # Add space between locations
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _clean_html_for_reportlab(self, html_content: str) -> str:
        """
        Clean HTML content for ReportLab compatibility.
        ReportLab supports a subset of HTML tags.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned HTML suitable for ReportLab
        """
        import re
        
        # Remove DOCTYPE, html, head, body tags - keep only content
        content = re.sub(r'<!DOCTYPE[^>]*>', '', html_content, flags=re.IGNORECASE)
        content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</body>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<meta[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert Qt-specific HTML to standard HTML
        # Remove Qt-specific attributes that ReportLab doesn't understand
        content = re.sub(r'-qt-[^:;]*:[^;]*;?', '', content)
        content = re.sub(r'margin-[^:]*:[^;]*;?', '', content)
        content = re.sub(r'text-indent:[^;]*;?', '', content)
        
        # Convert span tags with font styling to ReportLab compatible format
        # ReportLab supports: <b>, <i>, <u>, <font face="..." size="..." color="...">
        def convert_span_to_font(match):
            span_content = match.group(0)
            inner_text = re.search(r'>(.*?)</span>', span_content, re.DOTALL)
            if not inner_text:
                return span_content
            
            text = inner_text.group(1)
            
            # Extract font family
            font_match = re.search(r'font-family:\s*[\'"]?([^\'";]+)', span_content)
            font_face = font_match.group(1) if font_match else None
            
            # Extract font size
            size_match = re.search(r'font-size:\s*(\d+)pt', span_content)
            font_size = size_match.group(1) if size_match else None
            
            # Build font tag
            font_attrs = []
            if font_face:
                font_attrs.append(f'face="{font_face}"')
            if font_size:
                font_attrs.append(f'size="{font_size}"')
            
            if font_attrs:
                return f'<font {" ".join(font_attrs)}>{text}</font>'
            else:
                return text
        
        # Apply span conversion
        content = re.sub(r'<span[^>]*>.*?</span>', convert_span_to_font, content, flags=re.DOTALL)
        
        # Replace <p> tags with line breaks (ReportLab handles paragraphs differently)
        content = re.sub(r'<p[^>]*>', '', content)
        content = re.sub(r'</p>', '<br/>', content)
        
        # Replace empty paragraphs with line breaks
        content = re.sub(r'<br[^>]*>\s*<br[^>]*>', '<br/><br/>', content)
        
        # Clean up excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def _register_unicode_fonts(self):
        """Register Unicode-compatible fonts for Polish characters"""
        try:
            # Try to use DejaVu fonts (commonly available on Linux)
            # These fonts support Polish characters well
            font_paths = [
                # Linux paths
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf',
                # Alternative paths
                '/System/Library/Fonts/Arial.ttf',  # macOS
                'C:\\Windows\\Fonts\\arial.ttf',     # Windows
            ]
            
            fonts_registered = 0
            
            # Register DejaVu Sans family
            for font_name, font_file in [
                ('DejaVuSans', 'DejaVuSans.ttf'),
                ('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'),
                ('DejaVuSans-Oblique', 'DejaVuSans-Oblique.ttf'),
                ('DejaVuSans-BoldOblique', 'DejaVuSans-BoldOblique.ttf'),
                ('DejaVuSerif', 'DejaVuSerif.ttf'),
                ('DejaVuSerif-Bold', 'DejaVuSerif-Bold.ttf'),
                ('DejaVuSerif-Italic', 'DejaVuSerif-Italic.ttf'),
                ('DejaVuSerif-BoldItalic', 'DejaVuSerif-BoldItalic.ttf'),
            ]:
                for base_path in [
                    '/usr/share/fonts/truetype/dejavu/',  # Standard Linux path
                    '/usr/local/share/fonts/',             # Local fonts
                    '/System/Library/Fonts/',              # macOS
                    'C:\\Windows\\Fonts\\',                # Windows
                ]:
                    font_path = os.path.join(base_path, font_file)
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont(font_name, font_path))
                            fonts_registered += 1
                            self.logger.debug(f"Registered font: {font_name}")
                            break
                        except Exception as e:
                            self.logger.debug(f"Failed to register {font_name}: {e}")
                            continue
            
            if fonts_registered > 0:
                self.logger.info(f"Successfully registered {fonts_registered} Unicode fonts for PDF export")
                # Store that we have Unicode fonts available
                self.unicode_fonts_available = True
            else:
                self.logger.warning("No Unicode-compatible fonts found - Polish characters may not display properly")
                self.unicode_fonts_available = False
                
        except Exception as e:
            self.logger.error(f"Error registering Unicode fonts: {e}")
            self.unicode_fonts_available = False