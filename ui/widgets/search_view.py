"""Search view widget for displaying search interface and results."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QScrollArea, QFrame, QGridLayout,
                              QLineEdit, QComboBox, QSplitter)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from .search_result_card import SearchResultCard
from ..styles.styles import HEADER_COLOR
from i18n import _


class SearchView(QWidget):
    """Search view for finding content across scenes, characters, and locations."""
    
    # Signals for search interactions
    searchRequested = Signal(str, str)  # query, filter_type
    resultSelected = Signal(str, int, str, str)  # result_type, id, title, search_query
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_results = []
        self.current_query = ""
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the search view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(_("🔍 Search"))
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet(HEADER_COLOR)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Search input section
        search_section = QFrame()
        search_section.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        search_layout = QVBoxLayout(search_section)
        search_layout.setSpacing(10)
        
        # Search input row
        input_layout = QHBoxLayout()
        
        # Search field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_("Search scenes, characters, locations..."))
        self.search_input.setFont(QFont("Arial", 11))
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        input_layout.addWidget(self.search_input)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            _("All Types"),
            _("Scenes"),
            _("Characters"),
            _("Locations")
        ])
        self.filter_combo.setFont(QFont("Arial", 10))
        self.filter_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
        """)
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        input_layout.addWidget(self.filter_combo)
        
        search_layout.addLayout(input_layout)
        
        # Search info row
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel(_("Enter text to search across your project content"))
        self.info_label.setFont(QFont("Arial", 9))
        self.info_label.setStyleSheet("color: #6c757d;")
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        self.results_count_label = QLabel("")
        self.results_count_label.setFont(QFont("Arial", 9))
        self.results_count_label.setStyleSheet("color: #6c757d;")
        info_layout.addWidget(self.results_count_label)
        
        search_layout.addLayout(info_layout)
        layout.addWidget(search_section)
        
        # Results area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Results container
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(10)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area)
        
        # Empty/no results state
        self.empty_label = QLabel(_("Enter a search term to find content in your project"))
        self.empty_label.setFont(QFont("Arial", 12))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #adb5bd; padding: 60px 20px;")
        layout.addWidget(self.empty_label)
        
        self.update_display_state()
        
    def on_search_text_changed(self, text):
        """Handle search text changes with debouncing."""
        self.current_query = text.strip()
        self.search_timer.stop()
        
        if len(self.current_query) >= 2:  # Start searching after 2 characters
            self.search_timer.start(300)  # 300ms delay
        else:
            self.clear_results()
            
    def on_filter_changed(self, filter_text):
        """Handle filter type changes."""
        if self.current_query:
            self.perform_search()
            
    def perform_search(self):
        """Emit search request signal."""
        if not self.current_query:
            return
            
        # Map UI filter to backend filter
        filter_map = {
            _("All Types"): "all",
            _("Scenes"): "scenes", 
            _("Characters"): "characters",
            _("Locations"): "locations"
        }
        
        filter_type = filter_map.get(self.filter_combo.currentText(), "all")
        self.searchRequested.emit(self.current_query, filter_type)
        
    def load_search_results(self, search_results):
        """Load and display search results."""
        self.search_results = search_results.results if hasattr(search_results, 'results') else search_results
        self.clear_results()
        
        if not self.search_results:
            self.update_display_state()
            return
            
        # Group results by type for better organization
        scenes_results = [r for r in self.search_results if r.result_type.value == "scene"]
        characters_results = [r for r in self.search_results if r.result_type.value == "character"] 
        locations_results = [r for r in self.search_results if r.result_type.value == "location"]
        
        # Add type sections
        if scenes_results:
            self.add_section_header(_("Scenes"), len(scenes_results))
            for result in scenes_results:
                self.add_result_card(result)
                
        if characters_results:
            self.add_section_header(_("Characters"), len(characters_results))
            for result in characters_results:
                self.add_result_card(result)
                
        if locations_results:
            self.add_section_header(_("Locations"), len(locations_results))
            for result in locations_results:
                self.add_result_card(result)
        
        self.update_display_state()
        
    def add_section_header(self, title, count):
        """Add a section header for result type."""
        header = QLabel(f"{title} ({count})")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.setStyleSheet("""
            color: #495057;
            padding: 10px 0 5px 0;
            border-bottom: 1px solid #dee2e6;
            margin-top: 10px;
        """)
        self.results_layout.addWidget(header)
        
    def add_result_card(self, result):
        """Add a search result card."""
        card = SearchResultCard(result)
        card.clicked.connect(lambda r=result: self.resultSelected.emit(
            r.result_type.value, r.id, r.title, self.current_query
        ))
        self.results_layout.addWidget(card)
        
    def clear_results(self):
        """Clear all result cards."""
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                
    def update_display_state(self):
        """Update UI based on search state."""
        has_query = bool(self.current_query)
        has_results = len(self.search_results) > 0
        
        self.scroll_area.setVisible(has_results)
        
        if not has_query:
            self.empty_label.setText(_("Enter a search term to find content in your project"))
            self.empty_label.setVisible(True)
            self.results_count_label.setText("")
        elif has_results:
            self.empty_label.setVisible(False)
            self.results_count_label.setText(_("Found {} results").format(len(self.search_results)))
        else:
            self.empty_label.setText(_("No results found for '{}'").format(self.current_query))
            self.empty_label.setVisible(True)
            self.results_count_label.setText(_("0 results"))
            
    def focus_search_input(self):
        """Focus the search input field."""
        self.search_input.setFocus()
        self.search_input.selectAll()