"""
Signal — Rule Engine (Tier 1 Heuristic Processing)
Applies fast, zero-LLM heuristic rules for newsletters, marketing, and notifications.
"""

from typing import Any, Optional
from app.models.behavior import SenderProfile


class RuleEngine:
    """Applies heuristic rules for Tier 0 (auto-skip) and Tier 1 (rule-based) processing."""

    @staticmethod
    def process_tier0_or_1(
        sender_profile: SenderProfile,
        subject: str,
        snippet: str,
        body_text: str,
    ) -> Optional[dict[str, Any]]:
        """
        If signal qualifies for Tier 0 or Tier 1, returns a structured result without making LLM API calls.
        Returns None if signal requires full Tier 2 AI processing.
        """
        # Tier 0: Blocklisted or Marketing senders ignored repeatedly
        if sender_profile.processing_tier == 0 or sender_profile.is_blocked:
            return {
                "summary": f"Auto-archived signal from {sender_profile.display_name or sender_profile.email_address}",
                "suggested_category": "Promotions",
                "priority_score": 10,
                "suggested_bucket": "ignored",
                "bucket_reason": f"Auto-archived because senders from {sender_profile.domain} are marked as marketing/ignored.",
                "processing_tier": 0,
                "skip_reason": "Tier 0 marketing/sender blocklist rule",
                "actions": [],
                "entities": [],
                "is_marketing_or_newsletter": True,
            }

        # Tier 1: Known Newsletter / Notification rules
        if sender_profile.processing_tier == 1:
            category = "Newsletters" if sender_profile.sender_type == "newsletter" else "Notifications"
            return {
                "summary": f"{subject[:80]}..." if len(subject) > 80 else subject,
                "suggested_category": category,
                "priority_score": 30,
                "suggested_bucket": "ignored" if sender_profile.engagement_score < 0.2 else "this_week",
                "bucket_reason": f"Processed via rule engine for {sender_profile.sender_type} sender.",
                "processing_tier": 1,
                "skip_reason": "Tier 1 rule-based classification",
                "actions": [],
                "entities": [],
                "is_marketing_or_newsletter": True,
            }

        return None
