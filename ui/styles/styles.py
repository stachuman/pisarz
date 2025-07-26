"""Centralized styles for Pisarz application."""

# Project Card Styles
PROJECT_CARD_STYLE = """
QFrame {
    background-color: #ecf0f1;
    border: 1px solid #bdc3c7;
    border-radius: 5px;
}
QFrame:hover {
    background-color: #d5dbdb;
    border: 2px solid #3498db;
}
"""

# Scene Card Styles
SCENE_CARD_STYLE = """
QFrame {
    background-color: #ecf0f1;
    border: 1px solid #bdc3c7;
    border-radius: 5px;
}
QFrame:hover {
    background-color: #d5dbdb;
    border: 2px solid #e74c3c;
}
"""

# Legacy button styles - deprecated in favor of theme-based styling
# Use EnhancedThemeManager.get_theme_colors() with accent colors instead

# Text Colors
HEADER_COLOR = "color: #2c3e50; padding: 10px;"
SECONDARY_TEXT_COLOR = "color: #7f8c8d;"
MUTED_TEXT_COLOR = "color: #95a5a6; font-style: italic;"
INFO_TEXT_COLOR = "color: #7f8c8d; line-height: 1.5;"
SEPARATOR_COLOR = "color: #bdc3c7;"