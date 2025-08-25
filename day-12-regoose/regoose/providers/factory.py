"""LLM provider factory for different models."""

from typing import Union, Optional
from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .local_provider import LocalLLMProvider
from ..core.config import Settings


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        settings: Settings,
        llm_params: Optional[dict] = None,
        **kwargs
    ) -> LLMProvider:
        """Create LLM provider based on type."""
        
        # Merge settings with provided LLM parameters
        if llm_params is None:
            llm_params = {}
        
        if provider_type.lower() == "openai":
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                max_tokens=llm_params.get('max_tokens', settings.openai_max_tokens),
                temperature=llm_params.get('temperature'),
                top_p=llm_params.get('top_p'),
                presence_penalty=llm_params.get('presence_penalty'),
                frequency_penalty=llm_params.get('frequency_penalty')
            )
        
        elif provider_type.lower() == "deepseek":
            return DeepSeekProvider(
                api_key=settings.deepseek_api_key,
                model=settings.deepseek_model,
                max_tokens=llm_params.get('max_tokens', settings.deepseek_max_tokens),
                temperature=llm_params.get('temperature'),
                top_p=llm_params.get('top_p'),
                presence_penalty=llm_params.get('presence_penalty'),
                frequency_penalty=llm_params.get('frequency_penalty')
            )
        
        elif provider_type.lower() == "local":
            return LocalLLMProvider(
                endpoint=settings.local_llm_endpoint or "http://localhost:11434",
                model=settings.local_llm_model or "llama3.2",
                max_tokens=llm_params.get('max_tokens', 4096),
                temperature=llm_params.get('temperature'),
                top_p=llm_params.get('top_p'),
                presence_penalty=llm_params.get('presence_penalty'),
                frequency_penalty=llm_params.get('frequency_penalty')
            )
        
        elif provider_type.lower() == "auto":
            # Try local first, fallback to OpenAI
            if settings.local_llm_endpoint:
                try:
                    local_provider = LocalLLMProvider(
                        endpoint=settings.local_llm_endpoint,
                        model=settings.local_llm_model or "llama3.2",
                        max_tokens=llm_params.get('max_tokens', 4096),
                        temperature=llm_params.get('temperature'),
                        top_p=llm_params.get('top_p'),
                        presence_penalty=llm_params.get('presence_penalty'),
                        frequency_penalty=llm_params.get('frequency_penalty')
                    )
                    # Quick health check would go here in real implementation
                    return local_provider
                except:
                    pass
            
            # Fallback to OpenAI
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                max_tokens=llm_params.get('max_tokens', settings.openai_max_tokens),
                temperature=llm_params.get('temperature'),
                top_p=llm_params.get('top_p'),
                presence_penalty=llm_params.get('presence_penalty'),
                frequency_penalty=llm_params.get('frequency_penalty')
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
        
        # Check DeepSeek
        if settings.deepseek_api_key:
            providers.append("deepseek")
        
        # Check local LLM
        if settings.local_llm_endpoint:
            providers.append("local")
        
        # Auto is always available if at least one provider exists
        if providers:
            providers.append("auto")
        
        return providers
