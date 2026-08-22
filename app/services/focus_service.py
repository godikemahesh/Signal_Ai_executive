"""
Signal — Focus Service
Groups signals into human-readable buckets (Do now, Today, This week, Waiting, Completed, Ignored).
"""

from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    BUCKET_COMPLETED,
    BUCKET_DO_NOW,
    BUCKET_IGNORED,
    BUCKET_THIS_WEEK,
    BUCKET_TODAY,
    BUCKET_WAITING,
)
from app.models.signal import Signal
from app.repositories import get_signal_repository
from app.schemas.focus import BucketSummary, FocusViewResponse


class FocusService:
    """Focus view service for bucket queries."""

    BUCKET_METADATA = [
        (BUCKET_DO_NOW, "Do Now", "Requires immediate action. Act within minutes."),
        (BUCKET_TODAY, "Today", "Needs action before end of day."),
        (BUCKET_THIS_WEEK, "This Week", "Upcoming, plan for it."),
        (BUCKET_WAITING, "Waiting", "Waiting for someone else. No action needed."),
        (BUCKET_COMPLETED, "Completed", "Done. Logged for reference."),
        (BUCKET_IGNORED, "Ignored", "Auto-archived based on your behavior patterns."),
    ]

    @staticmethod
    async def get_buckets_summary(db: AsyncSession, user_id: UUID) -> FocusViewResponse:
        """Fetch signal counts for all focus buckets."""
        signal_repo = get_signal_repository(db=db)
        counts_map = await signal_repo.count_by_bucket(user_id)

        buckets = []
        for b_name, b_label, b_desc in FocusService.BUCKET_METADATA:
            buckets.append(
                BucketSummary(
                    bucket=b_name,
                    label=b_label,
                    count=counts_map.get(b_name, 0),
                    description=b_desc,
                )
            )

        return FocusViewResponse(buckets=buckets)

    @staticmethod
    async def get_signals_by_bucket(db: AsyncSession, user_id: UUID, bucket: str) -> list[Signal]:
        """Fetch signals in a specific bucket."""
        signal_repo = get_signal_repository(db=db)
        return await signal_repo.list_by_bucket(user_id, bucket, is_deleted=False)

