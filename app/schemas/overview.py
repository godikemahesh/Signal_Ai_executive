"""
Signal — Overview View Schemas
Response structures for the main Overview command center view.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.schemas.signal import SignalResponse


class OverviewStats(BaseModel):
    new: int = 0
    changed: int = 0
    archived: int = 0
    total_signals: int = 0
    decisions: int = 0


class HandledCategoryItem(BaseModel):
    category_key: str
    label: str
    count: int = 0
    action_text: str = "Auto-filtered"
    color: str = "slate"


class HandledAutomaticallySummary(BaseModel):
    newsletters_summarized: int = 0
    marketing_archived: int = 0
    github_notifications: int = 0
    promotions_archived: int = 0
    dynamic_categories: list[HandledCategoryItem] = []
    summary_text: str = "Everything else has been handled."


class OverviewResponse(BaseModel):
    greeting: str = "hey, Mahesh."
    summary: str = "Since your last visit, 3 things need your attention."
    stats: OverviewStats
    needs_action: list[SignalResponse] = []
    changed: list[SignalResponse] = []
    due_soon: list[SignalResponse] = []
    handled_automatically: HandledAutomaticallySummary
    last_updated: datetime
