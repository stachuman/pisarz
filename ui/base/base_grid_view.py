"""Base grid view widget with common styling and behavior."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QGridLayout, QPushButton, QFrame,
                              QLineEdit, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .enhanced_theme_manager import EnhancedThemeManager
from .ui_font_manager import UIFontManager
from i18n import _


class BaseGridView(QWidget):
    """Base grid view widget with common styling and behavior."""
    
    newItemRequested = Signal(str)  # title/name
    
    def __init__(self, title="Items", icon="📝", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.theme_manager = EnhancedThemeManager()
        self.font_manager = UIFontManager()
        self.items_data = []
        self.filtered_items = []
        
        self.setup_base_ui()
        self.apply_theme()
        
    def setup_base_ui(self):
        """Setup base grid view UI with common styling."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with title and new button
        self.header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(f"{self.icon} {self.title}")
        title_label.setFont(self.font_manager.get_title_font())
        self.header_layout.addWidget(title_label)
        
        self.header_layout.addStretch()
        
        # New item button
        self.new_item_btn = QPushButton(f"+ {_('New')} {self.title[:-1]}")  # Remove 's' from plural
        self.new_item_btn.clicked.connect(self._on_new_item_clicked)
        self.new_item_btn.setFixedSize(150, 35)
        self.header_layout.addWidget(self.new_item_btn)
        
        layout.addLayout(self.header_layout)
        
        # Filter/Search section
        self.filter_layout = QHBoxLayout()
        
        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(_("Search..."))
        self.search_field.textChanged.connect(self._on_search_changed)
        self.search_field.setFixedHeight(30)
        self.filter_layout.addWidget(self.search_field)
        
        # Filter combo (can be customized by subclasses)
        self.filter_combo = QComboBox()
        self.filter_combo.addItem(_("All"))
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self.filter_combo.setFixedHeight(30)
        self.filter_layout.addWidget(self.filter_combo)
        
        layout.addLayout(self.filter_layout)
        
        # Scroll area for grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Grid container
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)
        
        # Empty state label
        self.empty_label = QLabel(_("No items to display"))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(self.font_manager.get_heading_font())
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        
    def apply_theme(self):
        """Apply theme styling to the grid view."""
        colors = self.theme_manager.get_theme_colors()
        
        # Title styling
        if hasattr(self, 'header_layout'):
            title_label = self.header_layout.itemAt(0).widget()
            if title_label:
                title_label.setStyleSheet(f"color: {colors['heading']};")
        
        # New item button styling
        self.new_item_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["accent"]};
                color: white;
                border: 1px solid {colors["accent"]};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors["accent_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["accent_pressed"]};
            }}
        """)
        
        # Search field styling
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["input_background"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                padding: 8px;
                color: {colors["text"]};
            }}
            QLineEdit:focus {{
                border: 1px solid {colors["accent"]};
            }}
        """)
        
        # Filter combo styling
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors["input_background"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                padding: 8px;
                color: {colors["text"]};
            }}
            QComboBox:hover {{
                border: 1px solid {colors["accent"]};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        """)
        
        # Empty label styling
        self.empty_label.setStyleSheet(f"color: {colors['secondary_text']};")
        
    def refresh_theme(self):
        """Refresh theme styling."""
        self.apply_theme()
        
    def _on_new_item_clicked(self):
        """Handle new item button click."""
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, _("New Item"), _("Enter name:"))
        if ok and title.strip():
            self.newItemRequested.emit(title.strip())
            
    def _on_search_changed(self, text):
        """Handle search text changes."""
        self.filter_items()
        
    def _on_filter_changed(self, filter_text):
        """Handle filter changes."""
        self.filter_items()
        
    def load_items(self, items_data):
        """Load items data."""
        self.items_data = items_data
        self.filtered_items = items_data.copy()
        self.filter_items()
        
    def filter_items(self):
        """Filter items based on search and filter criteria."""
        search_text = self.search_field.text().lower()
        filter_text = self.filter_combo.currentText()
        
        # Base filtering by search text
        if search_text:
            self.filtered_items = [
                item for item in self.items_data 
                if search_text in self.get_item_search_text(item).lower()
            ]
        else:
            self.filtered_items = self.items_data.copy()
        
        # Additional filtering (to be implemented by subclasses)
        self.filtered_items = self.apply_additional_filters(self.filtered_items, filter_text)
        
        # Update grid display
        self.update_grid_display()
        
    def get_item_search_text(self, item):
        """Get searchable text for an item (to be implemented by subclasses)."""
        return str(item)
        
    def apply_additional_filters(self, items, filter_text):
        """Apply additional filtering logic (to be implemented by subclasses)."""
        return items
        
    def update_grid_display(self):
        """Update the grid display with filtered items."""
        # Clear existing items
        self.clear_grid()
        
        # Show/hide empty state
        if not self.filtered_items:
            self.empty_label.show()
            self.grid_container.hide()
            return
        else:
            self.empty_label.hide()
            self.grid_container.show()
        
        # Add items to grid
        columns = 4  # Default columns, can be customized
        for index, item in enumerate(self.filtered_items):
            row = index // columns
            col = index % columns
            
            card = self.create_item_card(item)
            if card:
                self.grid_layout.addWidget(card, row, col)
        
        # Add stretch to fill remaining space
        self.grid_layout.setRowStretch(len(self.filtered_items) // columns + 1, 1)
        
    def create_item_card(self, item):
        """Create a card widget for an item (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement create_item_card() method")
        
    def clear_grid(self):
        """Clear all items from the grid."""
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
    def add_filter_option(self, text):
        """Add a filter option to the filter combo."""
        self.filter_combo.addItem(text)
        
    def set_columns(self, columns):
        """Set the number of columns for the grid."""
        self.columns = columns
        
    def get_current_filter(self):
        """Get the current filter selection."""
        return self.filter_combo.currentText()
        
    def get_search_text(self):
        """Get the current search text."""
        return self.search_field.text()