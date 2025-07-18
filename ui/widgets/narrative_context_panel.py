"""
Narrative Context Management Panel.

This widget provides a UI for managing narrative context entries
that help maintain story continuity across scenes.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QLineEdit, QComboBox, QPushButton, QLabel, QSplitter,
    QGroupBox, QFormLayout, QMessageBox, QHeaderView, QMenu, QDialog,
    QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QFont

from typing import Optional, Dict, Any, List
from pathlib import Path

from core.logging_config import get_logger
from core.llm.context.narrative_context import NarrativeContextManager
from i18n import _


class NarrativeContextDialog(QDialog):
    """Dialog for editing narrative context entries."""
    
    def __init__(self, context_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.context_data = context_data
        self.is_edit_mode = context_data is not None
        
        self.setup_ui()
        self.load_data()
        
        title = _("Edit Context") if self.is_edit_mode else _("New Context")
        self.setWindowTitle(title)
        self.setMinimumSize(500, 400)
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Context type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "scene_summary",
            "character_state", 
            "plot_point",
            "world_state",
            "relationship_change",
            "timeline_event",
            "ai_response",
            "custom"
        ])
        form_layout.addRow(_("Type:"), self.type_combo)
        
        # Title
        self.title_edit = QLineEdit()
        form_layout.addRow(_("Title:"), self.title_edit)
        
        # Content
        self.content_edit = QTextEdit()
        self.content_edit.setMinimumHeight(200)
        form_layout.addRow(_("Content:"), self.content_edit)
        
        # Active checkbox
        self.active_checkbox = QCheckBox(_("Active"))
        self.active_checkbox.setChecked(True)
        form_layout.addRow("", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_data(self):
        """Load data from context_data if in edit mode."""
        if not self.is_edit_mode or not self.context_data:
            return
        
        # Set type
        context_type = self.context_data.get('context_type', 'custom')
        index = self.type_combo.findText(context_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        # Set title and content
        self.title_edit.setText(self.context_data.get('title', ''))
        self.content_edit.setPlainText(self.context_data.get('content', ''))
        
        # Set active state
        is_active = self.context_data.get('is_active', 1) == 1
        self.active_checkbox.setChecked(is_active)
    
    def get_data(self) -> Dict[str, Any]:
        """Get the form data."""
        return {
            'context_type': self.type_combo.currentText(),
            'title': self.title_edit.text().strip(),
            'content': self.content_edit.toPlainText().strip(),
            'is_active': 1 if self.active_checkbox.isChecked() else 0
        }


class NarrativeContextPanel(QWidget):
    """Panel for managing narrative context entries."""
    
    context_changed = Signal()  # Emitted when context is modified
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("ui.narrative_context")
        
        self.context_manager: Optional[NarrativeContextManager] = None
        self.current_project_path: Optional[Path] = None
        
        self.setup_ui()
        self.setup_connections()
        
        # Refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.refresh_contexts)
        
        self.logger.info(_("Narrative context panel initialized"))
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel(_("Narrative Context"))
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton(_("Add Context"))
        self.add_btn.clicked.connect(self.add_context)
        toolbar_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton(_("Edit"))
        self.edit_btn.clicked.connect(self.edit_context)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton(_("Delete"))
        self.delete_btn.clicked.connect(self.delete_context)
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)
        
        toolbar_layout.addStretch()
        
        self.refresh_btn = QPushButton(_("Refresh"))
        self.refresh_btn.clicked.connect(self.refresh_contexts)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Main content - horizontal splitter (left: tree, right: content)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Context tree
        self.context_tree = QTreeWidget()
        self.context_tree.setHeaderLabels([_("Type"), _("Title"), _("Updated")])
        self.context_tree.setRootIsDecorated(True)
        self.context_tree.setSortingEnabled(True)
        self.context_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.context_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.context_tree.setMinimumWidth(250)  # Ensure minimum width for tree
        
        # Adjust column widths for narrower tree
        header = self.context_tree.header()
        header.resizeSection(0, 80)   # Type column narrower
        header.resizeSection(1, 150)  # Title column
        header.setStretchLastSection(True)
        
        splitter.addWidget(self.context_tree)
        
        # Right side - Content preview (wider)
        preview_group = QGroupBox(_("Content Preview"))
        preview_layout = QVBoxLayout(preview_group)
        
        self.content_preview = QTextEdit()
        self.content_preview.setReadOnly(True)
        self.content_preview.setMinimumWidth(400)  # Ensure wider content area
        preview_layout.addWidget(self.content_preview)
        
        splitter.addWidget(preview_group)
        
        # Set splitter proportions (left: tree, right: content)
        splitter.setSizes([300, 500])  # Tree gets 300px, content gets 500px
        
        layout.addWidget(splitter)
        
        # Status
        self.status_label = QLabel(_("No project loaded"))
        layout.addWidget(self.status_label)
    
    def setup_connections(self):
        """Setup signal connections."""
        self.context_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.context_tree.itemDoubleClicked.connect(self.edit_context)
    
    def set_project(self, project_path: Path):
        """Set the current project."""
        try:
            self.current_project_path = project_path
            self.context_manager = NarrativeContextManager(project_path)
            
            self.status_label.setText(_("Project: {}").format(project_path.name))
            self.refresh_contexts()
            
            # Enable controls
            self.add_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            
            self.logger.info(_("Project set: {}").format(project_path))
            
        except Exception as e:
            self.logger.error(_("Failed to set project: {}").format(str(e)))
            QMessageBox.warning(
                self, 
                _("Error"), 
                _("Failed to load project context: {}").format(str(e))
            )
    
    def refresh_contexts(self):
        """Refresh the context list."""
        if not self.context_manager:
            return
        
        try:
            self.context_tree.clear()
            
            # Get all active contexts
            contexts = self.context_manager.get_active_context()
            
            # Group by type
            type_groups = {}
            for context in contexts:
                context_type = context['context_type']
                if context_type not in type_groups:
                    type_groups[context_type] = []
                type_groups[context_type].append(context)
            
            # Create tree items
            for context_type, group_contexts in type_groups.items():
                # Create parent item for context type
                parent_item = QTreeWidgetItem(self.context_tree)
                parent_item.setText(0, context_type.replace('_', ' ').title())
                parent_item.setText(1, f"({len(group_contexts)} entries)")
                parent_item.setData(0, Qt.ItemDataRole.UserRole, None)  # No data for parent
                
                # Create child items for each context
                for context in group_contexts:
                    child_item = QTreeWidgetItem(parent_item)
                    child_item.setText(0, "")
                    child_item.setText(1, context['title'])
                    child_item.setText(2, context.get('updated_at', ''))
                    child_item.setData(0, Qt.ItemDataRole.UserRole, context)
            
            # Expand all items
            self.context_tree.expandAll()
            
            self.logger.debug(_("Refreshed {} context entries").format(len(contexts)))
            
        except Exception as e:
            self.logger.error(_("Failed to refresh contexts: {}").format(str(e)))
    
    def on_selection_changed(self):
        """Handle selection changes in the tree."""
        try:
            current_item = self.context_tree.currentItem()
            
            if current_item:
                context_data = current_item.data(0, Qt.ItemDataRole.UserRole)
                
                if context_data:
                    # Show context content
                    self.content_preview.setPlainText(context_data.get('content', ''))
                    
                    # Enable edit/delete buttons
                    self.edit_btn.setEnabled(True)
                    self.delete_btn.setEnabled(True)
                else:
                    # Parent item selected
                    self.content_preview.clear()
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
            else:
                self.content_preview.clear()
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                
        except Exception as e:
            self.logger.error(_("Error handling selection change: {}").format(str(e)))
    
    def show_context_menu(self, position):
        """Show context menu for the tree."""
        item = self.context_tree.itemAt(position)
        if not item:
            return
        
        context_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not context_data:
            return  # Parent item, no context menu
        
        menu = QMenu(self)
        
        edit_action = QAction(_("Edit"), self)
        edit_action.triggered.connect(self.edit_context)
        menu.addAction(edit_action)
        
        delete_action = QAction(_("Delete"), self)
        delete_action.triggered.connect(self.delete_context)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        toggle_action = QAction(_("Toggle Active"), self)
        toggle_action.triggered.connect(self.toggle_context_active)
        menu.addAction(toggle_action)
        
        menu.exec(self.context_tree.mapToGlobal(position))
    
    def add_context(self):
        """Add a new context entry."""
        if not self.context_manager:
            return
        
        dialog = NarrativeContextDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                
                if not data['title'] or not data['content']:
                    QMessageBox.warning(
                        self,
                        _("Error"),
                        _("Title and content are required")
                    )
                    return
                
                context_id = self.context_manager.create_narrative_context(
                    context_type=data['context_type'],
                    title=data['title'],
                    content=data['content']
                )
                
                if data['is_active'] == 0:
                    self.context_manager.deactivate_context(context_id)
                
                self.refresh_contexts()
                self.context_changed.emit()
                
                self.logger.info(_("Added context: {}").format(data['title']))
                
            except Exception as e:
                self.logger.error(_("Failed to add context: {}").format(str(e)))
                QMessageBox.warning(
                    self,
                    _("Error"),
                    _("Failed to add context: {}").format(str(e))
                )
    
    def add_context_from_text(self, text: str) -> bool:
        """Add a new context entry from AI response text."""
        if not self.context_manager:
            return False
        
        try:
            # Generate a title based on the first line or truncated content
            lines = text.strip().split('\n')
            title = lines[0] if lines else "AI Response"
            if len(title) > 50:
                title = title[:47] + "..."
            
            # Create the context entry
            context_id = self.context_manager.create_narrative_context(
                context_type="ai_response",
                title=title,
                content=text
            )
            
            self.refresh_contexts()
            self.context_changed.emit()
            
            self.logger.info(_("Added AI response to context: {}").format(title))
            return True
            
        except Exception as e:
            self.logger.error(_("Failed to add AI response to context: {}").format(str(e)))
            return False
    
    def edit_context(self):
        """Edit the selected context entry."""
        if not self.context_manager:
            return
        
        current_item = self.context_tree.currentItem()
        if not current_item:
            return
        
        context_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not context_data:
            return
        
        dialog = NarrativeContextDialog(context_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                context_id = context_data['id']
                
                # Update the context
                success = self.context_manager.update_narrative_context(
                    context_id=context_id,
                    title=data['title'],
                    content=data['content']
                )
                
                if success:
                    # Handle active state change
                    if data['is_active'] != context_data.get('is_active', 1):
                        if data['is_active'] == 0:
                            self.context_manager.deactivate_context(context_id)
                        # Note: No reactivate method - would need to be added
                    
                    self.refresh_contexts()
                    self.context_changed.emit()
                    
                    self.logger.info(_("Updated context: {}").format(data['title']))
                else:
                    QMessageBox.warning(
                        self,
                        _("Error"),
                        _("Failed to update context")
                    )
                
            except Exception as e:
                self.logger.error(_("Failed to edit context: {}").format(str(e)))
                QMessageBox.warning(
                    self,
                    _("Error"),
                    _("Failed to edit context: {}").format(str(e))
                )
    
    def delete_context(self):
        """Delete the selected context entry."""
        if not self.context_manager:
            return
        
        current_item = self.context_tree.currentItem()
        if not current_item:
            return
        
        context_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not context_data:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            _("Confirm Delete"),
            _("Are you sure you want to delete the context '{}'?").format(context_data['title']),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.context_manager.deactivate_context(context_data['id'])
                
                if success:
                    self.refresh_contexts()
                    self.context_changed.emit()
                    
                    self.logger.info(_("Deleted context: {}").format(context_data['title']))
                else:
                    QMessageBox.warning(
                        self,
                        _("Error"),
                        _("Failed to delete context")
                    )
                    
            except Exception as e:
                self.logger.error(_("Failed to delete context: {}").format(str(e)))
                QMessageBox.warning(
                    self,
                    _("Error"),
                    _("Failed to delete context: {}").format(str(e))
                )
    
    def toggle_context_active(self):
        """Toggle the active state of the selected context."""
        if not self.context_manager:
            return
        
        current_item = self.context_tree.currentItem()
        if not current_item:
            return
        
        context_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not context_data:
            return
        
        try:
            context_id = context_data['id']
            is_active = context_data.get('is_active', 1) == 1
            
            if is_active:
                # Deactivate
                success = self.context_manager.deactivate_context(context_id)
                action = "deactivated"
            else:
                # Would need a reactivate method in the manager
                QMessageBox.information(
                    self,
                    _("Info"),
                    _("Reactivation not implemented. Please edit the context instead.")
                )
                return
            
            if success:
                self.refresh_contexts()
                self.context_changed.emit()
                
                self.logger.info(_("Context {} {}").format(action, context_data['title']))
            
        except Exception as e:
            self.logger.error(_("Failed to toggle context active state: {}").format(str(e)))
            QMessageBox.warning(
                self,
                _("Error"),
                _("Failed to toggle context state: {}").format(str(e))
            )