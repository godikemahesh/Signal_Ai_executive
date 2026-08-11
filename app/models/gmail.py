"""
Signal — Gmail Account Model
OAuth credentials and sync cursors for connected Gmail account.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GmailAccount(Base):
    __tablename__ = "gmail_account"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    access_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    history_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_full_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String, default="pending")
    sync_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    watch_expiration: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    watch_resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
