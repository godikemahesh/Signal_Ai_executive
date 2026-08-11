"""
Signal — AI Response Pydantic Schemas
Structured schemas expected from LLM JSON responses.
"""

from typing import Any, Optional
from pydantic import BaseModel


class ExtractedEntityAI(BaseModel):
    name: str                           # e.g., "Google SWE Internship"
    entity_type: str                    # e.g., "job_application", "order", "bill"
    status: str = "active"
    current_state: Optional[str] = None
    next_action: Optional[str] = None
    next_deadline: Optional[str] = None # ISO format string
    metadata: dict[str, Any] = {}


class DetectedActionAI(BaseModel):
    action: str                         # e.g., "reply", "pay", "start_assessment"
    description: str
    deadline: Optional[str] = None
    urgency: str = "medium"


class SignalAIAnalysisResult(BaseModel):
    summary: str                        # 1-line concise summary
    suggested_category: str             # e.g., "Job Hunt", "Bills & Payments"
    priority_score: int                 # 0-100 score
    suggested_bucket: str              # "do_now", "today", "this_week", "waiting", "completed", "ignored"
    bucket_reason: str
    entities: list[ExtractedEntityAI] = []
    actions: list[DetectedActionAI] = []
    is_marketing_or_newsletter: bool = False
