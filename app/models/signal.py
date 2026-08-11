"""
Signal — Signal Models
Signal, SignalThread, SignalAttachment, SignalEmbedding models.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, BigInteger, Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SignalThread(Base):
    __tablename__ = "signal_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    gmail_thread_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    last_signal_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    participants: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)

    gmail_message_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    gmail_thread_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("signal_threads.id", ondelete="SET NULL"), nullable=True)

    sender_email: Mapped[str] = mapped_column(String, nullable=False)
    sender_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sender_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("sender_profiles.id", ondelete="SET NULL"), nullable=True)

    to_recipients: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    cc_recipients: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    bcc_recipients: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    body_plain: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    body_html: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    body_sanitized: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    detected_actions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    detected_deadlines: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    extracted_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    pii_mapping: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    processing_tier: Mapped[int] = mapped_column(SmallInteger, default=2)
    processing_status: Mapped[str] = mapped_column(String, default="pending")
    skip_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    priority_score: Mapped[int] = mapped_column(SmallInteger, default=50)
    bucket: Mapped[str] = mapped_column(String, default="today")
    bucket_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_snoozed: Mapped[bool] = mapped_column(Boolean, default=False)
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    gmail_link: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    interacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    gmail_label_ids: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    gmail_internal_date: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    attachments = relationship("SignalAttachment", back_populates="signal", cascade="all, delete-orphan")


class SignalAttachment(Base):
    __tablename__ = "signal_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gmail_attachment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    signal = relationship("Signal", back_populates="attachments")


class SignalEmbedding(Base):
    __tablename__ = "signal_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String, default="all-MiniLM-L6-v2")
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(384), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
