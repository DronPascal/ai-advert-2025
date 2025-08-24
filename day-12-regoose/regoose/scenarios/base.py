"""Base classes for Scenarios."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ..actions.base import ActionContext


@dataclass
class ScenarioResult:
    """Result of a scenario execution."""
    success: bool
    context: ActionContext
    artifacts: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    
    @classmethod
    def success_result(cls, context: ActionContext, artifacts: Dict[str, str] = None) -> 'ScenarioResult':
        """Create a successful result."""
        return cls(
            success=True,
            context=context,
            artifacts=artifacts or context.artifacts
        )
    
    @classmethod  
    def error_result(cls, error: str, context: ActionContext = None) -> 'ScenarioResult':
        """Create an error result."""
        return cls(
            success=False,
            context=context or ActionContext(),
            error=error
        )


class BaseScenario(ABC):
    """Base class for scenarios."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute the scenario."""
        pass
