"""
Signal — Sender Profile Repository
Provides abstract, Fabric, and PostgreSQL implementations for SenderProfile persistence.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.fabric_dal import FabricDAL, get_fabric_dal
from app.core.serialization import deserialize_from_fabric, serialize_for_fabric
from app.models.behavior import SenderProfile


class SenderProfileRepository(ABC):
    """Abstract repository for SenderProfile persistence."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[SenderProfile]:
        """Fetch sender profile by email address."""
        pass

    @abstractmethod
    async def create(self, profile: SenderProfile) -> SenderProfile:
        """Create a new sender profile."""
        pass

    @abstractmethod
    async def update(self, profile: SenderProfile) -> SenderProfile:
        """Update an existing sender profile."""
        pass

    @abstractmethod
    async def upsert(self, profile: SenderProfile) -> SenderProfile:
        """Upsert sender profile by email address."""
        pass

    @abstractmethod
    async def list_top(self, limit: int = 20) -> list[SenderProfile]:
        """Fetch top sender profiles ordered by total_received descending."""
        pass


class FabricSenderProfileRepository(SenderProfileRepository):
    """Microsoft Fabric Lakehouse Sender Profile Repository."""

    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "sender_profiles"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[SenderProfile]:
        if not data:
            return None

        email = data.get("email_address", "").lower().strip()
        if not email:
            return None

        # Safe numeric parsing
        def _safe_int(val: Any, default: int = 0) -> int:
            if val is not None and not (isinstance(val, float) and (val != val)):
                try:
                    return int(val)
                except Exception:
                    return default
            return default

        def _safe_float(val: Any, default: float = 0.0) -> float:
            if val is not None and not (isinstance(val, float) and (val != val)):
                try:
                    return float(val)
                except Exception:
                    return default
            return default

        metadata = data.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = {}

        return SenderProfile(
            id=uuid.uuid4(),  # In-memory ID; Fabric PK is email_address
            email_address=email,
            domain=data.get("domain", email.split("@")[-1] if "@" in email else ""),
            display_name=data.get("display_name"),
            sender_type=data.get("sender_type", "unknown"),
            processing_tier=_safe_int(data.get("processing_tier"), 2),
            total_received=_safe_int(data.get("total_received"), 0),
            total_opened=_safe_int(data.get("total_opened"), 0),
            total_replied=_safe_int(data.get("total_replied"), 0),
            total_ignored=_safe_int(data.get("total_ignored"), 0),
            total_archived=_safe_int(data.get("total_archived"), 0),
            engagement_score=_safe_float(data.get("engagement_score"), 0.5),
            avg_response_time_sec=_safe_int(data.get("avg_response_time_sec"), 0),
            confidence=_safe_float(data.get("confidence"), 0.0),
            consecutive_ignores=_safe_int(data.get("consecutive_ignores"), 0),
            last_engagement_at=data.get("last_engagement_at"),
            last_signal_at=data.get("last_signal_at"),
            is_blocked=bool(data.get("is_blocked") or False),
            has_unsubscribe_link=bool(data.get("has_unsubscribe_link") or False),
            metadata_=metadata or {},
            created_at=data.get("created_at") or datetime.now(timezone.utc),
            updated_at=data.get("updated_at") or datetime.now(timezone.utc),
        )

    def _to_fabric_payload(self, profile: SenderProfile) -> dict[str, Any]:
        """Serialize SenderProfile for Fabric Lakehouse. PK is email_address."""
        email = (profile.email_address or "").lower().strip()
        metadata_str = json.dumps(profile.metadata_ or {}) if isinstance(profile.metadata_, dict) else "{}"

        payload = {
            "email_address": email,
            "domain": profile.domain or (email.split("@")[-1] if "@" in email else ""),
            "display_name": profile.display_name,
            "sender_type": profile.sender_type or "unknown",
            "processing_tier": int(profile.processing_tier) if profile.processing_tier is not None else 2,
            "total_received": int(profile.total_received or 0),
            "total_opened": int(profile.total_opened or 0),
            "total_replied": int(profile.total_replied or 0),
            "total_ignored": int(profile.total_ignored or 0),
            "total_archived": int(profile.total_archived or 0),
            "engagement_score": float(profile.engagement_score or 0.0),
            "avg_response_time_sec": float(profile.avg_response_time_sec or 0.0),
            "confidence": float(profile.confidence or 0.0),
            "consecutive_ignores": int(profile.consecutive_ignores or 0),
            "last_engagement_at": profile.last_engagement_at.isoformat() if isinstance(profile.last_engagement_at, datetime) else None,
            "last_signal_at": profile.last_signal_at.isoformat() if isinstance(profile.last_signal_at, datetime) else None,
            "is_blocked": bool(profile.is_blocked or False),
            "has_unsubscribe_link": bool(profile.has_unsubscribe_link or False),
            "metadata": metadata_str,
            "created_at": profile.created_at.isoformat() if isinstance(profile.created_at, datetime) else datetime.now(timezone.utc).isoformat(),
            "updated_at": profile.updated_at.isoformat() if isinstance(profile.updated_at, datetime) else datetime.now(timezone.utc).isoformat(),
        }
        return payload

    async def get_by_email(self, email: str) -> Optional[SenderProfile]:
        clean_email = email.lower().strip()
        raw = await self.dal.get_one(self.table_name, {"email_address": clean_email})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def create(self, profile: SenderProfile) -> SenderProfile:
        payload = self._to_fabric_payload(profile)
        await self.dal.insert(self.table_name, payload)
        return profile

    async def update(self, profile: SenderProfile) -> SenderProfile:
        profile.updated_at = datetime.now(timezone.utc)
        payload = self._to_fabric_payload(profile)
        await self.dal.upsert(self.table_name, payload, merge_keys=["email_address"])
        return profile

    async def upsert(self, profile: SenderProfile) -> SenderProfile:
        existing = await self.get_by_email(profile.email_address)
        if not existing:
            return await self.create(profile)
        return await self.update(profile)

    async def list_top(self, limit: int = 20) -> list[SenderProfile]:
        records = await self.dal.read(
            self.table_name,
            order_by="total_received",
            descending=True,
            limit=limit,
        )
        profiles = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            p = self._to_model(data)
            if p:
                profiles.append(p)
        return profiles


class PostgresSenderProfileRepository(SenderProfileRepository):
    """PostgreSQL Sender Profile Repository (Fallback)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[SenderProfile]:
        clean_email = email.lower().strip()
        res = await self.db.execute(
            select(SenderProfile).where(SenderProfile.email_address == clean_email)
        )
        return res.scalar_one_or_none()

    async def create(self, profile: SenderProfile) -> SenderProfile:
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update(self, profile: SenderProfile) -> SenderProfile:
        profile.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def upsert(self, profile: SenderProfile) -> SenderProfile:
        existing = await self.get_by_email(profile.email_address)
        if not existing:
            return await self.create(profile)
        existing.display_name = profile.display_name or existing.display_name
        existing.sender_type = profile.sender_type or existing.sender_type
        existing.processing_tier = profile.processing_tier
        existing.total_received = profile.total_received
        existing.total_opened = profile.total_opened
        existing.total_replied = profile.total_replied
        existing.total_ignored = profile.total_ignored
        existing.total_archived = profile.total_archived
        existing.engagement_score = profile.engagement_score
        existing.consecutive_ignores = profile.consecutive_ignores
        return await self.update(existing)

    async def list_top(self, limit: int = 20) -> list[SenderProfile]:
        res = await self.db.execute(
            select(SenderProfile).order_by(SenderProfile.total_received.desc()).limit(limit)
        )
        return list(res.scalars().all())


def get_sender_profile_repository(
    db: Optional[AsyncSession] = None,
    backend: Optional[str] = None,
) -> SenderProfileRepository:
    """Factory yielding configured SenderProfileRepository."""
    settings = get_settings()
    active_backend = backend or settings.database_backend
    if active_backend == "fabric":
        return FabricSenderProfileRepository()
    elif active_backend == "postgres":
        if db is None:
            raise ValueError("AsyncSession (db) required for PostgresSenderProfileRepository")
        return PostgresSenderProfileRepository(db)
    return FabricSenderProfileRepository()
