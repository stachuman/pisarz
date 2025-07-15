"""Scene card widget for displaying scene information."""

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGraphicsDropShadowEffect, QWidget, QMenu, QInputDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QAction

from ..styles.styles import SECONDARY_TEXT_COLOR, SEPARATOR_COLOR
from ..styles.themes import ThemeManager


class SceneCard(QFrame):
    """Karta sceny - imituje QML GridView."""
    
    sceneSelected = Signal(int, str)  # id, title
    sceneRenameRequested = Signal(int, str)  # id, new_title
    
    def __init__(self, scene_data, character_manager=None, location_manager=None, parent=None):
        super().__init__(parent)
        self.scene_data = scene_data
        self.character_manager = character_manager
        self.location_manager = location_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja karty sceny."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setFixedSize(240, 160)  # Increased size for additional info
        self._apply_theme_style()
        self._add_shadow_effect()
        self._setup_tooltip()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)
        
        # Header with title and badges
        header_layout = QHBoxLayout()
        
        # Tytuł sceny
        title_label = QLabel(self.scene_data.get("title", "Bez tytułu"))
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(40)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Character and location badges
        badges_layout = QVBoxLayout()
        badges_layout.setSpacing(2)
        
        character_count, location_count = self._get_counts()
        
        if character_count > 0:
            char_badge = self._create_badge(f"{character_count}👥", "#3498db")
            badges_layout.addWidget(char_badge)
        
        if location_count > 0:
            loc_badge = self._create_badge(f"{location_count}📍", "#27ae60")
            badges_layout.addWidget(loc_badge)
        
        if character_count == 0 and location_count == 0:
            badges_layout.addStretch()
            
        header_layout.addLayout(badges_layout)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(SEPARATOR_COLOR)
        layout.addWidget(separator)
        
        # Podgląd treści
        content = self.scene_data.get("content_rtf", "")
        if content and len(content) > 0:
            preview = content[:60] + "..." if len(content) > 60 else content
        else:
            preview = "Pusta scena"
            
        preview_label = QLabel(preview)
        preview_label.setFont(QFont("Arial", 9))
        preview_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet(SECONDARY_TEXT_COLOR)
        layout.addWidget(preview_label)
        
        # Character and location context info
        context_info = self._get_context_info()
        if context_info:
            context_label = QLabel(context_info)
            context_label.setFont(QFont("Arial", 8))
            context_label.setWordWrap(True)
            context_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
            layout.addWidget(context_label)
        
        # Spacer
        layout.addStretch()
        
        # Bottom row with scene number
        bottom_layout = QHBoxLayout()
        
        order_label = QLabel(f"Scena {self.scene_data.get('ord', 0)}")
        order_label.setFont(QFont("Arial", 9))
        order_label.setStyleSheet("color: #95a5a6;")
        bottom_layout.addWidget(order_label)
        
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)
        
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
    
    def _get_counts(self):
        """Get character and location counts for this scene."""
        scene_id = self.scene_data.get("id")
        character_count = 0
        location_count = 0
        
        try:
            if self.character_manager and scene_id:
                characters = self.character_manager.get_characters_for_scene(scene_id)
                character_count = len(characters)
            
            if self.location_manager and scene_id:
                locations = self.location_manager.get_scene_locations(scene_id)
                location_count = len(locations)
        except:
            pass
            # Silently handle error - counts will remain 0
        
        return character_count, location_count
    
    def _get_context_info(self):
        """Get context information about characters and locations in this scene."""
        scene_id = self.scene_data.get("id")
        context_parts = []
        
        try:
            if self.location_manager and scene_id:
                locations = self.location_manager.get_scene_locations(scene_id)
                if locations:
                    location_names = [loc.name for loc, role in locations[:2]]  # Show first 2
                    if len(locations) > 2:
                        location_text = f"📍 {', '.join(location_names)}..."
                    else:
                        location_text = f"📍 {', '.join(location_names)}"
                    context_parts.append(location_text)
            
            if self.character_manager and scene_id:
                characters = self.character_manager.get_characters_for_scene(scene_id)
                if characters:
                    char_names = [char.get('name', 'Unknown') for char in characters[:3]]  # Show first 3
                    if len(characters) > 3:
                        char_text = f"👤 {', '.join(char_names)}..."
                    else:
                        char_text = f"👤 {', '.join(char_names)}"
                    context_parts.append(char_text)
        except Exception as e:
            pass
            # Silently handle error - context info will be empty
        
        return " | ".join(context_parts)
    
    def _setup_tooltip(self):
        """Setup detailed tooltip with character and location information."""
        tooltip_parts = []
        scene_id = self.scene_data.get("id")
        scene_title = self.scene_data.get("title", "Untitled Scene")
        
        tooltip_parts.append(f"<b>{scene_title}</b>")
        tooltip_parts.append("")
        
        try:
            # Add location information
            if self.location_manager and scene_id:
                locations = self.location_manager.get_scene_locations(scene_id)
                if locations:
                    tooltip_parts.append("<b>📍 Locations:</b>")
                    for location, role in locations:
                        tooltip_parts.append(f"  • {location.name} ({role})")
                    tooltip_parts.append("")
            
            # Add character information
            if self.character_manager and scene_id:
                characters = self.character_manager.get_characters_for_scene(scene_id)
                if characters:
                    tooltip_parts.append("<b>👥 Characters:</b>")
                    for character in characters:
                        tooltip_parts.append(f"  • {character.get('name', 'Unknown')}")
                    tooltip_parts.append("")
            
            # Add relationships if we have both managers
            if self.location_manager and self.character_manager and scene_id:
                relationships = self._get_detailed_relationships()
                if relationships:
                    tooltip_parts.append("<b>🔗 Character-Location Relationships:</b>")
                    tooltip_parts.extend(relationships)
                    
        except Exception as e:
            pass
            # Silently handle error - tooltip will show basic info only
        
        if len(tooltip_parts) > 2:  # More than just title
            tooltip_text = "<br>".join(tooltip_parts)
            self.setToolTip(tooltip_text)
    
    def _get_detailed_relationships(self):
        """Get detailed character-location relationships for tooltip."""
        scene_id = self.scene_data.get("id")
        relationships = []
        
        try:
            # Get scene characters and locations
            characters = self.character_manager.get_characters_for_scene(scene_id)
            locations = self.location_manager.get_scene_locations(scene_id)
            
            scene_location_ids = [loc.id for loc, role in locations]
            
            for character in characters:
                char_id = character.get('id')
                char_name = character.get('name', 'Unknown')
                
                # Get all character-location relationships
                char_locations = self.location_manager.get_character_locations(char_id)
                
                # Filter to only locations that are in this scene
                relevant_relationships = []
                for char_loc, rel_type, description in char_locations:
                    if char_loc.id in scene_location_ids:
                        rel_text = f"{char_name} {rel_type} {char_loc.name}"
                        if description:
                            rel_text += f" ({description})"
                        relevant_relationships.append(f"  • {rel_text}")
                
                relationships.extend(relevant_relationships)
                
        except Exception as e:
            pass
            # Silently handle error - relationships won't be shown
        
        return relationships

    def mousePressEvent(self, event):
        """Obsługa kliknięcia na kartę."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.sceneSelected.emit(self.scene_data["id"], self.scene_data.get("title", "Scena"))
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)
    
    def show_context_menu(self, position):
        """Show context menu with rename option."""
        menu = QMenu(self)
        
        # Rename action
        rename_action = QAction("📝 Rename Scene", self)
        rename_action.triggered.connect(self.rename_scene)
        menu.addAction(rename_action)
        
        menu.exec(position)
    
    def rename_scene(self):
        """Show rename dialog and emit rename signal."""
        current_title = self.scene_data.get("title", "Untitled Scene")
        
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Scene",
            "Enter new scene title:",
            text=current_title
        )
        
        if ok and new_title.strip() and new_title.strip() != current_title:
            self.sceneRenameRequested.emit(self.scene_data["id"], new_title.strip())
