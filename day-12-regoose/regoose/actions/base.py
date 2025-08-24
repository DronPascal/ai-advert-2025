"""Base classes for Actions."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..providers.base import LLMProvider


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    
    @classmethod
    def success_result(cls, data: Dict[str, Any] = None, artifacts: Dict[str, str] = None) -> 'ActionResult':
        """Create a successful result."""
        return cls(
            success=True,
            data=data or {},
            artifacts=artifacts or {}
        )
    
    @classmethod
    def error_result(cls, error: str, data: Dict[str, Any] = None) -> 'ActionResult':
        """Create an error result."""
        return cls(
            success=False,
            data=data or {},
            error=error
        )


class ActionContext:
    """Context for action execution."""
    
    def __init__(self, initial_data: Dict[str, Any] = None):
        self.data = initial_data or {}
        self.artifacts = {}
        self.history = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in context."""
        self.data[key] = value
    
    def update(self, data: Dict[str, Any]) -> None:
        """Update context with new data."""
        self.data.update(data)
    
    def add_artifacts(self, artifacts: Dict[str, str]) -> None:
        """Add artifacts to context."""
        self.artifacts.update(artifacts)
    
    def add_to_history(self, action_name: str, result: ActionResult) -> None:
        """Add action execution to history."""
        self.history.append({
            "action": action_name,
            "success": result.success,
            "error": result.error,
            "data_keys": list(result.data.keys())
        })


class BaseAction(ABC):
    """Base class for all actions."""
    
    def __init__(self, llm_provider: LLMProvider, tools: Dict[str, Any]):
        self.llm = llm_provider
        self.tools = tools
    
    @abstractmethod
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute the action."""
        pass
    
    def get_dependencies(self) -> List[str]:
        """Get list of action dependencies."""
        return []
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate that context has required data."""
        return True
    
    def get_required_fields(self) -> List[str]:
        """Get list of required context fields."""
        return []
