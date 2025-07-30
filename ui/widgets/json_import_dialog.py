"""JSON Import Dialog for characters and locations."""

import json
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTextEdit, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QTabWidget, QWidget, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt

from ui.base.base_dialog import BaseDialog
from core.database.character_repository import Character
from core.database.location_repository import Location
from core.logging_config import get_logger
from i18n import _


class JSONImportDialog(BaseDialog):
    """Dialog for importing characters and locations from JSON."""
    
    def __init__(self, json_text: str, parent=None):
        self.logger = get_logger("ui.json_import")
        self.json_text = json_text
        self.parsed_data = None
        self.import_type = None  # 'characters' or 'locations'
        
        super().__init__(
            title=_("Import JSON Data"),
            width=800,
            height=600,
            modal=True,
            parent=parent
        )
        
        self.setup_ui()
        self.parse_json()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        # JSON preview section
        self.content_layout.addWidget(QLabel(_("JSON Data:")))
        self.json_edit = QTextEdit()
        self.json_edit.setPlainText(self.json_text)
        self.json_edit.setMaximumHeight(200)
        self.content_layout.addWidget(self.json_edit)
        
        # Parse button
        parse_button = QPushButton(_("Parse JSON"))
        parse_button.clicked.connect(self.parse_json)
        self.content_layout.addWidget(parse_button)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.content_layout.addWidget(self.preview_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.content_layout.addWidget(self.progress_bar)
        
        # Buttons (use BaseDialog's button_layout)
        self.import_button = QPushButton(_("Import"))
        self.import_button.clicked.connect(self.import_data)
        self.import_button.setEnabled(False)
        
        cancel_button = QPushButton(_("Cancel"))
        cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(self.import_button)
        self.button_layout.addWidget(cancel_button)
    
    def parse_json(self):
        """Parse JSON text and populate preview table."""
        try:
            json_text = self.json_edit.toPlainText().strip()
            
            # Extract JSON from markdown code blocks if present
            if '```json' in json_text:
                start = json_text.find('```json') + 7
                end = json_text.find('```', start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            elif '```' in json_text:
                start = json_text.find('```') + 3
                end = json_text.find('```', start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            
            self.parsed_data = json.loads(json_text)
            
            # Determine import type
            if 'characters' in self.parsed_data:
                self.import_type = 'characters'
                self.populate_characters_table()
            elif 'locations' in self.parsed_data:
                self.import_type = 'locations'
                self.populate_locations_table()
            else:
                raise ValueError(_("JSON must contain either 'characters' or 'locations' array"))
            
            self.import_button.setEnabled(True)
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, _("JSON Error"), _("Invalid JSON format: {}").format(str(e)))
        except Exception as e:
            QMessageBox.critical(self, _("Parse Error"), str(e))
    
    def populate_characters_table(self):
        """Populate table with character data."""
        characters = self.parsed_data['characters']
        if not characters:
            return
        
        # Get all possible columns from Character dataclass and first character
        character_fields = [f.name for f in Character.__dataclass_fields__.values() if f.name not in ['id', 'project_id', 'created_at']]
        first_char_keys = list(characters[0].keys())
        
        # Use character fields that are present in the data
        columns = [col for col in character_fields if col in first_char_keys]
        
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setRowCount(len(characters))
        self.preview_table.setHorizontalHeaderLabels([_(col.replace('_', ' ').title()) for col in columns])
        
        for row, character in enumerate(characters):
            for col, field in enumerate(columns):
                value = character.get(field, '')
                if isinstance(value, bool):
                    value = _("Yes") if value else _("No")
                elif value is None:
                    value = ''
                else:
                    value = str(value)
                
                item = QTableWidgetItem(value)
                self.preview_table.setItem(row, col, item)
        
        self.preview_table.resizeColumnsToContents()
    
    def populate_locations_table(self):
        """Populate table with location data."""
        locations = self.parsed_data['locations']
        if not locations:
            return
        
        # Get all possible columns from Location dataclass and first location
        location_fields = [f.name for f in Location.__dataclass_fields__.values() if f.name not in ['id', 'project_id', 'created_at']]
        first_loc_keys = list(locations[0].keys())
        
        # Use location fields that are present in the data
        columns = [col for col in location_fields if col in first_loc_keys]
        
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setRowCount(len(locations))
        self.preview_table.setHorizontalHeaderLabels([_(col.replace('_', ' ').title()) for col in columns])
        
        for row, location in enumerate(locations):
            for col, field in enumerate(columns):
                value = location.get(field, '')
                if value is None:
                    value = ''
                else:
                    value = str(value)
                
                item = QTableWidgetItem(value)
                self.preview_table.setItem(row, col, item)
        
        self.preview_table.resizeColumnsToContents()
    
    def import_data(self):
        """Import the parsed data using existing controllers."""
        # Re-parse JSON from current text (in case user edited it)
        self.parse_json()
        
        if not self.parsed_data:
            return
        
        try:
            # Get main window and project controller
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'project_controller'):
                main_window = main_window.parent()
            
            if not main_window:
                raise RuntimeError(_("Cannot access main window"))
            
            project_controller = main_window.project_controller
            if not project_controller.has_current_project():
                raise RuntimeError(_("No project loaded"))
            
            if self.import_type == 'characters':
                self.import_characters(main_window)
            elif self.import_type == 'locations':
                self.import_locations(main_window)
            
            #QMessageBox.information(self, _("Success"), _("Data imported successfully"))
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            #QMessageBox.critical(self, _("Import Error"), str(e))
    
    def import_characters(self, main_window):
        """Import characters using existing character controller."""
        characters = self.parsed_data['characters']
        character_controller = main_window.character_controller
        project_controller = main_window.project_controller
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(characters))
        
        for i, char_data in enumerate(characters):
            # Validate required fields
            if not char_data.get('name'):
                raise ValueError(_("Character at index {} missing required 'name' field").format(i))
            
            # Create character directly using manager to avoid opening dialog
            managers = project_controller.get_current_managers()
            character_manager = managers.get('character_manager')
            if not character_manager:
                raise RuntimeError(_("Character manager not available"))
            
            project_id = project_controller.get_project_id()
            
            # Prepare character data with type conversion
            create_data = {'name': char_data['name']}
            for k, v in char_data.items():
                if k != 'name' and v is not None:
                    # Convert non-string values for database compatibility
                    if isinstance(v, (list, dict)):
                        # Convert arrays/objects to JSON strings
                        import json
                        create_data[k] = json.dumps(v, ensure_ascii=False)
                    elif isinstance(v, bool):
                        create_data[k] = v  # Keep booleans as-is
                    elif isinstance(v, (int, float)):
                        create_data[k] = v  # Keep numbers as-is
                    else:
                        create_data[k] = str(v)  # Convert everything else to string
            
            # Create character directly
            character_id = character_manager.create_character(project_id, **create_data)
            if not character_id:
                raise RuntimeError(_("Failed to create character: {}").format(char_data['name']))
            
            # Emit signals to refresh UI without opening dialog
            character_controller.characterCreated.emit(char_data['name'])
            character_controller.charactersRefreshNeeded.emit()
            
            self.progress_bar.setValue(i + 1)
        
        self.progress_bar.setVisible(False)
    
    def import_locations(self, main_window):
        """Import locations using existing location controller."""
        locations = self.parsed_data['locations']
        
        # Check if location controller exists
        if not hasattr(main_window, 'location_controller'):
            raise NotImplementedError(_("Location import not yet implemented - location controller not found"))
        
        location_controller = main_window.location_controller
        project_controller = main_window.project_controller
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(locations))
        
        for i, loc_data in enumerate(locations):
            # Validate required fields
            if not loc_data.get('name'):
                raise ValueError(_("Location at index {} missing required 'name' field").format(i))
            
            # Create location directly using manager to avoid opening dialog
            managers = project_controller.get_current_managers()
            location_manager = managers.get('location_manager')
            if not location_manager:
                raise RuntimeError(_("Location manager not available"))
            
            project_id = project_controller.get_project_id()
            
            # Prepare location data with type conversion
            create_data = {'name': loc_data['name']}
            for k, v in loc_data.items():
                if k != 'name' and v is not None:
                    # Convert non-string values for database compatibility
                    if isinstance(v, (list, dict)):
                        # Convert arrays/objects to JSON strings
                        import json
                        create_data[k] = json.dumps(v, ensure_ascii=False)
                    elif isinstance(v, bool):
                        create_data[k] = v  # Keep booleans as-is
                    elif isinstance(v, (int, float)):
                        create_data[k] = v  # Keep numbers as-is
                    else:
                        create_data[k] = str(v)  # Convert everything else to string
            
            # Create location directly
            location_id = location_manager.create_location(project_id, **create_data)
            if not location_id:
                raise RuntimeError(_("Failed to create location: {}").format(loc_data['name']))
            
            # Emit signals to refresh UI without opening dialog
            location_controller.locationCreated.emit(loc_data['name'])
            location_controller.locationsRefreshNeeded.emit()
            
            self.progress_bar.setValue(i + 1)
        
        self.progress_bar.setVisible(False)