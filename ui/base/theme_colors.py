"""Enhanced theme colors for consistent UI styling."""

from typing import Dict

# Default theme colors
DEFAULT_THEME_COLORS = {
    # Basic colors
    "background": "#ffffff",
    "text": "#333333",
    "secondary_text": "#666666",
    "heading": "#2c3e50",
    
    # UI elements
    "border": "#e0e0e0",
    "accent": "#3498db",
    "accent_hover": "#2980b9",
    "accent_pressed": "#1f5f8b",
    
    # Cards
    "card_background": "#ffffff",
    "card_hover": "#f8f9fa",
    
    # Buttons
    "button_background": "#ffffff",
    "button_hover": "#f8f9fa",
    "button_pressed": "#e9ecef",
    "secondary_button": "#6c757d",
    "secondary_button_hover": "#5a6268",
    "secondary_button_pressed": "#4e555b",
    
    # Input fields
    "input_background": "#ffffff",
    "input_border": "#ced4da",
    "input_focus": "#3498db",
    
    # Status colors
    "success": "#28a745",
    "success_hover": "#218838",
    "success_pressed": "#1e7e34",
    "warning": "#ffc107",
    "warning_hover": "#e0a800",
    "warning_pressed": "#d39e00",
    "danger": "#dc3545",
    "danger_hover": "#c82333",
    "danger_pressed": "#bd2130",
    "info": "#17a2b8",
    "info_hover": "#138496",
    "info_pressed": "#117a8b",
    
    # Special elements
    "separator": "#e9ecef",
    "shadow": "rgba(0, 0, 0, 0.1)",
    "overlay": "rgba(0, 0, 0, 0.5)",
    
    # Navigation
    "nav_background": "#f8f9fa",
    "nav_hover": "#e9ecef",
    "nav_active": "#007bff",
    
    # Editor
    "editor_background": "#ffffff",
    "editor_selection": "#3498db",
    "editor_highlight": "#fff3cd",
    "editor_current_line": "#f8f9fa",
    
    # Toolbar
    "toolbar_background": "#f8f9fa",
    "toolbar_border": "#e9ecef",
    "toolbar_button_hover": "#e9ecef",
}

# Dark theme colors
DARK_THEME_COLORS = {
    # Basic colors
    "background": "#2b2b2b",
    "text": "#ffffff",
    "secondary_text": "#aaaaaa",
    "heading": "#ffffff",
    
    # UI elements
    "border": "#404040",
    "accent": "#4a9eff",
    "accent_hover": "#3a8eef",
    "accent_pressed": "#2a7edf",
    
    # Cards
    "card_background": "#363636",
    "card_hover": "#404040",
    
    # Buttons
    "button_background": "#404040",
    "button_hover": "#4a4a4a",
    "button_pressed": "#505050",
    "secondary_button": "#6c757d",
    "secondary_button_hover": "#5a6268",
    "secondary_button_pressed": "#4e555b",
    
    # Input fields
    "input_background": "#404040",
    "input_border": "#555555",
    "input_focus": "#4a9eff",
    
    # Status colors
    "success": "#28a745",
    "success_hover": "#218838",
    "success_pressed": "#1e7e34",
    "warning": "#ffc107",
    "warning_hover": "#e0a800",
    "warning_pressed": "#d39e00",
    "danger": "#dc3545",
    "danger_hover": "#c82333",
    "danger_pressed": "#bd2130",
    "info": "#17a2b8",
    "info_hover": "#138496",
    "info_pressed": "#117a8b",
    
    # Special elements
    "separator": "#404040",
    "shadow": "rgba(0, 0, 0, 0.3)",
    "overlay": "rgba(0, 0, 0, 0.7)",
    
    # Navigation
    "nav_background": "#363636",
    "nav_hover": "#404040",
    "nav_active": "#4a9eff",
    
    # Editor
    "editor_background": "#2b2b2b",
    "editor_selection": "#4a9eff",
    "editor_highlight": "#5a5a2a",
    "editor_current_line": "#363636",
    
    # Toolbar
    "toolbar_background": "#363636",
    "toolbar_border": "#404040",
    "toolbar_button_hover": "#404040",
}

# Blue theme colors
BLUE_THEME_COLORS = {
    # Basic colors
    "background": "#f8f9fa",
    "text": "#212529",
    "secondary_text": "#6c757d",
    "heading": "#1e3a8a",
    
    # UI elements
    "border": "#dee2e6",
    "accent": "#0d6efd",
    "accent_hover": "#0b5ed7",
    "accent_pressed": "#0a58ca",
    
    # Cards
    "card_background": "#ffffff",
    "card_hover": "#e3f2fd",
    
    # Buttons
    "button_background": "#ffffff",
    "button_hover": "#e3f2fd",
    "button_pressed": "#bbdefb",
    "secondary_button": "#6c757d",
    "secondary_button_hover": "#5a6268",
    "secondary_button_pressed": "#4e555b",
    
    # Input fields
    "input_background": "#ffffff",
    "input_border": "#ced4da",
    "input_focus": "#0d6efd",
    
    # Status colors
    "success": "#198754",
    "success_hover": "#157347",
    "success_pressed": "#146c43",
    "warning": "#fd7e14",
    "warning_hover": "#e8681c",
    "warning_pressed": "#d15c26",
    "danger": "#dc3545",
    "danger_hover": "#c82333",
    "danger_pressed": "#bd2130",
    "info": "#0dcaf0",
    "info_hover": "#31d2f2",
    "info_pressed": "#25cff2",
    
    # Special elements
    "separator": "#e9ecef",
    "shadow": "rgba(13, 110, 253, 0.15)",
    "overlay": "rgba(0, 0, 0, 0.5)",
    
    # Navigation
    "nav_background": "#e3f2fd",
    "nav_hover": "#bbdefb",
    "nav_active": "#0d6efd",
    
    # Editor
    "editor_background": "#ffffff",
    "editor_selection": "#0d6efd",
    "editor_highlight": "#fff3cd",
    "editor_current_line": "#f8f9fa",
    
    # Toolbar
    "toolbar_background": "#e3f2fd",
    "toolbar_border": "#bbdefb",
    "toolbar_button_hover": "#bbdefb",
}

# Theme collection
THEME_COLORS = {
    "default": DEFAULT_THEME_COLORS,
    "dark": DARK_THEME_COLORS,
    "blue": BLUE_THEME_COLORS,
}


def get_theme_colors(theme_name: str = "default") -> Dict[str, str]:
    """Get theme colors for the specified theme."""
    return THEME_COLORS.get(theme_name, DEFAULT_THEME_COLORS)