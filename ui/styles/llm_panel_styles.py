"""Style manager for LLM Assistant Panel - centralizes all inline styles."""

from typing import Dict, Any


class UIStyleManager:
    """Manages all UI styles for the LLM Assistant Panel components."""
    
    @staticmethod
    def get_enhanced_task_button_styles() -> Dict[str, str]:
        """Get styles for EnhancedTaskButton states."""
        return {
            'normal': """
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #5cb85c, stop: 1 #449d44);
                    color: white;
                    border: 1px solid #419241;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                    text-align: center;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #6bc56b, stop: 1 #4cae4c);
                    border-color: #52b852;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #449d44, stop: 1 #398a39);
                    border-color: #357a35;
                }
                QPushButton:disabled {
                    background: #e0e0e0;
                    color: #888888;
                    border-color: #cccccc;
                }
            """,
            'executing': """
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #f0ad4e, stop: 1 #ec971f);
                    color: white;
                    border: 1px solid #eb9316;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                }
            """
        }
    
    @staticmethod
    def get_response_area_styles() -> Dict[str, str]:
        """Get styles for EnhancedResponseArea components."""
        return {
            'response_label': """
                QLabel {
                    font-weight: bold; 
                    color: #2c3e50;
                    font-size: 10pt;
                    padding: 2px 0px;
                }
            """,
            'word_count_label': """
                QLabel {
                    color: #6c757d;
                    font-size: 8pt;
                    font-style: italic;
                }
            """,
            'response_text': """
                QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 10pt;
                    selection-background-color: #007acc;
                    selection-color: white;
                }
            """,
            'response_text_streaming': """
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 2px solid #007acc;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 10pt;
                }
            """
        }
    
    @staticmethod
    def get_control_section_styles() -> Dict[str, str]:
        """Get styles for control section components."""
        return {
            'title_label': """
                QLabel {
                    font-weight: bold;
                    font-size: 11pt;
                    color: #2c3e50;
                    padding: 5px 0px;
                }
            """,
            'status_label': """
                QLabel {
                    font-size: 9pt;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-weight: normal;
                }
            """,
            'task_combo': """
                QComboBox {
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 10pt;
                    background-color: white;
                    min-height: 20px;
                }
                QComboBox:focus {
                    border-color: #007acc;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-style: solid;
                    border-width: 4px 4px 0px 4px;
                    border-color: #6c757d transparent transparent transparent;
                }
            """,
            'content_label': """
                QLabel {
                    font-weight: bold;
                    font-size: 10pt;
                    color: #495057;
                    padding: 2px 0px;
                }
            """,
            'content_source_combo': """
                QComboBox {
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 9pt;
                    background-color: white;
                    min-height: 18px;
                }
                QComboBox:focus {
                    border-color: #007acc;
                }
            """
        }
    
    @staticmethod
    def get_execution_section_styles() -> Dict[str, str]:
        """Get styles for execution section components."""
        return {
            'title_label': """
                QLabel {
                    font-weight: bold;
                    font-size: 11pt;
                    color: #2c3e50;
                    padding: 5px 0px;
                }
            """,
            'status_label': """
                QLabel {
                    font-size: 9pt;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-weight: normal;
                }
            """,
            'progress_bar': """
                QProgressBar {
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    text-align: center;
                    font-size: 9pt;
                    background-color: #f8f9fa;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #007acc, stop: 1 #0056b3);
                    border-radius: 3px;
                }
            """,
            'tasks_widget': """
                QWidget {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    padding: 10px;
                    margin: 5px 0px;
                }
            """,
            'template_editor_btn': """
                QPushButton {
                    background-color: #6f42c1;
                    color: white;
                    border: 1px solid #6f42c1;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 9pt;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a359a;
                    border-color: #5a359a;
                }
                QPushButton:pressed {
                    background-color: #4e2a84;
                    border-color: #4e2a84;
                }
            """,
            'future_tasks_label': """
                QLabel {
                    font-weight: bold;
                    font-size: 10pt;
                    color: #6c757d;
                    padding: 8px 0px 4px 0px;
                    font-style: italic;
                }
            """
        }
    
    @staticmethod
    def get_status_styles() -> Dict[str, str]:
        """Get status-specific styles with color coding."""
        return {
            'ready': """
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            """,
            'processing': """
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            """,
            'completed': """
                background-color: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            """,
            'error': """
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            """,
            'warning': """
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            """
        }
    
    @staticmethod
    def get_additional_styles() -> Dict[str, str]:
        """Get additional component styles found in the actual UI."""
        return {
            'ai_assistant_title': """
                QLabel {
                    color: #2c3e50;
                    font-size: 12pt;
                    font-weight: bold;
                    padding: 4px 8px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
            """,
            'ready_status': """
                QLabel {
                    color: #28a745;
                    font-size: 9pt;
                    padding: 2px 6px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    font-weight: normal;
                }
            """
        }
    
    @staticmethod 
    def get_header_section_styles() -> Dict[str, str]:
        """Get styles for header section components."""
        return {
            'writing_assistant_title': """
                QLabel {
                    color: #2c3e50;
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #f8f9fa, stop: 1 #e9ecef);
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px;
                }
            """,
            'header_status_label': """
                QLabel {
                    color: #28a745;
                    font-size: 10pt;
                    font-weight: 500;
                    padding: 4px 8px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                }
            """,
            'header_progress_bar': """
                QProgressBar {
                    border: none;
                    border-radius: 3px;
                    background-color: #e9ecef;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #007acc, stop: 1 #0056b3);
                    border-radius: 3px;
                }
            """
        }
    
    @staticmethod
    def get_tasks_section_styles() -> Dict[str, str]:
        """Get styles for tasks section components."""
        return {
            'tasks_group_box': """
                QGroupBox {
                    font-weight: bold;
                    font-size: 11pt;
                    color: #495057;
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 8px;
                    background-color: white;
                }
            """,
            'template_editor_button': """
                QPushButton {
                    background-color: #8e44ad;
                    color: white;
                    border: none;
                    padding: 10px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #9b59b6;
                }
                QPushButton:pressed {
                    background-color: #7d3c98;
                }
            """,
            'future_tasks_placeholder': """
                QLabel {
                    color: #6c757d;
                    font-size: 9pt;
                    font-style: italic;
                    text-align: center;
                    padding: 8px;
                    background-color: #f8f9fa;
                    border: 1px dashed #dee2e6;
                    border-radius: 6px;
                }
            """
        }
    
    @staticmethod
    def get_dynamic_status_styles() -> Dict[str, str]:
        """Get dynamic status styles with base styling."""
        return {
            'base': """
                font-size: 10pt;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 4px;
            """,
            'success_content': """
                QLabel {
                    color: #155724;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                }
            """,
            'error_content': """
                QLabel {
                    color: #721c24;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                }
            """,
            'warning_content': """
                QLabel {
                    color: #856404;
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                }
            """,
            'processing_content': """
                QLabel {
                    color: #004085;
                    background-color: #cce7ff;
                    border: 1px solid #b8daff;
                }
            """,
            'info_content': """
                QLabel {
                    color: #0c5460;
                    background-color: #d1ecf1;
                    border: 1px solid #bee5eb;
                }
            """
        }
    
    @staticmethod
    def get_updated_control_section_styles() -> Dict[str, str]:
        """Get updated control section styles with new task combo styling."""
        return {
            'compact_task_combo': """
                QComboBox {
                    padding: 6px;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    background-color: white;
                }
            """,
            'content_source_label': """
                QLabel {
                    color: #495057;
                    font-size: 9pt;
                    font-weight: bold;
                    margin-top: 8px;
                    margin-bottom: 2px;
                }
            """,
            'compact_content_source_combo': """
                QComboBox {
                    padding: 4px 6px;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    background-color: white;
                    font-size: 9pt;
                }
            """
        }
    
    @classmethod
    def apply_additional_style(cls, widget, style_name: str):
        """Apply additional style to widget."""
        styles = cls.get_additional_styles()
        if style_name not in styles:
            raise ValueError(f"Unknown additional style: {style_name}. Available: {list(styles.keys())}")
        widget.setStyleSheet(styles[style_name])
    
    @classmethod
    def apply_enhanced_task_button_style(cls, button, state: str = 'normal'):
        """Apply style to EnhancedTaskButton."""
        styles = cls.get_enhanced_task_button_styles()
        if state not in styles:
            raise ValueError(f"Unknown button state: {state}. Available: {list(styles.keys())}")
        button.setStyleSheet(styles[state])
    
    @classmethod
    def apply_response_area_style(cls, widget, component: str):
        """Apply style to ResponseArea component."""
        styles = cls.get_response_area_styles()
        if component not in styles:
            raise ValueError(f"Unknown response area component: {component}. Available: {list(styles.keys())}")
        widget.setStyleSheet(styles[component])
    
    @classmethod
    def apply_control_section_style(cls, widget, component: str):
        """Apply style to control section component."""
        styles = cls.get_control_section_styles()
        if component not in styles:
            raise ValueError(f"Unknown control section component: {component}. Available: {list(styles.keys())}")
        widget.setStyleSheet(styles[component])
    
    @classmethod
    def apply_execution_section_style(cls, widget, component: str):
        """Apply style to execution section component."""
        styles = cls.get_execution_section_styles()
        if component not in styles:
            raise ValueError(f"Unknown execution section component: {component}. Available: {list(styles.keys())}")
        widget.setStyleSheet(styles[component])
    
    @classmethod
    def apply_status_style(cls, widget, status: str, base_style: str = ""):
        """Apply status-specific style to widget."""
        status_styles = cls.get_status_styles()
        if status not in status_styles:
            raise ValueError(f"Unknown status: {status}. Available: {list(status_styles.keys())}")
        
        full_style = base_style + status_styles[status]
        widget.setStyleSheet(full_style)
    
    @classmethod
    def apply_header_section_style(cls, widget, component: str):
        """Apply style to header section component."""
        styles = cls.get_header_section_styles()
        if component not in styles:
            raise ValueError(f"Unknown header component: {component}. Available: {list(styles.keys())}")
        widget.setStyleSheet(styles[component])
    
    @classmethod
    def apply_tasks_section_style(cls, widget, component: str):
        """Apply style to tasks section component."""
        styles = cls.get_tasks_section_styles()
        if component not in styles:
            raise ValueError(f"Unknown tasks component: {component}. Available: {list(styles.keys())}")
        widget.setStyleSheet(styles[component])
    
    @classmethod
    def apply_updated_control_section_style(cls, widget, component: str):
        """Apply style to updated control section component."""
        styles = cls.get_updated_control_section_styles()
        if component not in styles:
            raise ValueError(f"Unknown updated control component: {component}. Available: {list(styles.keys())}")
        widget.setStyleSheet(styles[component])
    
    @classmethod
    def apply_dynamic_status_style(cls, widget, status_type: str):
        """Apply dynamic status style combining base and content styles."""
        dynamic_styles = cls.get_dynamic_status_styles()
        base_style = dynamic_styles['base']
        
        status_key = f"{status_type}_content"
        if status_key not in dynamic_styles:
            raise ValueError(f"Unknown dynamic status type: {status_type}. Available: success, error, warning, processing, info")
        
        content_style = dynamic_styles[status_key]
        full_style = content_style + base_style
        widget.setStyleSheet(full_style)
    
    @classmethod
    def apply_response_text_error_style(cls, widget):
        """Apply error styling to response text widget."""
        error_style = """
            QTextEdit {
                background-color: #f8d7da;
                border: 2px solid #f5c6cb;
                border-radius: 8px;
                padding: 12px;
                color: #721c24;
                font-size: 11pt;
            }
        """
        widget.setStyleSheet(error_style)