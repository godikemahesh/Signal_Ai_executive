"""
Signal — Behavior Interaction Repository
Provides abstract, Fabric, and PostgreSQL implementations for BehaviorInteraction persistence.
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
from app.core.serialization import deserialize_from_fabric
from app.models.behavior import BehaviorInteraction


class BehaviorInteractionRepository(ABC):
    """Abstract repository for BehaviorInteraction persistence."""

    @abstractmethod
    async def create(self, interaction: BehaviorInteraction) -> BehaviorInteraction:
        """Record an interaction event."""
        pass

    @abstractmethod
    async def list_by_user(
        self, user_id: Union[str, UUID], limit: int = 50
    ) -> list[BehaviorInteraction]:
        """Fetch interactions for a user."""
        pass


class FabricBehaviorInteractionRepository(BehaviorInteractionRepository):
    """Microsoft Fabric Lakehouse Behavior Interaction Repository."""

    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "behavior_interactions"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[BehaviorInteraction]:
        if not data:
            return None

        int_id = data.get("id")
        if isinstance(int_id, str):
            try:
                int_id = UUID(int_id)
            except Exception:
                pass

        user_id = data.get("user_id")
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except Exception:
                pass

        sig_id = data.get("signal_id")
        if isinstance(sig_id, str):
            try:
                sig_id = UUID(sig_id)
            except Exception:
                pass

        # Column alias: interaction_metadata ↔ metadata_
        meta_raw = data.get("interaction_metadata") or data.get("metadata")
        metadata = {}
        if isinstance(meta_raw, str):
            try:
                metadata = json.loads(meta_raw)
            except Exception:
                metadata = {}
        elif isinstance(meta_raw, dict):
            metadata = meta_raw

        return BehaviorInteraction(
            id=int_id or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            signal_id=sig_id,
            interaction_type=data.get("interaction_type", "opened"),
            metadata_=metadata,
            created_at=data.get("created_at") or datetime.now(timezone.utc),
        )

    def _to_fabric_payload(self, interaction: BehaviorInteraction) -> dict[str, Any]:
        """Serialize BehaviorInteraction for Fabric. Column alias: metadata_ -> interaction_metadata."""
        meta_str = "{}"
        if isinstance(interaction.metadata_, dict):
            meta_str = json.dumps(interaction.metadata_)

        return {
            "id": str(interaction.id),
            "user_id": str(interaction.user_id),
            "signal_id": str(interaction.signal_id) if interaction.signal_id else None,
            "interaction_type": interaction.interaction_type or "opened",
            "interaction_metadata": meta_str,
            "created_at": (
                interaction.created_at.isoformat()
                if isinstance(interaction.created_at, datetime)
                else datetime.now(timezone.utc).isoformat()
            ),
        }

    async def create(self, interaction: BehaviorInteraction) -> BehaviorInteraction:
        payload = self._to_fabric_payload(interaction)
        await self.dal.insert(self.table_name, payload)
        return interaction

    async def list_by_user(
        self, user_id: Union[str, UUID], limit: int = 50
    ) -> list[BehaviorInteraction]:
        uid = str(user_id)
        records = await self.dal.read(
            self.table_name,
            filter_expr=f"user_id == '{uid}'",
            order_by="created_at",
            descending=True,
            limit=limit,
        )
        interactions = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            bi = self._to_model(data)
            if bi:
                interactions.append(bi)
        return interactions


class PostgresBehaviorInteractionRepository(BehaviorInteractionRepository):
    """PostgreSQL Behavior Interaction Repository (Fallback)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, interaction: BehaviorInteraction) -> BehaviorInteraction:
        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)
        return interaction

    async def list_by_user(
        self, user_id: Union[str, UUID], limit: int = 50
    ) -> list[BehaviorInteraction]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(
            select(BehaviorInteraction)
            .where(BehaviorInteraction.user_id == uid)
            .order_by(BehaviorInteraction.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())


def get_behavior_interaction_repository(
    db: Optional[AsyncSession] = None,
    backend: Optional[str] = None,
) -> BehaviorInteractionRepository:
    """Factory yielding configured BehaviorInteractionRepository."""
    settings = get_settings()
    active_backend = backend or settings.database_backend
    if active_backend == "fabric":
        return FabricBehaviorInteractionRepository()
    elif active_backend == "postgres":
        if db is None:
            raise ValueError("AsyncSession (db) required for PostgresBehaviorInteractionRepository")
        return PostgresBehaviorInteractionRepository(db)
    return FabricBehaviorInteractionRepository()
