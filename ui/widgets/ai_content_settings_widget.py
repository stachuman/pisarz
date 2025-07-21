"""AI Content Settings Widget for configuring content length options."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QSpinBox, QGroupBox, QGridLayout, QFrame)
from PySide6.QtCore import Signal, QSettings
from PySide6.QtGui import QFont

from i18n import _


class AIContentSettingsWidget(QWidget):
    """Widget for configuring AI content processing settings."""
    
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings()
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(_("AI Content Processing Settings"))
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 10px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Content Length Settings Group
        length_group = QGroupBox(_("Content Length Settings"))
        length_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        length_layout = QGridLayout(length_group)
        length_layout.setSpacing(15)
        
        # Scene Beginning Length
        beginning_label = QLabel(_("Scene Beginning Length:"))
        beginning_label.setFont(QFont("Arial", 10))
        beginning_label.setToolTip(_("Number of characters to use when 'Scene Beginning' is selected"))
        length_layout.addWidget(beginning_label, 0, 0)
        
        self.beginning_spinbox = QSpinBox()
        self.beginning_spinbox.setRange(100, 10000)
        self.beginning_spinbox.setSuffix(_(" characters"))
        self.beginning_spinbox.setValue(1000)  # Default
        self.beginning_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                min-width: 120px;
            }
        """)
        self.beginning_spinbox.valueChanged.connect(self.on_settings_changed)
        length_layout.addWidget(self.beginning_spinbox, 0, 1)
        
        # Scene End Length
        end_label = QLabel(_("Scene End Length:"))
        end_label.setFont(QFont("Arial", 10))
        end_label.setToolTip(_("Number of characters to use when 'Scene End' is selected"))
        length_layout.addWidget(end_label, 1, 0)
        
        self.end_spinbox = QSpinBox()
        self.end_spinbox.setRange(100, 10000)
        self.end_spinbox.setSuffix(_(" characters"))
        self.end_spinbox.setValue(1000)  # Default
        self.end_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                min-width: 120px;
            }
        """)
        self.end_spinbox.valueChanged.connect(self.on_settings_changed)
        length_layout.addWidget(self.end_spinbox, 1, 1)
        
        # Custom Length
        custom_label = QLabel(_("Custom Length:"))
        custom_label.setFont(QFont("Arial", 10))
        custom_label.setToolTip(_("Number of characters to use when 'Custom Length' is selected"))
        length_layout.addWidget(custom_label, 2, 0)
        
        self.custom_spinbox = QSpinBox()
        self.custom_spinbox.setRange(100, 50000)
        self.custom_spinbox.setSuffix(_(" characters"))
        self.custom_spinbox.setValue(2000)  # Default
        self.custom_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                min-width: 120px;
            }
        """)
        self.custom_spinbox.valueChanged.connect(self.on_settings_changed)
        length_layout.addWidget(self.custom_spinbox, 2, 1)
        
        # Add descriptions
        desc_frame = QFrame()
        desc_layout = QVBoxLayout(desc_frame)
        desc_layout.setContentsMargins(10, 10, 10, 10)
        
        description = QLabel(_(
            "These settings control how much content is passed to AI templates when different "
            "content source options are selected in the AI Assistant panel.\n\n"
            "• Scene Beginning: Uses the first N characters of the scene\n"
            "• Scene End: Uses the last N characters of the scene\n"
            "• Custom Length: Uses the first N characters for custom length option"
        ))
        description.setFont(QFont("Arial", 9))
        description.setStyleSheet("color: #6c757d; padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        description.setWordWrap(True)
        desc_layout.addWidget(description)
        
        length_layout.addWidget(desc_frame, 3, 0, 1, 2)
        
        layout.addWidget(length_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
    def on_settings_changed(self):
        """Handle settings change and save immediately."""
        self.save_settings()
        self.settings_changed.emit()
        
    def load_settings(self):
        """Load settings from QSettings."""
        # Load with defaults
        beginning_length = self.settings.value("ai_content/scene_beginning_length", 1000, type=int)
        end_length = self.settings.value("ai_content/scene_end_length", 1000, type=int)
        custom_length = self.settings.value("ai_content/custom_length", 2000, type=int)
        
        # Apply to UI
        self.beginning_spinbox.setValue(beginning_length)
        self.end_spinbox.setValue(end_length)
        self.custom_spinbox.setValue(custom_length)
        
    def save_settings(self):
        """Save current settings to QSettings."""
        self.settings.setValue("ai_content/scene_beginning_length", self.beginning_spinbox.value())
        self.settings.setValue("ai_content/scene_end_length", self.end_spinbox.value())
        self.settings.setValue("ai_content/custom_length", self.custom_spinbox.value())
        self.settings.sync()
        
    def get_scene_beginning_length(self) -> int:
        """Get scene beginning length setting."""
        return self.beginning_spinbox.value()
        
    def get_scene_end_length(self) -> int:
        """Get scene end length setting."""
        return self.end_spinbox.value()
        
    def get_custom_length(self) -> int:
        """Get custom length setting."""
        return self.custom_spinbox.value()
        
    @staticmethod
    def get_scene_beginning_length_from_settings() -> int:
        """Static method to get scene beginning length from settings."""
        settings = QSettings()
        return settings.value("ai_content/scene_beginning_length", 1000, type=int)
        
    @staticmethod
    def get_scene_end_length_from_settings() -> int:
        """Static method to get scene end length from settings."""
        settings = QSettings()
        return settings.value("ai_content/scene_end_length", 1000, type=int)
        
    @staticmethod
    def get_custom_length_from_settings() -> int:
        """Static method to get custom length from settings."""
        settings = QSettings()
        return settings.value("ai_content/custom_length", 2000, type=int)