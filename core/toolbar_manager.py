"""Toolbar manager for the embedded RTF editor."""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton, 
                               QColorDialog)
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QFont, QFontInfo, QTextCharFormat, QColor, QBrush
from i18n import _


class ToolbarManager(QObject):
    """Manages toolbar creation and formatting operations for the RTF editor."""
    
    # Signals for formatting operations
    fontFamilyChanged = Signal(str)
    fontSizeChanged = Signal(str)
    boldToggled = Signal()
    italicToggled = Signal()
    underlineToggled = Signal()
    textColorChanged = Signal(QColor)
    alignmentChanged = Signal(Qt.AlignmentFlag)
    saveRequested = Signal()
    focusModeRequested = Signal()
    contextPanelToggled = Signal()
    aiAssistantToggled = Signal()
    narrativeContextToggled = Signal()
    button_fixed_size = 32

    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.toolbar_widget = None
        self.font_combo = None
        self.font_size_combo = None
        self.bold_btn = None
        self.italic_btn = None
        self.underline_btn = None
        self.text_color_btn = None
        self.align_left_btn = None
        self.align_center_btn = None
        self.align_right_btn = None
        self.save_btn = None
        self.focus_mode_btn = None
        self.context_panel_btn = None
        self.ai_assistant_btn = None
        self.narrative_context_btn = None
        
    def create_toolbar(self) -> QWidget:
        """Create and return the toolbar widget."""
        self.toolbar_widget = QWidget()
        self.toolbar_widget.setFixedHeight(36)
        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(8, 2, 8, 2)
        toolbar_layout.setSpacing(8)
        
        # Font section
        self._create_font_section(toolbar_layout)
        self._add_separator(toolbar_layout)
        
        # Formatting section
        self._create_formatting_section(toolbar_layout)
        self._add_separator(toolbar_layout)
        
        # Text color section
        self._create_text_color_section(toolbar_layout)
        self._add_separator(toolbar_layout)
        
        # Alignment section
        self._create_alignment_section(toolbar_layout)
        self._add_separator(toolbar_layout)
        
        # Action buttons section
        self._create_action_buttons_section(toolbar_layout)
        
        # Flexible spacer
        toolbar_layout.addStretch()
        
        # Connect signals
        self._connect_signals()
        
        return self.toolbar_widget
    
    def _create_font_section(self, layout: QHBoxLayout):
        """Create font family and size controls."""
        # Font family
        font_label = QLabel(_("Czcionka:"))
        layout.addWidget(font_label)
        
        self.font_combo = QComboBox()
        self.font_combo.setEditable(False)
        self._setup_limited_font_list()
        self.font_combo.setMinimumWidth(130)
        self.font_combo.setMaximumWidth(150)
        layout.addWidget(self.font_combo)
        
        # Font size
        size_label = QLabel(_("Rozmiar:"))
        layout.addWidget(size_label)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.setEditable(False)  # Tylko dropdown, bez możliwości wpisywania
        sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36"]
        self.font_size_combo.addItems(sizes)
        self.font_size_combo.setCurrentText("12")
        self.font_size_combo.setMinimumWidth(50)
        self.font_size_combo.setMaximumWidth(70)
        layout.addWidget(self.font_size_combo)
    
    def _create_formatting_section(self, layout: QHBoxLayout):
        """Create bold, italic, underline buttons."""
        # Bold
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.bold_btn.setToolTip(_("Pogrubienie (Ctrl+B)"))
        self.bold_btn.setFixedSize(self.button_fixed_size, self.button_fixed_size)
        layout.addWidget(self.bold_btn)
        
        # Italic
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        font = QFont("Arial", 12)
        font.setItalic(True)
        self.italic_btn.setFont(font)
        self.italic_btn.setToolTip(_("Kursywa (Ctrl+I)"))
        self.italic_btn.setFixedSize(self.button_fixed_size, self.button_fixed_size)
        layout.addWidget(self.italic_btn)
        
        # Underline
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        font = QFont("Arial", 12)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.setToolTip(_("Podkreślenie (Ctrl+U)"))
        self.underline_btn.setFixedSize(self.button_fixed_size, self.button_fixed_size)
        layout.addWidget(self.underline_btn)
    
    def _create_text_color_section(self, layout: QHBoxLayout):
        """Create text color button."""
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setToolTip(_("Kolor tekstu"))
        self.text_color_btn.setFixedSize(self.button_fixed_size, self.button_fixed_size)
        self.text_color_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.text_color_btn)
    
    def _create_alignment_section(self, layout: QHBoxLayout):
        """Create alignment buttons."""
        # Left align
        self.align_left_btn = QPushButton("◀")
        self.align_left_btn.setToolTip(_("Wyrównaj do lewej"))
        self.align_left_btn.setFixedSize(self.button_fixed_size, self.button_fixed_size)
        layout.addWidget(self.align_left_btn)
        
        # Center align
        self.align_center_btn = QPushButton("‖")
        self.align_center_btn.setToolTip(_("Wyśrodkuj"))
        self.align_center_btn.setFixedSize(self.button_fixed_size, self.button_fixed_size)
        layout.addWidget(self.align_center_btn)
        
        # Right align
        self.align_right_btn = QPushButton("▶")
        self.align_right_btn.setToolTip(_("Wyrównaj do prawej"))
        self.align_right_btn.setFixedSize(self.button_fixed_size, self.button_fixed_size)
        layout.addWidget(self.align_right_btn)
    
    def _create_action_buttons_section(self, layout: QHBoxLayout):
        """Create action buttons (save, focus mode, context panel)."""
        # Save button
        self.save_btn = QPushButton(_("Zapisz"))
        self.save_btn.setToolTip(_("Zapisz (Ctrl+S)"))
        layout.addWidget(self.save_btn)
        
        self._add_separator(layout)
        
        # Focus mode button
        self.focus_mode_btn = QPushButton(_("Fokus"))
        self.focus_mode_btn.setToolTip(_("Tryb fokusu pisania (F11)"))
        layout.addWidget(self.focus_mode_btn)
        
        # Context panel toggle
        self.context_panel_btn = QPushButton("📝")
        self.context_panel_btn.setCheckable(True)
        self.context_panel_btn.setChecked(False)
        self.context_panel_btn.setToolTip(_("Toggle Scene Context Panel (Ctrl+E)"))
        self.context_panel_btn.setFixedSize(32, 32)
        layout.addWidget(self.context_panel_btn)
        
        # AI Assistant toggle
        self.ai_assistant_btn = QPushButton("🤖")
        self.ai_assistant_btn.setCheckable(True)
        self.ai_assistant_btn.setChecked(False)
        self.ai_assistant_btn.setToolTip(_("Toggle AI Assistant Panel (Ctrl+Alt+A)"))
        self.ai_assistant_btn.setFixedSize(32, 32)
        layout.addWidget(self.ai_assistant_btn)
        
        # Narrative Context toggle
        self.narrative_context_btn = QPushButton("📚")
        self.narrative_context_btn.setCheckable(True)
        self.narrative_context_btn.setChecked(False)
        self.narrative_context_btn.setToolTip(_("Toggle Narrative Context Panel (Ctrl+Alt+N)"))
        self.narrative_context_btn.setFixedSize(32, 32)
        layout.addWidget(self.narrative_context_btn)
    
    def _add_separator(self, layout: QHBoxLayout):
        """Add a separator widget."""
        separator = QWidget()
        separator.setFixedWidth(10)
        layout.addWidget(separator)
    
    def _setup_limited_font_list(self):
        """Setup font combo with preferred writing fonts."""
        preferred_fonts = [
            "Georgia", "Times New Roman", "Nimbus Roman", "Bitstream Charter",
            "Liberation Serif", "URW Bookman", "C059", "DejaVu Serif"
        ]
        
        self.font_combo.clear()
        
        for font_name in preferred_fonts:
            font = QFont(font_name)
            if QFontInfo(font).family() == font_name:
                self.font_combo.addItem(font_name)
        
        # Fallback if no fonts available
        if self.font_combo.count() == 0:
            self.font_combo.addItem("serif")
    
    def _connect_signals(self):
        """Connect toolbar signals to slots."""
        if self.font_combo:
            self.font_combo.currentTextChanged.connect(self.fontFamilyChanged.emit)
        if self.font_size_combo:
            self.font_size_combo.currentTextChanged.connect(self.fontSizeChanged.emit)
        if self.bold_btn:
            self.bold_btn.clicked.connect(self.boldToggled.emit)
        if self.italic_btn:
            self.italic_btn.clicked.connect(self.italicToggled.emit)
        if self.underline_btn:
            self.underline_btn.clicked.connect(self.underlineToggled.emit)
        if self.text_color_btn:
            self.text_color_btn.clicked.connect(self._on_text_color_clicked)
        if self.align_left_btn:
            self.align_left_btn.clicked.connect(
                lambda: self.alignmentChanged.emit(Qt.AlignmentFlag.AlignLeft)
            )
        if self.align_center_btn:
            self.align_center_btn.clicked.connect(
                lambda: self.alignmentChanged.emit(Qt.AlignmentFlag.AlignCenter)
            )
        if self.align_right_btn:
            self.align_right_btn.clicked.connect(
                lambda: self.alignmentChanged.emit(Qt.AlignmentFlag.AlignRight)
            )
        if self.save_btn:
            self.save_btn.clicked.connect(self.saveRequested.emit)
        if self.focus_mode_btn:
            self.focus_mode_btn.clicked.connect(self.focusModeRequested.emit)
        if self.context_panel_btn:
            self.context_panel_btn.clicked.connect(self.contextPanelToggled.emit)
        if self.ai_assistant_btn:
            self.ai_assistant_btn.clicked.connect(self.aiAssistantToggled.emit)
        if self.narrative_context_btn:
            self.narrative_context_btn.clicked.connect(self.narrativeContextToggled.emit)
    
    def _on_text_color_clicked(self):
        """Handle text color button click."""
        color = QColorDialog.getColor(Qt.GlobalColor.black, self.toolbar_widget, _("Wybierz kolor tekstu"))
        if color.isValid():
            self.textColorChanged.emit(color)
            # Update button color
            if self.text_color_btn:
                self.text_color_btn.setStyleSheet(
                    f"QPushButton {{ background-color: {color.name()}; color: white; font-weight: bold; }}"
                )
    
    def set_font_focus_policy(self, policy: Qt.FocusPolicy):
        """Set focus policy for font controls."""
        if self.font_combo:
            self.font_combo.setFocusPolicy(policy)
        if self.font_size_combo:
            self.font_size_combo.setFocusPolicy(policy)
    
    def update_format_state(self, format_info: QTextCharFormat):
        """Update toolbar buttons based on current text format."""
        if self.bold_btn:
            self.bold_btn.setChecked(format_info.fontWeight() == QFont.Weight.Bold)
        if self.italic_btn:
            self.italic_btn.setChecked(format_info.fontItalic())
        if self.underline_btn:
            self.underline_btn.setChecked(format_info.fontUnderline())
        
        # Update font family
        if self.font_combo:
            current_font_family = format_info.font().family()
            if current_font_family:
                self.font_combo.blockSignals(True)
                index = self.font_combo.findText(current_font_family)
                if index >= 0:
                    self.font_combo.setCurrentIndex(index)
                self.font_combo.blockSignals(False)
        
        # Update font size
        if self.font_size_combo:
            font_size = format_info.fontPointSize()
            if font_size > 0:
                self.font_size_combo.blockSignals(True)
                self.font_size_combo.setCurrentText(str(int(font_size)))
                self.font_size_combo.blockSignals(False)
    
    def set_default_font(self, font: QFont):
        """Set default font in the toolbar."""
        if self.font_combo:
            self.font_combo.blockSignals(True)
            font_family = font.family()
            index = self.font_combo.findText(font_family)
            if index >= 0:
                self.font_combo.setCurrentIndex(index)
            self.font_combo.blockSignals(False)
        
        if self.font_size_combo:
            self.font_size_combo.blockSignals(True)
            self.font_size_combo.setCurrentText(str(font.pointSize()))
            self.font_size_combo.blockSignals(False)
    
    def set_context_panel_state(self, visible: bool):
        """Set the context panel button state."""
        if self.context_panel_btn:
            self.context_panel_btn.setChecked(visible)
    
    def set_ai_assistant_state(self, visible: bool):
        """Set the AI assistant button state."""
        if self.ai_assistant_btn:
            self.ai_assistant_btn.setChecked(visible)
    
    def set_narrative_context_state(self, visible: bool):
        """Set the narrative context button state."""
        if self.narrative_context_btn:
            self.narrative_context_btn.setChecked(visible)