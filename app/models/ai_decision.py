"""
Signal — AI Decision and Ask Signal History Models
AIDecision and AskSignalHistory models.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    signal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)

    decision_type: Mapped[str] = mapped_column(String, nullable=False)
    decision_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    was_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class AskSignalHistory(Base):
    __tablename__ = "ask_signal_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)

    query: Mapped[str] = mapped_column(String, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    response: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    response_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    signals_referenced: Mapped[Optional[list[uuid.UUID]]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    entities_referenced: Mapped[Optional[list[uuid.UUID]]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)

    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
