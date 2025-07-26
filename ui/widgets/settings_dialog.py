"""Settings dialog for theme selection and other preferences."""

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QComboBox, QGridLayout,
                              QFrame, QTabWidget, QWidget)

from ui.base.base_dialog import BaseDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor

from ..styles.themes import ThemeManager
from .llm_settings_widget import LLMSettingsWidget
from .ai_content_settings_widget import AIContentSettingsWidget
from i18n import _, get_available_languages, get_current_language, set_language


class ThemePreview(QFrame):
    """Widget do podglądu motywu."""
    
    theme_selected = Signal(str)  # Add signal for theme selection
    
    def __init__(self, theme_name, theme_data, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.theme_data = theme_data
        self.setup_ui()
        
    def setup_ui(self):
        """Stwórz podgląd motywu."""
        self.setFixedSize(120, 80)
        self.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Nazwa motywu using parent's font manager
        name_label = QLabel(self.theme_name)
        parent_dialog = self.parent()
        while parent_dialog and not hasattr(parent_dialog, 'font_manager'):
            parent_dialog = parent_dialog.parent()
        
        if parent_dialog and hasattr(parent_dialog, 'font_manager'):
            from PySide6.QtGui import QFont
            name_label.setFont(parent_dialog.font_manager.get_font(9, weight=QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Kolory tła - symulacja
        color_frame = QFrame()
        color_frame.setFixedHeight(40)
        bg_color = self.theme_data.get('background', '#ffffff')
        text_color = self.theme_data.get('text', '#000000')
        
        # Use consistent border color
        border_color = '#cccccc'
        if parent_dialog and hasattr(parent_dialog, 'theme_manager'):
            border_color = parent_dialog.theme_manager.get_theme_colors().get('border', '#cccccc')
            
        color_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(color_frame)
        
        # Przykładowy tekst
        sample_text = QLabel("Abc")
        sample_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sample_text.setStyleSheet(f"color: {text_color}; font-size: 10px;")
        
        # Dodaj tekst na color_frame
        frame_layout = QVBoxLayout(color_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(sample_text)
        
        # Apply consistent theming
        border_color = '#dddddd'
        accent_color = '#3498db'
        if parent_dialog and hasattr(parent_dialog, 'theme_manager'):
            colors = parent_dialog.theme_manager.get_theme_colors()
            border_color = colors.get('border', border_color)
            accent_color = colors.get('accent', accent_color)
            
        self.setStyleSheet(f"""
            ThemePreview {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 5px;
            }}
            ThemePreview:hover {{
                border: 2px solid {accent_color};
            }}
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press to emit theme selection signal."""
        self.theme_selected.emit(self.theme_name)
        super().mousePressEvent(event)


class SettingsDialog(BaseDialog):
    """Dialog ustawień aplikacji."""
    
    themeChanged = Signal(str)  # theme_name
    languageChanged = Signal(str)  # language_code
    llmSettingsChanged = Signal()  # llm settings changed
    
    def __init__(self, parent=None):
        super().__init__(
            title=_("Application Settings"),
            width=900,
            height=750,
            modal=True,
            parent=parent
        )
        
        # Override BaseDialog's theme_manager with the specific one we need for settings
        self.settings_theme_manager = ThemeManager()
        self.current_theme = self.settings_theme_manager.get_current_theme()
        self.current_language = get_current_language()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja interfejsu dialogu."""
        # Title using create_section_title
        title = self.create_section_title(_("Application Settings"), 18)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_content_widget(title)
        
        # Tabs for different settings categories
        tabs = self.create_tab_widget()
        
        # === GENERAL TAB ===
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Language section
        language_group, language_layout = self.create_form_section(_("Language"))
        
        # Language selection using form section pattern
        lang_label = QLabel(_("Choose language:"))
        lang_label.setFont(self.font_manager.get_font(10))
        
        self.language_combo = QComboBox()
        languages = get_available_languages()
        for code, name in languages.items():
            self.language_combo.addItem(name, code)
            
        # Set current language
        current_index = self.language_combo.findData(self.current_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
            
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        language_layout.addRow(lang_label, self.language_combo)
        general_layout.addWidget(language_group)
        
        # Themes section
        themes_group, themes_layout = self.create_form_section(_("Theme"))
        
        # Description
        description = self.create_info_label(_("Choose color theme for the application"), "muted")
        description.setFont(self.font_manager.get_font(10))
        themes_layout.addRow(description)
        
        # Create themes grid widget
        themes_widget = self._create_themes_grid()
        themes_layout.addRow(themes_widget)
        general_layout.addWidget(themes_group)
        
        # Add stretch to general tab
        general_layout.addStretch()
        
        # Add general tab to tabs
        tabs.addTab(general_tab, _("General"))
        
        # === LLM TAB ===
        self.llm_settings_widget = LLMSettingsWidget()
        self.llm_settings_widget.settings_changed.connect(self.llmSettingsChanged.emit)
        tabs.addTab(self.llm_settings_widget, _("AI Assistant"))
        
        # === AI CONTENT TAB ===
        self.ai_content_settings_widget = AIContentSettingsWidget()
        self.ai_content_settings_widget.settings_changed.connect(self.llmSettingsChanged.emit)
        tabs.addTab(self.ai_content_settings_widget, _("AI Content"))
        
        # Add tabs to main layout
        self.add_content_widget(tabs)
        
        # Standard buttons
        self.create_standard_buttons(_("Apply"), self.accept, _("Close"))
    
    def _create_themes_grid(self):
        """Create the themes grid widget using BaseDialog patterns."""
        from PySide6.QtWidgets import QGridLayout, QWidget
        
        themes_widget = QWidget()
        themes_grid = QGridLayout(themes_widget)
        themes_grid.setSpacing(10)
        
        # Get available themes
        themes = self.settings_theme_manager.get_available_themes()
        
        # Handle both dictionary and list formats - fail explicitly for unexpected types
        if isinstance(themes, dict):
            themes_items = themes.items()
        elif isinstance(themes, list):
            # If it's a list of theme names, get theme data from theme manager
            if hasattr(self.settings_theme_manager, 'themes'):
                themes_items = [(theme_name, self.settings_theme_manager.themes.get(theme_name, {})) 
                              for theme_name in themes]
            else:
                raise AttributeError(f"Theme manager {type(self.settings_theme_manager)} doesn't have 'themes' attribute")
        else:
            raise TypeError(f"Expected dict or list from get_available_themes(), got {type(themes)}")
        
        for i, (theme_name, theme_data) in enumerate(themes_items):
            row = i // 3
            col = i % 3
            
            # Theme preview
            preview = ThemePreview(theme_name, theme_data, self)
            # Connect signal to avoid lambda capture issues
            preview.theme_selected.connect(self._on_theme_selected)
            themes_grid.addWidget(preview, row, col)
            
        return themes_widget
        
    def _on_theme_selected(self, theme_name):
        """Obsługa wyboru motywu."""
        self.current_theme = theme_name
        # Można dodać wizualne oznaczenie wybranego motywu
        
    def _on_language_changed(self, index):
        """Obsługa zmiany języka."""
        language_code = self.language_combo.itemData(index)
        if language_code and language_code != self.current_language:
            self.current_language = language_code
            # Ustaw język natychmiast
            if set_language(language_code):
                self.languageChanged.emit(language_code)
        
    def accept(self):
        """Zastosuj ustawienia i zamknij dialog."""
        if self.current_theme:
            self.settings_theme_manager.set_theme(self.current_theme)
            self.themeChanged.emit(self.current_theme)
        super().accept()