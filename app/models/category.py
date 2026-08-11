"""
Signal — Category Models
Category and SignalCategory models for dynamic AI-discovered categories.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class SignalCategory(Base):
    __tablename__ = "signal_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
