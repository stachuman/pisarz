"""Enhanced theme manager with comprehensive color support."""

from typing import Dict, Optional
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from .theme_colors import get_theme_colors, THEME_COLORS


class EnhancedThemeManager:
    """Enhanced theme manager with comprehensive color support."""
    
    def __init__(self):
        self.settings = QSettings()
        self.current_theme = self.get_current_theme()
        self.theme_colors = get_theme_colors(self._map_theme_name(self.current_theme))
        
    def _map_theme_name(self, old_theme_name: str) -> str:
        """Map old theme names to new theme names for backward compatibility."""
        theme_mapping = {
            "Professional": "default",
            "Jasny": "default", 
            "Ciemny": "dark",
            "Sepia": "default",
            "Leśny": "default",
            "Niebieskoszary": "blue",
            "Light": "default",
            "Dark": "dark",
            "Blue-gray": "blue"
        }
        return theme_mapping.get(old_theme_name, old_theme_name)
        
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.settings.value("theme", "default")
    
    def set_theme(self, theme_name: str):
        """Set the current theme."""
        mapped_theme = self._map_theme_name(theme_name)
        if mapped_theme in THEME_COLORS:
            self.current_theme = theme_name  # Store original name for compatibility
            self.theme_colors = get_theme_colors(mapped_theme)
            self.settings.setValue("theme", theme_name)
            self.apply_global_theme()
            
    def get_theme_colors(self) -> Dict[str, str]:
        """Get current theme colors."""
        return self.theme_colors
        
    def get_available_themes(self) -> dict:
        """Get available themes in the old format for compatibility."""
        # Return themes in the old format expected by settings dialog
        return {
            "Professional": {
                "name": "Professional",
                "description": "Modern professional theme with subtle colors",
                "background": THEME_COLORS["default"]["background"],
                "text": THEME_COLORS["default"]["text"],
                "accent": THEME_COLORS["default"]["accent"],
                "border": THEME_COLORS["default"]["border"]
            },
            "Ciemny": {
                "name": "Ciemny", 
                "description": "Dark theme for night work",
                "background": THEME_COLORS["dark"]["background"],
                "text": THEME_COLORS["dark"]["text"],
                "accent": THEME_COLORS["dark"]["accent"],
                "border": THEME_COLORS["dark"]["border"]
            },
            "Niebieskoszary": {
                "name": "Niebieskoszary",
                "description": "Professional theme in blue shades",
                "background": THEME_COLORS["blue"]["background"],
                "text": THEME_COLORS["blue"]["text"],
                "accent": THEME_COLORS["blue"]["accent"],
                "border": THEME_COLORS["blue"]["border"]
            }
        }
        
    def apply_global_theme(self):
        """Apply theme to the entire application."""
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.get_global_stylesheet())
            
    def get_global_stylesheet(self) -> str:
        """Get global stylesheet for the current theme."""
        colors = self.theme_colors
        
        return f"""
        /* Global application styling */
        QWidget {{
            background-color: {colors["background"]};
            color: {colors["text"]};
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 9pt;
        }}
        
        /* Main window */
        QMainWindow {{
            background-color: {colors["background"]};
            border: none;
        }}
        
        /* Labels */
        QLabel {{
            color: {colors["text"]};
            background-color: transparent;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors["button_background"]};
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            padding: 6px 12px;
            color: {colors["text"]};
        }}
        
        QPushButton:hover {{
            background-color: {colors["button_hover"]};
        }}
        
        QPushButton:pressed {{
            background-color: {colors["button_pressed"]};
        }}
        
        QPushButton:disabled {{
            background-color: {colors["separator"]};
            color: {colors["secondary_text"]};
            border: 1px solid {colors["separator"]};
        }}
        
        /* Input fields */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {colors["input_background"]};
            border: 1px solid {colors["input_border"]};
            border-radius: 4px;
            padding: 6px;
            color: {colors["text"]};
            selection-background-color: {colors["accent"]};
            selection-color: white;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {colors["input_focus"]};
        }}
        
        /* Combo boxes */
        QComboBox {{
            background-color: {colors["input_background"]};
            border: 1px solid {colors["input_border"]};
            border-radius: 4px;
            padding: 6px;
            color: {colors["text"]};
        }}
        
        QComboBox:hover {{
            border: 1px solid {colors["accent"]};
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors["input_background"]};
            border: 1px solid {colors["border"]};
            selection-background-color: {colors["accent"]};
            selection-color: white;
        }}
        
        /* Check boxes and radio buttons */
        QCheckBox, QRadioButton {{
            color: {colors["text"]};
            spacing: 8px;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}
        
        QCheckBox::indicator:unchecked {{
            background-color: {colors["input_background"]};
            border: 1px solid {colors["input_border"]};
            border-radius: 2px;
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors["accent"]};
            border: 1px solid {colors["accent"]};
            border-radius: 2px;
        }}
        
        /* Scroll areas */
        QScrollArea {{
            border: none;
            background-color: {colors["background"]};
        }}
        
        QScrollBar:vertical {{
            background-color: {colors["separator"]};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors["secondary_text"]};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors["accent"]};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        /* Frames */
        QFrame {{
            border: none;
        }}
        
        QFrame[frameShape="1"] {{ /* Box frame */
            border: 1px solid {colors["border"]};
            border-radius: 4px;
        }}
        
        QFrame[frameShape="4"] {{ /* HLine */
            color: {colors["separator"]};
        }}
        
        QFrame[frameShape="5"] {{ /* VLine */
            color: {colors["separator"]};
        }}
        
        /* Group boxes */
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            margin: 8px 0px;
            padding-top: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            background-color: {colors["background"]};
            color: {colors["heading"]};
        }}
        
        /* Tab widgets */
        QTabWidget::pane {{
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            background-color: {colors["background"]};
        }}
        
        QTabBar::tab {{
            background-color: {colors["button_background"]};
            border: 1px solid {colors["border"]};
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
            color: {colors["text"]};
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors["background"]};
            border-bottom: 1px solid {colors["accent"]};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors["button_hover"]};
        }}
        
        /* Menu bars and menus */
        QMenuBar {{
            background-color: {colors["nav_background"]};
            border-bottom: 1px solid {colors["border"]};
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
            color: {colors["text"]};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors["nav_hover"]};
        }}
        
        QMenu {{
            background-color: {colors["input_background"]};
            border: 1px solid {colors["border"]};
            padding: 4px 0px;
        }}
        
        QMenu::item {{
            padding: 6px 20px;
            color: {colors["text"]};
        }}
        
        QMenu::item:selected {{
            background-color: {colors["accent"]};
            color: white;
        }}
        
        /* Status bar */
        QStatusBar {{
            background-color: {colors["nav_background"]};
            border-top: 1px solid {colors["border"]};
            color: {colors["text"]};
        }}
        
        /* Splitters */
        QSplitter::handle {{
            background-color: {colors["separator"]};
        }}
        
        QSplitter::handle:horizontal {{
            width: 3px;
        }}
        
        QSplitter::handle:vertical {{
            height: 3px;
        }}
        
        /* Tool tips */
        QToolTip {{
            background-color: {colors["overlay"]};
            color: white;
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            padding: 6px;
        }}
        
        /* Progress bars */
        QProgressBar {{
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            text-align: center;
            background-color: {colors["separator"]};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors["accent"]};
            border-radius: 2px;
        }}
        
        /* Dialogs - Enhanced styling */
        QDialog {{
            background-color: {colors["background"]};
            color: {colors["text"]};
            border: 1px solid {colors["border"]};
        }}
        
        /* Message Box styling */
        QMessageBox {{
            background-color: {colors["background"]};
            color: {colors["text"]};
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
            min-height: 24px;
        }}
        
        /* List widgets */
        QListWidget {{
            background-color: {colors["input_background"]};
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            color: {colors["text"]};
            selection-background-color: {colors["accent"]};
            selection-color: white;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 4px 8px;
            border: none;
            min-height: 20px;
        }}
        
        QListWidget::item:hover {{
            background-color: {colors["button_hover"]};
        }}
        
        QListWidget::item:selected {{
            background-color: {colors["accent"]};
            color: white;
        }}
        
        /* Tree widgets */
        QTreeWidget {{
            background-color: {colors["input_background"]};
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            color: {colors["text"]};
            selection-background-color: {colors["accent"]};
            selection-color: white;
            outline: none;
        }}
        
        QTreeWidget::item {{
            padding: 4px;
            border: none;
            min-height: 20px;
        }}
        
        QTreeWidget::item:hover {{
            background-color: {colors["button_hover"]};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {colors["accent"]};
            color: white;
        }}
        """
    
    def get_card_stylesheet(self) -> str:
        """Get stylesheet for card widgets."""
        colors = self.theme_colors
        
        return f"""
        QFrame {{
            background-color: {colors["card_background"]};
            border: 1px solid {colors["border"]};
            border-radius: 8px;
        }}
        
        QFrame:hover {{
            background-color: {colors["card_hover"]};
            border: 1px solid {colors["accent"]};
        }}
        """
        
    def get_dialog_stylesheet(self) -> str:
        """Get stylesheet for dialog widgets."""
        colors = self.theme_colors
        
        return f"""
        QDialog {{
            background-color: {colors["background"]};
            color: {colors["text"]};
        }}
        """
        
    def get_accent_button_stylesheet(self) -> str:
        """Get stylesheet for accent/primary buttons."""
        colors = self.theme_colors
        
        return f"""
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
        """
        
    def get_danger_button_stylesheet(self) -> str:
        """Get stylesheet for danger buttons."""
        colors = self.theme_colors
        
        return f"""
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
        """