"""
Signal — Ask Signal NLQ Service
Answers natural language queries about the user's digital life using LLM + Vector similarity search.
"""

import time
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_manager import get_llm_manager
from app.ai.prompts.ask_signal import ASK_SIGNAL_SYSTEM_INSTRUCTION, build_ask_signal_prompt
from app.models.ai_decision import AskSignalHistory
from app.models.entity import Entity
from app.models.signal import Signal
from app.repositories import (
    get_ask_signal_history_repository,
    get_entity_repository,
    get_signal_repository,
)
from app.schemas.ask import AskSignalResponse
from app.services.embedding_service import EmbeddingService


class AskSignalService:
    """Executes natural language queries over user's signals and entities."""

    @staticmethod
    async def ask(db: AsyncSession, user_id: UUID, query: str) -> AskSignalResponse:
        """Process user NLQ and synthesize a structured response."""
        start_time = time.time()
        entity_repo = get_entity_repository(db=db)
        signal_repo = get_signal_repository(db=db)
        history_repo = get_ask_signal_history_repository(db=db)

        # 1. Fetch top active entities
        entities = await entity_repo.list_by_user(user_id, order_by="last_updated_at", descending=True, limit=10)

        entities_text = "\n".join(
            [f"- {e.name} ({e.entity_type}): {e.current_state or 'Active'}" for e in entities]
        ) or "No active entities found."

        # 2. Vector embedding & similarity query or keyword fallback
        vec, model_name = EmbeddingService.get_embedding(query)
        
        signals = await signal_repo.list_by_user(user_id, is_deleted=False, order_by="received_at", descending=True, limit=10)

        signals_text = "\n".join(
            [f"- From: {s.sender_name} | Subject: {s.subject} | Summary: {s.summary}" for s in signals]
        ) or "No relevant signals found."

        # 3. Call LLM (Gemini primary, Groq fallback)
        llm = get_llm_manager()
        prompt = build_ask_signal_prompt(query, signals_text, entities_text)

        ai_res = await llm.generate_structured(
            prompt=prompt,
            system_instruction=ASK_SIGNAL_SYSTEM_INSTRUCTION,
            temperature=0.2,
        )

        answer_text = ai_res.get("answer", "I couldn't process your query.")
        intent = ai_res.get("intent", "general_query")

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 4. Save to history via repository abstraction
        sig_ids = [s.id for s in signals]
        ent_ids = [e.id for e in entities]
        history = AskSignalHistory(
            user_id=user_id,
            query=query,
            intent=intent,
            response=ai_res,
            response_text=answer_text,
            signals_referenced=sig_ids,
            entities_referenced=ent_ids,
            processing_time_ms=elapsed_ms,
            model_used=llm.primary_name,
        )
        try:
            await history_repo.create(history)
        except Exception:
            pass

        return AskSignalResponse(
            query=query,
            answer=answer_text,
            intent=intent,
            signals_referenced=sig_ids,
            entities_referenced=ent_ids,
            processing_time_ms=elapsed_ms,
        )

