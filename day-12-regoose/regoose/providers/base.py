"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Response from LLM provider."""
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    metadata: Dict[str, Any] = {}
    tool_calls: Optional[List[Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass
    
    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum tokens for this provider."""
        pass
    
    def get_supported_parameters(self) -> List[str]:
        """Get list of supported LLM parameters."""
        return ["temperature", "max_tokens", "top_p", "presence_penalty", "frequency_penalty"]
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate and filter supported parameters."""
        supported = self.get_supported_parameters()
        return {k: v for k, v in kwargs.items() if k in supported and v is not None}
