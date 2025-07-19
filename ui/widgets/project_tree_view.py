"""Project tree navigation widget for project view."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTreeWidget, QTreeWidgetItem, QPushButton, 
                              QInputDialog, QMessageBox, QMenu)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen, QAction
from datetime import datetime
from typing import Optional

from ..styles.styles import HEADER_COLOR, NEW_SCENE_BUTTON_STYLE
from core.logging_config import get_logger
from i18n import _


class ProjectTreeView(QWidget):
    """Drzewko nawigacji w projekcie: Sceny, Postacie, Lokacje."""
    
    sceneSelected = Signal(int, str)        # id, title
    characterSelected = Signal(int, str)    # id, name (future)
    locationSelected = Signal(int, str)     # id, name (future)
    searchRequested = Signal()              # search category selected
    
    categorySelected = Signal(str)          # category name ("scenes", "characters", "locations", "search")
    
    newSceneRequested = Signal(str)         # title
    newCharacterRequested = Signal(str)     # name (future)
    newLocationRequested = Signal(str)      # name (future)
    
    backToProjectsRequested = Signal()
    projectPropertiesRequested = Signal()
    
    # Context menu signals
    generateContextRequested = Signal(int, str)     # scene_id, template_name
    editTemplateRequested = Signal(str)             # template_name
    refreshContextRequested = Signal(int)           # scene_id
    viewContextRequested = Signal(int)              # scene_id
    editContextRequested = Signal(int)              # scene_id
    
    def __init__(self, project_name="", parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self.project_title_label = None
        self.logger = get_logger(__name__)
        self.narrative_context_manager = None  # Will be set externally
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja drzewka nawigacji."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Nagłówek z nazwą projektu
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Projekty")
        back_btn.clicked.connect(self.backToProjectsRequested.emit)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        # Project properties button
        properties_btn = QPushButton("⚙️ " + _("Properties"))
        properties_btn.clicked.connect(self.projectPropertiesRequested.emit)
        properties_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(properties_btn)
        
        layout.addLayout(header_layout)
        
        self.project_title_label = QLabel(self.project_name)
        self.project_title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.project_title_label.setStyleSheet("color: #2c3e50; padding: 10px 0;")
        self.project_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.project_title_label)
        
        # Drzewko nawigacji
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFont(QFont("Arial", 11))  # Większa czcionka dla drzewka
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu_requested)
        layout.addWidget(self.tree)
        
        # Przyciski akcji
        self.actions_layout = QVBoxLayout()
        layout.addLayout(self.actions_layout)
        
        # Przycisk nowa scena
        self.new_scene_btn = QPushButton("+ Nowa Scena")
        self.new_scene_btn.clicked.connect(self._on_new_scene_clicked)
        self.new_scene_btn.setStyleSheet(NEW_SCENE_BUTTON_STYLE)
        self.actions_layout.addWidget(self.new_scene_btn)
        
        # Przycisk nowa postać (future)
        self.new_character_btn = QPushButton(_("New Character"))
        self.new_character_btn.clicked.connect(self._on_new_character_clicked)
        self.new_character_btn.setEnabled(True)
        self.new_character_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.actions_layout.addWidget(self.new_character_btn)
        
        # Przycisk nowa lokacja
        self.new_location_btn = QPushButton(_("New Location"))
        self.new_location_btn.clicked.connect(self._on_new_location_clicked)
        self.new_location_btn.setEnabled(True)
        self.new_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.actions_layout.addWidget(self.new_location_btn)
        
        self._setup_tree_structure()
        
    def _create_icon(self, icon_type, size=16):
        """Stwórz ikonę geometryczną dostosowaną do motywu."""
        from ..styles.themes import ThemeManager
        
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Użyj kolorów z aktualnego motywu
        try:
            theme_manager = ThemeManager()
            colors = theme_manager.get_theme_colors()
            main_color = QColor(colors["accent"])
            text_color = QColor(colors["text"])
        except:
            main_color = QColor("#3498db")
            text_color = QColor("#2c3e50")
            
        painter.setPen(QPen(text_color, 1))
        painter.setBrush(main_color)
        
        margin = 2
        rect = pixmap.rect().adjusted(margin, margin, -margin, -margin)
        
        if icon_type == "scenes":
            # Stos dokumentów
            painter.setBrush(main_color)
            
            # Pierwszy dokument (tło)
            doc1 = rect.adjusted(2, 2, -1, -1)
            painter.drawRect(doc1)
            
            # Drugi dokument (pierwszy plan)
            doc2 = rect.adjusted(0, 0, -3, -3)
            painter.setBrush(text_color)
            painter.drawRect(doc2)
            
            # Linie tekstu na pierwszym planie
            painter.setPen(QPen(main_color, 1))
            line_height = doc2.height() // 5
            for i in range(3):
                y = doc2.top() + (i + 2) * line_height
                painter.drawLine(doc2.left() + 2, y, doc2.right() - 2, y)
                
        elif icon_type == "characters" or icon_type == "character":
            # Stylizowana postać
            painter.setBrush(main_color)
            
            # Głowa (kółko)
            head_size = rect.width() // 3
            head_x = rect.center().x() - head_size // 2
            head_y = rect.top() + 1
            painter.drawEllipse(head_x, head_y, head_size, head_size)
            
            # Tors (zaokrąglony prostokąt)
            body_width = rect.width() // 2
            body_height = rect.height() // 2
            body_x = rect.center().x() - body_width // 2
            body_y = rect.top() + head_size + 1
            painter.setBrush(text_color)
            painter.drawRoundedRect(body_x, body_y, body_width, body_height, 2, 2)
            
            # Ramiona (małe kółka)
            arm_size = 3
            painter.setBrush(main_color)
            painter.drawEllipse(body_x - arm_size, body_y + 2, arm_size, arm_size)
            painter.drawEllipse(body_x + body_width, body_y + 2, arm_size, arm_size)
            
        elif icon_type == "locations":
            # Dom (trójkąt + prostokąt)
            from PySide6.QtCore import QPoint
            from PySide6.QtGui import QPolygon
            
            # Dach (trójkąt)
            roof_height = rect.height() // 3
            roof_points = [
                QPoint(rect.center().x(), rect.top()),
                QPoint(rect.left() + 2, rect.top() + roof_height), 
                QPoint(rect.right() - 2, rect.top() + roof_height)
            ]
            painter.drawPolygon(QPolygon(roof_points))
            
            # Ściany (dom)
            house_rect = rect.adjusted(2, roof_height, -2, -2)
            painter.drawRect(house_rect)
            
            # Drzwi
            door_width = rect.width() // 4
            door_height = rect.height() // 3
            door_x = rect.center().x() - door_width // 2
            door_y = rect.bottom() - door_height - 2
            painter.setBrush(text_color)
            painter.drawRect(door_x, door_y, door_width, door_height)
            
        elif icon_type in ["scene", "scene_fresh", "scene_stale", "scene_no_context"]:
            # Strona dokumentu z zagniętym rogiem - with context status
            
            # Determine color based on context status
            if icon_type == "scene_fresh":
                status_color = QColor("#27ae60")  # Green - up to date
            elif icon_type == "scene_stale":
                status_color = QColor("#f39c12")  # Orange - needs refresh
            elif icon_type == "scene_no_context":
                status_color = QColor("#e74c3c")  # Red - no context
            else:
                status_color = main_color  # Default blue
            
            painter.setBrush(status_color)
            
            # Główny dokument
            main_doc = rect.adjusted(0, 0, -3, 0)
            painter.drawRect(main_doc)
            
            # Zagiętý roh (trójkąt)
            from PySide6.QtCore import QPoint
            from PySide6.QtGui import QPolygon
            
            corner_size = rect.width() // 3
            corner_points = [
                QPoint(rect.right() - corner_size, rect.top()),
                QPoint(rect.right(), rect.top()),
                QPoint(rect.right(), rect.top() + corner_size)
            ]
            painter.setBrush(text_color)
            painter.drawPolygon(QPolygon(corner_points))
            
            # Linia tekstu
            painter.setPen(QPen(text_color, 1))
            text_y = rect.center().y()
            painter.drawLine(rect.left() + 2, text_y, rect.right() - corner_size - 1, text_y)
            
            # Add status indicator dot in bottom right
            if icon_type != "scene":
                painter.setBrush(status_color)
                painter.setPen(QPen(status_color, 1))
                dot_size = 4
                dot_x = rect.right() - dot_size - 1
                dot_y = rect.bottom() - dot_size - 1
                painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)
            
        elif icon_type == "search":
            # Lupa (magnifying glass)
            painter.setBrush(Qt.GlobalColor.transparent)
            painter.setPen(QPen(text_color, 2))
            
            # Kółko lupy
            lens_size = rect.width() // 2
            lens_rect = rect.adjusted(2, 2, -lens_size//2, -lens_size//2)
            painter.drawEllipse(lens_rect)
            
            # Rączka lupy
            handle_start_x = lens_rect.right() - 2
            handle_start_y = lens_rect.bottom() - 2
            handle_end_x = rect.right() - 2
            handle_end_y = rect.bottom() - 2
            painter.drawLine(handle_start_x, handle_start_y, handle_end_x, handle_end_y)
            
        elif icon_type == "empty":
            # Stylizowany plus w kółku
            painter.setBrush(text_color)
            
            # Kółko tła
            circle_rect = rect.adjusted(1, 1, -1, -1)
            painter.drawEllipse(circle_rect)
            
            # Plus (białe linie)
            painter.setPen(QPen(main_color, 2))
            center = rect.center()
            plus_size = rect.width() // 3
            
            # Pionowa linia
            painter.drawLine(center.x(), center.y() - plus_size//2, center.x(), center.y() + plus_size//2)
            # Pozioma linia
            painter.drawLine(center.x() - plus_size//2, center.y(), center.x() + plus_size//2, center.y())
            
        painter.end()
        return QIcon(pixmap)
        
    def update_project_name(self, project_name):
        """Zaktualizuj nazwę projektu bez resetowania UI."""
        self.project_name = project_name
        if self.project_title_label:
            self.project_title_label.setText(project_name)
        
    def _setup_tree_structure(self):
        """Stwórz podstawową strukturę drzewka."""
        self.tree.clear()
        
        # Search
        self.search_item = QTreeWidgetItem([_("🔍 Search")])
        self.search_item.setIcon(0, self._create_icon("search"))
        self.search_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "category": "search"})
        self.tree.addTopLevelItem(self.search_item)
        
        # Sceny
        self.scenes_item = QTreeWidgetItem([_("Scenes")])
        self.scenes_item.setIcon(0, self._create_icon("scenes"))
        self.scenes_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "category": "scenes"})
        self.tree.addTopLevelItem(self.scenes_item)
        self.scenes_item.setExpanded(True)
        
        # Postacie
        self.characters_item = QTreeWidgetItem([_("Characters")])
        self.characters_item.setIcon(0, self._create_icon("characters"))
        self.characters_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "category": "characters"})
        self.tree.addTopLevelItem(self.characters_item)
        self.characters_item.setExpanded(True)
        
        # Lokacje (future)
        self.locations_item = QTreeWidgetItem([_("Locations")])
        self.locations_item.setIcon(0, self._create_icon("locations"))
        self.locations_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "category": "locations"})
        self.tree.addTopLevelItem(self.locations_item)
        self.locations_item.setExpanded(True)
    
    def set_narrative_context_manager(self, manager):
        """Set the narrative context manager for checking context freshness."""
        self.narrative_context_manager = manager
    
    def _get_scene_context_status(self, scene: dict) -> str:
        """Determine the narrative context status for a scene."""
        if not self.narrative_context_manager:
            return "scene"  # Default if no context manager
        
        scene_id = scene.get("id")
        scene_modified = scene.get("modified_at")
        
        if not scene_id or not scene_modified:
            return "scene"
        
        try:
            # Check if there's any narrative context for this scene
            context_entries = self.narrative_context_manager.get_context_for_scene(scene_id)
            
            if not context_entries:
                return "scene_no_context"  # No context exists
            
            # Parse scene modified time (SQLite format: 'YYYY-MM-DD HH:MM:SS')
            try:
                if 'T' in scene_modified:
                    scene_modified_dt = datetime.fromisoformat(scene_modified.replace('Z', '+00:00'))
                else:
                    # SQLite datetime format
                    scene_modified_dt = datetime.strptime(scene_modified, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid scene modified_at format: {scene_modified}")
                return "scene"
            
            # Check if any context is newer than scene modification
            for entry in context_entries:
                if entry.get("updated_at"):
                    try:
                        context_updated_str = entry["updated_at"]
                        if 'T' in context_updated_str:
                            context_updated = datetime.fromisoformat(context_updated_str.replace('Z', '+00:00'))
                        else:
                            # SQLite datetime format
                            context_updated = datetime.strptime(context_updated_str, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid context updated_at format: {context_updated_str}")
                        continue
                    if context_updated >= scene_modified_dt:
                        return "scene_fresh"  # Context is up to date
            
            return "scene_stale"  # Context exists but is stale
            
        except Exception as e:
            self.logger.warning(f"Error checking scene context status: {e}")
            return "scene"  # Default on error
        
    def load_scenes(self, scenes, preserve_selection=True):
        """Załaduj sceny do drzewka."""
        # Zachowaj selekcję
        selected_data = None
        if preserve_selection and self.tree.currentItem():
            selected_data = self.tree.currentItem().data(0, Qt.ItemDataRole.UserRole)
        
        # Przebuduj listę scen
        self.scenes_item.takeChildren()
        
        for scene in scenes:
            # Determine context status and appropriate icon
            context_status = self._get_scene_context_status(scene)
            
            scene_item = QTreeWidgetItem([scene.get("title", "Bez tytułu")])
            scene_item.setIcon(0, self._create_icon(context_status))
            
            # Enhanced tooltip with context information
            tooltip = f"{_('Scene')}: {scene.get('title', _('Untitled'))}"
            if scene.get("modified_at"):
                tooltip += f"\n{_('Last modified')}: {scene['modified_at']}"
            
            if context_status == "scene_fresh":
                tooltip += f"\n✓ {_('Narrative context is up to date')}"
            elif context_status == "scene_stale":
                tooltip += f"\n⚠ {_('Narrative context needs refresh')}"
            elif context_status == "scene_no_context":
                tooltip += f"\n⚠ {_('No narrative context available')}"
                
            scene_item.setToolTip(0, tooltip)
            
            scene_item.setData(0, Qt.ItemDataRole.UserRole, {
                "type": "scene", 
                "id": scene["id"], 
                "title": scene.get("title", "Scena"),
                "context_status": context_status,
                "modified_at": scene.get("modified_at")
            })
            self.scenes_item.addChild(scene_item)
            
        if not scenes:
            empty_item = QTreeWidgetItem(["(brak scen)"])
            empty_item.setIcon(0, self._create_icon("empty"))
            empty_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "empty"})
            empty_item.setDisabled(True)
            self.scenes_item.addChild(empty_item)
            
        # Przywróć selekcję
        if selected_data:
            self._restore_selection(selected_data)
            
    def load_characters(self, characters, preserve_selection=True):
        """Załaduj postacie do drzewka."""
        # Zachowaj selekcję
        selected_data = None
        if preserve_selection and self.tree.currentItem():
            selected_data = self.tree.currentItem().data(0, Qt.ItemDataRole.UserRole)
        
        # Wyczyść obecne postacie
        self.characters_item.takeChildren()
        
        # Dodaj postacie
        for character in characters:
            character_item = QTreeWidgetItem([character.get("name", _("Untitled"))])
            character_item.setIcon(0, self._create_icon("character"))
            character_item.setData(0, Qt.ItemDataRole.UserRole, {
                "type": "character", 
                "id": character["id"], 
                "name": character.get("name", _("Untitled"))
            })
            self.characters_item.addChild(character_item)
            
        if not characters:
            empty_item = QTreeWidgetItem([_("(no characters)")])
            empty_item.setIcon(0, self._create_icon("empty"))
            empty_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "empty"})
            empty_item.setDisabled(True)
            self.characters_item.addChild(empty_item)
            
        # Przywróć selekcję
        if selected_data:
            self._restore_selection(selected_data)
    
    def load_locations(self, locations, preserve_selection=True):
        """Załaduj lokacje do drzewka."""
        # Zachowaj selekcję
        selected_data = None
        if preserve_selection and self.tree.currentItem():
            selected_data = self.tree.currentItem().data(0, Qt.ItemDataRole.UserRole)
        
        # Wyczyść obecne lokacje
        self.locations_item.takeChildren()
        
        # Dodaj lokacje
        for location in locations:
            location_item = QTreeWidgetItem([location.get("name", _("Untitled Location"))])
            location_item.setIcon(0, self._create_icon("locations"))
            location_item.setData(0, Qt.ItemDataRole.UserRole, {
                "type": "location", 
                "id": location["id"], 
                "name": location.get("name", _("Untitled Location"))
            })
            self.locations_item.addChild(location_item)
            
        if not locations:
            empty_item = QTreeWidgetItem([_("(no locations)")])
            empty_item.setIcon(0, self._create_icon("empty"))
            empty_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "empty"})
            empty_item.setDisabled(True)
            self.locations_item.addChild(empty_item)
            
        # Przywróć selekcję
        if selected_data:
            self._restore_selection(selected_data)
            
    def _restore_selection(self, selected_data):
        """Przywróć selekcję w drzewku."""
        self.tree.blockSignals(True)
        
        try:
            if selected_data.get("type") == "category":
                category_items = {"search": self.search_item, "scenes": self.scenes_item, "characters": self.characters_item, "locations": self.locations_item}
                item = category_items.get(selected_data.get("category"))
                if item:
                    self.tree.setCurrentItem(item)
                    
            elif selected_data.get("type") == "scene":
                scene_id = selected_data.get("id")
                for i in range(self.scenes_item.childCount()):
                    child = self.scenes_item.child(i)
                    child_data = child.data(0, Qt.ItemDataRole.UserRole)
                    if child_data and child_data.get("id") == scene_id:
                        self.tree.setCurrentItem(child)
                        break
        finally:
            self.tree.blockSignals(False)
            
    def refresh_icons(self):
        """Odśwież ikony po zmianie motywu."""
        # Odśwież ikony kategorii
        self.search_item.setIcon(0, self._create_icon("search"))
        self.scenes_item.setIcon(0, self._create_icon("scenes"))
        self.characters_item.setIcon(0, self._create_icon("characters"))
        self.locations_item.setIcon(0, self._create_icon("locations"))
        
        # Odśwież ikony scen
        for i in range(self.scenes_item.childCount()):
            child = self.scenes_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole)
            if child_data:
                if child_data.get("type") == "scene":
                    child.setIcon(0, self._create_icon("scene"))
                elif child_data.get("type") == "empty":
                    child.setIcon(0, self._create_icon("empty"))
            
    def _on_item_clicked(self, item, column):
        """Obsługa kliknięcia na element drzewka."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        if data.get("type") == "category":
            # Kliknięcie na kategorię - pokaż widok kafelków
            category = data["category"]
            if category == "search":
                self.searchRequested.emit()
            self.categorySelected.emit(category)
        elif data.get("type") == "scene":
            self.sceneSelected.emit(data["id"], data["title"])
        elif data.get("type") == "character":
            self.characterSelected.emit(data["id"], data["name"])
        elif data.get("type") == "location":
            self.locationSelected.emit(data["id"], data["name"])
    
    def _on_context_menu_requested(self, position):
        """Handle right-click context menu requests."""
        item = self.tree.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "scene":
            return
        
        scene_id = data.get("id")
        scene_title = data.get("title", "Scene")
        context_status = data.get("context_status", "scene")
        
        # Re-check the context status in real-time to get the most current status
        if self.narrative_context_manager:
            # Get fresh scene data for status check
            fresh_scene_data = {"id": scene_id, "title": scene_title, "modified_at": data.get("modified_at")}
            context_status = self._get_scene_context_status(fresh_scene_data)
        
        # Create context menu
        menu = QMenu(self)
        
        # Generate Context submenu
        generate_menu = QMenu(_("Generate Context with Template"), self)
        
        # Add common narrative context templates (using actual template files)
        templates = [
            ("scene_summary", _("Scene Summary")),
            ("continue_with_context", _("Continue with Context")),
            ("expand_scene", _("Expand Scene")), 
            ("dialogue_enhancement", _("Dialogue Enhancement")),
            ("rewrite_scene", _("Rewrite Scene"))
        ]
        
        for template_key, template_name in templates:
            action = QAction(template_name, self)
            action.triggered.connect(lambda checked, tid=scene_id, tname=template_key: 
                                   self.generateContextRequested.emit(tid, tname))
            generate_menu.addAction(action)
        
        menu.addMenu(generate_menu)
        
        # Refresh Context action (if context exists but is stale)
        if context_status in ["scene_stale", "scene_fresh"]:
            menu.addSeparator()
            refresh_action = QAction(_("Refresh Narrative Context"), self)
            refresh_action.triggered.connect(lambda checked, sid=scene_id: 
                                           self.refreshContextRequested.emit(sid))
            menu.addAction(refresh_action)
        
        # View Context action (if context exists)
        if context_status in ["scene_stale", "scene_fresh"]:
            view_context_action = QAction(_("📄 View Generated Context"), self)
            view_context_action.triggered.connect(lambda checked, sid=scene_id: 
                                                self.viewContextRequested.emit(sid))
            menu.addAction(view_context_action)
            
            # Edit Context action (if context exists)
            edit_context_action = QAction(_("✏️ Edit Generated Context"), self)
            edit_context_action.triggered.connect(lambda checked, sid=scene_id: 
                                                self.editContextRequested.emit(sid))
            menu.addAction(edit_context_action)
        
        # Edit Templates action
        menu.addSeparator()
        edit_templates_action = QAction(_("Edit Templates..."), self)
        edit_templates_action.triggered.connect(lambda: self.editTemplateRequested.emit("scene_summary"))
        menu.addAction(edit_templates_action)
        
        # Show the menu
        menu.exec(self.tree.mapToGlobal(position))
            
    def _on_new_scene_clicked(self):
        """Obsługa kliknięcia przycisku nowa scena."""
        title, ok = QInputDialog.getText(self, "Nowa Scena", "Tytuł sceny:")
        if ok and title.strip():
            self.newSceneRequested.emit(title.strip())
            
    def _on_new_character_clicked(self):
        """Obsługa kliknięcia przycisku nowa postać."""
        name, ok = QInputDialog.getText(
            self, 
            _("New Character"), 
            _("Character name:"),
            text=_("Untitled")
        )
        
        if ok and name.strip():
            self.newCharacterRequested.emit(name.strip())
        elif ok:
            QMessageBox.warning(
                self, 
                _("Warning"), 
                _("Character name cannot be empty.")
            )
        
    def _on_new_location_clicked(self):
        """Obsługa kliknięcia przycisku nowa lokacja."""
        name, ok = QInputDialog.getText(
            self, 
            _("New Location"), 
            _("Location name:"),
            text=_("Untitled Location")
        )
        
        if ok and name.strip():
            self.newLocationRequested.emit(name.strip())
        elif ok:
            QMessageBox.warning(
                self, 
                _("Warning"), 
                _("Location name cannot be empty.")
            )