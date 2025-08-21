"""LLM provider factory for different models."""

from typing import Union, Optional
from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .local_provider import LocalLLMProvider
from ..core.config import Settings


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        settings: Settings,
        **kwargs
    ) -> LLMProvider:
        """Create LLM provider based on type."""
        
        if provider_type.lower() == "openai":
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                max_tokens=settings.openai_max_tokens
            )
        
        elif provider_type.lower() == "local":
            return LocalLLMProvider(
                endpoint=settings.local_llm_endpoint or "http://localhost:11434",
                model=settings.local_llm_model or "llama3.2",
                max_tokens=kwargs.get('max_tokens', 4096)
            )
        
        elif provider_type.lower() == "auto":
            # Try local first, fallback to OpenAI
            if settings.local_llm_endpoint:
                try:
                    local_provider = LocalLLMProvider(
                        endpoint=settings.local_llm_endpoint,
                        model=settings.local_llm_model or "llama3.2"
                    )
                    # Quick health check would go here in real implementation
                    return local_provider
                except:
                    pass
            
            # Fallback to OpenAI
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                max_tokens=settings.openai_max_tokens
            )
        
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def get_available_providers(settings: Settings) -> list[str]:
        """Get list of available providers."""
        providers = []
        
        # Check OpenAI
        if settings.openai_api_key:
            providers.append("openai")
        
        # Check local LLM
        if settings.local_llm_endpoint:
            providers.append("local")
        
        # Auto is always available if at least one provider exists
        if providers:
            providers.append("auto")
        
        return providers
