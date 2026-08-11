"""
Signal — Abstract LLM Provider Interface
Defines standard methods for structured text generation, extraction, and NLQ.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers (Gemini, Groq, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Generate structured JSON output from LLM."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate plain text output from LLM."""
        pass
