"""Base dialog widget with common styling and behavior."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .enhanced_theme_manager import EnhancedThemeManager
from .ui_font_manager import UIFontManager
from i18n import _


class BaseDialog(QDialog):
    """Base dialog widget with common styling and behavior."""
    
    def __init__(self, title="Dialog", width=400, height=300, modal=True, parent=None):
        super().__init__(parent)
        self.theme_manager = EnhancedThemeManager()
        self.font_manager = UIFontManager()
        self.setup_base_ui(title, width, height, modal)
        self.apply_theme()
        
    def setup_base_ui(self, title, width, height, modal):
        """Setup base dialog UI with common styling."""
        self.setWindowTitle(title)
        self.setMinimumSize(width, height)
        self.setModal(modal)
        
        # Set window flags for non-modal dialogs
        if not modal:
            self.setWindowFlags(
                Qt.Window | 
                Qt.WindowStaysOnTopHint | 
                Qt.WindowCloseButtonHint | 
                Qt.WindowMinimizeButtonHint
            )
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Content area (to be filled by subclasses)
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)
        
        # Button area
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        
    def apply_theme(self):
        """Apply theme styling to the dialog."""
        colors = self.theme_manager.get_theme_colors()
        
        self.setStyleSheet(f"""
            BaseDialog {{
                background-color: {colors["background"]};
                color: {colors["text"]};
            }}
            QPushButton {{
                background-color: {colors["button_background"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["button_pressed"]};
            }}
        """)
    
    def refresh_theme(self):
        """Refresh theme styling."""
        self.apply_theme()
        
    def add_content_widget(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)
        
    def add_content_layout(self, layout):
        """Add a layout to the content area."""
        self.content_layout.addLayout(layout)
        
    def add_stretch(self):
        """Add a stretch to the content area."""
        self.content_layout.addStretch()
        
    def create_button_box(self, buttons=None):
        """Create a standard button box."""
        if buttons is None:
            buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        self.button_layout.addWidget(button_box)
        return button_box
        
    def create_custom_button(self, text, callback=None, style="primary"):
        """Create a custom styled button."""
        button = QPushButton(text)
        
        if callback:
            button.clicked.connect(callback)
            
        # Apply button-specific styling
        colors = self.theme_manager.get_theme_colors()
        if style == "primary":
            button.setStyleSheet(f"""
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
        elif style == "secondary":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors["secondary_button"]};
                    color: {colors["text"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {colors["secondary_button_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["secondary_button_pressed"]};
                }}
            """)
        elif style == "danger":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors["danger"]};
                    color: white;
                    border: 1px solid {colors["danger"]};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {colors["danger_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["danger_pressed"]};
                }}
            """)
        
        return button
        
    def add_button(self, button):
        """Add a button to the button area."""
        self.button_layout.addWidget(button)
        
    def add_button_stretch(self):
        """Add a stretch to the button area."""
        self.button_layout.addStretch()
    
    def create_section_title(self, text, font_size=14):
        """Create a section title label."""
        from PySide6.QtWidgets import QLabel
        label = QLabel(text)
        label.setFont(self.font_manager.get_font(size=font_size, weight=QFont.Weight.Bold))
        
        colors = self.theme_manager.get_theme_colors()
        label.setStyleSheet(f"color: {colors['heading']}; margin-top: 10px;")
        
        return label
    
    def get_muted_text_style(self):
        """Get muted text style for secondary information."""
        colors = self.theme_manager.get_theme_colors()
        return f"color: {colors.get('muted_text', '#666666')}; font-size: 11px;"
    
    def get_small_muted_text_style(self):
        """Get small muted text style for hints and references."""
        colors = self.theme_manager.get_theme_colors()
        return f"color: {colors.get('muted_text', '#666666')}; font-size: 10px;"
    
    def get_help_text_style(self):
        """Get help text style for guidance information."""
        colors = self.theme_manager.get_theme_colors()
        return f"color: {colors.get('muted_text', '#666666')}; padding: 5px;"
    
    def get_muted_background_style(self):
        """Get muted background style for preview areas."""
        colors = self.theme_manager.get_theme_colors()
        return f"""background-color: {colors.get('input_background', '#f8f9fa')};
                 border: 1px solid {colors.get('border', '#dee2e6')};
                 border-radius: 4px;
                 padding: 8px;"""
    
    def create_tab_widget(self):
        """Create a standard tab widget with theme styling."""
        from PySide6.QtWidgets import QTabWidget
        tab_widget = QTabWidget()
        
        # Apply theme styling to tab widget
        colors = self.theme_manager.get_theme_colors()
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {colors.get('border', '#cccccc')};
                background-color: {colors.get('background', '#ffffff')};
            }}
            QTabBar::tab {{
                background-color: {colors.get('tab_background', '#f0f0f0')};
                color: {colors.get('text', '#000000')};
                border: 1px solid {colors.get('border', '#cccccc')};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors.get('background', '#ffffff')};
                border-bottom: 1px solid {colors.get('background', '#ffffff')};
            }}
            QTabBar::tab:hover {{
                background-color: {colors.get('tab_hover', '#e0e0e0')};
            }}
        """)
        
        return tab_widget
    
    def create_form_section(self, title, parent_layout=None):
        """Create a form section with title and form layout."""
        from PySide6.QtWidgets import QGroupBox, QFormLayout
        
        group = QGroupBox(title)
        form_layout = QFormLayout(group)
        form_layout.setSpacing(12)
        
        # Apply theme styling to group box
        colors = self.theme_manager.get_theme_colors()
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {colors.get('heading', '#2c3e50')};
                border: 1px solid {colors.get('border', '#cccccc')};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        if parent_layout:
            parent_layout.addWidget(group)
        
        return group, form_layout
    
    def create_info_label(self, text, style="muted"):
        """Create an info label with predefined styling."""
        from PySide6.QtWidgets import QLabel
        label = QLabel(text)
        label.setWordWrap(True)
        
        if style == "muted":
            label.setStyleSheet(self.get_muted_text_style())
        elif style == "small_muted":
            label.setStyleSheet(self.get_small_muted_text_style())
        elif style == "help":
            label.setStyleSheet(self.get_help_text_style())
        
        return label
    
    def create_parameter_row(self, min_val, max_val, default_val, param_name, value_changed_callback=None, use_default_callback=None):
        """Create a parameter row with spinbox, default button, and reference label."""
        from PySide6.QtWidgets import QHBoxLayout, QSpinBox, QLabel
        
        layout = QHBoxLayout()
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default_val)
        if value_changed_callback:
            spin.valueChanged.connect(value_changed_callback)
        layout.addWidget(spin)
        
        if use_default_callback:
            default_btn = self.create_custom_button(_("Use Default"), use_default_callback, "secondary")
            layout.addWidget(default_btn)
        
        ref_label = QLabel()
        ref_label.setStyleSheet(self.get_small_muted_text_style())
        layout.addWidget(ref_label)
        layout.addStretch()
        
        return layout, spin, ref_label
    
    def create_double_parameter_row(self, min_val, max_val, step, decimals, default_val, param_name, use_default_callback=None):
        """Create a parameter row with double spinbox, default button, and reference label."""
        from PySide6.QtWidgets import QHBoxLayout, QDoubleSpinBox, QLabel
        
        layout = QHBoxLayout()
        
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setDecimals(decimals)
        spin.setValue(default_val)
        layout.addWidget(spin)
        
        if use_default_callback:
            default_btn = self.create_custom_button(_("Use Default"), use_default_callback, "secondary")
            layout.addWidget(default_btn)
        
        ref_label = QLabel()
        ref_label.setStyleSheet(self.get_small_muted_text_style())
        layout.addWidget(ref_label)
        layout.addStretch()
        
        return layout, spin, ref_label
    
    def create_text_input(self, placeholder="", max_height=None):
        """Create a styled text input widget."""
        from PySide6.QtWidgets import QTextEdit
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText(placeholder)
        if max_height:
            text_edit.setMaximumHeight(max_height)
        
        # Apply theme styling
        colors = self.theme_manager.get_theme_colors()
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {colors.get('border', '#dee2e6')};
                border-radius: 4px;
                padding: 8px;
                background-color: {colors.get('input_background', '#ffffff')};
                color: {colors.get('text', '#000000')};
            }}
            QTextEdit:focus {{
                border-color: {colors.get('accent', '#007acc')};
            }}
        """)
        
        return text_edit
    
    def create_line_input(self, placeholder=""):
        """Create a styled line input widget."""
        from PySide6.QtWidgets import QLineEdit
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        
        # Apply theme styling
        colors = self.theme_manager.get_theme_colors()
        line_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {colors.get('border', '#dee2e6')};
                border-radius: 4px;
                padding: 8px;
                background-color: {colors.get('input_background', '#ffffff')};
                color: {colors.get('text', '#000000')};
            }}
            QLineEdit:focus {{
                border-color: {colors.get('accent', '#007acc')};
            }}
        """)
        
        return line_edit
    
    def create_search_widget(self, placeholder="Search...", filter_callback=None):
        """Create a search widget with QLineEdit and filter callback."""
        from PySide6.QtWidgets import QHBoxLayout, QLabel
        
        search_layout = QHBoxLayout()
        search_label = QLabel(_("Search:"))
        search_input = self.create_line_input(placeholder)
        
        if filter_callback:
            search_input.textChanged.connect(filter_callback)
            
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        
        return search_layout, search_input
    
    def create_selection_list_widget(self, double_click_callback=None, selection_changed_callback=None):
        """Create a list widget with selection management and optional callbacks."""
        from PySide6.QtWidgets import QListWidget
        from PySide6.QtCore import Qt
        
        list_widget = QListWidget()
        list_widget.setFont(self.font_manager.get_font(10))
        
        # Apply theme styling
        colors = self.theme_manager.get_theme_colors()
        list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {colors.get('border', '#dee2e6')};
                border-radius: 4px;
                background-color: {colors.get('input_background', '#ffffff')};
                color: {colors.get('text', '#000000')};
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {colors.get('border', '#eee')};
            }}
            QListWidget::item:selected {{
                background-color: {colors.get('accent', '#007acc')};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {colors.get('hover_background', '#f0f0f0')};
            }}
        """)
        
        if double_click_callback:
            list_widget.itemDoubleClicked.connect(double_click_callback)
        if selection_changed_callback:
            list_widget.itemSelectionChanged.connect(selection_changed_callback)
            
        return list_widget
    
    def create_standard_buttons(self, save_text=None, save_callback=None, cancel_text=None, cancel_callback=None, extra_buttons=None):
        """Create standard dialog buttons with consistent layout."""
        if save_text is None:
            save_text = _("Save")
        if cancel_text is None:
            cancel_text = _("Cancel")
        if cancel_callback is None:
            cancel_callback = self.reject
            
        # Add stretch before buttons
        self.add_button_stretch()
        
        # Add extra buttons first (left side)
        buttons = {}
        if extra_buttons:
            for button_text, callback, style in extra_buttons:
                btn = self.create_custom_button(button_text, callback, style)
                self.add_button(btn)
                buttons[button_text.lower().replace(' ', '_')] = btn
        
        # Add another stretch to separate action buttons from standard buttons
        if extra_buttons:
            self.add_button_stretch()
        
        # Cancel button
        cancel_btn = self.create_custom_button(cancel_text, cancel_callback, "secondary")
        self.add_button(cancel_btn)
        buttons['cancel'] = cancel_btn
        
        # Save button
        save_btn = self.create_custom_button(save_text, save_callback or self.accept, "primary")
        save_btn.setDefault(True)
        self.add_button(save_btn)
        buttons['save'] = save_btn
        
        return buttons
    
    def create_splitter(self, orientation, widgets, sizes=None):
        """Create a splitter with widgets and optional size proportions."""
        from PySide6.QtWidgets import QSplitter
        from PySide6.QtCore import Qt
        
        splitter = QSplitter(orientation)
        
        for widget in widgets:
            splitter.addWidget(widget)
            
        if sizes:
            splitter.setSizes(sizes)
            
        return splitter
    
    def add_validation_rule(self, field_name, field_widget, validator_func, error_message=""):
        """Add a validation rule for a form field."""
        if not hasattr(self, '_validation_rules'):
            self._validation_rules = {}
            
        self._validation_rules[field_name] = {
            'widget': field_widget,
            'validator': validator_func,
            'error': error_message
        }
    
    def validate_form(self):
        """Validate all registered form fields and return validation errors."""
        if not hasattr(self, '_validation_rules'):
            return []
            
        errors = []
        for field_name, rule in self._validation_rules.items():
            widget = rule['widget']
            validator = rule['validator']
            error_msg = rule['error']
            
            # Get field value based on widget type
            if hasattr(widget, 'text'):
                value = widget.text().strip()
            elif hasattr(widget, 'toPlainText'):
                value = widget.toPlainText().strip()
            elif hasattr(widget, 'value'):
                value = widget.value()
            elif hasattr(widget, 'currentText'):
                value = widget.currentText().strip()
            else:
                continue
                
            if not validator(value):
                errors.append(error_msg or f"{field_name} validation failed")
                
        return errors
    
    def handle_operation(self, operation_func, success_msg=None, error_msg=None, success_callback=None):
        """Handle an operation with consistent error handling and user feedback."""
        from PySide6.QtWidgets import QMessageBox
        
        try:
            result = operation_func()
            
            if result is not False:  # Allow None, but treat False as failure
                if success_msg:
                    QMessageBox.information(self, _("Success"), success_msg)
                if success_callback:
                    success_callback(result)
                return True
            else:
                if error_msg:
                    QMessageBox.critical(self, _("Error"), error_msg)
                return False
                
        except Exception as e:
            error_text = error_msg or _("An error occurred: {}").format(str(e))
            QMessageBox.critical(self, _("Error"), error_text)
            return False
    
    def load_data_to_fields(self, data, field_mappings):
        """Load data to form fields using field mappings."""
        if not data:
            return
            
        for field_widget, data_key, default_value in field_mappings:
            try:
                if isinstance(data, dict):
                    value = data.get(data_key, default_value)
                else:
                    value = getattr(data, data_key, default_value)
                
                # Set value based on widget type
                if hasattr(field_widget, 'setText'):
                    field_widget.setText(str(value or ''))
                elif hasattr(field_widget, 'setPlainText'):
                    field_widget.setPlainText(str(value or ''))
                elif hasattr(field_widget, 'setValue'):
                    field_widget.setValue(value if value is not None else default_value)
                elif hasattr(field_widget, 'setCurrentText'):
                    field_widget.setCurrentText(str(value or ''))
                elif hasattr(field_widget, 'setChecked'):
                    field_widget.setChecked(bool(value))
                    
            except Exception as e:
                # Log error but continue loading other fields
                print(f"Warning: Could not load field {data_key}: {e}")
    
    def add_shortcut(self, key_sequence, callback):
        """Add a keyboard shortcut to the dialog."""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        shortcut = QShortcut(QKeySequence(key_sequence), self)
        shortcut.activated.connect(callback)
        return shortcut