"""
Task registry for LLM operations.
Manages available tasks and their definitions.
"""

import logging
from typing import Dict, Optional, List
from core.logging_config import get_logger
from .definitions import TaskDefinition, TaskParameter, ParameterType


class TaskRegistry:
    """Registry for LLM tasks."""
    
    def __init__(self):
        self.logger = get_logger("llm.task_registry")
        self._tasks: Dict[str, TaskDefinition] = {}
        self._initialize_default_tasks()
    
    def _initialize_default_tasks(self):
        """Initialize default tasks for Phase 1."""
        # Continue scene task
        continue_scene = TaskDefinition(
            id="continue_scene",
            name="Continue Scene",
            description="Continue writing the current scene based on context",
            template="""Continue writing this scene naturally and creatively.

Current text: {current_text}

Scene context: {scene_summary}

Continue the scene in a way that flows naturally from the existing text. Keep the same tone and style."""
        )
        
        self.register_task(continue_scene)
        self.logger.info("Default tasks registered")
    
    def register_task(self, task: TaskDefinition):
        """Register a new task."""
        if task.id in self._tasks:
            self.logger.warning(f"Task {task.id} already exists, overwriting")
        
        self._tasks[task.id] = task
        self.logger.debug(f"Registered task: {task.id}")
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task definition by ID."""
        return self._tasks.get(task_id)
    
    def get_task_ids(self) -> List[str]:
        """Get list of all registered task IDs."""
        return list(self._tasks.keys())
    
    def get_all_tasks(self) -> Dict[str, TaskDefinition]:
        """Get all registered tasks."""
        return self._tasks.copy()
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from registry."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self.logger.debug(f"Removed task: {task_id}")
            return True
        return False
    
    def clear_tasks(self):
        """Clear all tasks from registry."""
        self._tasks.clear()
        self.logger.info("All tasks cleared from registry")
    
    def get_task_count(self) -> int:
        """Get number of registered tasks."""
        return len(self._tasks)