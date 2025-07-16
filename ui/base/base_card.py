"""Base card widget with common styling and behavior."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QMouseEvent

from .enhanced_theme_manager import EnhancedThemeManager
from .ui_font_manager import UIFontManager


class BaseCard(QFrame):
    """Base card widget with common styling and behavior."""
    
    clicked = Signal()
    
    def __init__(self, width=200, height=120, parent=None):
        super().__init__(parent)
        self.theme_manager = EnhancedThemeManager()
        self.font_manager = UIFontManager()
        self.setup_base_ui(width, height)
        self.apply_theme()
        
    def setup_base_ui(self, width, height):
        """Setup base card UI with common styling."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(8)
        
    def apply_theme(self):
        """Apply theme styling to the card."""
        colors = self.theme_manager.get_theme_colors()
        
        self.setStyleSheet(f"""
            BaseCard {{
                background-color: {colors["card_background"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
            }}
            BaseCard:hover {{
                background-color: {colors["card_hover"]};
                border: 1px solid {colors["accent"]};
            }}
        """)
    
    def refresh_theme(self):
        """Refresh theme styling."""
        self.apply_theme()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def create_title_label(self, text, font_size=12, bold=True):
        """Create a styled title label."""
        label = QLabel(text)
        if bold:
            font = self.font_manager.get_font(size=font_size, weight=QFont.Weight.Bold)
        else:
            font = self.font_manager.get_font(size=font_size)
        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        return label
    
    def create_info_label(self, text, font_size=10):
        """Create a styled info label."""
        label = QLabel(text)
        label.setFont(self.font_manager.get_font(size=font_size))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        colors = self.theme_manager.get_theme_colors()
        label.setStyleSheet(f"color: {colors['secondary_text']};")
        
        return label
    
    def create_header_layout(self):
        """Create a header layout for title and badges."""
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        return header_layout
    
    def add_stretch(self):
        """Add a stretch to the main layout."""
        self.main_layout.addStretch()
    
    def add_widget(self, widget):
        """Add a widget to the main layout."""
        self.main_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the main layout."""
        self.main_layout.addLayout(layout)