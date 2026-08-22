"""
Signal — Signal Category Repository
Provides abstract, Fabric, and PostgreSQL implementations for SignalCategory persistence.
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
from app.models.category import SignalCategory


class SignalCategoryRepository(ABC):
    @abstractmethod
    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalCategory]:
        pass

    @abstractmethod
    async def create(self, signal_category: SignalCategory) -> SignalCategory:
        pass

    @abstractmethod
    async def create_batch(self, signal_categories: list[SignalCategory]) -> list[SignalCategory]:
        pass


class FabricSignalCategoryRepository(SignalCategoryRepository):
    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "signal_categories"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[SignalCategory]:
        if not data:
            return None
        sc_id = data.get("id")
        if isinstance(sc_id, str):
            try:
                sc_id = UUID(sc_id)
            except Exception:
                pass
        sig_id = data.get("signal_id")
        if isinstance(sig_id, str):
            try:
                sig_id = UUID(sig_id)
            except Exception:
                pass
        cat_id = data.get("category_id")
        if isinstance(cat_id, str):
            try:
                cat_id = UUID(cat_id)
            except Exception:
                pass
        # Map assigned_by → is_primary
        assigned_by = data.get("assigned_by", "ai")
        is_primary = (assigned_by == "primary")

        return SignalCategory(
            id=sc_id or uuid.uuid4(),
            signal_id=sig_id or uuid.uuid4(),
            category_id=cat_id or uuid.uuid4(),
            confidence=float(data.get("confidence", 1.0)),
            is_primary=is_primary,
            created_at=data.get("created_at") or datetime.now(timezone.utc),
        )

    def _to_fabric_payload(self, sc: SignalCategory) -> dict[str, Any]:
        """Serialize SignalCategory to Fabric payload with is_primary → assigned_by mapping."""
        payload = {
            "id": str(sc.id),
            "signal_id": str(sc.signal_id),
            "category_id": str(sc.category_id),
            "confidence": float(sc.confidence) if sc.confidence else 1.0,
            "assigned_by": "primary" if sc.is_primary else "ai",
            "created_at": sc.created_at.isoformat() if sc.created_at else datetime.now(timezone.utc).isoformat(),
        }
        return payload

    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalCategory]:
        sid = str(signal_id)
        records = await self.dal.read(self.table_name, filter_expr=f"signal_id == '{sid}'")
        results = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            sc = self._to_model(data)
            if sc:
                results.append(sc)
        return results

    async def create(self, signal_category: SignalCategory) -> SignalCategory:
        payload = self._to_fabric_payload(signal_category)
        await self.dal.insert(self.table_name, payload)
        return signal_category

    async def create_batch(self, signal_categories: list[SignalCategory]) -> list[SignalCategory]:
        if not signal_categories:
            return []
        payloads = [self._to_fabric_payload(sc) for sc in signal_categories]
        await self.dal.insert(self.table_name, payloads)
        return signal_categories


class PostgresSignalCategoryRepository(SignalCategoryRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalCategory]:
        sid = UUID(str(signal_id)) if isinstance(signal_id, str) else signal_id
        res = await self.db.execute(select(SignalCategory).where(SignalCategory.signal_id == sid))
        return list(res.scalars().all())

    async def create(self, signal_category: SignalCategory) -> SignalCategory:
        self.db.add(signal_category)
        await self.db.commit()
        await self.db.refresh(signal_category)
        return signal_category

    async def create_batch(self, signal_categories: list[SignalCategory]) -> list[SignalCategory]:
        for sc in signal_categories:
            self.db.add(sc)
        await self.db.commit()
        return signal_categories


def get_signal_category_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> SignalCategoryRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricSignalCategoryRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresSignalCategoryRepository")
        return PostgresSignalCategoryRepository(db)
    return FabricSignalCategoryRepository()
