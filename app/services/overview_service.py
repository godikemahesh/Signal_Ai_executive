"""
Signal — Overview Service
Builds the live command center view ("147 signals → 4 decisions").
"""

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BUCKET_COMPLETED, BUCKET_DO_NOW, BUCKET_IGNORED, BUCKET_TODAY
from app.models.signal import Signal
from app.models.user import UserProfile
from app.schemas.overview import HandledAutomaticallySummary, HandledCategoryItem, OverviewResponse, OverviewStats


class OverviewService:
    """Builds the primary live Overview view."""

    @staticmethod
    async def get_overview(db: AsyncSession, user: UserProfile) -> OverviewResponse:
        """Fetch live command center overview with real database stats."""
        now = datetime.now(timezone.utc)

        # Fetch all active signals for user
        all_signals_res = await db.execute(
            select(Signal)
            .where(Signal.user_id == user.id, Signal.is_deleted == False)
            .order_by(Signal.received_at.desc())
        )
        all_signals = list(all_signals_res.scalars().all())

        # Filter categories dynamically
        needs_action = [
            s for s in all_signals
            if not s.is_archived
            and s.bucket not in [BUCKET_COMPLETED, BUCKET_IGNORED]
            and s.bucket in [BUCKET_DO_NOW, BUCKET_TODAY]
        ]

        due_soon = [
            s for s in all_signals
            if not s.is_archived and s.detected_deadlines and len(s.detected_deadlines) > 0
        ]

        changed = [
            s for s in all_signals
            if not s.is_archived and s.bucket == BUCKET_TODAY and s not in needs_action
        ]

        archived_signals = [
            s for s in all_signals
            if s.is_archived or s.bucket == BUCKET_IGNORED
        ]

        # Categorize handled automatically counts dynamically
        category_counts: dict[str, dict] = {}

        for s in all_signals:
            if not (s.is_archived or s.bucket in [BUCKET_IGNORED, BUCKET_COMPLETED] or s.priority_score < 50):
                continue

            sender = (s.sender_email or "").lower()
            subject = (s.subject or "").lower()
            meta_cat = (s.extracted_metadata.get("category") or "").lower() if s.extracted_metadata else ""
            ent_type = (s.extracted_metadata.get("entity_type") or "").lower() if s.extracted_metadata else ""

            if "github" in sender or "gitlab" in sender or "vercel" in sender or "googlecloud" in sender or meta_cat == "github":
                cat_key = "github"
                cat_label = "GitHub notifications"
                action_text = "Non-blocking"
                color = "blue"
            elif "newsletter" in subject or "digest" in subject or meta_cat in ["newsletter", "newsletters"] or "weekly" in subject:
                cat_key = "newsletter"
                cat_label = "newsletters summarized"
                action_text = "→ Auto-read"
                color = "emerald"
            elif "security" in subject or "sign-in" in subject or "verification" in subject or "login" in subject or meta_cat == "security":
                cat_key = "security"
                cat_label = "security & auth alerts"
                action_text = "Auto-verified"
                color = "amber"
            elif "linkedin" in sender or "twitter" in sender or "facebook" in sender or meta_cat in ["social", "personal"]:
                cat_key = "social"
                cat_label = "social & network updates"
                action_text = "Auto-muted"
                color = "purple"
            elif "bank" in sender or "stripe" in sender or "receipt" in subject or "invoice" in subject or meta_cat in ["finance", "bill"] or ent_type in ["bill", "payment"]:
                cat_key = "finance"
                cat_label = "receipts & billing statements"
                action_text = "Auto-logged"
                color = "indigo"
            elif ent_type in ["order", "delivery"] or meta_cat in ["shopping", "order"]:
                cat_key = "order"
                cat_label = "order & delivery tracking"
                action_text = "Auto-tracked"
                color = "cyan"
            elif meta_cat and meta_cat not in ["general", "other"]:
                cat_key = meta_cat.lower().replace(" ", "_")
                cat_label = f"{meta_cat} updates"
                action_text = "Auto-handled"
                color = "teal"
            else:
                cat_key = "marketing"
                cat_label = "marketing emails archived"
                action_text = "Auto-filtered"
                color = "slate"

            if cat_key not in category_counts:
                category_counts[cat_key] = {
                    "category_key": cat_key,
                    "label": cat_label,
                    "count": 0,
                    "action_text": action_text,
                    "color": color,
                }
            category_counts[cat_key]["count"] += 1

        dynamic_categories = [
            HandledCategoryItem(**item) for item in category_counts.values() if item["count"] > 0
        ]

        newsletters_count = category_counts.get("newsletter", {}).get("count", 0)
        marketing_count = category_counts.get("marketing", {}).get("count", len(archived_signals))
        github_count = category_counts.get("github", {}).get("count", 0)

        total_signals = len(all_signals)
        decisions_count = len(needs_action)

        stats = OverviewStats(
            new=len(needs_action),
            changed=len(changed),
            archived=len(archived_signals),
            total_signals=total_signals,
            decisions=decisions_count,
        )

        handled = HandledAutomaticallySummary(
            newsletters_summarized=newsletters_count,
            marketing_archived=marketing_count,
            github_notifications=github_count,
            dynamic_categories=dynamic_categories,
            summary_text=f"{newsletters_count} newsletters summarized, {marketing_count} marketing archived",
        )

        greeting_name = user.display_name.split()[0] if user.display_name else "there"
        summary_text = (
            f"Since your last visit, {len(needs_action)} item(s) need your attention."
            if needs_action
            else "Everything else has been handled. Nothing needs your attention."
        )

        # Update last_visit_at timestamp
        user.last_visit_at = now
        await db.commit()

        return OverviewResponse(
            greeting=f"hey, {greeting_name}.",
            summary=summary_text,
            stats=stats,
            needs_action=needs_action,
            changed=changed,
            due_soon=due_soon,
            handled_automatically=handled,
            last_updated=now,
        )

