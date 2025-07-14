"""Scene card widget for displaying scene information."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ..styles.styles import SECONDARY_TEXT_COLOR, SEPARATOR_COLOR
from ..styles.themes import ThemeManager


class SceneCard(QFrame):
    """Karta sceny - imituje QML GridView."""
    
    sceneSelected = Signal(int, str)  # id, title
    
    def __init__(self, scene_data, parent=None):
        super().__init__(parent)
        self.scene_data = scene_data
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja karty sceny."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setFixedSize(220, 140)
        self._apply_theme_style()
        self._add_shadow_effect()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Tytuł sceny
        title_label = QLabel(self.scene_data.get("title", "Bez tytułu"))
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(40)
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(SEPARATOR_COLOR)
        layout.addWidget(separator)
        
        # Podgląd treści
        content = self.scene_data.get("content_rtf", "")
        if content and len(content) > 0:
            preview = content[:80] + "..." if len(content) > 80 else content
        else:
            preview = "Pusta scena"
            
        preview_label = QLabel(preview)
        preview_label.setFont(QFont("Arial", 10))
        preview_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet(SECONDARY_TEXT_COLOR)
        layout.addWidget(preview_label)
        
        # Spacer
        layout.addStretch()
        
        # Numer sceny
        order_label = QLabel(f"Scena {self.scene_data.get('ord', 0)}")
        order_label.setFont(QFont("Arial", 9))
        order_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        order_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(order_label)
        
    def _apply_theme_style(self):
        """Zastosuj style zgodne z aktualnym motywem."""
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        style = f"""
        SceneCard {{
            background-color: {colors["secondary_bg"]};
            border: 1px solid {colors["border"]};
            border-radius: 8px;
        }}
        SceneCard:hover {{
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
            self.sceneSelected.emit(self.scene_data["id"], self.scene_data.get("title", "Scena"))
        super().mousePressEvent(event)