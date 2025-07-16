"""Base dialog widget with common styling and behavior."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .enhanced_theme_manager import EnhancedThemeManager
from .ui_font_manager import UIFontManager
from i18n import _


class BaseDialog(QDialog):
    """Base dialog widget with common styling and behavior."""
    
    def __init__(self, title="Dialog", width=400, height=300, modal=True, parent=None):
        super().__init__(parent)
        self.theme_manager = EnhancedThemeManager()
        self.font_manager = UIFontManager()
        self.setup_base_ui(title, width, height, modal)
        self.apply_theme()
        
    def setup_base_ui(self, title, width, height, modal):
        """Setup base dialog UI with common styling."""
        self.setWindowTitle(title)
        self.setMinimumSize(width, height)
        self.setModal(modal)
        
        # Set window flags for non-modal dialogs
        if not modal:
            self.setWindowFlags(
                Qt.Window | 
                Qt.WindowStaysOnTopHint | 
                Qt.WindowCloseButtonHint | 
                Qt.WindowMinimizeButtonHint
            )
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Content area (to be filled by subclasses)
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)
        
        # Button area
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        
    def apply_theme(self):
        """Apply theme styling to the dialog."""
        colors = self.theme_manager.get_theme_colors()
        
        self.setStyleSheet(f"""
            BaseDialog {{
                background-color: {colors["background"]};
                color: {colors["text"]};
            }}
            QPushButton {{
                background-color: {colors["button_background"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["button_pressed"]};
            }}
        """)
    
    def refresh_theme(self):
        """Refresh theme styling."""
        self.apply_theme()
        
    def add_content_widget(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)
        
    def add_content_layout(self, layout):
        """Add a layout to the content area."""
        self.content_layout.addLayout(layout)
        
    def add_stretch(self):
        """Add a stretch to the content area."""
        self.content_layout.addStretch()
        
    def create_button_box(self, buttons=None):
        """Create a standard button box."""
        if buttons is None:
            buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        self.button_layout.addWidget(button_box)
        return button_box
        
    def create_custom_button(self, text, callback=None, style="primary"):
        """Create a custom styled button."""
        button = QPushButton(text)
        
        if callback:
            button.clicked.connect(callback)
            
        # Apply button-specific styling
        colors = self.theme_manager.get_theme_colors()
        if style == "primary":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors["accent"]};
                    color: white;
                    border: 1px solid {colors["accent"]};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {colors["accent_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["accent_pressed"]};
                }}
            """)
        elif style == "secondary":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors["secondary_button"]};
                    color: {colors["text"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {colors["secondary_button_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["secondary_button_pressed"]};
                }}
            """)
        elif style == "danger":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors["danger"]};
                    color: white;
                    border: 1px solid {colors["danger"]};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {colors["danger_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["danger_pressed"]};
                }}
            """)
        
        return button
        
    def add_button(self, button):
        """Add a button to the button area."""
        self.button_layout.addWidget(button)
        
    def add_button_stretch(self):
        """Add a stretch to the button area."""
        self.button_layout.addStretch()
    
    def create_section_title(self, text, font_size=14):
        """Create a section title label."""
        from PySide6.QtWidgets import QLabel
        label = QLabel(text)
        label.setFont(self.font_manager.get_font(size=font_size, weight=QFont.Weight.Bold))
        
        colors = self.theme_manager.get_theme_colors()
        label.setStyleSheet(f"color: {colors['heading']}; margin-top: 10px;")
        
        return label