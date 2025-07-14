"""Project tree navigation widget for project view."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTreeWidget, QTreeWidgetItem, QPushButton, 
                              QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen

from ..styles.styles import HEADER_COLOR, NEW_SCENE_BUTTON_STYLE


class ProjectTreeView(QWidget):
    """Drzewko nawigacji w projekcie: Sceny, Postacie, Lokacje."""
    
    sceneSelected = Signal(int, str)        # id, title
    characterSelected = Signal(int, str)    # id, name (future)
    locationSelected = Signal(int, str)     # id, name (future)
    
    categorySelected = Signal(str)          # category name ("scenes", "characters", "locations")
    
    newSceneRequested = Signal(str)         # title
    newCharacterRequested = Signal(str)     # name (future)
    newLocationRequested = Signal(str)      # name (future)
    
    backToProjectsRequested = Signal()
    
    def __init__(self, project_name="", parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self.project_title_label = None
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
        self.new_character_btn = QPushButton("+ Nowa Postać")
        self.new_character_btn.clicked.connect(self._on_new_character_clicked)
        self.new_character_btn.setEnabled(False)  # TODO: Enable in future versions
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
        
        # Przycisk nowa lokacja (future)
        self.new_location_btn = QPushButton("+ Nowa Lokacja")
        self.new_location_btn.clicked.connect(self._on_new_location_clicked)
        self.new_location_btn.setEnabled(False)  # TODO: Enable in future versions
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
                
        elif icon_type == "characters":
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
            
        elif icon_type == "scene":
            # Strona dokumentu z zagniętym rogiem
            painter.setBrush(main_color)
            
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
        
        # Sceny
        self.scenes_item = QTreeWidgetItem(["Sceny"])
        self.scenes_item.setIcon(0, self._create_icon("scenes"))
        self.scenes_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "category": "scenes"})
        self.tree.addTopLevelItem(self.scenes_item)
        self.scenes_item.setExpanded(True)
        
        # Postacie (future)
        self.characters_item = QTreeWidgetItem(["Postacie"])
        self.characters_item.setIcon(0, self._create_icon("characters"))
        self.characters_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "category": "characters"})
        self.tree.addTopLevelItem(self.characters_item)
        self.characters_item.setExpanded(True)
        
        # Lokacje (future)
        self.locations_item = QTreeWidgetItem(["Lokacje"])
        self.locations_item.setIcon(0, self._create_icon("locations"))
        self.locations_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "category": "locations"})
        self.tree.addTopLevelItem(self.locations_item)
        self.locations_item.setExpanded(True)
        
    def load_scenes(self, scenes, preserve_selection=True):
        """Załaduj sceny do drzewka."""
        # Zachowaj selekcję
        selected_data = None
        if preserve_selection and self.tree.currentItem():
            selected_data = self.tree.currentItem().data(0, Qt.ItemDataRole.UserRole)
        
        # Przebuduj listę scen
        self.scenes_item.takeChildren()
        
        for scene in scenes:
            scene_item = QTreeWidgetItem([scene.get("title", "Bez tytułu")])
            scene_item.setIcon(0, self._create_icon("scene"))
            scene_item.setData(0, Qt.ItemDataRole.UserRole, {
                "type": "scene", 
                "id": scene["id"], 
                "title": scene.get("title", "Scena")
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
            
    def _restore_selection(self, selected_data):
        """Przywróć selekcję w drzewku."""
        self.tree.blockSignals(True)
        
        try:
            if selected_data.get("type") == "category":
                category_items = {"scenes": self.scenes_item, "characters": self.characters_item, "locations": self.locations_item}
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
            self.categorySelected.emit(data["category"])
        elif data.get("type") == "scene":
            self.sceneSelected.emit(data["id"], data["title"])
        elif data.get("type") == "character":
            self.characterSelected.emit(data["id"], data["name"])
        elif data.get("type") == "location":
            self.locationSelected.emit(data["id"], data["name"])
            
    def _on_new_scene_clicked(self):
        """Obsługa kliknięcia przycisku nowa scena."""
        title, ok = QInputDialog.getText(self, "Nowa Scena", "Tytuł sceny:")
        if ok and title.strip():
            self.newSceneRequested.emit(title.strip())
            
    def _on_new_character_clicked(self):
        """Obsługa kliknięcia przycisku nowa postać."""
        QMessageBox.information(self, "Funkcja niedostępna", "Postacie będą dostępne w przyszłych wersjach.")
        
    def _on_new_location_clicked(self):
        """Obsługa kliknięcia przycisku nowa lokacja."""
        QMessageBox.information(self, "Funkcja niedostępna", "Lokacje będą dostępne w przyszłych wersjach.")