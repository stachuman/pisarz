"""Location card widget for displaying location information."""

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGraphicsDropShadowEffect, QMenu)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ..styles.themes import ThemeManager
from i18n import _


class LocationCard(QFrame):
    """Card widget for displaying location information."""
    
    clicked = Signal(int, str)  # location_id, name
    edit_requested = Signal(int)  # location_id
    delete_requested = Signal(int)  # location_id
    
    def __init__(self, location_id: int, name: str, description: str = "", 
                 scene_count: int = 0, character_count: int = 0, 
                 location_type: str = "", atmosphere: str = "", parent=None):
        super().__init__(parent)
        self.location_id = location_id
        self.location_name = name
        self.description = description
        self.scene_count = scene_count
        self.character_count = character_count
        self.location_type = location_type
        self.atmosphere = atmosphere
        
        self.setup_ui()
        self.apply_theme()
        self._setup_tooltip()
    
    def setup_ui(self):
        """Setup the location card UI."""
        self.setFixedSize(300, 140)  # Same size as character cards
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        # Theme styling will be applied in apply_theme()
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Header with name and reference badges
        header_layout = QHBoxLayout()
        
        # Location name
        self.name_label = QLabel(self.location_name)
        self.name_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.name_label.setWordWrap(True)
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        # Reference badges (scenes and characters)
        if self.scene_count > 0:
            scene_badge = self._create_badge(f"{self.scene_count}🎬", "#3498db")
            header_layout.addWidget(scene_badge)
        
        if self.character_count > 0:
            character_badge = self._create_badge(f"{self.character_count}👥", "#9b59b6")
            header_layout.addWidget(character_badge)
        
        layout.addLayout(header_layout)
        
        # Type and atmosphere info
        if self.location_type or self.atmosphere:
            info_layout = QHBoxLayout()
            if self.location_type:
                type_label = QLabel(f"🏢 {self.location_type}")
                type_label.setFont(QFont("Arial", 8))
                type_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
                info_layout.addWidget(type_label)
            
            if self.atmosphere:
                atmosphere_label = QLabel(f"✨ {self.atmosphere}")
                atmosphere_label.setFont(QFont("Arial", 8))
                atmosphere_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
                info_layout.addWidget(atmosphere_label)
            
            info_layout.addStretch()
            layout.addLayout(info_layout)
        
        # Description preview
        preview_text = self.description[:60] + "..." if len(self.description) > 60 else self.description
        if not preview_text.strip():
            preview_text = _("Location description...")
            
        self.description_label = QLabel(preview_text)
        self.description_label.setFont(QFont("Arial", 9))
        # Theme styling will be applied in apply_theme()
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        layout.addStretch()
    
    def _create_badge(self, text, color):
        """Create a small badge widget."""
        badge = QLabel(text)
        badge.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                padding: 2px 6px;
                margin: 1px;
            }}
        """)
        badge.setFixedHeight(16)
        return badge
    
    def _setup_tooltip(self):
        """Setup detailed tooltip with location information."""
        tooltip_parts = []
        
        tooltip_parts.append(f"<b>{self.location_name}</b>")
        tooltip_parts.append("")
        
        # Add type and atmosphere
        if self.location_type:
            tooltip_parts.append(f"<b>Type:</b> {self.location_type}")
        if self.atmosphere:
            tooltip_parts.append(f"<b>Atmosphere:</b> {self.atmosphere}")
        if self.location_type or self.atmosphere:
            tooltip_parts.append("")
        
        # Add description if available
        if self.description.strip():
            tooltip_parts.append(f"<i>{self.description[:150]}{'...' if len(self.description) > 150 else ''}</i>")
            tooltip_parts.append("")
        
        # Add reference information
        if self.scene_count > 0 or self.character_count > 0:
            tooltip_parts.append("<b>📊 References:</b>")
            if self.scene_count > 0:
                tooltip_parts.append(f"  • {self.scene_count} scene(s)")
            if self.character_count > 0:
                tooltip_parts.append(f"  • {self.character_count} character(s)")
        
        if len(tooltip_parts) > 2:  # More than just name
            tooltip_text = "<br>".join(tooltip_parts)
            self.setToolTip(tooltip_text)
    
    def mousePressEvent(self, event):
        """Handle mouse click to select location."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.location_id, self.location_name)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)
    
    def _show_context_menu(self, pos):
        """Show context menu for location actions."""
        menu = QMenu(self)
        
        edit_action = menu.addAction(_("Edit Location"))
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.location_id))
        
        delete_action = menu.addAction(_("Delete Location"))
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.location_id))
        
        menu.exec(pos)
    
    def apply_theme(self):
        """Apply current theme colors to the card."""
        theme_manager = ThemeManager()
        self._apply_theme_style(theme_manager)
        
    def _apply_theme_style(self, theme_manager):
        """Apply theme-specific styling."""
        colors = theme_manager.get_theme_colors()
        
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['background']};
            }}
            QFrame:hover {{
                border-color: {colors['accent']};
                background-color: {colors['secondary_bg']};
            }}
        """)
        
        # Update text colors
        self.name_label.setStyleSheet(f"color: {colors['text']};")
        self.description_label.setStyleSheet(f"color: {colors['secondary_text']};")
    
    def update_counts(self, scene_count, character_count):
        """Update reference counts and refresh the card."""
        self.scene_count = scene_count
        self.character_count = character_count
        
        # Clear and rebuild UI
        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        self.setup_ui()
        self.apply_theme()
        self._setup_tooltip()
