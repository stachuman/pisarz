"""Font manager for consistent typography across the application."""

from typing import Dict, Optional, List
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import QSettings


class FontManager:
    """Manager for consistent font usage throughout the application."""
    
    def __init__(self):
        self.settings = QSettings()
        self.font_database = QFontDatabase()
        self.load_settings()
        
    def load_settings(self):
        """Load font settings from configuration."""
        self.default_family = self.settings.value("font/default_family", self.get_default_font_family())
        self.default_size = int(self.settings.value("font/default_size", 9))
        self.editor_family = self.settings.value("font/editor_family", self.get_default_monospace_family())
        self.editor_size = int(self.settings.value("font/editor_size", 11))
        self.ui_scale = float(self.settings.value("font/ui_scale", 1.0))
        
    def save_settings(self):
        """Save font settings to configuration."""
        self.settings.setValue("font/default_family", self.default_family)
        self.settings.setValue("font/default_size", self.default_size)
        self.settings.setValue("font/editor_family", self.editor_family)
        self.settings.setValue("font/editor_size", self.editor_size)
        self.settings.setValue("font/ui_scale", self.ui_scale)
        
    def get_default_font_family(self) -> str:
        """Get the default system font family."""
        system_fonts = ["Segoe UI", "SF Pro Display", "Roboto", "Ubuntu", "Arial", "sans-serif"]
        
        for font_family in system_fonts:
            if self.font_database.hasFamily(font_family):
                return font_family
        
        return "Arial"  # Fallback
        
    def get_default_monospace_family(self) -> str:
        """Get the default monospace font family."""
        mono_fonts = ["JetBrains Mono", "Fira Code", "Consolas", "Monaco", "Menlo", "Ubuntu Mono", "Courier New"]
        
        for font_family in mono_fonts:
            if self.font_database.hasFamily(font_family):
                return font_family
        
        return "Courier New"  # Fallback
        
    def get_available_fonts(self) -> List[str]:
        """Get list of available system fonts."""
        return self.font_database.families()
        
    def get_available_monospace_fonts(self) -> List[str]:
        """Get list of available monospace fonts."""
        all_fonts = self.font_database.families()
        mono_fonts = []
        
        for font_family in all_fonts:
            font = QFont(font_family)
            if font.fixedPitch():
                mono_fonts.append(font_family)
        
        return mono_fonts
        
    def set_default_font(self, family: str, size: int):
        """Set the default UI font."""
        self.default_family = family
        self.default_size = size
        self.save_settings()
        
    def set_editor_font(self, family: str, size: int):
        """Set the editor font."""
        self.editor_family = family
        self.editor_size = size
        self.save_settings()
        
    def set_ui_scale(self, scale: float):
        """Set the UI scale factor."""
        self.ui_scale = scale
        self.save_settings()
        
    def scale_size(self, size: int) -> int:
        """Scale font size according to UI scale."""
        return int(size * self.ui_scale)
        
    def get_font(self, size: int = None, weight: QFont.Weight = QFont.Weight.Normal, 
                 italic: bool = False, family: str = None) -> QFont:
        """Get a font with specified properties."""
        if family is None:
            family = self.default_family
        if size is None:
            size = self.default_size
            
        size = self.scale_size(size)
        
        font = QFont(family, size, weight)
        font.setItalic(italic)
        
        return font
        
    def get_editor_font(self, size: int = None) -> QFont:
        """Get editor font."""
        if size is None:
            size = self.editor_size
            
        size = self.scale_size(size)
        return QFont(self.editor_family, size)
        
    def get_title_font(self, size: int = 20) -> QFont:
        """Get title font."""
        return self.get_font(size=size, weight=QFont.Weight.Bold)
        
    def get_heading_font(self, size: int = 16) -> QFont:
        """Get heading font."""
        return self.get_font(size=size, weight=QFont.Weight.Bold)
        
    def get_subheading_font(self, size: int = 14) -> QFont:
        """Get subheading font."""
        return self.get_font(size=size, weight=QFont.Weight.Bold)
        
    def get_body_font(self, size: int = None) -> QFont:
        """Get body text font."""
        if size is None:
            size = self.default_size
        return self.get_font(size=size)
        
    def get_caption_font(self, size: int = 8) -> QFont:
        """Get caption font."""
        return self.get_font(size=size)
        
    def get_button_font(self, size: int = None) -> QFont:
        """Get button font."""
        if size is None:
            size = self.default_size
        return self.get_font(size=size, weight=QFont.Weight.Medium)
        
    def get_label_font(self, size: int = None) -> QFont:
        """Get label font."""
        if size is None:
            size = self.default_size
        return self.get_font(size=size)
        
    def get_input_font(self, size: int = None) -> QFont:
        """Get input field font."""
        if size is None:
            size = self.default_size
        return self.get_font(size=size)
        
    def get_menu_font(self, size: int = None) -> QFont:
        """Get menu font."""
        if size is None:
            size = self.default_size
        return self.get_font(size=size)
        
    def get_tooltip_font(self, size: int = 8) -> QFont:
        """Get tooltip font."""
        return self.get_font(size=size)
        
    def get_status_font(self, size: int = 8) -> QFont:
        """Get status bar font."""
        return self.get_font(size=size)
        
    def get_code_font(self, size: int = None) -> QFont:
        """Get code font (monospace)."""
        if size is None:
            size = self.editor_size
        size = self.scale_size(size)
        return QFont(self.editor_family, size)
        
    def get_font_info(self, font: QFont) -> Dict[str, any]:
        """Get information about a font."""
        return {
            "family": font.family(),
            "size": font.pointSize(),
            "weight": font.weight(),
            "italic": font.italic(),
            "bold": font.bold(),
            "fixed_pitch": font.fixedPitch(),
            "pixel_size": font.pixelSize(),
            "stretch": font.stretch(),
            "style": font.style(),
            "style_hint": font.styleHint(),
            "style_name": font.styleName(),
            "style_strategy": font.styleStrategy()
        }
        
    def create_font_from_info(self, info: Dict[str, any]) -> QFont:
        """Create a font from font info dictionary."""
        font = QFont(info["family"], info["size"])
        font.setWeight(info["weight"])
        font.setItalic(info["italic"])
        font.setStyle(info["style"])
        font.setStyleHint(info["style_hint"])
        font.setStyleStrategy(info["style_strategy"])
        font.setStretch(info["stretch"])
        return font
        
    def get_font_sizes(self) -> List[int]:
        """Get standard font sizes."""
        return [6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]
        
    def get_font_weights(self) -> Dict[str, QFont.Weight]:
        """Get available font weights."""
        return {
            "Thin": QFont.Weight.Thin,
            "Extra Light": QFont.Weight.ExtraLight,
            "Light": QFont.Weight.Light,
            "Normal": QFont.Weight.Normal,
            "Medium": QFont.Weight.Medium,
            "DemiBold": QFont.Weight.DemiBold,
            "Bold": QFont.Weight.Bold,
            "ExtraBold": QFont.Weight.ExtraBold,
            "Black": QFont.Weight.Black
        }
        
    def validate_font(self, family: str, size: int) -> bool:
        """Validate if font family and size are valid."""
        if not self.font_database.hasFamily(family):
            return False
            
        if size < 6 or size > 72:
            return False
            
        return True
        
    def get_font_metrics(self, font: QFont) -> Dict[str, int]:
        """Get font metrics for a given font."""
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        
        return {
            "height": metrics.height(),
            "ascent": metrics.ascent(),
            "descent": metrics.descent(),
            "leading": metrics.leading(),
            "line_spacing": metrics.lineSpacing(),
            "max_width": metrics.maxWidth(),
            "average_char_width": metrics.averageCharWidth(),
            "x_height": metrics.xHeight(),
            "cap_height": metrics.capHeight()
        }
        
    def calculate_text_width(self, text: str, font: QFont) -> int:
        """Calculate the width of text in pixels."""
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        return metrics.horizontalAdvance(text)
        
    def calculate_text_height(self, font: QFont, lines: int = 1) -> int:
        """Calculate the height of text in pixels."""
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        return metrics.height() * lines
        
    def elide_text(self, text: str, font: QFont, width: int) -> str:
        """Elide text to fit within specified width."""
        from PySide6.QtGui import QFontMetrics
        from PySide6.QtCore import Qt
        metrics = QFontMetrics(font)
        return metrics.elidedText(text, Qt.TextElideMode.ElideRight, width)
        
    def word_wrap_text(self, text: str, font: QFont, width: int) -> List[str]:
        """Word wrap text to fit within specified width."""
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if metrics.horizontalAdvance(test_line) <= width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
            
        return lines
        
    def get_font_stylesheet(self, font: QFont) -> str:
        """Get CSS stylesheet for a font."""
        weight_map = {
            QFont.Weight.Thin: "100",
            QFont.Weight.ExtraLight: "200",
            QFont.Weight.Light: "300",
            QFont.Weight.Normal: "400",
            QFont.Weight.Medium: "500",
            QFont.Weight.DemiBold: "600",
            QFont.Weight.Bold: "700",
            QFont.Weight.ExtraBold: "800",
            QFont.Weight.Black: "900"
        }
        
        weight = weight_map.get(font.weight(), "400")
        style = "italic" if font.italic() else "normal"
        
        return f"""
        font-family: "{font.family()}";
        font-size: {font.pointSize()}pt;
        font-weight: {weight};
        font-style: {style};
        """