"""Context panel manager for the embedded RTF editor."""

from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import Qt, QObject, Signal


class ContextPanelManager(QObject):
    """Manages the scene context panel for the RTF editor."""
    
    # Signals - pass through from context panel to main application
    contextPanelToggled = Signal(bool)
    characterAddedToScene = Signal(int, str)  # character_id, role
    characterRemovedFromScene = Signal(int)   # character_id
    locationAddedToScene = Signal(int, str)   # location_id, role
    locationRemovedFromScene = Signal(int)    # location_id
    newCharacterRequestedFromScene = Signal(str)  # name
    newLocationRequestedFromScene = Signal(str)   # name
    characterSelectedFromScene = Signal(int)     # character_id
    locationSelectedFromScene = Signal(int)      # location_id
    
    def __init__(self, splitter: QSplitter, parent=None):
        super().__init__(parent)
        self.splitter = splitter
        self.context_panel = None
        self.context_panel_visible = False  # Start with panel hidden
        
    def initialize_context_panel(self, character_manager, location_manager, project_id):
        """Initialize the context panel with managers."""
        from ui.widgets.scene_context_panel import SceneContextPanel
        
        if self.context_panel is None:
            self.context_panel = SceneContextPanel()
            self.context_panel.set_managers(character_manager, location_manager, project_id)
            self.splitter.addWidget(self.context_panel)
            
            # Set visibility based on current state
            self.context_panel.setVisible(self.context_panel_visible)
            
            # Set initial splitter sizes based on visibility
            if self.context_panel_visible:
                self.splitter.setSizes([800, 300])
            else:
                self.splitter.setSizes([1100, 0])
            
            # Connect context panel signals
            self._connect_context_panel_signals()
        else:
            # Update existing panel with new managers
            self.context_panel.set_managers(character_manager, location_manager, project_id)
    
    def set_scene_context(self, scene_id):
        """Set the current scene for the context panel."""
        if self.context_panel:
            self.context_panel.set_scene_id(scene_id)
    
    def toggle_context_panel(self):
        """Toggle the visibility of the context panel."""
        if self.context_panel:
            self.context_panel_visible = not self.context_panel_visible
            self.context_panel.setVisible(self.context_panel_visible)
            self.contextPanelToggled.emit(self.context_panel_visible)
            
            # Adjust splitter sizes
            if self.context_panel_visible:
                self.splitter.setSizes([800, 300])
            else:
                self.splitter.setSizes([1100, 0])
    
    def _connect_context_panel_signals(self):
        """Connect context panel signals to handle character/location management."""
        if not self.context_panel:
            return
        
        # Pass through signals to main application
        self.context_panel.character_added.connect(self.characterAddedToScene.emit)
        self.context_panel.character_removed.connect(self.characterRemovedFromScene.emit)
        self.context_panel.location_added.connect(self.locationAddedToScene.emit)
        self.context_panel.location_removed.connect(self.locationRemovedFromScene.emit)
        self.context_panel.new_character_requested.connect(self.newCharacterRequestedFromScene.emit)
        self.context_panel.new_location_requested.connect(self.newLocationRequestedFromScene.emit)
        self.context_panel.character_selected.connect(self.characterSelectedFromScene.emit)
        self.context_panel.location_selected.connect(self.locationSelectedFromScene.emit)
    
    def refresh_context_panel(self):
        """Refresh the context panel data."""
        if self.context_panel:
            self.context_panel.refresh_context()
    
    def is_visible(self):
        """Check if the context panel is visible."""
        return self.context_panel_visible
    
    def set_visible(self, visible):
        """Set the visibility of the context panel."""
        if self.context_panel:
            self.context_panel_visible = visible
            self.context_panel.setVisible(visible)
            self.contextPanelToggled.emit(visible)
            
            # Adjust splitter sizes
            if visible:
                self.splitter.setSizes([800, 300])
            else:
                self.splitter.setSizes([1100, 0])
    
    def cleanup(self):
        """Clean up resources when the manager is destroyed."""
        if self.context_panel:
            self.context_panel.setParent(None)
            self.context_panel = None
        self.context_panel_visible = False