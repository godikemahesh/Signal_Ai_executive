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
        counts_res = await db.execute(
            select(Signal.bucket, func.count(Signal.id))
            .where(Signal.user_id == user_id, Signal.is_deleted == False)
            .group_by(Signal.bucket)
        )
        counts_map = dict(counts_res.all())

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
        res = await db.execute(
            select(Signal)
            .where(Signal.user_id == user_id, Signal.bucket == bucket, Signal.is_deleted == False)
            .order_by(Signal.priority_score.desc(), Signal.received_at.desc())
        )
        return list(res.scalars().all())
