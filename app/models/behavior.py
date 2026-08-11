"""
Signal — Behavior Models
SenderProfile, BehaviorPattern, BehaviorInteraction, KnownDomain.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SenderProfile(Base):
    __tablename__ = "sender_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_address: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    sender_type: Mapped[str] = mapped_column(String, default="unknown")
    processing_tier: Mapped[int] = mapped_column(SmallInteger, default=2)

    total_received: Mapped[int] = mapped_column(Integer, default=0)
    total_opened: Mapped[int] = mapped_column(Integer, default=0)
    total_replied: Mapped[int] = mapped_column(Integer, default=0)
    total_ignored: Mapped[int] = mapped_column(Integer, default=0)
    total_archived: Mapped[int] = mapped_column(Integer, default=0)

    engagement_score: Mapped[float] = mapped_column(Float, default=0.5)
    avg_response_time_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    consecutive_ignores: Mapped[int] = mapped_column(Integer, default=0)
    last_engagement_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_signal_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    has_unsubscribe_link: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class BehaviorPattern(Base):
    __tablename__ = "behavior_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)

    pattern_type: Mapped[str] = mapped_column(String, nullable=False)
    pattern_key: Mapped[str] = mapped_column(String, nullable=False)
    pattern_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)

    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class BehaviorInteraction(Base):
    __tablename__ = "behavior_interactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    signal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)

    interaction_type: Mapped[str] = mapped_column(String, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class KnownDomain(Base):
    __tablename__ = "known_domains"

    domain: Mapped[str] = mapped_column(String, primary_key=True)
    default_sender_type: Mapped[str] = mapped_column(String, nullable=False)
    default_tier: Mapped[int] = mapped_column(SmallInteger, default=1)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
