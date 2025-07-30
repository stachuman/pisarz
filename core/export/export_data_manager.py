"""
Export Data Manager - Leverages existing repository pattern and managers.
Provides clean data access for export operations using the existing infrastructure.
"""

import logging
from typing import Dict, Any, List, Optional

from .models import ExportScope, ExportScopeType, ExportData
from ..error_handler import get_error_handler, ErrorLevel, ErrorCategory


class ExportDataManager:
    """
    Manages data access for export operations using existing managers.
    Reuses AppProjectController's managers to ensure fresh data access.
    """
    
    def __init__(self, project_controller):
        """
        Initialize with project controller to access existing managers.
        
        Args:
            project_controller: AppProjectController instance
        """
        self.project_controller = project_controller
        self.managers = project_controller.get_current_managers()
        self.error_handler = get_error_handler()
        self.logger = logging.getLogger(__name__)
        
        # Validate that we have a current project loaded
        if not project_controller.has_current_project():
            raise ValueError("No project currently loaded in project controller")
    
    def get_export_data(self, scope: ExportScope) -> Optional[ExportData]:
        """
        Get all data needed for export based on scope.
        
        Args:
            scope: ExportScope defining what to export
            
        Returns:
            ExportData container with all requested data, or None if error
        """
        try:
            
            # Get project metadata
            project_metadata = self.get_project_metadata(scope.project_id)
            if not project_metadata:
                self.logger.error(f"Failed to get project metadata for project {scope.project_id}")
                return None
            
            # Initialize export data container
            export_data = ExportData(project_metadata=project_metadata)
            
            # Get scenes based on scope
            scenes = self.get_scenes_for_export(scope)
            if scenes is not None:
                export_data.scenes = scenes
            else:
                self.logger.warning("Failed to get scenes for export")
                return None
            
            # Get characters if requested
            if scope.include_characters:
                characters = self.get_characters_for_export(scope)
                if characters is not None:
                    export_data.characters = characters
                else:
                    self.logger.warning("Failed to get characters for export")
            
            # Get locations if requested
            if scope.include_locations:
                locations = self.get_locations_for_export(scope)
                if locations is not None:
                    export_data.locations = locations
                else:
                    self.logger.warning("Failed to get locations for export")
            
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error getting export data: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to get export data for scope {scope.scope_type.value}"
            )
            return None
    
    def get_scenes_for_export(self, scope: ExportScope) -> Optional[List[Dict[str, Any]]]:
        """
        Get scenes using existing SceneManager methods.
        
        Args:
            scope: ExportScope defining which scenes to get
            
        Returns:
            List of scene dictionaries, or None if error
        """
        try:
            scene_manager = self.managers.get('scene_manager')
            if not scene_manager:
                raise RuntimeError("Scene manager not available in project controller")
            
            if scope.scope_type == ExportScopeType.ALL_SCENES:
                # Get all scenes for the project
                scenes = scene_manager.get_scenes_by_project(scope.project_id)
                
            elif scope.scope_type in [ExportScopeType.CURRENT_SCENE, ExportScopeType.SELECTED_SCENES]:
                # Get specific scenes by ID
                if not scope.scene_ids:
                    raise ValueError(f"scene_ids required for scope type {scope.scope_type.value}")
                
                scenes = []
                for scene_id in scope.scene_ids:
                    scene = scene_manager.get_scene(scene_id)
                    if scene:
                        scenes.append(scene)
                    else:
                        self.logger.warning(f"Scene {scene_id} not found")
                        
            elif scope.scope_type == ExportScopeType.FULL_PROJECT:
                # For full project, include all scenes
                scenes = scene_manager.get_scenes_by_project(scope.project_id)
                
            else:
                raise ValueError(f"Unsupported scope type: {scope.scope_type}")
            
            return scenes
            
        except Exception as e:
            self.logger.error(f"Error getting scenes for export: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to get scenes for scope {scope.scope_type.value}"
            )
            return None
    
    def get_characters_for_export(self, scope: ExportScope) -> Optional[List[Dict[str, Any]]]:
        """
        Get characters using existing CharacterManager methods.
        
        Args:
            scope: ExportScope defining the project
            
        Returns:
            List of character dictionaries, or None if error
        """
        try:
            character_manager = self.managers.get('character_manager')
            if not character_manager:
                raise RuntimeError("Character manager not available in project controller")
            
            # Get all characters for the project
            characters = character_manager.get_characters(scope.project_id)
            
            return characters
            
        except Exception as e:
            self.logger.error(f"Error getting characters for export: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to get characters for project {scope.project_id}"
            )
            return None
    
    def get_locations_for_export(self, scope: ExportScope) -> Optional[List[Dict[str, Any]]]:
        """
        Get locations using existing LocationManager methods.
        
        Args:
            scope: ExportScope defining the project
            
        Returns:
            List of location dictionaries, or None if error
        """
        try:
            location_manager = self.managers.get('location_manager')
            if not location_manager:
                raise RuntimeError("Location manager not available in project controller")
            
            # Get all locations for the project
            locations = location_manager.get_locations(scope.project_id)
            
            return locations
            
        except Exception as e:
            self.logger.error(f"Error getting locations for export: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to get locations for project {scope.project_id}"
            )
            return None
    
    def get_project_metadata(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Get project metadata using existing ProjectManager methods.
        
        Args:
            project_id: Project ID to get metadata for
            
        Returns:
            Dictionary with project metadata, or None if error
        """
        try:
            project_manager = self.managers.get('project_manager')
            if not project_manager:
                raise RuntimeError("Project manager not available in project controller")
            
            # Get project data using existing method
            project_data = project_manager.get_project_data(project_id)
            
            if not project_data:
                raise ValueError(f"Project {project_id} not found")
            
            return project_data
            
        except Exception as e:
            self.logger.error(f"Error getting project metadata: {e}")
            self.error_handler.handle_error(
                e, ErrorLevel.ERROR, ErrorCategory.DATABASE,
                f"Failed to get project metadata for project {project_id}"
            )
            return None
    
    def get_current_project_id(self) -> Optional[int]:
        """
        Get the current project ID from the project controller.
        
        Returns:
            Current project ID, or None if no project loaded
        """
        return self.project_controller.get_project_id()
    
    def validate_scope(self, scope: ExportScope) -> List[str]:
        """
        Validate that the export scope is feasible with current data.
        
        Args:
            scope: ExportScope to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            # Check if project exists
            if not self.get_project_metadata(scope.project_id):
                errors.append(f"Project {scope.project_id} not found")
                return errors  # Don't continue validation if project missing
            
            # Check specific scene IDs if provided
            if scope.scene_ids:
                scene_manager = self.managers.get('scene_manager')
                if scene_manager:
                    for scene_id in scope.scene_ids:
                        scene = scene_manager.get_scene(scene_id)
                        if not scene:
                            errors.append(f"Scene {scene_id} not found")
                else:
                    errors.append("Scene manager not available")
            
            # Check if there are any scenes to export
            scenes = self.get_scenes_for_export(scope)
            if scenes is not None and len(scenes) == 0:
                errors.append("No scenes found to export")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors