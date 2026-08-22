"""
Signal — Behavior Engine (Internal User Behavior Learning)
Tracks interactions and updates sender engagement metrics.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior import BehaviorInteraction, SenderProfile
from app.repositories import get_behavior_interaction_repository, get_sender_profile_repository


class BehaviorEngine:
    """Records user interactions and updates sender behavior profiles."""

    @staticmethod
    async def record_interaction(
        db: AsyncSession,
        user_id: UUID,
        signal_id: Optional[UUID],
        interaction_type: str,
        sender_email: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Record an interaction event and recalculate sender engagement."""
        interaction_repo = get_behavior_interaction_repository(db=db)
        sender_repo = get_sender_profile_repository(db=db)

        interaction = BehaviorInteraction(
            user_id=user_id,
            signal_id=signal_id,
            interaction_type=interaction_type,
            metadata_=metadata or {},
        )
        await interaction_repo.create(interaction)

        # Update sender profile engagement if sender_email is provided
        if sender_email:
            profile = await sender_repo.get_by_email(sender_email)
            if profile:
                profile.total_received += 1
                if interaction_type in ("opened", "clicked_gmail"):
                    profile.total_opened += 1
                    profile.consecutive_ignores = 0
                elif interaction_type == "replied":
                    profile.total_replied += 1
                    profile.consecutive_ignores = 0
                elif interaction_type in ("archived", "ignored", "deleted"):
                    profile.total_ignored += 1
                    profile.consecutive_ignores += 1

                # Recalculate engagement score
                total = profile.total_received or 1
                profile.engagement_score = (profile.total_opened + profile.total_replied) / total

                # Auto-demote to tier 0 after 10 consecutive ignores
                if profile.consecutive_ignores >= 10:
                    profile.processing_tier = 0

                await sender_repo.update(profile)

