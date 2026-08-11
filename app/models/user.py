"""
Signal — User Models
UserProfile model representing the single user.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="Asia/Kolkata")

    last_visit_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {
            "notifications_enabled": True,
            "digest_time": "07:30",
            "auto_archive_threshold": 10,
            "processing_tier_default": 2,
        },
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
