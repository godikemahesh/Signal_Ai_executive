"""
Signal — Priority Scorer Engine
Computes internal 0-100 priority score and resolves human-readable bucket.
User NEVER sees numbers — only buckets (do_now, today, this_week, waiting, completed, ignored).
"""

from typing import Optional
from app.core.constants import (
    BUCKET_COMPLETED,
    BUCKET_DO_NOW,
    BUCKET_IGNORED,
    BUCKET_THIS_WEEK,
    BUCKET_TODAY,
    BUCKET_WAITING,
)


class PriorityScorer:
    """Internal priority calculation engine."""

    @staticmethod
    def calculate_priority(
        ai_priority_score: int,
        sender_engagement_score: float,
        has_urgent_deadline: bool = False,
        is_marketing: bool = False,
    ) -> tuple[int, str, str]:
        """
        Combines AI analysis with sender historical behavior score.
        Returns:
            (final_score_0_100, bucket_name, bucket_reason)
        """
        if is_marketing:
            return 10, BUCKET_IGNORED, "Auto-archived promotional signal"

        # Base score weighted 60% AI, 40% historical engagement
        score_val = sender_engagement_score if sender_engagement_score is not None else 0.5
        history_weight = int(score_val * 100)
        final_score = int(0.6 * ai_priority_score + 0.4 * history_weight)


        if has_urgent_deadline:
            final_score = min(100, final_score + 25)

        # Map internal score to human bucket
        if final_score >= 80:
            bucket = BUCKET_DO_NOW
            reason = "Requires immediate attention or action"
        elif final_score >= 60:
            bucket = BUCKET_TODAY
            reason = "Needs action before end of day"
        elif final_score >= 40:
            bucket = BUCKET_THIS_WEEK
            reason = "Upcoming item to plan for this week"
        elif final_score >= 20:
            bucket = BUCKET_WAITING
            reason = "Status update or waiting for response"
        else:
            bucket = BUCKET_IGNORED
            reason = "Low priority or historical low engagement"

        return final_score, bucket, reason
