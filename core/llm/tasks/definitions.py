"""
Task definitions for LLM operations.
Defines the structure and parameters for different AI writing tasks.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ParameterType(Enum):
    """Types of task parameters."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CHOICE = "choice"


@dataclass
class TaskParameter:
    """Definition of a task parameter."""
    name: str
    type: ParameterType
    description: str
    default: Any = None
    required: bool = True
    choices: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def validate(self, value: Any) -> bool:
        """Validate parameter value."""
        if value is None:
            return not self.required
        
        if self.type == ParameterType.STRING:
            return isinstance(value, str)
        elif self.type == ParameterType.INTEGER:
            if not isinstance(value, int):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
            return True
        elif self.type == ParameterType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
            return True
        elif self.type == ParameterType.BOOLEAN:
            return isinstance(value, bool)
        elif self.type == ParameterType.CHOICE:
            return self.choices is not None and value in self.choices
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter to dictionary."""
        return {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'default': self.default,
            'required': self.required,
            'choices': self.choices,
            'min_value': self.min_value,
            'max_value': self.max_value
        }


@dataclass
class TaskDefinition:
    """Definition of an LLM task."""
    id: str
    name: str
    description: str
    template: str
    parameters: List[TaskParameter] = field(default_factory=list)
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt from template and context."""
        # For Phase 1, simple string replacement
        # Phase 3 will use Jinja2 templates
        prompt = self.template
        
        # Replace context variables
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate task parameters."""
        for param in self.parameters:
            value = params.get(param.name)
            if not param.validate(value):
                return False
        return True
    
    def get_parameter_defaults(self) -> Dict[str, Any]:
        """Get default parameter values."""
        return {
            param.name: param.default 
            for param in self.parameters 
            if param.default is not None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task definition to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template': self.template,
            'parameters': [param.to_dict() for param in self.parameters]
        }