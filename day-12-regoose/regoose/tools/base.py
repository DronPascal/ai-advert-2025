"""Base tool interface for MCP integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    output: str
    error: str = ""
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """Abstract base class for MCP tools."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get tool name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get tool description."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass
