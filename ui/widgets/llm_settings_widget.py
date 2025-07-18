"""
LLM Settings Widget for configuring AI providers.
Provides UI for configuring llama.cpp and other LLM providers.
"""

import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QTextEdit, QTabWidget, QFormLayout, QMessageBox, QProgressBar,
    QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont

from core.logging_config import get_logger
from core.llm.settings import get_llm_settings
from i18n import _


class LLMConnectionTestThread(QThread):
    """Thread for testing LLM provider connections."""
    
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, provider_name: str):
        super().__init__()
        self.provider_name = provider_name
        self.logger = get_logger("llm.connection_test")
    
    def run(self):
        """Test the connection to the LLM provider."""
        try:
            from core.llm.service import LLMService
            
            # Create temporary service for testing
            service = LLMService()
            service.initialize(self.provider_name)
            
            if service.is_initialized():
                # Try a simple generation test
                test_context = {
                    'current_text': 'Test',
                    'scene_summary': 'Test scene',
                    'project_name': 'Test'
                }
                
                response = service.execute_task('continue_scene', test_context)
                
                if response and len(response) > 0:
                    self.finished.emit(True, _("Connection successful"))
                else:
                    self.finished.emit(False, _("No response from provider"))
            else:
                self.finished.emit(False, _("Failed to initialize provider"))
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            self.finished.emit(False, str(e))


class LLMSettingsWidget(QWidget):
    """Widget for configuring LLM providers."""
    
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("llm.settings_widget")
        self.settings_manager = get_llm_settings()
        self.test_thread: Optional[LLMConnectionTestThread] = None
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(_("AI Provider Configuration"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(_("Configure AI providers for writing assistance"))
        desc_label.setStyleSheet("color: #666666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Global settings
        global_group = QGroupBox(_("General Settings"))
        global_layout = QFormLayout(global_group)
        
        self.context_length_spinbox = QSpinBox()
        self.context_length_spinbox.setRange(100, 2000)
        self.context_length_spinbox.setValue(500)
        self.context_length_spinbox.setSuffix(" " + _("characters"))
        self.context_length_spinbox.setToolTip(_("Number of characters to include from the current scene for context"))
        global_layout.addRow(_("Context Length:"), self.context_length_spinbox)
        
        layout.addWidget(global_group)
        
        # Provider selection
        provider_group = QGroupBox(_("Provider Selection"))
        provider_layout = QFormLayout(provider_group)
        
        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addRow(_("Active Provider:"), self.provider_combo)
        
        layout.addWidget(provider_group)
        
        # Configuration tabs
        self.config_tabs = QTabWidget()
        self.config_tabs.setMinimumHeight(400)
        layout.addWidget(self.config_tabs)
        
        # Setup provider-specific tabs
        self.setup_llamacpp_tab()
        self.setup_ollama_tab()
        self.setup_openai_tab()
        self.setup_anthropic_tab()
        self.setup_mock_tab()
        
        # Test result display (separate from buttons)
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        self.test_result.setMinimumHeight(30)
        self.test_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.test_result.setStyleSheet("padding: 5px; margin: 5px;")
        layout.addWidget(self.test_result)
        
        # Test connection progress bar (separate from buttons)
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        self.test_progress.setFixedHeight(20)
        self.test_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.test_progress)
        
        # Buttons layout - including test connection
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()
        
        self.test_button = QPushButton(_("Test Connection"))
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setMaximumWidth(150)
        button_layout.addWidget(self.test_button)
        
        self.reset_button = QPushButton(_("Reset to Defaults"))
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.reset_button.setMaximumWidth(150)
        button_layout.addWidget(self.reset_button)
        
        self.apply_button = QPushButton(_("Apply Settings"))
        self.apply_button.clicked.connect(self.apply_settings)
        self.apply_button.setDefault(True)
        self.apply_button.setMaximumWidth(150)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
    
    def setup_llamacpp_tab(self):
        """Setup llama.cpp configuration tab."""
        # Create scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Server settings
        server_group = QGroupBox(_("Server Configuration"))
        server_layout = QFormLayout(server_group)
        server_layout.setSpacing(8)
        
        self.llamacpp_host = QLineEdit()
        self.llamacpp_host.setPlaceholderText("localhost")
        self.llamacpp_host.setMinimumWidth(200)
        server_layout.addRow(_("Host:"), self.llamacpp_host)
        
        self.llamacpp_port = QSpinBox()
        self.llamacpp_port.setRange(1, 65535)
        self.llamacpp_port.setValue(8080)
        self.llamacpp_port.setMinimumWidth(120)
        server_layout.addRow(_("Port:"), self.llamacpp_port)
        
        self.llamacpp_timeout = QSpinBox()
        self.llamacpp_timeout.setRange(5, 300)
        self.llamacpp_timeout.setValue(30)
        self.llamacpp_timeout.setSuffix(" " + _("seconds"))
        self.llamacpp_timeout.setMinimumWidth(120)
        server_layout.addRow(_("Timeout:"), self.llamacpp_timeout)
        
        layout.addWidget(server_group)
        
        # Generation settings
        gen_group = QGroupBox(_("Generation Parameters"))
        gen_layout = QFormLayout(gen_group)
        gen_layout.setSpacing(8)
        
        self.llamacpp_max_tokens = QSpinBox()
        self.llamacpp_max_tokens.setRange(1, 4096)
        self.llamacpp_max_tokens.setValue(512)
        self.llamacpp_max_tokens.setMinimumWidth(120)
        gen_layout.addRow(_("Max Tokens:"), self.llamacpp_max_tokens)
        
        self.llamacpp_temperature = QDoubleSpinBox()
        self.llamacpp_temperature.setRange(0.0, 2.0)
        self.llamacpp_temperature.setSingleStep(0.1)
        self.llamacpp_temperature.setValue(0.7)
        self.llamacpp_temperature.setDecimals(2)
        self.llamacpp_temperature.setMinimumWidth(120)
        gen_layout.addRow(_("Temperature:"), self.llamacpp_temperature)
        
        self.llamacpp_top_p = QDoubleSpinBox()
        self.llamacpp_top_p.setRange(0.0, 1.0)
        self.llamacpp_top_p.setSingleStep(0.1)
        self.llamacpp_top_p.setValue(0.9)
        self.llamacpp_top_p.setDecimals(2)
        self.llamacpp_top_p.setMinimumWidth(120)
        gen_layout.addRow(_("Top P:"), self.llamacpp_top_p)
        
        self.llamacpp_top_k = QSpinBox()
        self.llamacpp_top_k.setRange(1, 100)
        self.llamacpp_top_k.setValue(40)
        self.llamacpp_top_k.setMinimumWidth(120)
        gen_layout.addRow(_("Top K:"), self.llamacpp_top_k)
        
        self.llamacpp_repeat_penalty = QDoubleSpinBox()
        self.llamacpp_repeat_penalty.setRange(0.5, 2.0)
        self.llamacpp_repeat_penalty.setSingleStep(0.1)
        self.llamacpp_repeat_penalty.setValue(1.1)
        self.llamacpp_repeat_penalty.setDecimals(2)
        self.llamacpp_repeat_penalty.setMinimumWidth(120)
        gen_layout.addRow(_("Repeat Penalty:"), self.llamacpp_repeat_penalty)
        
        layout.addWidget(gen_group)
        
        # Help text
        help_text = QLabel(_(
            "Configure your local llama.cpp server. Make sure the server is running "
            "with the --host and --port parameters matching these settings."
        ))
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666666; font-style: italic; margin-top: 10px; padding: 10px;")
        layout.addWidget(help_text)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Set widget to scroll area
        scroll_area.setWidget(widget)
        
        self.config_tabs.addTab(scroll_area, _("llama.cpp"))
    
    def setup_ollama_tab(self):
        """Setup Ollama configuration tab."""
        # Create scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Server settings
        server_group = QGroupBox(_("Server Configuration"))
        server_layout = QFormLayout(server_group)
        server_layout.setSpacing(8)
        
        self.ollama_host = QLineEdit()
        self.ollama_host.setPlaceholderText("192.168.1.102")
        self.ollama_host.setMinimumWidth(200)
        server_layout.addRow(_("Host:"), self.ollama_host)
        
        self.ollama_port = QSpinBox()
        self.ollama_port.setRange(1, 65535)
        self.ollama_port.setValue(11434)
        self.ollama_port.setMinimumWidth(120)
        server_layout.addRow(_("Port:"), self.ollama_port)
        
        self.ollama_timeout = QSpinBox()
        self.ollama_timeout.setRange(5, 300)
        self.ollama_timeout.setValue(30)
        self.ollama_timeout.setSuffix(" " + _("seconds"))
        self.ollama_timeout.setMinimumWidth(120)
        server_layout.addRow(_("Timeout:"), self.ollama_timeout)
        
        layout.addWidget(server_group)
        
        # Connection test for Ollama
        connection_group = QGroupBox(_("Connection"))
        connection_layout = QHBoxLayout(connection_group)
        
        self.ollama_test_btn = QPushButton(_("Test Connection & Fetch Models"))
        self.ollama_test_btn.clicked.connect(self.test_ollama_connection)
        self.ollama_test_btn.setToolTip(_("Test connection to Ollama server and automatically fetch available models"))
        connection_layout.addWidget(self.ollama_test_btn)
        
        self.ollama_connection_status = QLabel(_("Not connected"))
        self.ollama_connection_status.setStyleSheet("color: #666;")
        connection_layout.addWidget(self.ollama_connection_status)
        connection_layout.addStretch()
        
        layout.addWidget(connection_group)
        
        # Model settings
        model_group = QGroupBox(_("Model Configuration"))
        model_layout = QFormLayout(model_group)
        model_layout.setSpacing(8)
        
        # Model selection with dropdown and refresh
        model_row_layout = QHBoxLayout()
        self.ollama_model = QComboBox()
        self.ollama_model.setMinimumWidth(300)
        self.ollama_model.setEditable(False)  # Non-editable dropdown only
        self.ollama_model.setToolTip(_("Select Ollama model from dropdown"))
        # Add placeholder item to ensure dropdown appearance
        self.ollama_model.addItem(_("(No models loaded - click Refresh Models)"))
        model_row_layout.addWidget(self.ollama_model)
        
        self.ollama_refresh_models_btn = QPushButton(_("Refresh Models"))
        self.ollama_refresh_models_btn.setMaximumWidth(120)
        self.ollama_refresh_models_btn.clicked.connect(self.refresh_ollama_models)
        self.ollama_refresh_models_btn.setToolTip(_("Fetch available models from Ollama server"))
        model_row_layout.addWidget(self.ollama_refresh_models_btn)
        
        model_layout.addRow(_("Model:"), model_row_layout)
        
        layout.addWidget(model_group)
        
        # Generation settings
        gen_group = QGroupBox(_("Generation Parameters"))
        gen_layout = QFormLayout(gen_group)
        gen_layout.setSpacing(8)
        
        self.ollama_max_tokens = QSpinBox()
        self.ollama_max_tokens.setRange(1, 4096)
        self.ollama_max_tokens.setValue(512)
        self.ollama_max_tokens.setMinimumWidth(120)
        gen_layout.addRow(_("Max Tokens:"), self.ollama_max_tokens)
        
        self.ollama_temperature = QDoubleSpinBox()
        self.ollama_temperature.setRange(0.0, 2.0)
        self.ollama_temperature.setSingleStep(0.1)
        self.ollama_temperature.setValue(0.7)
        self.ollama_temperature.setDecimals(2)
        self.ollama_temperature.setMinimumWidth(120)
        gen_layout.addRow(_("Temperature:"), self.ollama_temperature)
        
        self.ollama_top_p = QDoubleSpinBox()
        self.ollama_top_p.setRange(0.0, 1.0)
        self.ollama_top_p.setSingleStep(0.1)
        self.ollama_top_p.setValue(0.9)
        self.ollama_top_p.setDecimals(2)
        self.ollama_top_p.setMinimumWidth(120)
        gen_layout.addRow(_("Top P:"), self.ollama_top_p)
        
        self.ollama_top_k = QSpinBox()
        self.ollama_top_k.setRange(1, 100)
        self.ollama_top_k.setValue(40)
        self.ollama_top_k.setMinimumWidth(120)
        gen_layout.addRow(_("Top K:"), self.ollama_top_k)
        
        self.ollama_repeat_penalty = QDoubleSpinBox()
        self.ollama_repeat_penalty.setRange(0.5, 2.0)
        self.ollama_repeat_penalty.setSingleStep(0.1)
        self.ollama_repeat_penalty.setValue(1.1)
        self.ollama_repeat_penalty.setDecimals(2)
        self.ollama_repeat_penalty.setMinimumWidth(120)
        gen_layout.addRow(_("Repeat Penalty:"), self.ollama_repeat_penalty)
        
        layout.addWidget(gen_group)
        
        # Help text
        help_text = QLabel(_(
            "Configure your Ollama server. Make sure Ollama is running and accessible "
            "at the specified host and port. Click 'Refresh Models' to fetch available models "
            "from the server, or type the model name manually if not in the list."
        ))
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666666; font-style: italic; margin-top: 10px; padding: 10px;")
        layout.addWidget(help_text)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Set widget to scroll area
        scroll_area.setWidget(widget)
        
        self.config_tabs.addTab(scroll_area, _("Ollama"))
    
    def setup_openai_tab(self):
        """Setup OpenAI configuration tab."""
        # Create scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # API settings
        api_group = QGroupBox(_("API Configuration"))
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(8)
        
        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.Password)
        self.openai_api_key.setPlaceholderText(_("Enter your OpenAI API key"))
        self.openai_api_key.setMinimumWidth(300)
        api_layout.addRow(_("API Key:"), self.openai_api_key)
        
        self.openai_model = QComboBox()
        self.openai_model.addItems(['gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'])
        self.openai_model.setMinimumWidth(200)
        api_layout.addRow(_("Model:"), self.openai_model)
        
        layout.addWidget(api_group)
        
        # Generation settings
        gen_group = QGroupBox(_("Generation Parameters"))
        gen_layout = QFormLayout(gen_group)
        gen_layout.setSpacing(8)
        
        self.openai_max_tokens = QSpinBox()
        self.openai_max_tokens.setRange(1, 4096)
        self.openai_max_tokens.setValue(512)
        self.openai_max_tokens.setMinimumWidth(120)
        gen_layout.addRow(_("Max Tokens:"), self.openai_max_tokens)
        
        self.openai_temperature = QDoubleSpinBox()
        self.openai_temperature.setRange(0.0, 2.0)
        self.openai_temperature.setSingleStep(0.1)
        self.openai_temperature.setValue(0.7)
        self.openai_temperature.setDecimals(2)
        self.openai_temperature.setMinimumWidth(120)
        gen_layout.addRow(_("Temperature:"), self.openai_temperature)
        
        self.openai_top_p = QDoubleSpinBox()
        self.openai_top_p.setRange(0.0, 1.0)
        self.openai_top_p.setSingleStep(0.1)
        self.openai_top_p.setValue(1.0)
        self.openai_top_p.setDecimals(2)
        self.openai_top_p.setMinimumWidth(120)
        gen_layout.addRow(_("Top P:"), self.openai_top_p)
        
        self.openai_presence_penalty = QDoubleSpinBox()
        self.openai_presence_penalty.setRange(-2.0, 2.0)
        self.openai_presence_penalty.setSingleStep(0.1)
        self.openai_presence_penalty.setValue(0.0)
        self.openai_presence_penalty.setDecimals(2)
        self.openai_presence_penalty.setMinimumWidth(120)
        gen_layout.addRow(_("Presence Penalty:"), self.openai_presence_penalty)
        
        self.openai_frequency_penalty = QDoubleSpinBox()
        self.openai_frequency_penalty.setRange(-2.0, 2.0)
        self.openai_frequency_penalty.setSingleStep(0.1)
        self.openai_frequency_penalty.setValue(0.0)
        self.openai_frequency_penalty.setDecimals(2)
        self.openai_frequency_penalty.setMinimumWidth(120)
        gen_layout.addRow(_("Frequency Penalty:"), self.openai_frequency_penalty)
        
        layout.addWidget(gen_group)
        
        # Help text
        help_text = QLabel(_(
            "Configure your OpenAI API key and model settings. You need a valid OpenAI API key "
            "from https://platform.openai.com/api-keys to use this provider."
        ))
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666666; font-style: italic; margin-top: 10px; padding: 10px;")
        layout.addWidget(help_text)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Set widget to scroll area
        scroll_area.setWidget(widget)
        
        self.config_tabs.addTab(scroll_area, _("OpenAI"))
    
    def setup_anthropic_tab(self):
        """Setup Anthropic configuration tab."""
        # Create scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # API settings
        api_group = QGroupBox(_("API Configuration"))
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(8)
        
        self.anthropic_api_key = QLineEdit()
        self.anthropic_api_key.setEchoMode(QLineEdit.Password)
        self.anthropic_api_key.setPlaceholderText(_("Enter your Anthropic API key"))
        self.anthropic_api_key.setMinimumWidth(300)
        api_layout.addRow(_("API Key:"), self.anthropic_api_key)
        
        self.anthropic_model = QComboBox()
        self.anthropic_model.addItems(['claude-3-sonnet-20240229', 'claude-3-opus-20240229'])
        self.anthropic_model.setMinimumWidth(200)
        api_layout.addRow(_("Model:"), self.anthropic_model)
        
        layout.addWidget(api_group)
        
        # Note about availability
        note_label = QLabel(_("Anthropic provider will be available in future versions"))
        note_label.setStyleSheet("color: #888888; font-style: italic; padding: 10px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Set widget to scroll area
        scroll_area.setWidget(widget)
        
        self.config_tabs.addTab(scroll_area, _("Anthropic"))
    
    def setup_mock_tab(self):
        """Setup mock provider configuration tab."""
        # Create scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Mock settings
        mock_group = QGroupBox(_("Mock Provider Settings"))
        mock_layout = QFormLayout(mock_group)
        mock_layout.setSpacing(8)
        
        self.mock_delay = QDoubleSpinBox()
        self.mock_delay.setRange(0.0, 5.0)
        self.mock_delay.setSingleStep(0.1)
        self.mock_delay.setValue(0.5)
        self.mock_delay.setDecimals(1)
        self.mock_delay.setSuffix(" " + _("seconds"))
        self.mock_delay.setMinimumWidth(120)
        mock_layout.addRow(_("Response Delay:"), self.mock_delay)
        
        layout.addWidget(mock_group)
        
        # Description
        desc_label = QLabel(_(
            "Mock provider is for testing purposes. It generates sample responses "
            "without connecting to any external service."
        ))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666; font-style: italic; padding: 10px;")
        layout.addWidget(desc_label)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Set widget to scroll area
        scroll_area.setWidget(widget)
        
        self.config_tabs.addTab(scroll_area, _("Mock"))
    
    def load_settings(self):
        """Load settings from the settings manager."""
        try:
            # Load available providers
            self.provider_combo.clear()
            for provider_name in self.settings_manager.get_available_providers():
                display_name = self.settings_manager.get_provider_display_name(provider_name)
                self.provider_combo.addItem(display_name, provider_name)
            
            # Set current provider
            current_provider = self.settings_manager.get_current_provider()
            index = self.provider_combo.findData(current_provider)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)
            
            # Load global settings
            context_length = self.settings_manager.get_context_length()
            self.context_length_spinbox.setValue(context_length)
            
            # Load provider-specific settings
            self.load_llamacpp_settings()
            self.load_ollama_settings()
            self.load_openai_settings()
            self.load_anthropic_settings()
            self.load_mock_settings()
            
            self.logger.debug("LLM settings loaded")
            
        except Exception as e:
            self.logger.error(f"Error loading LLM settings: {e}")
    
    def load_llamacpp_settings(self):
        """Load llama.cpp specific settings."""
        provider = self.settings_manager.get_provider_config('llamacpp')
        if provider:
            self.llamacpp_host.setText(provider.get_setting('host', 'localhost'))
            self.llamacpp_port.setValue(provider.get_setting('port', 8080))
            self.llamacpp_timeout.setValue(provider.get_setting('timeout', 30))
            self.llamacpp_max_tokens.setValue(provider.get_setting('max_tokens', 512))
            self.llamacpp_temperature.setValue(provider.get_setting('temperature', 0.7))
            self.llamacpp_top_p.setValue(provider.get_setting('top_p', 0.9))
            self.llamacpp_top_k.setValue(provider.get_setting('top_k', 40))
            self.llamacpp_repeat_penalty.setValue(provider.get_setting('repeat_penalty', 1.1))
    
    def load_ollama_settings(self):
        """Load Ollama specific settings."""
        provider = self.settings_manager.get_provider_config('ollama')
        if provider:
            self.ollama_host.setText(provider.get_setting('host', '192.168.1.102'))
            self.ollama_port.setValue(provider.get_setting('port', 11434))
            self.ollama_timeout.setValue(provider.get_setting('timeout', 30))
            
            # Handle model selection for combo box
            model = provider.get_setting('model', 'tom_himanen/deepseek-r1-roo-cline-tools:70b')
            index = self.ollama_model.findText(model)
            if index >= 0:
                self.ollama_model.setCurrentIndex(index)
            else:
                # Add model to dropdown if not present
                self.ollama_model.addItem(model)
                self.ollama_model.setCurrentIndex(self.ollama_model.count() - 1)
            
            self.ollama_max_tokens.setValue(provider.get_setting('max_tokens', 512))
            self.ollama_temperature.setValue(provider.get_setting('temperature', 0.7))
            self.ollama_top_p.setValue(provider.get_setting('top_p', 0.9))
            self.ollama_top_k.setValue(provider.get_setting('top_k', 40))
            self.ollama_repeat_penalty.setValue(provider.get_setting('repeat_penalty', 1.1))
            
            # Try to quietly load available models if dropdown only has placeholder
            if self.ollama_model.count() <= 1:
                try:
                    self._quietly_load_ollama_models()
                except Exception as e:
                    self.logger.debug(f"Could not auto-load Ollama models: {e}")
                    # If auto-loading fails, just keep the editable text
    
    def load_openai_settings(self):
        """Load OpenAI specific settings."""
        provider = self.settings_manager.get_provider_config('openai')
        if provider:
            self.openai_api_key.setText(provider.get_setting('api_key', ''))
            model = provider.get_setting('model', 'gpt-4')
            index = self.openai_model.findText(model)
            if index >= 0:
                self.openai_model.setCurrentIndex(index)
            self.openai_max_tokens.setValue(provider.get_setting('max_tokens', 512))
            self.openai_temperature.setValue(provider.get_setting('temperature', 0.7))
            self.openai_top_p.setValue(provider.get_setting('top_p', 1.0))
            self.openai_presence_penalty.setValue(provider.get_setting('presence_penalty', 0.0))
            self.openai_frequency_penalty.setValue(provider.get_setting('frequency_penalty', 0.0))
    
    def load_anthropic_settings(self):
        """Load Anthropic specific settings."""
        provider = self.settings_manager.get_provider_config('anthropic')
        if provider:
            self.anthropic_api_key.setText(provider.get_setting('api_key', ''))
            model = provider.get_setting('model', 'claude-3-sonnet-20240229')
            index = self.anthropic_model.findText(model)
            if index >= 0:
                self.anthropic_model.setCurrentIndex(index)
    
    def load_mock_settings(self):
        """Load mock provider specific settings."""
        provider = self.settings_manager.get_provider_config('mock')
        if provider:
            self.mock_delay.setValue(provider.get_setting('response_delay', 0.5))
    
    def on_provider_changed(self):
        """Handle provider selection change."""
        provider_name = self.provider_combo.currentData()
        if provider_name:
            # Switch to appropriate tab
            tab_mapping = {
                'llamacpp': 0,
                'ollama': 1,
                'openai': 2,
                'anthropic': 3,
                'mock': 4
            }
            
            tab_index = tab_mapping.get(provider_name, 0)
            self.config_tabs.setCurrentIndex(tab_index)
    
    def apply_settings(self):
        """Apply current settings to the settings manager."""
        try:
            # Apply global settings
            context_length = self.context_length_spinbox.value()
            self.settings_manager.set_context_length(context_length)
            
            # Set current provider
            provider_name = self.provider_combo.currentData()
            if provider_name:
                self.settings_manager.set_current_provider(provider_name)
            
            # Apply provider-specific settings
            self.apply_llamacpp_settings()
            self.apply_ollama_settings()
            self.apply_openai_settings()
            self.apply_anthropic_settings()
            self.apply_mock_settings()
            
            # Emit signal to notify about changes
            self.settings_changed.emit()
            
            self.logger.info("LLM settings applied")
            QMessageBox.information(self, _("Settings"), _("LLM settings have been applied successfully"))
            
        except Exception as e:
            self.logger.error(f"Error applying LLM settings: {e}")
            QMessageBox.critical(self, _("Error"), _("Failed to apply settings: {}").format(str(e)))
    
    def apply_llamacpp_settings(self):
        """Apply llama.cpp specific settings."""
        settings = {
            'host': self.llamacpp_host.text().strip() or 'localhost',
            'port': self.llamacpp_port.value(),
            'timeout': self.llamacpp_timeout.value(),
            'max_tokens': self.llamacpp_max_tokens.value(),
            'temperature': self.llamacpp_temperature.value(),
            'top_p': self.llamacpp_top_p.value(),
            'top_k': self.llamacpp_top_k.value(),
            'repeat_penalty': self.llamacpp_repeat_penalty.value()
        }
        
        for key, value in settings.items():
            self.settings_manager.update_provider_setting('llamacpp', key, value)
    
    def apply_ollama_settings(self):
        """Apply Ollama specific settings."""
        settings = {
            'host': self.ollama_host.text().strip() or '192.168.1.102',
            'port': self.ollama_port.value(),
            'timeout': self.ollama_timeout.value(),
            'model': self.ollama_model.currentText().strip() if not self.ollama_model.currentText().startswith("(No models loaded") else '',
            'max_tokens': self.ollama_max_tokens.value(),
            'temperature': self.ollama_temperature.value(),
            'top_p': self.ollama_top_p.value(),
            'top_k': self.ollama_top_k.value(),
            'repeat_penalty': self.ollama_repeat_penalty.value()
        }
        
        for key, value in settings.items():
            self.settings_manager.update_provider_setting('ollama', key, value)
    
    def apply_openai_settings(self):
        """Apply OpenAI specific settings."""
        settings = {
            'api_key': self.openai_api_key.text().strip(),
            'model': self.openai_model.currentText(),
            'max_tokens': self.openai_max_tokens.value(),
            'temperature': self.openai_temperature.value(),
            'top_p': self.openai_top_p.value(),
            'presence_penalty': self.openai_presence_penalty.value(),
            'frequency_penalty': self.openai_frequency_penalty.value()
        }
        
        for key, value in settings.items():
            self.settings_manager.update_provider_setting('openai', key, value)
    
    def apply_anthropic_settings(self):
        """Apply Anthropic specific settings."""
        settings = {
            'api_key': self.anthropic_api_key.text().strip(),
            'model': self.anthropic_model.currentText()
        }
        
        for key, value in settings.items():
            self.settings_manager.update_provider_setting('anthropic', key, value)
    
    def apply_mock_settings(self):
        """Apply mock provider specific settings."""
        settings = {
            'response_delay': self.mock_delay.value()
        }
        
        for key, value in settings.items():
            self.settings_manager.update_provider_setting('mock', key, value)
    
    def test_connection(self):
        """Test connection to the selected provider."""
        provider_name = self.provider_combo.currentData()
        if not provider_name:
            return
        
        # Apply current settings before testing
        self.apply_settings()
        
        # Start test
        self.test_button.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # Indeterminate
        self.test_result.setText(_("Testing connection..."))
        self.test_result.setStyleSheet("color: #666666;")
        
        # Run test in thread
        self.test_thread = LLMConnectionTestThread(provider_name)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.start()
    
    def on_test_finished(self, success: bool, message: str):
        """Handle connection test completion."""
        self.test_button.setEnabled(True)
        self.test_progress.setVisible(False)
        
        if success:
            self.test_result.setText(f"✓ {message}")
            self.test_result.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.test_result.setText(f"✗ {message}")
            self.test_result.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        if self.test_thread:
            self.test_thread.deleteLater()
            self.test_thread = None
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, _("Reset Settings"),
            _("Are you sure you want to reset all LLM settings to defaults?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset settings manager to defaults
            self.settings_manager._initialize_default_providers()
            self.load_settings()
            self.logger.info("LLM settings reset to defaults")
    
    def _quietly_load_ollama_models(self):
        """Quietly load Ollama models without showing messages."""
        try:
            # Apply current host/port settings first
            host = self.ollama_host.text().strip() or "192.168.1.102"
            port = self.ollama_port.value()
            timeout = self.ollama_timeout.value()
            
            # Store current selection
            current_model = self.ollama_model.currentText()
            
            # Fetch models
            models = self._fetch_ollama_models(host, port, timeout)
            
            # Update combo box
            self.ollama_model.clear()
            
            if models:
                for model in models:
                    # Add model with name and additional info as tooltip
                    model_name = model.get('name', '')
                    model_size = model.get('size', 0)
                    model_modified = model.get('modified_at', '')
                    
                    self.ollama_model.addItem(model_name)
                    
                    # Set tooltip with additional info
                    if model_size > 0:
                        size_gb = model_size / (1024**3)
                        tooltip = f"Size: {size_gb:.1f}GB"
                        if model_modified:
                            tooltip += f"\nModified: {model_modified[:10]}"
                        self.ollama_model.setItemData(
                            self.ollama_model.count() - 1, 
                            tooltip, 
                            Qt.ItemDataRole.ToolTipRole
                        )
                
                # Restore previous selection if it exists
                if current_model and not current_model.startswith("(No models loaded"):
                    index = self.ollama_model.findText(current_model)
                    if index >= 0:
                        self.ollama_model.setCurrentIndex(index)
                    else:
                        # Add the current model to dropdown
                        self.ollama_model.addItem(current_model)
                        self.ollama_model.setCurrentIndex(self.ollama_model.count() - 1)
                
                self.logger.debug(f"Quietly loaded {len(models)} Ollama models")
            else:
                # No models found, add placeholder and current model
                self.ollama_model.addItem(_("(No models loaded - click Refresh Models)"))
                if current_model and not current_model.startswith("(No models loaded"):
                    self.ollama_model.addItem(current_model)
                    self.ollama_model.setCurrentIndex(self.ollama_model.count() - 1)
                
        except Exception as e:
            self.logger.debug(f"Could not quietly load Ollama models: {e}")
            # Silent failure, add placeholder and keep current model
            self.ollama_model.addItem(_("(No models loaded - click Refresh Models)"))
            if current_model and not current_model.startswith("(No models loaded"):
                self.ollama_model.addItem(current_model)
                self.ollama_model.setCurrentIndex(self.ollama_model.count() - 1)

    def refresh_ollama_models(self):
        """Fetch available models from Ollama server."""
        try:
            # Apply current host/port settings first
            host = self.ollama_host.text().strip() or "192.168.1.102"
            port = self.ollama_port.value()
            timeout = self.ollama_timeout.value()
            
            self.ollama_refresh_models_btn.setEnabled(False)
            self.ollama_refresh_models_btn.setText(_("Fetching..."))
            
            # Store current selection
            current_model = self.ollama_model.currentText()
            
            # Fetch models
            models = self._fetch_ollama_models(host, port, timeout)
            
            # Update combo box
            self.ollama_model.clear()
            
            if models:
                for model in models:
                    # Add model with name and additional info as tooltip
                    model_name = model.get('name', '')
                    model_size = model.get('size', 0)
                    model_modified = model.get('modified_at', '')
                    
                    self.ollama_model.addItem(model_name)
                    
                    # Set tooltip with additional info
                    if model_size > 0:
                        size_gb = model_size / (1024**3)
                        tooltip = f"Size: {size_gb:.1f}GB"
                        if model_modified:
                            tooltip += f"\nModified: {model_modified[:10]}"
                        self.ollama_model.setItemData(
                            self.ollama_model.count() - 1, 
                            tooltip, 
                            Qt.ItemDataRole.ToolTipRole
                        )
                
                # Restore previous selection if it exists
                if current_model and not current_model.startswith("(No models loaded"):
                    index = self.ollama_model.findText(current_model)
                    if index >= 0:
                        self.ollama_model.setCurrentIndex(index)
                    else:
                        # Add the current model to dropdown
                        self.ollama_model.addItem(current_model)
                        self.ollama_model.setCurrentIndex(self.ollama_model.count() - 1)
                
                self.logger.info(f"Loaded {len(models)} Ollama models")
                QMessageBox.information(
                    self, 
                    _("Success"), 
                    _("Loaded {} models from Ollama server").format(len(models))
                )
            else:
                self.logger.warning("No models found on Ollama server")
                QMessageBox.warning(
                    self, 
                    _("Warning"), 
                    _("No models found on Ollama server. Make sure models are installed.")
                )
            
        except Exception as e:
            self.logger.error(f"Error fetching Ollama models: {e}")
            QMessageBox.critical(
                self, 
                _("Error"), 
                _("Failed to fetch models from Ollama server:\n{}").format(str(e))
            )
        finally:
            self.ollama_refresh_models_btn.setEnabled(True)
            self.ollama_refresh_models_btn.setText(_("Refresh Models"))
    
    def _fetch_ollama_models(self, host: str, port: int, timeout: int) -> list:
        """Fetch models from Ollama server."""
        import requests
        from urllib.parse import urljoin
        
        try:
            base_url = f"http://{host}:{port}"
            response = requests.get(
                urljoin(base_url, "/api/tags"),
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('models', [])
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {e}")
        except Exception as e:
            raise Exception(f"Failed to fetch models: {e}")
    
    def test_ollama_connection(self):
        """Test Ollama connection and fetch models automatically."""
        try:
            # Update connection status
            self.ollama_connection_status.setText(_("Testing..."))
            self.ollama_connection_status.setStyleSheet("color: #666;")
            self.ollama_test_btn.setEnabled(False)
            
            # Get connection parameters
            host = self.ollama_host.text().strip() or "192.168.1.102"
            port = self.ollama_port.value()
            timeout = self.ollama_timeout.value()
            
            # Test connection first
            models = self._fetch_ollama_models(host, port, timeout)
            
            # Connection successful - update status
            self.ollama_connection_status.setText(_("Connected - {} models found").format(len(models)))
            self.ollama_connection_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            # Update model dropdown
            current_model = self.ollama_model.currentText()
            self.ollama_model.clear()
            
            if models:
                for model in models:
                    model_name = model.get('name', '')
                    model_size = model.get('size', 0)
                    model_modified = model.get('modified_at', '')
                    
                    self.ollama_model.addItem(model_name)
                    
                    # Set tooltip with additional info
                    if model_size > 0:
                        size_gb = model_size / (1024**3)
                        tooltip = f"Size: {size_gb:.1f}GB"
                        if model_modified:
                            tooltip += f"\nModified: {model_modified[:10]}"
                        self.ollama_model.setItemData(
                            self.ollama_model.count() - 1, 
                            tooltip, 
                            Qt.ItemDataRole.ToolTipRole
                        )
                
                # Restore previous selection
                if current_model and not current_model.startswith("(No models loaded"):
                    index = self.ollama_model.findText(current_model)
                    if index >= 0:
                        self.ollama_model.setCurrentIndex(index)
                    else:
                        self.ollama_model.setEditText(current_model)
            
            self.logger.info(f"Successfully connected to Ollama at {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Ollama connection test failed: {e}")
            self.ollama_connection_status.setText(_("Connection failed"))
            self.ollama_connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            QMessageBox.warning(
                self,
                _("Connection Failed"),
                _("Failed to connect to Ollama server:\n{}").format(str(e))
            )
        finally:
            self.ollama_test_btn.setEnabled(True)