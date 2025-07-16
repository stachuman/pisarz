"""
Location management system for Pisarz writing application.

Handles CRUD operations for locations and manages tri-directional linking
between locations, scenes, and characters.
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from .db import get_db_connection
from .error_handler import get_error_handler, ErrorLevel, ErrorCategory

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """Represents a location in the story."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    name: str = ""
    type: str = ""  # Indoor/Outdoor/Mixed/Virtual
    description: str = ""
    atmosphere: str = ""
    details: str = ""
    significance: str = ""
    notes: str = ""
    created_at: Optional[str] = None


@dataclass
class PlotThread:
    """Represents a plot thread in the story."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    name: str = ""
    type: str = ""  # Main/Subplot/Arc/Theme
    description: str = ""
    status: str = "planned"  # planned/active/completed/abandoned
    priority: int = 1
    start_scene_id: Optional[int] = None
    end_scene_id: Optional[int] = None
    notes: str = ""
    created_at: Optional[str] = None


class LocationManager:
    """Manages location operations and relationships."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.error_handler = get_error_handler()
    
    def create_location(self, project_id: int, name: str, **kwargs) -> Optional[int]:
        """Create a new location and return its ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                location_data = {
                    'project_id': project_id,
                    'name': name,
                    'type': kwargs.get('type', ''),
                    'description': kwargs.get('description', ''),
                    'atmosphere': kwargs.get('atmosphere', ''),
                    'details': kwargs.get('details', ''),
                    'significance': kwargs.get('significance', ''),
                    'notes': kwargs.get('notes', '')
                }
                
                cursor = conn.execute("""
                    INSERT INTO locations (project_id, name, type, description, atmosphere, details, significance, notes)
                    VALUES (:project_id, :name, :type, :description, :atmosphere, :details, :significance, :notes)
                """, location_data)
                
                conn.commit()
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Creating location: {name}",
                                        show_to_user=False)
            return None
    
    def get_location(self, location_id: int) -> Optional[Location]:
        """Get a single location by ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM locations WHERE id = ?
                """, (location_id,))
                
                row = cursor.fetchone()
                if row:
                    return Location(**dict(row))
                return None
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting location: {location_id}",
                                        show_to_user=False)
            return None
    
    def get_locations(self, project_id: int) -> List[Location]:
        """Get all locations for a project."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM locations 
                    WHERE project_id = ?
                    ORDER BY name
                """, (project_id,))
                
                return [Location(**dict(row)) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting locations for project: {project_id}",
                                        show_to_user=False)
            return []
    
    def update_location(self, location_id: int, **kwargs) -> bool:
        """Update a location's properties."""
        try:
            # Build dynamic UPDATE query
            fields = []
            values = []
            
            for field in ['name', 'type', 'description', 'atmosphere', 'details', 'significance', 'notes']:
                if field in kwargs:
                    fields.append(f"{field} = ?")
                    values.append(kwargs[field])
            
            if not fields:
                return True  # Nothing to update
            
            values.append(location_id)
            
            with get_db_connection(self.db_path) as conn:
                conn.execute(f"""
                    UPDATE locations 
                    SET {', '.join(fields)}
                    WHERE id = ?
                """, values)
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Updating location: {location_id}",
                                        show_to_user=False)
            return False
    
    def delete_location(self, location_id: int) -> bool:
        """Delete a location and all its relationships."""
        try:
            with get_db_connection(self.db_path) as conn:
                # Delete relationships first
                conn.execute("DELETE FROM scene_locations WHERE location_id = ?", (location_id,))
                conn.execute("DELETE FROM character_locations WHERE location_id = ?", (location_id,))
                
                # Delete the location
                conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Deleting location: {location_id}",
                                        show_to_user=False)
            return False
    
    # Scene-Location relationships
    
    def link_location_to_scene(self, location_id: int, scene_id: int, role: str = "primary") -> bool:
        """Link a location to a scene with a specific role."""
        try:
            with get_db_connection(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO scene_locations (scene_id, location_id, role)
                    VALUES (?, ?, ?)
                """, (scene_id, location_id, role))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Linking location {location_id} to scene {scene_id}",
                                        show_to_user=False)
            return False
    
    def unlink_location_from_scene(self, location_id: int, scene_id: int) -> bool:
        """Remove link between location and scene."""
        try:
            with get_db_connection(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM scene_locations 
                    WHERE scene_id = ? AND location_id = ?
                """, (scene_id, location_id))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Unlinking location {location_id} from scene {scene_id}",
                                        show_to_user=False)
            return False
    
    def get_scene_locations(self, scene_id: int) -> List[Tuple[Location, str]]:
        """Get all locations linked to a scene with their roles."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT l.*, sl.role
                    FROM locations l
                    JOIN scene_locations sl ON l.id = sl.location_id
                    WHERE sl.scene_id = ?
                    ORDER BY sl.role, l.name
                """, (scene_id,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    role = row_dict.pop('role')
                    location = Location(**row_dict)
                    results.append((location, role))
                
                return results
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting locations for scene: {scene_id}",
                                        show_to_user=False)
            return []
    
    def get_location_scenes(self, location_id: int) -> List[Tuple[Dict, str]]:
        """Get all scenes that occur at a location with their roles."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT s.*, sl.role
                    FROM scenes s
                    JOIN scene_locations sl ON s.id = sl.scene_id
                    WHERE sl.location_id = ?
                    ORDER BY s.ord
                """, (location_id,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    role = row_dict.pop('role')
                    results.append((row_dict, role))
                
                return results
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting scenes for location: {location_id}",
                                        show_to_user=False)
            return []
    
    # Character-Location relationships
    
    def link_character_to_location(self, character_id: int, location_id: int, 
                                 relationship_type: str = "visits", description: str = "") -> bool:
        """Link a character to a location with relationship type."""
        try:
            with get_db_connection(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO character_locations 
                    (character_id, location_id, relationship_type, description)
                    VALUES (?, ?, ?, ?)
                """, (character_id, location_id, relationship_type, description))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Linking character {character_id} to location {location_id}",
                                        show_to_user=False)
            return False
    
    def unlink_character_from_location(self, character_id: int, location_id: int) -> bool:
        """Remove link between character and location."""
        try:
            with get_db_connection(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM character_locations 
                    WHERE character_id = ? AND location_id = ?
                """, (character_id, location_id))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Unlinking character {character_id} from location {location_id}",
                                        show_to_user=False)
            return False
    
    def get_location_characters(self, location_id: int) -> List[Tuple[Dict, str, str]]:
        """Get all characters associated with a location."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT c.*, cl.relationship_type, cl.description
                    FROM characters c
                    JOIN character_locations cl ON c.id = cl.character_id
                    WHERE cl.location_id = ?
                    ORDER BY c.importance DESC, c.name
                """, (location_id,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    relationship_type = row_dict.pop('relationship_type')
                    description = row_dict.pop('description')
                    results.append((row_dict, relationship_type, description))
                
                return results
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting characters for location: {location_id}",
                                        show_to_user=False)
            return []
    
    def get_character_locations(self, character_id: int) -> List[Tuple[Location, str, str]]:
        """Get all locations associated with a character."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT l.*, cl.relationship_type, cl.description
                    FROM locations l
                    JOIN character_locations cl ON l.id = cl.location_id
                    WHERE cl.character_id = ?
                    ORDER BY l.name
                """, (character_id,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    relationship_type = row_dict.pop('relationship_type')
                    description = row_dict.pop('description')
                    location = Location(**row_dict)
                    results.append((location, relationship_type, description))
                
                return results
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting locations for character: {character_id}",
                                        show_to_user=False)
            return []
    
    # Plot Thread operations
    
    def create_plot_thread(self, project_id: int, name: str, **kwargs) -> Optional[int]:
        """Create a new plot thread and return its ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                plot_data = {
                    'project_id': project_id,
                    'name': name,
                    'type': kwargs.get('type', ''),
                    'description': kwargs.get('description', ''),
                    'status': kwargs.get('status', 'planned'),
                    'priority': kwargs.get('priority', 1),
                    'start_scene_id': kwargs.get('start_scene_id'),
                    'end_scene_id': kwargs.get('end_scene_id'),
                    'notes': kwargs.get('notes', '')
                }
                
                cursor = conn.execute("""
                    INSERT INTO plot_threads 
                    (project_id, name, type, description, status, priority, start_scene_id, end_scene_id, notes)
                    VALUES (:project_id, :name, :type, :description, :status, :priority, :start_scene_id, :end_scene_id, :notes)
                """, plot_data)
                
                conn.commit()
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Creating plot thread: {name}",
                                        show_to_user=False)
            return None
    
    def get_plot_threads(self, project_id: int) -> List[PlotThread]:
        """Get all plot threads for a project."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM plot_threads 
                    WHERE project_id = ?
                    ORDER BY priority DESC, name
                """, (project_id,))
                
                return [PlotThread(**dict(row)) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Getting plot threads for project: {project_id}",
                                        show_to_user=False)
            return []
    
    def update_plot_thread(self, plot_id: int, **kwargs) -> bool:
        """Update a plot thread's properties."""
        try:
            fields = []
            values = []
            
            valid_fields = ['name', 'type', 'description', 'status', 'priority', 'start_scene_id', 'end_scene_id', 'notes']
            for field in valid_fields:
                if field in kwargs:
                    fields.append(f"{field} = ?")
                    values.append(kwargs[field])
            
            if not fields:
                return True
            
            values.append(plot_id)
            
            with get_db_connection(self.db_path) as conn:
                conn.execute(f"""
                    UPDATE plot_threads 
                    SET {', '.join(fields)}
                    WHERE id = ?
                """, values)
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Updating plot thread: {plot_id}",
                                        show_to_user=False)
            return False
    
    def delete_plot_thread(self, plot_id: int) -> bool:
        """Delete a plot thread and its scene associations."""
        try:
            with get_db_connection(self.db_path) as conn:
                # Delete scene associations first
                conn.execute("DELETE FROM scene_plot_threads WHERE plot_thread_id = ?", (plot_id,))
                
                # Delete the plot thread
                conn.execute("DELETE FROM plot_threads WHERE id = ?", (plot_id,))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.error_handler.log_error(e, ErrorCategory.DATABASE,
                                        context=f"Deleting plot thread: {plot_id}",
                                        show_to_user=False)
            return False