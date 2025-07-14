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

# Button Styles
NEW_PROJECT_BUTTON_STYLE = """
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
}
QPushButton:hover {
    background-color: #2980b9;
}
"""

NEW_SCENE_BUTTON_STYLE = """
QPushButton {
    background-color: #e74c3c;
    color: white;
    border: none;
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
}
QPushButton:hover {
    background-color: #c0392b;
}
QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}
"""

# Text Colors
HEADER_COLOR = "color: #2c3e50; padding: 10px;"
SECONDARY_TEXT_COLOR = "color: #7f8c8d;"
MUTED_TEXT_COLOR = "color: #95a5a6; font-style: italic;"
INFO_TEXT_COLOR = "color: #7f8c8d; line-height: 1.5;"
SEPARATOR_COLOR = "color: #bdc3c7;"