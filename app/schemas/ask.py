"""
Signal — Ask Signal Schemas
Request/Response models for Natural Language Queries.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class AskSignalRequest(BaseModel):
    query: str


class AskSignalResponse(BaseModel):
    query: str
    answer: str
    intent: Optional[str] = None
    signals_referenced: list[UUID] = []
    entities_referenced: list[UUID] = []
    data: Optional[dict[str, Any]] = None
    processing_time_ms: int = 0
