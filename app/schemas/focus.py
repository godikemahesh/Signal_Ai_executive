"""
Signal — Focus View Schemas
Response structures for human-readable priority buckets.
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.schemas.signal import SignalResponse


class BucketSummary(BaseModel):
    bucket: str
    label: str
    count: int
    description: str


class FocusViewResponse(BaseModel):
    buckets: list[BucketSummary]


class MoveBucketRequest(BaseModel):
    new_bucket: str
    reason: Optional[str] = "User manually moved bucket"
