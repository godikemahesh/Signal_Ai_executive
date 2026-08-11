"""
Signal — Sender Classifier (Tier 0 & Tier 1 Cost Reduction)
Identifies blocklisted/marketing senders to skip expensive LLM API calls.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior import KnownDomain, SenderProfile


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

        # 1. Lookup existing profile
        result = await db.execute(
            select(SenderProfile).where(SenderProfile.email_address == sender_email)
        )
        profile = result.scalar_one_or_none()

        if profile:
            return profile

        # 2. Lookup known domain default tier
        domain_res = await db.execute(
            select(KnownDomain).where(KnownDomain.domain == domain)
        )
        known = domain_res.scalar_one_or_none()

        default_type = known.default_sender_type if known else "unknown"
        default_tier = known.default_tier if known else 2

        profile = SenderProfile(
            email_address=sender_email,
            domain=domain,
            display_name=sender_name,
            sender_type=default_type,
            processing_tier=default_tier,
            confidence=0.8 if known else 0.0,
        )
        try:
            db.add(profile)
            await db.flush()
            return profile
        except Exception:
            await db.rollback()
            result = await db.execute(
                select(SenderProfile).where(SenderProfile.email_address == sender_email)
            )
            existing_prof = result.scalar_one_or_none()
            if existing_prof:
                return existing_prof
            # If still not found, return detached profile
            return profile
