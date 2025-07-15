"""Font manager for the embedded RTF editor."""

from PySide6.QtWidgets import QTextEdit, QColorDialog
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QFont, QFontInfo, QTextCharFormat, QColor, QBrush


class FontManager(QObject):
    """Manages font operations for the RTF editor."""
    
    def __init__(self, text_edit: QTextEdit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
        
    def change_font_family(self, font_name):
        """Change font family."""
        if not font_name:
            return
            
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            format = QTextCharFormat()
            format.setFontFamily(font_name)
            cursor.mergeCharFormat(format)
        else:
            font_obj = self.text_edit.currentFont()
            font_obj.setFamily(font_name)
            self.text_edit.setCurrentFont(font_obj)
        
        # Restore focus to editor
        self.text_edit.setFocus()
            
    def change_font_size(self, size_text):
        """Change font size."""
        try:
            size = int(size_text)
            
            # Validate font size range
            if size < 1 or size > 999:
                return
                
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                format = QTextCharFormat()
                format.setFontPointSize(size)
                cursor.mergeCharFormat(format)
            else:
                font = self.text_edit.currentFont()
                font.setPointSize(size)
                self.text_edit.setCurrentFont(font)
                
        except ValueError:
            # Ignore invalid values
            return
        
        # Restore focus to editor
        self.text_edit.setFocus()
            
    def toggle_bold(self):
        """Toggle bold formatting."""
        cursor = self.text_edit.textCursor()
        current_format = cursor.charFormat()
        
        # Check current bold state
        is_bold = current_format.fontWeight() == QFont.Weight.Bold
        
        # Toggle state
        format = QTextCharFormat()
        format.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Restore focus to editor
        self.text_edit.setFocus()
            
    def toggle_italic(self):
        """Toggle italic formatting."""
        cursor = self.text_edit.textCursor()
        current_format = cursor.charFormat()
        
        # Check current italic state
        is_italic = current_format.fontItalic()
        
        # Toggle state
        format = QTextCharFormat()
        format.setFontItalic(not is_italic)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Restore focus to editor
        self.text_edit.setFocus()
            
    def toggle_underline(self):
        """Toggle underline formatting."""
        cursor = self.text_edit.textCursor()
        current_format = cursor.charFormat()
        
        # Check current underline state
        is_underline = current_format.fontUnderline()
        
        # Toggle state
        format = QTextCharFormat()
        format.setFontUnderline(not is_underline)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Restore focus to editor
        self.text_edit.setFocus()
            
    def change_text_color(self):
        """Change text color with color dialog."""
        color = QColorDialog.getColor(Qt.GlobalColor.black, self.text_edit, "Wybierz kolor tekstu")
        if color.isValid():
            cursor = self.text_edit.textCursor()
            format = QTextCharFormat()
            format.setForeground(QBrush(color))
            
            if cursor.hasSelection():
                cursor.mergeCharFormat(format)
            else:
                self.text_edit.mergeCurrentCharFormat(format)
        
        # Restore focus to editor
        self.text_edit.setFocus()
        
    def change_text_color_from_toolbar(self, color):
        """Change text color from toolbar manager signal."""
        cursor = self.text_edit.textCursor()
        format = QTextCharFormat()
        format.setForeground(QBrush(color))
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.mergeCurrentCharFormat(format)
        
        # Restore focus to editor
        self.text_edit.setFocus()
            
    def set_alignment(self, alignment):
        """Set text alignment."""
        self.text_edit.setAlignment(alignment)
        
        # Restore focus to editor
        self.text_edit.setFocus()
        
    def set_default_font(self):
        """Set default font for editor and new text."""
        # Best fonts for book writing available in system (in order of preference)
        preferred_fonts = ["Georgia", "Times New Roman", "Nimbus Roman", "Bitstream Charter", 
                          "Liberation Serif", "URW Bookman", "C059", "DejaVu Serif"]
        selected_font = None
        
        for font_name in preferred_fonts:
            font = QFont(font_name, 12)
            if QFontInfo(font).family() == font_name:
                selected_font = font
                break
                
        if not selected_font:
            # Fallback to system serif font
            selected_font = QFont("serif", 12)
            
        # Set font for entire editor
        self.text_edit.setFont(selected_font)
        
        # Set font as current (for new text)
        self.text_edit.setCurrentFont(selected_font)
        
        return selected_font
    
    def get_preferred_fonts(self):
        """Get list of preferred writing fonts."""
        return ["Georgia", "Times New Roman", "Nimbus Roman", "Bitstream Charter", 
                "Liberation Serif", "URW Bookman", "C059", "DejaVu Serif"]