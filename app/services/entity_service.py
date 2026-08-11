"""
Signal — Entity & Knowledge Graph Service
Manages real-world entities (Job applications, Orders, Bills) and builds the Timeline view.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity, EntityTimelineEvent, SignalEntity


TRACKABLE_ENTITY_TYPES = {
    "job_application", "interview", "order", "delivery",
    "bill", "payment", "subscription", "travel", "flight"
}

TRACKABLE_CATEGORIES = {
    "interview", "job_application", "job hunt", "finance", "bill", "bills & payments",
    "shopping", "order", "online shopping", "travel", "flight", "subscription"
}

NOISE_KEYWORDS = {
    "security alert", "data shared", "privacy policy", "terms of service",
    "verification code", "sign-in alert", "login", "newsletter", "digest",
    "unsubscribe", "weekly", "edition", "promotional", "discount", "account alert",
    "security notification", "password reset", "new sign-in", "access granted",
    "google account", "login alert", "otp", "two-factor", "2fa", "verification"
}

NOISE_ENTITY_NAMES = {
    "google", "google account", "bolt.new", "bolt", "github account",
    "microsoft account", "apple id", "security team"
}


class EntityService:
    """Manages entities and timeline events extracted from signals."""

    @staticmethod
    def is_meaningful_timeline_entity(
        item: dict[str, Any],
        signal_subject: str = "",
        signal_category: str = ""
    ) -> bool:
        """Determines if an extracted entity represents a real-world trackable multi-stage lifecycle thread."""
        name = (item.get("name") or "").strip()
        name_lower = name.lower()
        raw_type = (item.get("entity_type") or "other").lower().strip()
        metadata = item.get("metadata") or {}
        subject_lower = (signal_subject or "").lower()
        cat_lower = (signal_category or "").lower()

        # 1. Reject empty names or trivial length (< 3 chars)
        if not name or len(name) < 3:
            return False

        # 2. Reject known noise entity names lacking specific tracking metadata
        if name_lower in NOISE_ENTITY_NAMES and not any([
            metadata.get("amount"), metadata.get("order_id"), metadata.get("tracking_number"),
            metadata.get("flight_number"), metadata.get("job_title"), metadata.get("due_date")
        ]):
            return False

        # 3. Reject noise keywords in entity name, subject, current_state, or next_action
        current_state = (item.get("current_state") or "").lower()
        next_action = (item.get("next_action") or "").lower()
        combined_text = f"{name_lower} {subject_lower} {current_state} {next_action}"
        if any(kw in combined_text for kw in NOISE_KEYWORDS):
            return False

        # 4. Multi-Stage Narrative Filter: Check if entity_type or signal_category is a trackable life thread
        is_trackable_type = raw_type in TRACKABLE_ENTITY_TYPES or any(
            t in raw_type for t in ["job", "interview", "order", "purchase", "bill", "invoice", "travel", "flight", "sub"]
        )
        is_trackable_category = any(
            c in cat_lower for c in ["job", "interview", "finance", "bill", "shop", "order", "travel", "flight", "sub"]
        )

        if not is_trackable_type and not is_trackable_category:
            # Exception: Require strong structured tracking metadata
            has_strong_metadata = any([
                metadata.get("amount"),
                metadata.get("order_id"),
                metadata.get("tracking_number"),
                metadata.get("flight_number"),
                metadata.get("job_title"),
            ])
            if not has_strong_metadata:
                return False

        # 5. Structured Data Requirement for generic/other entity types
        if raw_type in ("other", "company", "account", "project", "course"):
            has_structured_data = any([
                metadata.get("amount"),
                metadata.get("tracking_number"),
                metadata.get("order_id"),
                metadata.get("job_title"),
                metadata.get("due_date"),
                metadata.get("flight_number"),
                item.get("next_deadline"),
            ])
            if not has_structured_data:
                return False

        return True

    @staticmethod
    async def process_extracted_entities(
        db: AsyncSession,
        user_id: UUID,
        signal_id: UUID,
        extracted_entities: list[dict[str, Any]],
        received_at: datetime,
        signal_subject: str = "",
        signal_category: str = "",
    ):
        """Link or create entities from Tier 2 AI extraction with smart gatekeeping and merging."""
        for item in extracted_entities:
            if not EntityService.is_meaningful_timeline_entity(item, signal_subject, signal_category):
                continue

            name = item.get("name").strip()
            raw_type = (item.get("entity_type") or "other").lower().strip()

            if raw_type in TRACKABLE_ENTITY_TYPES:
                entity_type = raw_type
            elif "job" in raw_type or "interview" in raw_type:
                entity_type = "job_application"
            elif "order" in raw_type or "purchase" in raw_type:
                entity_type = "order"
            elif "bill" in raw_type or "invoice" in raw_type:
                entity_type = "bill"
            elif "travel" in raw_type or "flight" in raw_type:
                entity_type = "travel"
            elif "sub" in raw_type:
                entity_type = "subscription"
            else:
                entity_type = "other"

            # Smart Merging: Find existing entity by exact name or brand substring match
            name_lower = name.lower()
            res = await db.execute(
                select(Entity).where(Entity.user_id == user_id)
            )
            existing_entities = list(res.scalars().all())

            matched_entity = None
            for e in existing_entities:
                e_name_lower = e.name.lower()
                # 1. Exact match (case-insensitive)
                if e_name_lower == name_lower:
                    matched_entity = e
                    break
                # 2. Substring / Brand match for active entities of compatible entity_type
                if e.status == "active" and (e.entity_type == entity_type or e.entity_type in TRACKABLE_ENTITY_TYPES):
                    if e_name_lower in name_lower or name_lower in e_name_lower:
                        matched_entity = e
                        break

            if not matched_entity:
                entity = Entity(
                    user_id=user_id,
                    name=name,
                    entity_type=entity_type,
                    status=item.get("status", "active"),
                    current_state=item.get("current_state"),
                    next_action=item.get("next_action"),
                    first_seen_at=received_at,
                    last_updated_at=received_at,
                    metadata_=item.get("metadata", {}),
                )
                db.add(entity)
                await db.flush()
            else:
                entity = matched_entity
                entity.current_state = item.get("current_state") or entity.current_state
                entity.next_action = item.get("next_action") or entity.next_action
                entity.last_updated_at = received_at
                entity.signal_count += 1
                if item.get("metadata"):
                    current_meta = dict(entity.metadata_ or {})
                    current_meta.update({k: v for k, v in item["metadata"].items() if v is not None})
                    entity.metadata_ = current_meta

            # Link Signal to Entity
            sig_ent = SignalEntity(
                signal_id=signal_id,
                entity_id=entity.id,
                relationship_type="updated",
                extracted_data=item,
            )
            db.add(sig_ent)

            # Add Timeline Event
            event = EntityTimelineEvent(
                entity_id=entity.id,
                signal_id=signal_id,
                title=item.get("current_state") or name,
                event_date=received_at,
                status="completed" if not item.get("next_action") else "action_required",
            )
            db.add(event)

        await db.commit()

