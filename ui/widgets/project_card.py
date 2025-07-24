"""Project card widget for displaying project information."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ..styles.styles import SECONDARY_TEXT_COLOR
from ..styles.themes import ThemeManager


class ProjectCard(QFrame):
    """Karta projektu - imituje QML GridView."""
    
    projectSelected = Signal(int, str)  # project_id, name
    
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja karty projektu."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setFixedSize(200, 120)
        self._apply_theme_style()
        self._add_shadow_effect()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Nazwa projektu
        name_label = QLabel(self.project_data["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Spacer
        layout.addStretch()
        
        # Informacje o projekcie
        info_label = QLabel("Projekt")
        info_label.setFont(QFont("Arial", 10))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet(SECONDARY_TEXT_COLOR)
        layout.addWidget(info_label)
        
    def _apply_theme_style(self):
        """Zastosuj style zgodne z aktualnym motywem."""
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        style = f"""
        ProjectCard {{
            background-color: {colors["secondary_bg"]};
            border: 1px solid {colors["border"]};
            border-radius: 8px;
        }}
        ProjectCard:hover {{
            background-color: {colors["background"]};
            border: 2px solid {colors["accent"]};
        }}
        """
        self.setStyleSheet(style)
        
    def _add_shadow_effect(self):
        """Dodaj efekt cienia do karty."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 50))  # Półprzezroczysty czarny
        self.setGraphicsEffect(shadow)
        
    def mousePressEvent(self, event):
        """Obsługa kliknięcia na kartę."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.projectSelected.emit(self.project_data["id"], self.project_data["name"])
        super().mousePressEvent(event)