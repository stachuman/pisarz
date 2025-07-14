"""Theme management system for Pisarz application."""

import json
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QSettings


class ThemeManager:
    """Manager motywów kolorystycznych."""
    
    def __init__(self):
        self.settings = QSettings()
        self.themes = self._load_themes()
        
    def _load_themes(self):
        """Załaduj definicje motywów."""
        return {
            "Professional": {
                "name": "Professional",
                "description": "Modern professional theme with subtle colors",
                "background": "#ffffff",
                "text": "#1a202c",
                "secondary_bg": "#f7fafc", 
                "secondary_text": "#4a5568",
                "accent": "#4299e1",
                "accent_hover": "#3182ce",
                "border": "#e2e8f0",
                "editor_bg": "#ffffff",
                "editor_text": "#2d3748",
                "success": "#38a169",
                "warning": "#d69e2e",
                "danger": "#e53e3e",
                "muted": "#718096"
            },
            "Jasny": {
                "name": "Jasny",
                "description": "Klasyczny jasny motyw",
                "background": "#ffffff",
                "text": "#2c3e50",
                "secondary_bg": "#f8fafc", 
                "secondary_text": "#64748b",
                "accent": "#3b82f6",
                "accent_hover": "#2563eb",
                "border": "#e2e8f0",
                "editor_bg": "#ffffff",
                "editor_text": "#1e293b"
            },
            "Ciemny": {
                "name": "Ciemny", 
                "description": "Ciemny motyw dla pracy w nocy",
                "background": "#0f172a",
                "text": "#f1f5f9",
                "secondary_bg": "#1e293b",
                "secondary_text": "#94a3b8", 
                "accent": "#6366f1",
                "accent_hover": "#4f46e5",
                "border": "#334155",
                "editor_bg": "#0f172a",
                "editor_text": "#e2e8f0"
            },
            "Sepia": {
                "name": "Sepia",
                "description": "Ciepły motyw przypominający stare książki",
                "background": "#fef7ed",
                "text": "#78350f", 
                "secondary_bg": "#fef3c7",
                "secondary_text": "#a16207",
                "accent": "#d97706",
                "accent_hover": "#b45309",
                "border": "#fbbf24",
                "editor_bg": "#fffbeb",
                "editor_text": "#451a03"
            },
            "Leśny": {
                "name": "Leśny",
                "description": "Spokojny zielony motyw",
                "background": "#f0fdf4",
                "text": "#14532d",
                "secondary_bg": "#dcfce7", 
                "secondary_text": "#166534",
                "accent": "#16a34a",
                "accent_hover": "#15803d",
                "border": "#86efac",
                "editor_bg": "#f7fee7",
                "editor_text": "#052e16"
            },
            "Niebieskoszary": {
                "name": "Niebieskoszary",
                "description": "Profesjonalny motyw w odcieniach niebieskiego",
                "background": "#f8fafc",
                "text": "#1e293b",
                "secondary_bg": "#e2e8f0",
                "secondary_text": "#475569", 
                "accent": "#0f766e",
                "accent_hover": "#0d9488",
                "border": "#cbd5e1",
                "editor_bg": "#ffffff",
                "editor_text": "#0f172a"
            }
        }
        
    def get_available_themes(self):
        """Pobierz dostępne motywy."""
        return self.themes
        
    def get_current_theme(self):
        """Pobierz aktualny motyw."""
        return self.settings.value("theme", "Professional")
        
    def set_theme(self, theme_name):
        """Ustaw aktywny motyw."""
        if theme_name not in self.themes:
            theme_name = "Professional"
            
        self.settings.setValue("theme", theme_name)
        self._apply_theme(theme_name)
        
    def _apply_theme(self, theme_name):
        """Zastosuj motyw do aplikacji."""
        theme = self.themes.get(theme_name, self.themes["Professional"])
        
        app = QApplication.instance()
        if not app:
            return
            
        # Utwórz paletę kolorów
        palette = QPalette()
        
        # Kolory tła
        palette.setColor(QPalette.ColorRole.Window, QColor(theme["background"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme["text"]))
        
        # Kolory pól tekstowych
        palette.setColor(QPalette.ColorRole.Base, QColor(theme["editor_bg"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme["editor_text"]))
        
        # Kolory przycisków
        palette.setColor(QPalette.ColorRole.Button, QColor(theme["secondary_bg"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme["text"]))
        
        # Kolory zaznaczenia
        palette.setColor(QPalette.ColorRole.Highlight, QColor(theme["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        
        # Kolory nieaktywne
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(theme["secondary_text"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(theme["secondary_text"]))
        
        # Zastosuj paletę
        app.setPalette(palette)
        
        # Dodatkowe style CSS dla specjalnych elementów
        self._apply_theme_stylesheet(theme)
        
    def _apply_theme_stylesheet(self, theme):
        """Zastosuj dodatkowe style CSS."""
        app = QApplication.instance()
        if not app:
            return
            
        # Professional stylesheet with modern, clean design
        stylesheet = f"""
        /* General Application Styling */
        QMainWindow {{
            background-color: {theme["background"]};
            color: {theme["text"]};
        }}
        
        /* Professional Button Styling */
        QPushButton {{
            background-color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            padding: 6px 12px;
            color: {theme["text"]};
            font-weight: 400;
            font-size: 13px;
            min-height: 16px;
        }}
        
        QPushButton:hover {{
            background-color: {theme["secondary_bg"]};
            border-color: {theme["accent"]};
            color: {theme["text"]};
        }}
        
        QPushButton:pressed {{
            background-color: {theme["accent"]};
            border-color: {theme["accent"]};
            color: white;
        }}
        
        QPushButton:checked {{
            background-color: {theme["accent"]};
            border-color: {theme["accent"]};
            color: white;
        }}
        
        QPushButton:disabled {{
            background-color: {theme["secondary_bg"]};
            border-color: {theme["border"]};
            color: {theme.get("muted", theme["secondary_text"])};
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            padding: 6px 8px;
            color: {theme["text"]};
            selection-background-color: {theme["accent"]};
            selection-color: white;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {theme["accent"]};
            outline: none;
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            padding: 4px 8px;
            color: {theme["text"]};
            min-height: 20px;
        }}
        
        QComboBox:hover {{
            border-color: {theme["accent"]};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {theme["text"]};
            margin-right: 6px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            padding: 4px;
            color: {theme["text"]};
            selection-background-color: {theme["accent"]};
            selection-color: white;
        }}
        
        /* Tree Widget Professional Style */
        QTreeWidget {{
            background-color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            color: {theme["text"]};
            selection-background-color: {theme["accent"]};
            outline: none;
            font-size: 13px;
        }}
        
        QTreeWidget::item {{
            padding: 4px 8px;
            border: none;
            min-height: 20px;
        }}
        
        QTreeWidget::item:hover {{
            background-color: {theme["secondary_bg"]};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {theme["accent"]};
            color: white;
        }}
        
        QTreeWidget::branch:hover {{
            background-color: {theme["secondary_bg"]};
        }}
        
        /* Labels */
        QLabel {{
            color: {theme["text"]};
            font-size: 13px;
        }}
        
        /* Group Boxes */
        QGroupBox {{
            font-weight: 500;
            font-size: 14px;
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            background-color: {theme["background"]};
        }}
        
        /* List Widgets */
        QListWidget {{
            background-color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            color: {theme["text"]};
            selection-background-color: {theme["accent"]};
            selection-color: white;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 4px 8px;
            border: none;
            min-height: 20px;
        }}
        
        QListWidget::item:hover {{
            background-color: {theme["secondary_bg"]};
        }}
        
        QListWidget::item:selected {{
            background-color: {theme["accent"]};
            color: white;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {theme["secondary_bg"]};
            border: none;
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme["border"]};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {theme["accent"]};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {theme["secondary_bg"]};
            border: none;
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {theme["border"]};
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {theme["accent"]};
        }}
        
        /* Splitter */
        QSplitter::handle {{
            background-color: {theme["border"]};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {theme["secondary_bg"]};
            border-top: 1px solid {theme["border"]};
            color: {theme["text"]};
            font-size: 12px;
        }}
        
        /* Dialogs */
        QDialog {{
            background-color: {theme["background"]};
            color: {theme["text"]};
        }}
        
        /* Tool Tips */
        QToolTip {{
            background-color: {theme["text"]};
            color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
        }}
        """
        
        # Apply the professional stylesheet globally
        app.setStyleSheet(stylesheet)
        
    def get_theme_colors(self, theme_name=None):
        """Pobierz kolory konkretnego motywu."""
        if not theme_name:
            theme_name = self.get_current_theme()
        return self.themes.get(theme_name, self.themes["Professional"])