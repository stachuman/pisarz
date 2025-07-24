"""Character card widget for displaying character information."""

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGraphicsDropShadowEffect, QMenu)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ..styles.themes import ThemeManager
from i18n import _


class CharacterCard(QFrame):
    """Card widget for displaying character information."""
    
    clicked = Signal(int, str)  # character_id, name
    edit_requested = Signal(int)  # character_id
    delete_requested = Signal(int)  # character_id
    
    def __init__(self, character_id: int, name: str, description: str = "", 
                 location_manager=None, parent=None):
        super().__init__(parent)
        self.character_id = character_id
        self.character_name = name
        self.description = description or ""  # Ensure description is never None
        self.location_manager = location_manager
        
        self.setup_ui()
        self.apply_theme()
        self._setup_tooltip()
        
    def setup_ui(self):
        """Setup the character card UI."""
        self.setFixedSize(300, 140)  # Increased size for location info
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
        
        # Header with name and location badge
        header_layout = QHBoxLayout()
        
        # Character name
        self.name_label = QLabel(self.character_name)
        self.name_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.name_label.setWordWrap(True)
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        # Location count badge
        location_count = self._get_location_count()
        if location_count > 0:
            location_badge = self._create_badge(f"{location_count}📍", "#e67e22")
            header_layout.addWidget(location_badge)
        
        layout.addLayout(header_layout)
        
        # Description preview
        description_safe = self.description or ""
        preview_text = description_safe[:60] + "..." if len(description_safe) > 60 else description_safe
        if not preview_text.strip():
            preview_text = _("Character description...")
            
        self.description_label = QLabel(preview_text)
        self.description_label.setFont(QFont("Arial", 9))
        # Theme styling will be applied in apply_theme()
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # Location relationships
        location_info = self._get_location_info()
        if location_info:
            location_label = QLabel(location_info)
            location_label.setFont(QFont("Arial", 8))
            location_label.setWordWrap(True)
            location_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
            layout.addWidget(location_label)
        
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
    
    def _get_location_count(self):
        """Get the number of locations this character is associated with."""
        if not self.location_manager:
            return 0
        
        try:
            locations = self.location_manager.get_character_locations(self.character_id)
            return len(locations)
        except Exception as e:
            # Silently handle error - count will remain 0
            return 0
    
    def _get_location_info(self):
        """Get location relationship information for this character."""
        if not self.location_manager:
            return ""
        
        try:
            locations = self.location_manager.get_character_locations(self.character_id)
            if not locations:
                return ""
            
            # Group by relationship type
            relationships = {}
            for location, rel_type, description in locations:
                if rel_type not in relationships:
                    relationships[rel_type] = []
                relationships[rel_type].append(location.name)
            
            # Format the relationships
            rel_parts = []
            for rel_type, location_names in relationships.items():
                if len(location_names) > 2:
                    rel_text = f"{rel_type}: {', '.join(location_names[:2])}..."
                else:
                    rel_text = f"{rel_type}: {', '.join(location_names)}"
                rel_parts.append(rel_text)
            
            return " | ".join(rel_parts)
        except Exception as e:
            # Silently handle error - location info will be empty
            return ""
    
    def _setup_tooltip(self):
        """Setup detailed tooltip with location relationship information."""
        tooltip_parts = []
        
        tooltip_parts.append(f"<b>{self.character_name}</b>")
        tooltip_parts.append("")
        
        # Add description if available
        description_text = self.description or ""
        if description_text and description_text.strip():
            tooltip_parts.append(f"<i>{description_text[:150]}{'...' if len(description_text) > 150 else ''}</i>")
            tooltip_parts.append("")
        
        try:
            if self.location_manager:
                locations = self.location_manager.get_character_locations(self.character_id)
                if locations:
                    tooltip_parts.append("<b>📍 Location Relationships:</b>")
                    for location, rel_type, description in locations:
                        rel_text = f"  • {rel_type} {location.name}"
                        if description:
                            rel_text += f" ({description})"
                        tooltip_parts.append(rel_text)
                    
        except:
            pass
            # Silently handle error - tooltip will show basic info only
        
        if len(tooltip_parts) > 2:  # More than just name
            tooltip_text = "<br>".join(tooltip_parts)
            self.setToolTip(tooltip_text)

    def mousePressEvent(self, event):
        """Handle mouse click to select character."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.character_id, self.character_name)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        else:
            super().mousePressEvent(event)
    
    def _show_context_menu(self, pos):
        """Show context menu for character actions."""
        menu = QMenu(self)
        
        edit_action = menu.addAction(_("Edit Character"))
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.character_id))
        
        delete_action = menu.addAction(_("Delete Character"))
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.character_id))
        
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
    
    def update_character_info(self, name, description):
        """Update character information and refresh display."""
        self.character_name = name
        self.description = description or ""  # Ensure description is never None
        
        self.name_label.setText(name)
        
        # Update description preview
        description_safe = self.description or ""
        preview_text = description_safe[:60] + "..." if len(description_safe) > 60 else description_safe
        if not preview_text.strip():
            preview_text = _("Character description...")
        self.description_label.setText(preview_text)
        
        # Refresh tooltip
        self._setup_tooltip()
