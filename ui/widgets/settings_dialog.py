"""Settings dialog for theme selection and other preferences."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QComboBox, QGroupBox, QGridLayout,
                              QFrame, QColorDialog, QSizePolicy, QTabWidget, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor

from ..styles.themes import ThemeManager
from .llm_settings_widget import LLMSettingsWidget
from .ai_content_settings_widget import AIContentSettingsWidget
from i18n import _, get_available_languages, get_current_language, set_language


class ThemePreview(QFrame):
    """Widget do podglądu motywu."""
    
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
        
        # Nazwa motywu
        name_label = QLabel(self.theme_name)
        name_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Kolory tła - symulacja
        color_frame = QFrame()
        color_frame.setFixedHeight(40)
        bg_color = self.theme_data.get('background', '#ffffff')
        text_color = self.theme_data.get('text', '#000000')
        
        color_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid #cccccc;
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
        
        # Styluj całą kartę zgodnie z motywem
        self.setStyleSheet(f"""
            ThemePreview {{
                background-color: {bg_color};
                border: 2px solid #dddddd;
                border-radius: 5px;
            }}
            ThemePreview:hover {{
                border: 2px solid #3498db;
            }}
        """)


class SettingsDialog(QDialog):
    """Dialog ustawień aplikacji."""
    
    themeChanged = Signal(str)  # theme_name
    languageChanged = Signal(str)  # language_code
    llmSettingsChanged = Signal()  # llm settings changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.current_theme = self.theme_manager.get_current_theme()
        self.current_language = get_current_language()
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja interfejsu dialogu."""
        self.setWindowTitle(_("Application Settings"))
        self.setMinimumSize(800, 700)
        self.resize(900, 750)
        
        layout = QVBoxLayout(self)
        
        # Nagłówek
        title = QLabel(_("Application Settings"))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Tabs for different settings categories
        tabs = QTabWidget()
        
        # === GENERAL TAB ===
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Language section
        language_group = QGroupBox(_("Language"))
        language_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        language_layout = QVBoxLayout(language_group)
        
        # Wybór języka
        lang_layout = QHBoxLayout()
        lang_label = QLabel(_("Choose language:"))
        lang_label.setFont(QFont("Arial", 10))
        lang_layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        languages = get_available_languages()
        for code, name in languages.items():
            self.language_combo.addItem(name, code)
            
        # Ustaw aktualny język
        current_index = self.language_combo.findData(self.current_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
            
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        
        language_layout.addLayout(lang_layout)
        general_layout.addWidget(language_group)
        
        # Themes section
        themes_group = QGroupBox(_("Theme"))
        themes_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        themes_layout = QVBoxLayout(themes_group)
        
        # Opis
        description = QLabel(_("Choose color theme for the application"))
        description.setFont(QFont("Arial", 10))
        description.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        themes_layout.addWidget(description)
        
        # Siatka z podglądami motywów
        themes_grid = QGridLayout()
        themes_grid.setSpacing(10)
        
        # Pobierz dostępne motywy
        themes = self.theme_manager.get_available_themes()
        
        for i, (theme_name, theme_data) in enumerate(themes.items()):
            row = i // 3
            col = i % 3
            
            # Kontener dla podglądu i nazwy
            theme_container = QVBoxLayout()
            
            # Podgląd motywu
            preview = ThemePreview(theme_name, theme_data)
            preview.mousePressEvent = lambda event, name=theme_name: self._on_theme_selected(name)
            theme_container.addWidget(preview)
            
            # Widget kontener
            container_widget = QFrame()
            container_widget.setLayout(theme_container)
            themes_grid.addWidget(container_widget, row, col)
            
        themes_layout.addLayout(themes_grid)
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
        layout.addWidget(tabs)
        
        # === PRZYCISKI ===
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Przycisk Anuluj
        cancel_btn = QPushButton(_("Close"))
        cancel_btn.setFixedSize(100, 35)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        # Przycisk Zastosuj
        apply_btn = QPushButton(_("Close"))
        apply_btn.setFixedSize(100, 35)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        apply_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(apply_btn)
        
        layout.addLayout(buttons_layout)
        
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
            self.theme_manager.set_theme(self.current_theme)
            self.themeChanged.emit(self.current_theme)
        super().accept()