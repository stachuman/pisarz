"""
Data models for export functionality.
Defines the configuration and result structures for export operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ExportScopeType(Enum):
    """Export scope types"""
    CURRENT_SCENE = "current_scene"
    SELECTED_SCENES = "selected_scenes"
    ALL_SCENES = "all_scenes"
    FULL_PROJECT = "full_project"


class ExportFormat(Enum):
    """Supported export formats"""
    PDF = "pdf"
    TXT = "txt"
    HTML = "html"
    DOCX = "docx"
    JSON = "json"


@dataclass
class ExportScope:
    """Defines what data to export"""
    project_id: int
    scope_type: ExportScopeType
    scene_ids: Optional[List[int]] = None
    include_characters: bool = True
    include_locations: bool = True
    include_metadata: bool = True
    
    def __post_init__(self):
        """Validate scope configuration"""
        if self.scope_type == ExportScopeType.SELECTED_SCENES and not self.scene_ids:
            raise ValueError("scene_ids required when scope_type is SELECTED_SCENES")
        if self.scope_type == ExportScopeType.CURRENT_SCENE and not self.scene_ids:
            raise ValueError("scene_ids required when scope_type is CURRENT_SCENE")


@dataclass
class ExportConfig:
    """Export configuration parameters"""
    scope: ExportScope
    format: ExportFormat
    output_path: str
    template_name: str = "default"
    styling_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate export configuration"""
        if not self.output_path:
            raise ValueError("output_path is required")
        if not self.scope:
            raise ValueError("scope is required")


@dataclass
class ExportResult:
    """Result of export operation"""
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    exported_items_count: int = 0
    file_size_bytes: int = 0
    format_used: Optional[ExportFormat] = None
    duration_seconds: float = 0.0
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.file_size_bytes / (1024 * 1024) if self.file_size_bytes > 0 else 0.0
    
    def __str__(self) -> str:
        """String representation for logging"""
        if self.success:
            return f"Export successful: {self.exported_items_count} items to {self.output_path}"
        else:
            return f"Export failed: {self.error_message}"


@dataclass
class ExportData:
    """Container for data to be exported"""
    project_metadata: Dict[str, Any]
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    characters: List[Dict[str, Any]] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def total_items(self) -> int:
        """Total number of items to export"""
        return len(self.scenes) + len(self.characters) + len(self.locations)
    
    @property
    def total_word_count(self) -> int:
        """Total word count from all scenes"""
        return sum(scene.get('word_count', 0) for scene in self.scenes)