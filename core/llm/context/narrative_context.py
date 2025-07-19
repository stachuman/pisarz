"""
Narrative Context Manager for maintaining story continuity across scenes.

This module provides functionality to track and maintain narrative context
that can be used by LLM templates for consistent story continuation.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from core.logging_config import get_logger
from core.db import execute_query, execute_insert, execute_update
from i18n import _


class NarrativeContextManager:
    """Manages narrative context for story continuation."""
    
    def __init__(self, project_path: Path):
        """Initialize narrative context manager for a project."""
        self.logger = get_logger("llm.narrative_context")
        self.project_path = project_path
        self.db_path = project_path / "pisarz.db"
        
        if not self.db_path.exists():
            raise ValueError(_("Project database not found"))
        
        # Note: narrative_context table is created by the main database schema in db.py
        
        self.logger.info(_("Narrative context manager initialized"))
    
    def create_narrative_context(self, context_type: str, title: str, content: str, 
                                scene_id: Optional[int] = None, 
                                metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new narrative context entry.
        
        Args:
            context_type: Type of context (summary, character_state, plot_point, etc.)
            title: Title/name of the context entry
            content: The context content
            scene_id: Optional scene ID this context is associated with
            metadata: Optional metadata dictionary
            
        Returns:
            ID of the created context entry
        """
        try:
            # Get project ID
            project_data = execute_query(
                self.db_path,
                "SELECT id FROM projects LIMIT 1"
            )
            if not project_data:
                raise ValueError(_("Project not found in database"))
            
            project_id = project_data[0]["id"]
            
            # Prepare metadata
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Insert narrative context
            context_id = execute_insert(
                self.db_path,
                """INSERT INTO narrative_context 
                   (project_id, scene_id, context_type, title, content, metadata) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_id, scene_id, context_type, title, content, metadata_json)
            )
            
            self.logger.debug(_("Created narrative context: {} - {}").format(context_type, title))
            return context_id
            
        except Exception as e:
            self.logger.error(_("Failed to create narrative context: {}").format(str(e)))
            raise
    
    def get_active_context(self, context_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active narrative context entries.
        
        Args:
            context_type: Optional filter by context type
            
        Returns:
            List of narrative context entries
        """
        try:
            project_data = execute_query(
                self.db_path,
                "SELECT id FROM projects LIMIT 1"
            )
            if not project_data:
                return []
            
            project_id = project_data[0]["id"]
            
            if context_type:
                contexts = execute_query(
                    self.db_path,
                    """SELECT nc.*, s.title as scene_title 
                       FROM narrative_context nc
                       LEFT JOIN scenes s ON nc.scene_id = s.id
                       WHERE nc.project_id = ? AND nc.context_type = ? AND nc.is_active = 1
                       ORDER BY nc.updated_at DESC""",
                    (project_id, context_type)
                )
            else:
                contexts = execute_query(
                    self.db_path,
                    """SELECT nc.*, s.title as scene_title 
                       FROM narrative_context nc
                       LEFT JOIN scenes s ON nc.scene_id = s.id
                       WHERE nc.project_id = ? AND nc.is_active = 1
                       ORDER BY nc.context_type, nc.updated_at DESC""",
                    (project_id,)
                )
            
            # Parse metadata
            for context in contexts:
                if context.get('metadata'):
                    try:
                        context['metadata'] = json.loads(context['metadata'])
                    except json.JSONDecodeError:
                        context['metadata'] = {}
                else:
                    context['metadata'] = {}
            
            return contexts
            
        except Exception as e:
            self.logger.error(_("Failed to get active context: {}").format(str(e)))
            return []
    
    def update_narrative_context(self, context_id: int, title: Optional[str] = None, 
                                content: Optional[str] = None, 
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing narrative context entry.
        
        Args:
            context_id: ID of the context to update
            title: New title (optional)
            content: New content (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if update was successful
        """
        try:
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            
            if content is not None:
                updates.append("content = ?")
                params.append(content)
            
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
            
            if not updates:
                return True  # Nothing to update
            
            updates.append("updated_at = datetime('now')")
            params.append(context_id)
            
            sql = f"UPDATE narrative_context SET {', '.join(updates)} WHERE id = ?"
            
            execute_update(self.db_path, sql, tuple(params))
            
            self.logger.debug(_("Updated narrative context: {}").format(context_id))
            return True
            
        except Exception as e:
            self.logger.error(_("Failed to update narrative context: {}").format(str(e)))
            return False
    
    def deactivate_context(self, context_id: int) -> bool:
        """
        Deactivate a narrative context entry (soft delete).
        
        Args:
            context_id: ID of the context to deactivate
            
        Returns:
            True if deactivation was successful
        """
        try:
            execute_update(
                self.db_path,
                "UPDATE narrative_context SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (context_id,)
            )
            
            self.logger.debug(_("Deactivated narrative context: {}").format(context_id))
            return True
            
        except Exception as e:
            self.logger.error(_("Failed to deactivate narrative context: {}").format(str(e)))
            return False
    
    def get_context_for_scene(self, scene_id: int) -> List[Dict[str, Any]]:
        """
        Get narrative context associated with a specific scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            List of narrative context entries for the scene
        """
        try:
            contexts = execute_query(
                self.db_path,
                """SELECT * FROM narrative_context 
                   WHERE scene_id = ? AND is_active = 1
                   ORDER BY context_type, updated_at DESC""",
                (scene_id,)
            )
            
            # Parse metadata
            for context in contexts:
                if context.get('metadata'):
                    try:
                        context['metadata'] = json.loads(context['metadata'])
                    except json.JSONDecodeError:
                        context['metadata'] = {}
                else:
                    context['metadata'] = {}
            
            return contexts
            
        except Exception as e:
            self.logger.error(_("Failed to get context for scene: {}").format(str(e)))
            return []
    
    def deactivate_scene_context(self, scene_id: int, context_type: Optional[str] = None) -> bool:
        """
        Deactivate all context entries for a scene, optionally filtered by type.
        
        Args:
            scene_id: ID of the scene
            context_type: Optional filter by context type
            
        Returns:
            True if successful
        """
        try:
            if context_type:
                execute_update(
                    self.db_path,
                    """UPDATE narrative_context 
                       SET is_active = 0, updated_at = datetime('now') 
                       WHERE scene_id = ? AND context_type = ? AND is_active = 1""",
                    (scene_id, context_type)
                )
                self.logger.debug(_("Deactivated context type '{}' for scene {}").format(context_type, scene_id))
            else:
                execute_update(
                    self.db_path,
                    """UPDATE narrative_context 
                       SET is_active = 0, updated_at = datetime('now') 
                       WHERE scene_id = ? AND is_active = 1""",
                    (scene_id,)
                )
                self.logger.debug(_("Deactivated all context for scene {}").format(scene_id))
            
            return True
            
        except Exception as e:
            self.logger.error(_("Failed to deactivate scene context: {}").format(str(e)))
            return False
    
    def replace_scene_context(self, scene_id: int, context_type: str, title: str, 
                            content: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Replace all context of a specific type for a scene with new context.
        
        Args:
            scene_id: ID of the scene
            context_type: Type of context to replace
            title: Title for new context
            content: Content for new context
            metadata: Optional metadata
            
        Returns:
            ID of the newly created context entry
        """
        try:
            # First, deactivate existing context of this type for the scene
            self.deactivate_scene_context(scene_id, context_type)
            
            # Then create new context
            context_id = self.create_narrative_context(
                context_type=context_type,
                title=title,
                content=content,
                scene_id=scene_id,
                metadata=metadata
            )
            
            self.logger.debug(_("Replaced context type '{}' for scene {} with new context {}").format(
                context_type, scene_id, context_id))
            
            return context_id
            
        except Exception as e:
            self.logger.error(_("Failed to replace scene context: {}").format(str(e)))
            raise
    
    def reactivate_context(self, context_id: int) -> bool:
        """
        Reactivate a previously deactivated context entry.
        
        Args:
            context_id: ID of the context to reactivate
            
        Returns:
            True if successful
        """
        try:
            execute_update(
                self.db_path,
                "UPDATE narrative_context SET is_active = 1, updated_at = datetime('now') WHERE id = ?",
                (context_id,)
            )
            
            self.logger.debug(_("Reactivated narrative context: {}").format(context_id))
            return True
            
        except Exception as e:
            self.logger.error(_("Failed to reactivate narrative context: {}").format(str(e)))
            return False
    
    def build_context_summary(self, max_length: int = 2000) -> str:
        """
        Build a comprehensive context summary for LLM use.
        
        Args:
            max_length: Maximum length of the summary
            
        Returns:
            Formatted context summary
        """
        try:
            contexts = self.get_active_context()
            
            if not contexts:
                return ""
            
            # Group contexts by type
            context_groups = {}
            for context in contexts:
                context_type = context['context_type']
                if context_type not in context_groups:
                    context_groups[context_type] = []
                context_groups[context_type].append(context)
            
            # Build summary
            summary_parts = []
            
            for context_type, group_contexts in context_groups.items():
                type_summary = f"\n## {context_type.replace('_', ' ').title()}\n"
                
                for context in group_contexts[:3]:  # Limit to 3 most recent per type
                    type_summary += f"- **{context['title']}**: {context['content'][:200]}...\n"
                
                summary_parts.append(type_summary)
            
            full_summary = "\n".join(summary_parts)
            
            # Truncate if too long
            if len(full_summary) > max_length:
                full_summary = full_summary[:max_length] + "..."
            
            return full_summary
            
        except Exception as e:
            self.logger.error(_("Failed to build context summary: {}").format(str(e)))
            return ""
    
    def auto_generate_scene_summary(self, scene_id: int, scene_content: str) -> Optional[int]:
        """
        Automatically generate a narrative context summary for a scene.
        
        Args:
            scene_id: ID of the scene
            scene_content: Content of the scene
            
        Returns:
            ID of the created context entry, or None if failed
        """
        try:
            # Get scene info
            scene_data = execute_query(
                self.db_path,
                "SELECT title FROM scenes WHERE id = ?",
                (scene_id,)
            )
            
            if not scene_data:
                return None
            
            scene_title = scene_data[0]['title']
            
            # Extract key points from scene content (simplified extraction)
            content_preview = scene_content[:500] if scene_content else ""
            
            summary_content = f"Scene: {scene_title}\nKey events: {content_preview}"
            
            # Create narrative context
            context_id = self.create_narrative_context(
                context_type="scene_summary",
                title=f"Summary: {scene_title}",
                content=summary_content,
                scene_id=scene_id,
                metadata={
                    "auto_generated": True,
                    "scene_length": len(scene_content),
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            return context_id
            
        except Exception as e:
            self.logger.error(_("Failed to auto-generate scene summary: {}").format(str(e)))
            return None


def get_narrative_context_manager(project_path: Path) -> NarrativeContextManager:
    """Get a narrative context manager for the given project."""
    return NarrativeContextManager(project_path)