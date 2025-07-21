"""
Narrative context repository using the new database access layer.
Replaces narrative context management with clean repository pattern.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import json

from .base_repository import BaseRepository
from core.logging_config import get_logger


@dataclass
class NarrativeContext:
    """Represents a narrative context entry."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    scene_id: Optional[int] = None
    context_type: str = "general"  # general, character, plot, setting, etc.
    title: str = ""
    content: str = ""
    metadata: str = "{}"  # JSON string for additional data
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True


class NarrativeContextRepository(BaseRepository[NarrativeContext]):
    """Repository for narrative context data access."""
    
    @property
    def table_name(self) -> str:
        return "narrative_context"
    
    @property
    def model_class(self) -> type[NarrativeContext]:
        return NarrativeContext
    
    @property
    def required_fields(self) -> List[str]:
        return ["project_id", "title"]
    
    def get_active_contexts(self, project_id: int) -> List[NarrativeContext]:
        """Get all active narrative contexts for a project."""
        return self.get_all(
            where={"project_id": project_id, "is_active": True},
            order_by="created_at ASC"
        )
    
    def get_by_type(self, project_id: int, context_type: str, active_only: bool = True) -> List[NarrativeContext]:
        """Get narrative contexts by type."""
        where = {"project_id": project_id, "context_type": context_type}
        if active_only:
            where["is_active"] = True
        
        return self.get_all(
            where=where,
            order_by="created_at ASC"
        )
    
    def get_by_scene(self, scene_id: int, active_only: bool = True) -> List[NarrativeContext]:
        """Get narrative contexts associated with a specific scene."""
        where = {"scene_id": scene_id}
        if active_only:
            where["is_active"] = True
        
        return self.get_all(
            where=where,
            order_by="created_at ASC"
        )
    
    
    def search_content(self, project_id: int, search_term: str, active_only: bool = True) -> List[NarrativeContext]:
        """Search narrative contexts by content."""
        where = {
            "project_id": project_id,
            "content": {"LIKE": f"%{search_term}%"}
        }
        if active_only:
            where["is_active"] = True
        
        return self.get_all(
            where=where,
            order_by="created_at ASC"
        )
    
    def deactivate_context(self, context_id: int) -> bool:
        """Deactivate a narrative context."""
        return self.update(context_id, is_active=False)
    
    def activate_context(self, context_id: int) -> bool:
        """Activate a narrative context."""
        return self.update(context_id, is_active=True)
    
    
    def get_context_summary(self, project_id: int) -> Dict[str, Any]:
        """Get a summary of narrative contexts for a project."""
        total_contexts = self.count({"project_id": project_id})
        active_contexts = self.count({"project_id": project_id, "is_active": True})
        
        # Get context types distribution
        query = """
            SELECT context_type, COUNT(*) as count
            FROM narrative_context 
            WHERE project_id = ? AND is_active = 1
            GROUP BY context_type
            ORDER BY count DESC
        """
        
        type_distribution = {}
        try:
            rows = self.execute_custom_query(query, [project_id])
            for row in rows:
                type_distribution[row[0]] = row[1]
        except Exception as e:
            self.logger.error(f"Error getting context type distribution: {e}")
        
        return {
            "total_contexts": total_contexts,
            "active_contexts": active_contexts,
            "inactive_contexts": total_contexts - active_contexts,
            "type_distribution": type_distribution
        }


class NarrativeContextManager:
    """
    Narrative context manager using the new repository pattern.
    Provides backward compatibility while using the new database layer.
    """
    
    def __init__(self, project_path: Path):
        """Initialize narrative context manager for a project."""
        self.project_path = project_path
        self.db_path = project_path / "pisarz.db"
        self.context_repo = NarrativeContextRepository(self.db_path)
        self.logger = get_logger(__name__)
        
        if not self.db_path.exists():
            raise ValueError("Project database not found")
    
    def create_context(self, project_id: int, title: str, **kwargs) -> Optional[int]:
        """Create a new narrative context. If scene_id is provided, replaces any existing contexts for that scene."""
        scene_id = kwargs.get('scene_id')
        if scene_id:
            # If creating context for a specific scene, ensure consistency by replacing existing contexts
            context_type = kwargs.get('context_type', 'general')
            content = kwargs.get('content', '')
            metadata = kwargs.get('metadata')
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {}
            return self.replace_scene_context(scene_id, context_type, title, content, metadata)
        else:
            # For non-scene contexts, use regular create
            return self.context_repo.create(project_id=project_id, title=title, **kwargs)
    
    def get_context(self, context_id: int) -> Optional[Dict[str, Any]]:
        """Get a narrative context by ID."""
        context = self.context_repo.get_by_id(context_id)
        return asdict(context) if context else None
    
    def update_context(self, context_id: int, **kwargs) -> bool:
        """Update a narrative context."""
        return self.context_repo.update(context_id, **kwargs)
    
    def delete_context(self, context_id: int) -> bool:
        """Delete a narrative context."""
        return self.context_repo.delete(context_id)
    
    def get_active_contexts(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all active narrative contexts for a project."""
        contexts = self.context_repo.get_active_contexts(project_id)
        return [asdict(context) for context in contexts]
    
    def get_contexts_by_type(self, project_id: int, context_type: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get narrative contexts by type."""
        contexts = self.context_repo.get_by_type(project_id, context_type, active_only)
        return [asdict(context) for context in contexts]
    
    def get_contexts_by_scene(self, scene_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get narrative contexts for a scene."""
        contexts = self.context_repo.get_by_scene(scene_id, active_only)
        return [asdict(context) for context in contexts]
    
    
    def search_contexts(self, project_id: int, search_term: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Search narrative contexts by content."""
        contexts = self.context_repo.search_content(project_id, search_term, active_only)
        return [asdict(context) for context in contexts]
    
    def deactivate_context(self, context_id: int) -> bool:
        """Deactivate a narrative context."""
        return self.context_repo.deactivate_context(context_id)
    
    def activate_context(self, context_id: int) -> bool:
        """Activate a narrative context."""
        return self.context_repo.activate_context(context_id)
    
    def get_context_summary(self, project_id: int) -> Dict[str, Any]:
        """Get a summary of narrative contexts."""
        return self.context_repo.get_context_summary(project_id)
    
    def update_context_metadata(self, context_id: int, metadata: Dict[str, Any]) -> bool:
        """Update context metadata."""
        metadata_json = json.dumps(metadata)
        return self.context_repo.update(context_id, metadata=metadata_json)
    
    def get_context_metadata(self, context_id: int) -> Dict[str, Any]:
        """Get context metadata as a dictionary."""
        context = self.context_repo.get_by_id(context_id)
        if context and context.metadata:
            try:
                return json.loads(context.metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def build_context_summary(self, max_length: int = 1500) -> str:
        """Build a context summary from all active contexts."""
        try:
            # This is a simplified implementation - we need project_id
            # For now, return empty string to prevent errors
            return ""
        except Exception as e:
            return ""
    
    def replace_scene_context(self, scene_id: int, context_type: str, title: str, content: str, metadata: Dict[str, Any] = None) -> Optional[int]:
        """Replace ALL existing contexts for a scene with a single new context. 
        Ensures consistency: each scene has either no context or exactly one active context."""
        try:
            # Get project_id from scene_id by checking existing contexts or querying scenes table
            project_id = None
            
            # First try to get project_id from existing contexts for this scene
            existing_any_contexts = self.context_repo.get_all(where={"scene_id": scene_id})
            if existing_any_contexts:
                project_id = existing_any_contexts[0].project_id
            
            # If no existing contexts, query the scenes table to get project_id
            if not project_id:
                scenes_query = "SELECT project_id FROM scenes WHERE id = ?"
                scenes_rows = self.context_repo.execute_custom_query(scenes_query, [scene_id])
                if scenes_rows:
                    project_id = scenes_rows[0][0]
            
            if not project_id:
                self.logger.error(f"Could not determine project_id for scene_id {scene_id}")
                return None
            
            # Delete ALL existing contexts for this scene (regardless of type)
            # This ensures consistency: only one context per scene
            all_existing_contexts = self.context_repo.get_all(where={"scene_id": scene_id})
            for context in all_existing_contexts:
                if context.id:
                    self.context_repo.delete(context.id)
                    self.logger.debug(f"Deleted existing context {context.id} of type {context.context_type} for scene {scene_id}")
            
            # Create new context - this will be the ONLY context for this scene
            metadata_json = json.dumps(metadata) if metadata else "{}"
            context_id = self.context_repo.create(
                project_id=project_id,
                scene_id=scene_id,
                context_type=context_type,
                title=title,
                content=content,
                metadata=metadata_json,
                is_active=True
            )
            
            self.logger.info(f"Created new context {context_id} of type {context_type} for scene {scene_id}, replaced all previous contexts")
            return context_id
            
        except Exception as e:
            self.logger.error(f"Error replacing scene context: {e}")
            return None