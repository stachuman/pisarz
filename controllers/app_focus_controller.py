"""Focus mode and theme management controller for the main application."""

from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QObject, Signal, Qt

from ui.base.enhanced_theme_manager import EnhancedThemeManager
from i18n import _


class AppFocusController(QObject):
    """Handles focus mode and theme management for the main application."""
    
    # Signals
    focusModeChanged = Signal(bool)  # focus_mode_active
    themeChanged = Signal(str)  # theme_name
    statusMessage = Signal(str)  # message
    
    def __init__(self, main_window: QMainWindow, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.theme_manager = EnhancedThemeManager()
        self.focus_mode = False
        self.project_widget = None
        self.workspace = None
        self.status_bar = None
        self.llm_panel = None
        self.saved_splitter_sizes = None
        self.saved_ai_assistant_visible = False
        
    def setup_components(self, project_widget: QWidget, workspace, status_bar, llm_panel=None):
        """Set references to UI components."""
        self.project_widget = project_widget
        self.workspace = workspace
        self.status_bar = status_bar
        self.llm_panel = llm_panel
        
    def initialize_theme(self):
        """Initialize and apply global theme."""
        self.theme_manager.apply_global_theme()
        
    def toggle_focus_mode(self):
        """Toggle focus mode on/off."""
        self.focus_mode = not self.focus_mode
        
        if self.focus_mode:
            self._enter_focus_mode()
        else:
            self._exit_focus_mode()
            
        self.focusModeChanged.emit(self.focus_mode)
    
    def exit_focus_mode_if_active(self):
        """Exit focus mode only if it's currently active."""
        if self.focus_mode:
            self.toggle_focus_mode()
    
    def is_focus_mode_active(self) -> bool:
        """Check if focus mode is currently active."""
        return self.focus_mode
    
    def on_ai_assistant_visibility_changed(self, visible: bool):
        """Handle AI assistant visibility change during focus mode."""
        # Update saved state for when we exit focus mode
        self.saved_ai_assistant_visible = visible
        
        if self.focus_mode and self.project_widget:
            # Find the main vertical splitter
            main_splitter = self.project_widget.findChild(QSplitter)
            if main_splitter:
                # Update focus mode layout based on AI assistant visibility
                if visible:
                    # Show AI assistant at bottom in focus mode
                    main_splitter.setSizes([700, 300])  # [top=700, ai=300]
                else:
                    # Hide AI assistant in focus mode
                    main_splitter.setSizes([1000, 0])  # [top=1000, ai=0]
    
    def _enter_focus_mode(self):
        """Enter focus mode - fullscreen with minimal UI."""
        self.main_window.showFullScreen()
        
        if self.status_bar:
            self.status_bar.hide()
        
        # Handle new layout: main vertical splitter with horizontal splitter at top
        if self.project_widget:
            # Find the main vertical splitter
            main_splitter = self.project_widget.findChild(QSplitter)
            if main_splitter:
                # Save current main splitter sizes
                self.saved_main_splitter_sizes = main_splitter.sizes()
                
                # Find the horizontal splitter within the top widget
                horizontal_splitter = main_splitter.widget(0).findChild(QSplitter)
                if horizontal_splitter:
                    # Save current horizontal splitter sizes
                    self.saved_horizontal_splitter_sizes = horizontal_splitter.sizes()
                    # Hide navigation panel in focus mode
                    horizontal_splitter.setSizes([0, 1200])  # [nav=0, workspace=1200]
                
                # Save AI assistant panel visibility
                if self.llm_panel:
                    self.saved_ai_assistant_visible = self.llm_panel.isVisible()
                
                # Calculate new sizes for focus mode
                if self.llm_panel and self.saved_ai_assistant_visible:
                    # Keep AI assistant at bottom in focus mode
                    main_splitter.setSizes([700, 300])  # [top=700, ai=300]
                else:
                    # Hide AI assistant in focus mode
                    main_splitter.setSizes([1000, 0])  # [top=1000, ai=0]
        
        # Apply focus mode styling
        self._apply_focus_window_style()
        
        if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
            self._apply_focus_mode_style()
    
    def _exit_focus_mode(self):
        """Exit focus mode - restore normal window."""
        self.main_window.showNormal()
        
        if self.status_bar:
            self.status_bar.show()
        
        # Restore new layout structure
        if self.project_widget:
            # Find the main vertical splitter
            main_splitter = self.project_widget.findChild(QSplitter)
            if main_splitter:
                # Restore saved main splitter sizes or use defaults
                if hasattr(self, 'saved_main_splitter_sizes') and self.saved_main_splitter_sizes:
                    main_splitter.setSizes(self.saved_main_splitter_sizes)
                else:
                    # Default layout (top + AI assistant)
                    if self.llm_panel and self.saved_ai_assistant_visible:
                        main_splitter.setSizes([700, 300])  # [top=700, ai=300]
                    else:
                        main_splitter.setSizes([1000, 0])  # [top=1000, ai=0]
                
                # Restore horizontal splitter within the top widget
                horizontal_splitter = main_splitter.widget(0).findChild(QSplitter)
                if horizontal_splitter:
                    # Restore saved horizontal splitter sizes or use defaults
                    if hasattr(self, 'saved_horizontal_splitter_sizes') and self.saved_horizontal_splitter_sizes:
                        horizontal_splitter.setSizes(self.saved_horizontal_splitter_sizes)
                    else:
                        # Default horizontal layout (nav + workspace)
                        horizontal_splitter.setSizes([300, 900])  # [nav=300, workspace=900]
        
        # Remove focus mode styling
        self._remove_focus_window_style()
        
        if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
            self._remove_focus_mode_style()
    
    def _apply_focus_mode_style(self):
        """Apply minimalist style in focus mode."""
        editor = self.workspace.current_editor
        if not editor:
            return
            
        # Hide toolbar in focus mode
        toolbar_widget = None
        for child in editor.findChildren(QWidget):
            if isinstance(child.layout(), QHBoxLayout) and child.findChild(QPushButton):
                toolbar_widget = child
                break
                
        if toolbar_widget:
            toolbar_widget.hide()
            
        # Get colors from current theme
        from ui.styles.themes import ThemeManager
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        # Apply minimalist style consistent with theme
        editor.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors["background"]};
                color: {colors["text"]};
                border: none;
                padding: 50px;
                font-size: 14pt;
                line-height: 1.6;
                selection-background-color: {colors["accent"]};
                selection-color: white;
            }}
        """)
    
    def _remove_focus_mode_style(self):
        """Remove focus mode style."""
        editor = self.workspace.current_editor
        if not editor:
            return
            
        # Show toolbar
        toolbar_widget = None
        for child in editor.findChildren(QWidget):
            if isinstance(child.layout(), QHBoxLayout) and child.findChild(QPushButton):
                toolbar_widget = child
                break
                
        if toolbar_widget:
            toolbar_widget.show()
            
        # Restore normal style
        editor.text_edit.setStyleSheet("")
    
    def _apply_focus_window_style(self):
        """Apply window style in focus mode."""
        from ui.styles.themes import ThemeManager
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        # Apply background consistent with theme
        self.main_window.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
            }}
            QWidget {{
                background-color: {colors["background"]};
                color: {colors["text"]};
            }}
        """)
    
    def _remove_focus_window_style(self):
        """Remove focus mode window style."""
        # Restore default style
        self.main_window.setStyleSheet("")
    
    def apply_focus_styles_if_active(self):
        """Apply focus mode styles if focus mode is currently active."""
        if self.focus_mode:
            self._apply_focus_window_style()
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                self._apply_focus_mode_style()
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        self.statusMessage.emit(_("Applied theme: {}").format(theme_name))
        self.themeChanged.emit(theme_name)
        
        # Refresh focus mode styles if active
        if self.focus_mode:
            self.apply_focus_styles_if_active()
    
    def get_theme_manager(self):
        """Get the theme manager instance."""
        return self.theme_manager