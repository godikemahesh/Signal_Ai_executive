"""
Signal — Known Domains Repository
Provides abstract, Fabric, and PostgreSQL implementations for KnownDomain persistence and lookup.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.fabric_dal import FabricDAL, get_fabric_dal
from app.core.serialization import deserialize_from_fabric, serialize_for_fabric
from app.models.behavior import KnownDomain


class KnownDomainRepository(ABC):
    """Abstract Known Domain repository interface."""

    @abstractmethod
    async def get_by_domain(self, domain: str) -> Optional[KnownDomain]:
        """Lookup known domain configuration by domain string."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100) -> list[KnownDomain]:
        """List all registered known domains."""
        pass

    @abstractmethod
    async def create(self, known_domain: KnownDomain) -> KnownDomain:
        """Add a new known domain."""
        pass

    @abstractmethod
    async def update(self, known_domain: KnownDomain) -> KnownDomain:
        """Update an existing known domain."""
        pass

    @abstractmethod
    async def delete(self, domain: str) -> bool:
        """Delete a known domain."""
        pass


class FabricKnownDomainRepository(KnownDomainRepository):
    """Microsoft Fabric Lakehouse Known Domains Repository."""

    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "known_domains"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[KnownDomain]:
        """Converts Fabric row dict into KnownDomain model instance."""
        if not data:
            return None

        # Map Fabric columns (category/entity_type) to model attributes
        sender_type = data.get("default_sender_type") or data.get("category") or "unknown"
        tier = data.get("default_tier", 1)
        desc = data.get("description") or data.get("entity_type")

        return KnownDomain(
            domain=data.get("domain", "").lower().strip(),
            default_sender_type=sender_type,
            default_tier=int(tier),
            description=desc,
        )

    async def get_by_domain(self, domain: str) -> Optional[KnownDomain]:
        clean_domain = domain.lower().strip()
        raw = await self.dal.get_one(self.table_name, {"domain": clean_domain})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def list_all(self, limit: int = 100) -> list[KnownDomain]:
        raw_list = await self.dal.read(self.table_name, limit=limit)
        models = []
        for r in raw_list:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            m = self._to_model(data)
            if m:
                models.append(m)
        return models

    async def create(self, known_domain: KnownDomain) -> KnownDomain:
        payload = serialize_for_fabric(known_domain, table_name=self.table_name)
        await self.dal.insert(self.table_name, payload)
        return known_domain

    async def update(self, known_domain: KnownDomain) -> KnownDomain:
        payload = serialize_for_fabric(known_domain, table_name=self.table_name)
        await self.dal.upsert(self.table_name, payload, merge_keys=["domain"])
        return known_domain

    async def delete(self, domain: str) -> bool:
        clean_domain = domain.lower().strip()
        await self.dal.delete(self.table_name, f"domain = '{clean_domain}'")
        return True


class PostgresKnownDomainRepository(KnownDomainRepository):
    """PostgreSQL Known Domain Repository (Reference / Fallback)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_domain(self, domain: str) -> Optional[KnownDomain]:
        clean_domain = domain.lower().strip()
        res = await self.db.execute(select(KnownDomain).where(KnownDomain.domain == clean_domain))
        return res.scalar_one_or_none()

    async def list_all(self, limit: int = 100) -> list[KnownDomain]:
        res = await self.db.execute(select(KnownDomain).limit(limit))
        return list(res.scalars().all())

    async def create(self, known_domain: KnownDomain) -> KnownDomain:
        self.db.add(known_domain)
        await self.db.commit()
        await self.db.refresh(known_domain)
        return known_domain

    async def update(self, known_domain: KnownDomain) -> KnownDomain:
        await self.db.commit()
        await self.db.refresh(known_domain)
        return known_domain

    async def delete(self, domain: str) -> bool:
        kd = await self.get_by_domain(domain)
        if kd:
            await self.db.delete(kd)
            await self.db.commit()
            return True
        return False


def get_known_domain_repository(
    db: Optional[AsyncSession] = None,
    backend: Optional[str] = None,
) -> KnownDomainRepository:
    """Factory yielding configured KnownDomainRepository (Fabric default, Postgres fallback)."""
    settings = get_settings()
    active_backend = backend or settings.database_backend

    if active_backend == "fabric":
        return FabricKnownDomainRepository()
    elif active_backend == "postgres":
        if db is None:
            raise ValueError("AsyncSession (db) required for PostgresKnownDomainRepository")
        return PostgresKnownDomainRepository(db)
    else:
        return FabricKnownDomainRepository()
