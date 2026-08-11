"""
Signal — Timeline View Schemas
Response structures for entity timelines (Life Events).
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TimelineEventResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    status: str = "completed"        # "completed", "in_progress", "action_required", "pending"
    event_order: Optional[int] = None

    class Config:
        from_attributes = True


class EntityResponse(BaseModel):
    id: UUID
    name: str
    entity_type: str
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    signal_count: int = 0
    next_action: Optional[str] = None
    next_deadline: Optional[datetime] = None
    current_state: Optional[str] = None
    events: list[TimelineEventResponse] = Field(default_factory=list, validation_alias="timeline_events")
    first_seen_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

