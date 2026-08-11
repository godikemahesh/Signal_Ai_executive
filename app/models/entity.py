"""
Signal — Entity Models
Entity, SignalEntity, EntityRelationship, and EntityTimelineEvent models.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    next_action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    next_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    current_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    timeline_events = relationship("EntityTimelineEvent", back_populates="entity", cascade="all, delete-orphan", order_by="EntityTimelineEvent.event_order")


class SignalEntity(Base):
    __tablename__ = "signal_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)

    relationship_type: Mapped[str] = mapped_column(String, default="related")
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String, nullable=False)

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class EntityTimelineEvent(Base):
    __tablename__ = "entity_timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    signal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="completed")
    event_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    entity = relationship("Entity", back_populates="timeline_events")
