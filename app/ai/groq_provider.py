"""
Signal — Groq LLM Provider Implementation
Fallback LLM provider using Groq API SDK (llama-3.1-70b-versatile).
"""

import json
import logging
from typing import Any, Optional

from groq import AsyncGroq

from app.ai.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GroqLLMProvider(BaseLLMProvider):
    """Groq API SDK implementation."""

    def __init__(self, api_key: str, model_name: str = "llama-3.1-70b-versatile"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = AsyncGroq(api_key=api_key) if api_key else None

    @property
    def provider_name(self) -> str:
        return f"groq ({self.model_name})"

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Generate structured JSON using Groq."""
        if not self.client:
            raise RuntimeError("Groq API key not configured")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        candidate_models = [self.model_name, "llama-3.3-70b-versatile", "llama3-70b-8192", "llama-3.1-8b-instant"]
        last_exception = None

        for m_name in candidate_models:
            try:
                response = await self.client.chat.completions.create(
                    model=m_name,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                raw_text = response.choices[0].message.content.strip()
                return json.loads(raw_text)
            except Exception as e:
                logger.warning(f"Groq model '{m_name}' failed: {e}. Trying fallback models...")
                last_exception = e

        logger.error(f"Groq LLM error across candidate models: {last_exception}")
        raise RuntimeError(f"Groq provider failed: {last_exception}") from last_exception

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate text using Groq."""
        if not self.client:
            raise RuntimeError("Groq API key not configured")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        candidate_models = [self.model_name, "llama-3.3-70b-versatile", "llama3-70b-8192", "llama-3.1-8b-instant"]
        last_exception = None

        for m_name in candidate_models:
            try:
                response = await self.client.chat.completions.create(
                    model=m_name,
                    messages=messages,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Groq model '{m_name}' failed: {e}. Trying fallback models...")
                last_exception = e

        logger.error(f"Groq LLM error across candidate models: {last_exception}")
        raise RuntimeError(f"Groq provider failed: {last_exception}") from last_exception

