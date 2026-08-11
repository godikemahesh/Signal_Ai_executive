"""
Signal — Signal Schemas
Pydantic models for raw and processed Signals.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class SignalActionItem(BaseModel):
    action: str                       # e.g., "reply", "pay", "start_assessment"
    description: str                  # e.g., "Reply to Stripe recruiter"
    deadline: Optional[datetime] = None
    urgency: str = "medium"           # "high", "medium", "low"


class SignalDeadlineItem(BaseModel):
    description: str
    date: datetime
    is_hard_deadline: bool = True


class SignalResponse(BaseModel):
    id: UUID
    gmail_message_id: str
    gmail_thread_id: Optional[str] = None

    sender_email: str
    sender_name: Optional[str] = None

    subject: Optional[str] = None
    snippet: Optional[str] = None
    body_plain: Optional[str] = None

    summary: Optional[str] = None
    detected_actions: list[dict[str, Any]] = []
    detected_deadlines: list[dict[str, Any]] = []

    processing_tier: int = 2
    processing_status: str = "completed"

    priority_score: int = 50
    bucket: str = "today"
    bucket_reason: Optional[str] = None

    is_read: bool = False
    is_starred: bool = False
    is_archived: bool = False
    is_snoozed: bool = False
    snoozed_until: Optional[datetime] = None

    gmail_link: Optional[str] = None
    received_at: datetime

    class Config:
        from_attributes = True
