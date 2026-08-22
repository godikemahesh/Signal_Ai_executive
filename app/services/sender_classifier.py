"""
Signal — Sender Classifier (Tier 0 & Tier 1 Cost Reduction)
Identifies blocklisted/marketing senders to skip expensive LLM API calls.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior import SenderProfile
from app.repositories import get_known_domain_repository, get_sender_profile_repository


class SenderClassifier:
    """
    Tier 0: Sender Blocklist & Domain Lookup for smart LLM cost reduction.
    If a sender is identified as marketing or blocklisted, it skips Tier 2 AI processing.
    """

    @staticmethod
    async def get_or_create_sender_profile(
        db: AsyncSession, sender_email: str, sender_name: Optional[str] = None
    ) -> SenderProfile:
        """Lookup existing sender profile or create one using domain rules."""
        sender_email = sender_email.lower().strip()
        domain = sender_email.split("@")[-1] if "@" in sender_email else ""

        sender_repo = get_sender_profile_repository(db=db)

        # 1. Lookup existing profile
        profile = await sender_repo.get_by_email(sender_email)
        if profile:
            return profile

        # 2. Lookup known domain default tier via repository abstraction
        domain_repo = get_known_domain_repository(db=db)
        known = await domain_repo.get_by_domain(domain)

        default_type = known.default_sender_type if known else "unknown"
        default_tier = known.default_tier if known else 2

        profile = SenderProfile(
            email_address=sender_email,
            domain=domain,
            display_name=sender_name,
            sender_type=default_type,
            processing_tier=default_tier,
            confidence=0.8 if known else 0.0,
            engagement_score=0.5,
            total_received=0,
            total_opened=0,
            total_replied=0,
            total_ignored=0,
            total_archived=0,
            consecutive_ignores=0,
            avg_response_time_sec=0,
        )


        try:
            return await sender_repo.create(profile)
        except Exception:
            existing_prof = await sender_repo.get_by_email(sender_email)
            if existing_prof:
                return existing_prof
            return profile

