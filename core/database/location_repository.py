"""
Location repository using the new database access layer.
Replaces the LocationManager with cleaner, more maintainable code.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from .base_repository import BaseRepository


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


class LocationRepository(BaseRepository[Location]):
    """Repository for location data access."""
    
    @property
    def table_name(self) -> str:
        return "locations"
    
    @property
    def model_class(self) -> type[Location]:
        return Location
    
    @property
    def required_fields(self) -> List[str]:
        return ["project_id", "name"]
    
    def get_by_project(self, project_id: int) -> List[Location]:
        """Get all locations for a specific project."""
        return self.get_all(where={"project_id": project_id}, order_by="name ASC")
    
    def search_by_name(self, project_id: int, name_pattern: str) -> List[Location]:
        """Search locations by name pattern."""
        return self.get_all(
            where={
                "project_id": project_id,
                "name": {"LIKE": f"%{name_pattern}%"}
            },
            order_by="name ASC"
        )
    
    def get_by_type(self, project_id: int, location_type: str) -> List[Location]:
        """Get locations by type."""
        return self.get_all(
            where={"project_id": project_id, "type": location_type},
            order_by="name ASC"
        )
    
    def get_by_scene(self, scene_id: int) -> List[Location]:
        """Get locations associated with a specific scene."""
        query = """
            SELECT l.* FROM locations l
            JOIN scene_locations sl ON l.id = sl.location_id
            WHERE sl.scene_id = ?
            ORDER BY l.name ASC
        """
        rows = self.execute_custom_query(query, [scene_id])
        return [self._row_to_model(row) for row in rows]
    
    def get_by_scene_with_roles(self, scene_id: int) -> List[tuple]:
        """Get locations in a scene with their roles. Returns list of (Location, role) tuples."""
        query = """
            SELECT l.*, sl.role FROM locations l
            JOIN scene_locations sl ON l.id = sl.location_id
            WHERE sl.scene_id = ?
            ORDER BY l.name ASC
        """
        rows = self.execute_custom_query(query, [scene_id])
        
        result = []
        for row in rows:
            try:
                # Convert row to dictionary first
                row_dict = dict(row) if hasattr(row, 'keys') else {}
                if not row_dict:
                    continue
                    
                # Extract role and remove it from location data
                role = row_dict.pop('role', '')
                
                # Create location from remaining data
                from dataclasses import fields
                location = self.model_class(**{k: v for k, v in row_dict.items() 
                                              if k in {f.name for f in fields(self.model_class)}})
                result.append((location, role))
            except Exception as e:
                self.logger.error(f"Error processing location with role from scene {scene_id}: {e}")
                continue
        
        return result
    
    def link_to_scene(self, location_id: int, scene_id: int, role: str = "") -> bool:
        """Link a location to a scene."""
        try:
            # Use direct database connection with commit for INSERT operation
            from core.db import get_db_connection
            with get_db_connection(self.db_path) as conn:
                query = "INSERT OR REPLACE INTO scene_locations (scene_id, location_id, role) VALUES (?, ?, ?)"
                cursor = conn.execute(query, [scene_id, location_id, role])
                conn.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error linking location {location_id} to scene {scene_id}: {e}")
            return False
    
    def unlink_from_scene(self, location_id: int, scene_id: int) -> bool:
        """Unlink a location from a scene."""
        try:
            # Use direct database connection with commit for DELETE operation
            from core.db import get_db_connection
            with get_db_connection(self.db_path) as conn:
                query = "DELETE FROM scene_locations WHERE scene_id = ? AND location_id = ?"
                cursor = conn.execute(query, [scene_id, location_id])
                conn.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error unlinking location {location_id} from scene {scene_id}: {e}")
            return False
    
    def get_location_dependencies(self, location_id: int) -> dict:
        """Get all dependencies for a location (where it's used)."""
        dependencies = {
            'scenes': [],
            'characters': [],
            'total_count': 0
        }
        
        try:
            # Get scenes that use this location
            query = """
                SELECT s.id, s.title, s.ord, sl.role 
                FROM scenes s
                JOIN scene_locations sl ON s.id = sl.scene_id
                WHERE sl.location_id = ?
                ORDER BY s.ord ASC, s.title ASC
            """
            rows = self.execute_custom_query(query, [location_id])
            
            for row in rows:
                scene_info = {
                    'id': row['id'] if hasattr(row, 'keys') else row[0],
                    'title': row['title'] if hasattr(row, 'keys') else row[1],
                    'ord': row['ord'] if hasattr(row, 'keys') else row[2],
                    'role': row['role'] if hasattr(row, 'keys') else row[3]
                }
                dependencies['scenes'].append(scene_info)
            
            # Get characters linked to this location (if character_locations table exists)
            try:
                query = """
                    SELECT c.id, c.name, cl.relationship_type, cl.description
                    FROM characters c
                    JOIN character_locations cl ON c.id = cl.character_id
                    WHERE cl.location_id = ?
                    ORDER BY c.name ASC
                """
                rows = self.execute_custom_query(query, [location_id])
                
                for row in rows:
                    char_info = {
                        'id': row['id'] if hasattr(row, 'keys') else row[0],
                        'name': row['name'] if hasattr(row, 'keys') else row[1],
                        'relationship_type': row['relationship_type'] if hasattr(row, 'keys') else row[2],
                        'description': row['description'] if hasattr(row, 'keys') else row[3]
                    }
                    dependencies['characters'].append(char_info)
            except Exception:
                # Table might not exist, that's okay
                pass
            
            dependencies['total_count'] = len(dependencies['scenes']) + len(dependencies['characters'])
            
        except Exception as e:
            self.logger.error(f"Error getting dependencies for location {location_id}: {e}")
        
        return dependencies
    
    def delete_with_cascade(self, location_id: int) -> bool:
        """Delete a location and cascade delete from all related tables."""
        try:
            from core.db import get_db_connection
            with get_db_connection(self.db_path) as conn:
                # Start transaction
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # Delete from scene_locations table first (foreign key dependency)
                    conn.execute("DELETE FROM scene_locations WHERE location_id = ?", [location_id])
                    
                    # Delete from character_locations table if it exists
                    try:
                        conn.execute("DELETE FROM character_locations WHERE location_id = ?", [location_id])
                    except Exception:
                        # Table might not exist, that's okay
                        pass
                    
                    # Delete the location itself
                    conn.execute("DELETE FROM locations WHERE id = ?", [location_id])
                    
                    # Commit transaction
                    conn.commit()
                    
                    self.logger.info(f"Successfully deleted location {location_id} with cascade")
                    return True
                    
                except Exception as e:
                    # Rollback on any error
                    conn.rollback()
                    self.logger.error(f"Error in cascade delete transaction for location {location_id}: {e}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error deleting location {location_id} with cascade: {e}")
            return False


class PlotThreadRepository(BaseRepository[PlotThread]):
    """Repository for plot thread data access."""
    
    @property
    def table_name(self) -> str:
        return "plot_threads"
    
    @property
    def model_class(self) -> type[PlotThread]:
        return PlotThread
    
    @property
    def required_fields(self) -> List[str]:
        return ["project_id", "name"]
    
    def get_by_project(self, project_id: int) -> List[PlotThread]:
        """Get all plot threads for a specific project."""
        return self.get_all(
            where={"project_id": project_id}, 
            order_by="priority DESC, name ASC"
        )
    
    def get_by_status(self, project_id: int, status: str) -> List[PlotThread]:
        """Get plot threads by status."""
        return self.get_all(
            where={"project_id": project_id, "status": status},
            order_by="priority DESC, name ASC"
        )
    
    def get_active_threads(self, project_id: int) -> List[PlotThread]:
        """Get active plot threads."""
        return self.get_by_status(project_id, "active")
    
    def get_by_scene(self, scene_id: int) -> List[PlotThread]:
        """Get plot threads involving a specific scene."""
        query = """
            SELECT * FROM plot_threads 
            WHERE start_scene_id = ? OR end_scene_id = ?
            ORDER BY priority DESC, name ASC
        """
        rows = self.execute_custom_query(query, [scene_id, scene_id])
        return [self._row_to_model(row) for row in rows]


class LocationManager:
    """
    Modernized location manager using the new repository pattern.
    Provides backward compatibility while using the new database layer.
    """
    
    def __init__(self, db_path: Path = None):
        from core.llm.settings import GLOBAL_DB_PATH
        self.db_path = db_path or GLOBAL_DB_PATH
        self.location_repo = LocationRepository(db_path)
        self.plot_repo = PlotThreadRepository(db_path)
    
    # Location methods
    def create_location(self, project_id: int, name: str, **kwargs) -> Optional[int]:
        """Create a new location."""
        return self.location_repo.create(project_id=project_id, name=name, **kwargs)
    
    def get_location(self, location_id: int) -> Optional[Dict[str, Any]]:
        """Get a location by ID (returns dictionary for backward compatibility)."""
        location = self.location_repo.get_by_id(location_id)
        return asdict(location) if location else None
    
    def get_location_object(self, location_id: int) -> Optional[Location]:
        """Get a location by ID as a Location dataclass object."""
        return self.location_repo.get_by_id(location_id)
    
    def get_locations(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all locations for a project."""
        locations = self.location_repo.get_by_project(project_id)
        return [asdict(loc) for loc in locations]
    
    def get_locations_by_project(self, project_id: int) -> List[Location]:
        """Get all locations for a project (returns dataclass objects)."""
        return self.location_repo.get_by_project(project_id)
    
    def get_location_objects(self, project_id: int) -> List[Location]:
        """Get all locations for a project as Location objects (alias for get_locations_by_project)."""
        return self.location_repo.get_by_project(project_id)
    
    def update_location(self, location_id: int, **kwargs) -> bool:
        """Update a location."""
        return self.location_repo.update(location_id, **kwargs)
    
    def delete_location(self, location_id: int) -> bool:
        """Delete a location with cascade deletion from all related tables."""
        return self.location_repo.delete_with_cascade(location_id)
    
    def search_locations(self, project_id: int, name_pattern: str) -> List[Location]:
        """Search locations by name."""
        return self.location_repo.search_by_name(project_id, name_pattern)
    
    def get_scene_locations(self, scene_id: int) -> List[tuple]:
        """Get locations associated with a specific scene. Returns list of (location_object, role) tuples."""
        try:
            # Use the repository method that returns (Location, role) tuples
            location_role_pairs = self.location_repo.get_by_scene_with_roles(scene_id)
            return location_role_pairs
        except Exception as e:
            self.location_repo.logger.error(f"Error getting locations for scene {scene_id}: {e}")
            return []
    
    def get_location_scenes(self, location_id: int) -> List[tuple]:
        """Get scenes that use a specific location. Returns list of (scene_dict, role) tuples."""
        try:
            query = """
                SELECT s.*, sl.role FROM scenes s
                JOIN scene_locations sl ON s.id = sl.scene_id
                WHERE sl.location_id = ?
                ORDER BY s.ord ASC, s.title ASC
            """
            rows = self.location_repo.execute_custom_query(query, [location_id])
            
            result = []
            for row in rows:
                try:
                    # Convert row to dictionary
                    row_dict = dict(row) if hasattr(row, 'keys') else {}
                    if not row_dict:
                        continue
                    
                    # Extract role and remove it from scene data  
                    role = row_dict.pop('role', '')
                    
                    # Create scene dictionary (remaining data)
                    result.append((row_dict, role))
                except Exception as e:
                    self.location_repo.logger.error(f"Error processing scene for location {location_id}: {e}")
                    continue
            return result
        except Exception as e:
            self.location_repo.logger.error(f"Error getting scenes for location {location_id}: {e}")
            return []
    
    def get_location_characters(self, location_id: int) -> List[tuple]:
        """Get characters associated with a location. Returns list of (char_dict, relationship, description) tuples."""
        try:
            query = """
                SELECT c.*, cl.relationship_type, cl.description FROM characters c
                JOIN character_locations cl ON c.id = cl.character_id
                WHERE cl.location_id = ?
                ORDER BY c.importance DESC, c.name ASC
            """
            rows = self.location_repo.execute_custom_query(query, [location_id])
            
            result = []
            for row in rows:
                try:
                    # Convert row to dictionary
                    row_dict = dict(row) if hasattr(row, 'keys') else {}
                    if not row_dict:
                        continue
                    
                    # Extract relationship and description
                    relationship = row_dict.pop('relationship_type', '')
                    description = row_dict.pop('description', '')
                    
                    # Create character dictionary (remaining data)
                    result.append((row_dict, relationship, description))
                except Exception as e:
                    self.location_repo.logger.error(f"Error processing character for location {location_id}: {e}")
                    continue
            return result
        except Exception as e:
            self.location_repo.logger.error(f"Error getting characters for location {location_id}: {e}")
            return []
    
    # Plot thread methods
    def create_plot_thread(self, project_id: int, name: str, **kwargs) -> Optional[int]:
        """Create a new plot thread."""
        return self.plot_repo.create(project_id=project_id, name=name, **kwargs)
    
    def get_plot_thread(self, thread_id: int) -> Optional[PlotThread]:
        """Get a plot thread by ID."""
        return self.plot_repo.get_by_id(thread_id)
    
    def get_plot_threads_by_project(self, project_id: int) -> List[PlotThread]:
        """Get all plot threads for a project."""
        return self.plot_repo.get_by_project(project_id)
    
    def update_plot_thread(self, thread_id: int, **kwargs) -> bool:
        """Update a plot thread."""
        return self.plot_repo.update(thread_id, **kwargs)
    
    def delete_plot_thread(self, thread_id: int) -> bool:
        """Delete a plot thread."""
        return self.plot_repo.delete(thread_id)
    
    def get_active_plot_threads(self, project_id: int) -> List[PlotThread]:
        """Get active plot threads."""
        return self.plot_repo.get_active_threads(project_id)
    
    # Additional convenience methods
    def get_location_count(self, project_id: int) -> int:
        """Get the number of locations in a project."""
        return self.location_repo.count({"project_id": project_id})
    
    def get_location_dependencies(self, location_id: int) -> dict:
        """Get all dependencies for a location (where it's used)."""
        return self.location_repo.get_location_dependencies(location_id)
    
    def get_plot_thread_count(self, project_id: int) -> int:
        """Get the number of plot threads in a project."""
        return self.plot_repo.count({"project_id": project_id})
    
    def location_exists(self, project_id: int, name: str) -> bool:
        """Check if a location with the given name exists."""
        return self.location_repo.exists({"project_id": project_id, "name": name})
    
    def plot_thread_exists(self, project_id: int, name: str) -> bool:
        """Check if a plot thread with the given name exists."""
        return self.plot_repo.exists({"project_id": project_id, "name": name})
    
    # Scene-Location linking methods
    def link_location_to_scene(self, location_id: int, scene_id: int, role: str = "") -> bool:
        """Link a location to a scene."""
        return self.location_repo.link_to_scene(location_id, scene_id, role)
    
    def unlink_location_from_scene(self, location_id: int, scene_id: int) -> bool:
        """Unlink a location from a scene."""
        return self.location_repo.unlink_from_scene(location_id, scene_id)