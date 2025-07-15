"""Search result card widget for displaying individual search results."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics, QPalette

from i18n import _


class SearchResultCard(QFrame):
    """Card widget for displaying a single search result."""
    
    clicked = Signal()  # Emitted when card is clicked
    
    def __init__(self, search_result, parent=None):
        super().__init__(parent)
        self.search_result = search_result
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the search result card UI."""
        self.setFixedHeight(90)
        self.setStyleSheet("""
            SearchResultCard {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin: 2px;
            }
            SearchResultCard:hover {
                border-color: #007bff;
                background-color: #f8f9ff;
            }
        """)
        
        # Enable mouse tracking for hover effects
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Header row with title and type badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Title
        self.title_label = QLabel(self.search_result.title)
        self.title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #212529;")
        
        # Truncate title if too long
        font_metrics = QFontMetrics(self.title_label.font())
        max_width = 300
        elided_title = font_metrics.elidedText(
            self.search_result.title, 
            Qt.TextElideMode.ElideRight, 
            max_width
        )
        self.title_label.setText(elided_title)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Type badge
        type_badge = QLabel(self._get_type_display())
        type_badge.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        type_badge.setStyleSheet(f"""
            background-color: {self._get_type_color()};
            color: white;
            padding: 3px 8px;
            border-radius: 10px;
        """)
        header_layout.addWidget(type_badge)
        
        layout.addLayout(header_layout)
        
        # Snippet with highlighting
        if self.search_result.snippet:
            snippet_text = self._clean_snippet(self.search_result.snippet)
            self.snippet_label = QLabel(snippet_text)
            self.snippet_label.setFont(QFont("Arial", 9))
            self.snippet_label.setStyleSheet("color: #6c757d; line-height: 1.4;")
            self.snippet_label.setWordWrap(True)
            self.snippet_label.setMaximumHeight(35)  # Limit to ~2 lines
            layout.addWidget(self.snippet_label)
        
        # Metadata row (rank, additional info)
        metadata_layout = QHBoxLayout()
        
        # Relevance indicator
        relevance_text = _("Relevance: {:.1f}%").format(self.search_result.rank * 100)
        relevance_label = QLabel(relevance_text)
        relevance_label.setFont(QFont("Arial", 8))
        relevance_label.setStyleSheet("color: #adb5bd;")
        metadata_layout.addWidget(relevance_label)
        
        metadata_layout.addStretch()
        
        # Additional metadata based on type
        if hasattr(self.search_result, 'metadata') and self.search_result.metadata:
            metadata_text = self._get_metadata_text()
            if metadata_text:
                metadata_label = QLabel(metadata_text)
                metadata_label.setFont(QFont("Arial", 8))
                metadata_label.setStyleSheet("color: #adb5bd;")
                metadata_layout.addWidget(metadata_label)
        
        layout.addLayout(metadata_layout)
        
    def _get_type_display(self):
        """Get display text for result type."""
        type_map = {
            "scene": _("Scene"),
            "character": _("Character"),
            "location": _("Location")
        }
        return type_map.get(self.search_result.result_type.value, self.search_result.result_type.value)
        
    def _get_type_color(self):
        """Get color for result type badge."""
        color_map = {
            "scene": "#007bff",      # Blue
            "character": "#28a745",  # Green
            "location": "#ffc107"    # Yellow/orange
        }
        return color_map.get(self.search_result.result_type.value, "#6c757d")
        
    def _clean_snippet(self, snippet):
        """Clean and format snippet text."""
        if not snippet:
            return ""
            
        # Replace HTML-style highlighting with simpler formatting
        cleaned = snippet.replace("<mark>", "**").replace("</mark>", "**")
        
        # Limit length and ensure it ends nicely
        max_length = 120
        if len(cleaned) > max_length:
            # Find last space before limit
            truncate_pos = cleaned.rfind(" ", 0, max_length)
            if truncate_pos > max_length - 20:  # Only truncate if we don't lose too much
                cleaned = cleaned[:truncate_pos] + "..."
            else:
                cleaned = cleaned[:max_length] + "..."
                
        return cleaned
        
    def _get_metadata_text(self):
        """Get additional metadata text based on result type."""
        if not hasattr(self.search_result, 'metadata') or not self.search_result.metadata:
            return ""
            
        metadata = self.search_result.metadata
        result_type = self.search_result.result_type.value
        
        if result_type == "character":
            parts = []
            if metadata.get('importance', 0) > 1:
                parts.append(_("Important"))
            if metadata.get('is_protagonist'):
                parts.append(_("Protagonist"))
            if metadata.get('is_antagonist'):
                parts.append(_("Antagonist"))
            return " • ".join(parts)
            
        elif result_type == "location":
            parts = []
            if metadata.get('type'):
                parts.append(metadata['type'])
            if metadata.get('atmosphere'):
                parts.append(metadata['atmosphere'])
            return " • ".join(parts[:2])  # Limit to 2 items
            
        elif result_type == "scene":
            if metadata.get('content_length', 0) > 0:
                length = metadata['content_length']
                if length > 1000:
                    return _("Long scene")
                elif length > 300:
                    return _("Medium scene")
                else:
                    return _("Short scene")
                    
        return ""
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)