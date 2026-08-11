"""
Signal — Gemini LLM Provider Implementation
Primary LLM provider using Google Generative AI SDK (gemini-2.0-flash).
"""

import json
import logging
from typing import Any, Optional

import google.generativeai as genai

from app.ai.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API SDK implementation."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        if api_key:
            genai.configure(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return f"gemini ({self.model_name})"

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Generate structured JSON response using Gemini."""
        raw_candidates = [self.model_name, "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]
        candidate_models = []
        for m in raw_candidates:
            if m not in candidate_models:
                candidate_models.append(m)

        last_exception = None

        for m_name in candidate_models:
            try:
                model = genai.GenerativeModel(
                    model_name=m_name,
                    system_instruction=system_instruction,
                    generation_config={
                        "temperature": temperature,
                        "response_mime_type": "application/json",
                    },
                )
                response = model.generate_content(prompt)
                raw_text = response.text.strip()

                if raw_text.startswith("```json"):
                    raw_text = raw_text.replace("```json", "", 1).rsplit("```", 1)[0].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text.replace("```", "", 1).rsplit("```", 1)[0].strip()

                return json.loads(raw_text)
            except Exception as e:
                logger.warning(f"Gemini model '{m_name}' failed: {e}. Trying fallback models if available...")
                last_exception = e

        logger.error(f"Gemini LLM error across all candidate models: {last_exception}")
        raise RuntimeError(f"Gemini provider failed: {last_exception}") from last_exception

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate text response using Gemini."""
        raw_candidates = [self.model_name, "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]
        candidate_models = []
        for m in raw_candidates:
            if m not in candidate_models:
                candidate_models.append(m)

        last_exception = None

        for m_name in candidate_models:
            try:
                model = genai.GenerativeModel(
                    model_name=m_name,
                    system_instruction=system_instruction,
                    generation_config={"temperature": temperature},
                )
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini model '{m_name}' text generation failed: {e}")
                last_exception = e

        logger.error(f"Gemini LLM error across all candidate models: {last_exception}")
        raise RuntimeError(f"Gemini provider failed: {last_exception}") from last_exception

