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
        return self.settings.value("theme", "Jasny")
        
    def set_theme(self, theme_name):
        """Ustaw aktywny motyw."""
        if theme_name not in self.themes:
            theme_name = "Jasny"
            
        self.settings.setValue("theme", theme_name)
        self._apply_theme(theme_name)
        
    def _apply_theme(self, theme_name):
        """Zastosuj motyw do aplikacji."""
        theme = self.themes.get(theme_name, self.themes["Jasny"])
        
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
            
        # Globalne style dla aplikacji
        stylesheet = f"""
        /* Przyciski */
        QPushButton {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 {theme["secondary_bg"]}, stop: 1 {theme["border"]});
            border: 1px solid {theme["border"]};
            border-radius: 6px;
            padding: 8px 16px;
            color: {theme["text"]};
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 {theme["accent"]}, stop: 1 {theme["accent_hover"]});
            color: white;
            border: 2px solid {theme["accent"]};
        }}
        
        QPushButton:pressed {{
            background-color: {theme["accent_hover"]};
            border: 2px solid {theme["accent_hover"]};
        }}
        
        /* Drzewko */
        QTreeWidget {{
            background-color: {theme["background"]};
            border: 1px solid {theme["border"]};
            border-radius: 6px;
            color: {theme["text"]};
            selection-background-color: {theme["accent"]};
            outline: none;
        }}
        
        QTreeWidget::item {{
            padding: 4px 8px;
            border-radius: 4px;
            margin: 1px;
        }}
        
        QTreeWidget::item:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 {theme["secondary_bg"]}, stop: 1 {theme["background"]});
            border: 1px solid {theme["border"]};
        }}
        
        QTreeWidget::item:selected {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 {theme["accent"]}, stop: 1 {theme["accent_hover"]});
            color: white;
            border: 1px solid {theme["accent_hover"]};
        }}
        
        QTreeWidget::item:selected:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 {theme["accent_hover"]}, stop: 1 {theme["accent"]});
        }}
        
        /* Ramki i panele */
        QFrame {{
            background-color: {theme["background"]};
            color: {theme["text"]};
        }}
        
        /* Paski przewijania */
        QScrollBar:vertical {{
            background: {theme["secondary_bg"]};
            border: none;
            width: 14px;
            border-radius: 7px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 {theme["accent"]}, stop: 1 {theme["accent_hover"]});
            border-radius: 7px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 {theme["accent_hover"]}, stop: 1 {theme["accent"]});
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        """
        
        # Nie zastosowuj globalnych styli dla przycisków - zostawiamy lokalne
        # app.setStyleSheet(stylesheet)
        
    def get_theme_colors(self, theme_name=None):
        """Pobierz kolory konkretnego motywu."""
        if not theme_name:
            theme_name = self.get_current_theme()
        return self.themes.get(theme_name, self.themes["Jasny"])