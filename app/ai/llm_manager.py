"""
Signal — LLM Manager
Handles provider selection, primary execution, and seamless fallback.
"""

import logging
from typing import Any, Optional

from app.ai.base import BaseLLMProvider
from app.ai.gemini_provider import GeminiLLMProvider
from app.ai.groq_provider import GroqLLMProvider
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMManager:
    """Manages primary and fallback LLM providers."""

    def __init__(self):
        settings = get_settings()
        
        self.providers: dict[str, BaseLLMProvider] = {}
        
        if settings.gemini_api_key:
            self.providers["gemini"] = GeminiLLMProvider(
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model,
            )

        if settings.groq_api_key:
            self.providers["groq"] = GroqLLMProvider(
                api_key=settings.groq_api_key,
                model_name=settings.groq_model,
            )

        self.primary_name = settings.primary_llm_provider
        self.fallback_name = settings.fallback_llm_provider

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        return self.providers.get(name)

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Try primary LLM provider; on failure, automatically try fallback provider."""
        primary = self.get_provider(self.primary_name)
        if primary:
            try:
                logger.info(f"Executing structured LLM call with primary provider: {primary.provider_name}")
                return await primary.generate_structured(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    json_schema=json_schema,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning(f"Primary LLM provider '{self.primary_name}' failed: {e}. Trying fallback...")

        fallback = self.get_provider(self.fallback_name)
        if fallback:
            logger.info(f"Executing structured LLM call with fallback provider: {fallback.provider_name}")
            return await fallback.generate_structured(
                prompt=prompt,
                system_instruction=system_instruction,
                json_schema=json_schema,
                temperature=temperature,
            )

        raise RuntimeError("No working LLM provider available! Please configure valid GEMINI_API_KEY or GROQ_API_KEY.")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Try primary LLM provider; on failure, automatically try fallback provider."""
        primary = self.get_provider(self.primary_name)
        if primary:
            try:
                return await primary.generate_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning(f"Primary LLM provider '{self.primary_name}' failed: {e}. Trying fallback...")

        fallback = self.get_provider(self.fallback_name)
        if fallback:
            return await fallback.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
            )

        raise RuntimeError("No working LLM provider available!")


_llm_manager_instance: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    global _llm_manager_instance
    if _llm_manager_instance is None:
        _llm_manager_instance = LLMManager()
    return _llm_manager_instance
