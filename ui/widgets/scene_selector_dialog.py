"""Scene selector dialog for linking characters to scenes."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QListWidget, QListWidgetItem, 
                              QLineEdit, QComboBox, QSpinBox, QFormLayout,
                              QGroupBox, QMessageBox, QSplitter, QTextEdit)

from ui.base.base_dialog import BaseDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from i18n import _


class SceneSelector(BaseDialog):
    """Dialog for selecting scenes to link to a character."""
    
    scenesSelected = Signal(list)  # List of (scene_id, role, importance) tuples
    
    def __init__(self, scenes_data, already_linked_scene_ids=None, parent=None):
        self.scenes_data = scenes_data
        self.already_linked_scene_ids = set(already_linked_scene_ids or [])
        self.selected_scenes = []
        
        super().__init__(
            title=_("Select Scenes to Link"),
            width=600,
            height=500,
            modal=True,
            parent=parent
        )
        
        self.setup_ui()
        self.load_scenes()
        
    def setup_ui(self):
        """Setup the scene selector dialog UI."""
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel(_("Search:"))
        self.search_edit = self.create_line_input(_("Search scenes by title..."))
        self.search_edit.textChanged.connect(self.filter_scenes)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        self.add_content_layout(search_layout)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Available scenes
        scenes_widget, scenes_layout = self.create_form_section(_("Available Scenes"))
        
        self.scenes_list = QListWidget()
        self.scenes_list.setFont(self.font_manager.get_font(10))
        self.scenes_list.itemClicked.connect(self.on_scene_clicked)
        self.scenes_list.itemDoubleClicked.connect(self.on_scene_double_clicked)
        scenes_layout.addWidget(self.scenes_list)
        
        # Right side - Link details
        details_widget, details_layout = self.create_form_section(_("Link Details"))
        
        # Current scene info
        self.scene_info_label = self.create_info_label(_("Select a scene to see details"), "muted")
        self.scene_info_label.setFont(self.font_manager.get_font(9))
        self.scene_info_label.setWordWrap(True)
        details_layout.addWidget(self.scene_info_label)
        
        # Link settings form
        # Role in scene
        self.role_combo = QComboBox()
        self.role_combo.setEditable(True)
        self.role_combo.addItems([
            _("Protagonist"),
            _("Supporting Character"),
            _("Antagonist"),
            _("Minor Character"),
            _("Mentioned Only"),
            _("Narrator"),
            _("Cameo")
        ])
        details_layout.addRow(_("Role in Scene:"), self.role_combo)
        
        # Importance level
        self.importance_spin = QSpinBox()
        self.importance_spin.setRange(1, 5)
        self.importance_spin.setValue(3)
        self.importance_spin.setToolTip(_("1=Minor, 2=Secondary, 3=Regular, 4=Important, 5=Central"))
        details_layout.addRow(_("Importance (1-5):"), self.importance_spin)
        
        # Add to selection button
        self.add_scene_btn = self.create_custom_button(_("Add Scene"), self.add_scene_to_selection, "primary")
        self.add_scene_btn.setEnabled(False)
        details_layout.addWidget(self.add_scene_btn)
        
        # Selected scenes list
        selected_label = QLabel(_("Selected Scenes:"))
        selected_label.setFont(self.font_manager.get_font(9, weight=QFont.Weight.Bold))
        details_layout.addWidget(selected_label)
        
        self.selected_list = QListWidget()
        self.selected_list.setFont(self.font_manager.get_font(9))
        self.selected_list.setMaximumHeight(100)
        details_layout.addWidget(self.selected_list)
        
        # Remove selected button
        self.remove_btn = self.create_custom_button(_("Remove Selected"), self.remove_selected_scene, "secondary")
        self.remove_btn.setEnabled(False)
        self.selected_list.itemClicked.connect(lambda: self.remove_btn.setEnabled(True))
        details_layout.addWidget(self.remove_btn)
        
        # QFormLayout doesn't have addStretch, use a spacer widget instead
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        details_layout.addItem(spacer)
        
        # Add to splitter
        splitter.addWidget(scenes_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 200])
        
        self.add_content_widget(splitter)
        
        # Buttons using BaseDialog functionality
        self.add_button_stretch()
        
        self.cancel_btn = self.create_custom_button(_("Cancel"), self.reject, "secondary")
        self.add_button(self.cancel_btn)
        
        self.link_btn = self.create_custom_button(_("Link Scenes"), self.accept_selection, "primary")
        self.link_btn.setEnabled(False)
        self.link_btn.setDefault(True)
        self.add_button(self.link_btn)
        
    def load_scenes(self):
        """Load available scenes into the list."""
        self.scenes_list.clear()
        
        for scene in self.scenes_data:
            scene_id = scene['id']
            scene_title = scene['title']
            
            # Skip already linked scenes
            if scene_id in self.already_linked_scene_ids:
                continue
                
            item = QListWidgetItem(scene_title)
            item.setData(Qt.ItemDataRole.UserRole, scene)
            self.scenes_list.addItem(item)
            
    def filter_scenes(self, text):
        """Filter scenes based on search text."""
        for i in range(self.scenes_list.count()):
            item = self.scenes_list.item(i)
            scene_data = item.data(Qt.ItemDataRole.UserRole)
            scene_title = scene_data['title'].lower()
            
            # Show item if search text is found in title
            visible = text.lower() in scene_title
            item.setHidden(not visible)
            
    def on_scene_clicked(self, item):
        """Handle scene selection in the list."""
        scene_data = item.data(Qt.ItemDataRole.UserRole)
        
        # Update scene info
        info_text = f"<b>{scene_data['title']}</b><br>"
        if scene_data.get('content_rtf'):
            # Extract plain text preview from RTF
            content = scene_data['content_rtf'][:200] + "..." if len(scene_data['content_rtf']) > 200 else scene_data['content_rtf']
            info_text += f"<br><i>{content}</i>"
        else:
            info_text += f"<br><i>{_('No content yet')}</i>"
            
        self.scene_info_label.setText(info_text)
        self.add_scene_btn.setEnabled(True)
        
    def on_scene_double_clicked(self, item):
        """Handle double-click to quickly add scene."""
        self.on_scene_clicked(item)
        self.add_scene_to_selection()
        
    def add_scene_to_selection(self):
        """Add current scene to selection with role and importance."""
        current_item = self.scenes_list.currentItem()
        if not current_item:
            return
            
        scene_data = current_item.data(Qt.ItemDataRole.UserRole)
        scene_id = scene_data['id']
        scene_title = scene_data['title']
        role = self.role_combo.currentText().strip()
        importance = self.importance_spin.value()
        
        # Check if already selected
        for selected_scene in self.selected_scenes:
            if selected_scene[0] == scene_id:
                QMessageBox.information(self, _("Already Selected"), 
                                      _("This scene is already selected."))
                return
                
        # Add to selection
        self.selected_scenes.append((scene_id, role, importance))
        
        # Update selected list display
        display_text = f"{scene_title} ({role}, {_('Importance')}: {importance})"
        selected_item = QListWidgetItem(display_text)
        selected_item.setData(Qt.ItemDataRole.UserRole, scene_id)
        self.selected_list.addItem(selected_item)
        
        # Enable link button
        self.link_btn.setEnabled(True)
        
        # Remove from available scenes
        self.scenes_list.takeItem(self.scenes_list.row(current_item))
        
        # Clear selection
        self.scene_info_label.setText(_("Select a scene to see details"))
        self.add_scene_btn.setEnabled(False)
        
    def remove_selected_scene(self):
        """Remove selected scene from selection."""
        current_item = self.selected_list.currentItem()
        if not current_item:
            return
            
        scene_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Remove from selected_scenes list
        self.selected_scenes = [s for s in self.selected_scenes if s[0] != scene_id]
        
        # Remove from UI list
        self.selected_list.takeItem(self.selected_list.row(current_item))
        
        # Re-add to available scenes
        for scene in self.scenes_data:
            if scene['id'] == scene_id and scene_id not in self.already_linked_scene_ids:
                item = QListWidgetItem(scene['title'])
                item.setData(Qt.ItemDataRole.UserRole, scene)
                self.scenes_list.addItem(item)
                break
                
        # Update button states
        self.link_btn.setEnabled(len(self.selected_scenes) > 0)
        self.remove_btn.setEnabled(False)
        
    def accept_selection(self):
        """Accept the current selection and emit signal."""
        if not self.selected_scenes:
            QMessageBox.warning(self, _("No Selection"), 
                              _("Please select at least one scene."))
            return
            
        self.scenesSelected.emit(self.selected_scenes)
        self.accept()