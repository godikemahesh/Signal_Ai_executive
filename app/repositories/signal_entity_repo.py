"""
Signal — Signal Entity Repository
Provides abstract, Fabric, and PostgreSQL implementations for Entity, SignalEntity, and EntityTimelineEvent persistence.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.fabric_dal import FabricDAL, get_fabric_dal
from app.core.serialization import deserialize_from_fabric, serialize_for_fabric
from app.models.entity import Entity, EntityTimelineEvent, SignalEntity


# ============================================================
# EntityRepository
# ============================================================

class EntityRepository(ABC):
    @abstractmethod
    async def get_by_id(self, entity_id: Union[str, UUID], user_id: Optional[Union[str, UUID]] = None) -> Optional[Entity]:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: Union[str, UUID], order_by: str = "last_updated_at",
                           descending: bool = True, limit: Optional[int] = None) -> list[Entity]:
        pass

    @abstractmethod
    async def create(self, entity: Entity) -> Entity:
        pass

    @abstractmethod
    async def update(self, entity: Entity) -> Entity:
        pass

    @abstractmethod
    async def delete(self, entity_id: Union[str, UUID]) -> bool:
        pass



class FabricEntityRepository(EntityRepository):
    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "entities"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[Entity]:
        if not data:
            return None
        eid = data.get("id")
        if isinstance(eid, str):
            try:
                eid = UUID(eid)
            except Exception:
                pass
        uid = data.get("user_id")
        if isinstance(uid, str):
            try:
                uid = UUID(uid)
            except Exception:
                pass
        metadata = data.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = {}

        sig_count = data.get("signal_count")
        if sig_count is not None and not (isinstance(sig_count, float) and (sig_count != sig_count)):
            try:
                sig_count = int(sig_count)
            except Exception:
                sig_count = 0
        else:
            sig_count = 0

        return Entity(
            id=eid or uuid.uuid4(),
            user_id=uid or uuid.uuid4(),
            name=data.get("name", ""),
            entity_type=data.get("entity_type", "other"),
            status=data.get("status", "active"),
            metadata_=metadata or {},
            signal_count=sig_count,
            first_seen_at=data.get("first_seen_at"),
            last_updated_at=data.get("last_updated_at"),
            next_action=data.get("next_action"),
            next_deadline=data.get("next_deadline"),
            current_state=data.get("current_state"),
            created_at=data.get("created_at") or datetime.now(timezone.utc),
            updated_at=data.get("updated_at") or datetime.now(timezone.utc),
        )


    async def get_by_id(self, entity_id: Union[str, UUID], user_id: Optional[Union[str, UUID]] = None) -> Optional[Entity]:
        eid = str(entity_id)
        filters = {"id": eid}
        if user_id:
            filters["user_id"] = str(user_id)
        raw = await self.dal.get_one(self.table_name, filters)
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        entity = self._to_model(data)
        # Load timeline events
        if entity:
            entity.timeline_events = await self._load_timeline_events(str(entity.id))
        return entity

    async def _load_timeline_events(self, entity_id: str) -> list[EntityTimelineEvent]:
        te_dal = self.dal
        records = await te_dal.read("entity_timeline_events", filter_expr=f"entity_id == '{entity_id}'")
        events = []
        for r in records:
            data = deserialize_from_fabric(r, table_name="entity_timeline_events")
            evt = _timeline_event_to_model(data)
            if evt:
                events.append(evt)
        events.sort(key=lambda e: e.event_order or 0)
        return events

    async def list_by_user(self, user_id: Union[str, UUID], order_by: str = "last_updated_at",
                           descending: bool = True, limit: Optional[int] = None) -> list[Entity]:
        uid = str(user_id)
        filter_expr = f"user_id == '{uid}'"
        records = await self.dal.read(self.table_name, filter_expr=filter_expr)
        results = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            e = self._to_model(data)
            if e:
                # Load timeline events for each entity
                e.timeline_events = await self._load_timeline_events(str(e.id))
                results.append(e)
        # Sort by order_by field
        results.sort(
            key=lambda e: getattr(e, order_by, None) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=descending,
        )
        if limit:
            results = results[:limit]
        return results

    async def create(self, entity: Entity) -> Entity:
        if not entity.id:
            entity.id = uuid.uuid4()
        payload = serialize_for_fabric(entity, table_name=self.table_name)
        # The metadata column is named 'metadata' in Fabric but 'metadata_' in SQLAlchemy
        if "metadata_" in payload:
            payload["metadata"] = payload.pop("metadata_")
        await self.dal.insert(self.table_name, payload)
        return entity


    async def update(self, entity: Entity) -> Entity:
        entity.updated_at = datetime.now(timezone.utc)
        payload = serialize_for_fabric(entity, table_name=self.table_name)
        if "metadata_" in payload:
            payload["metadata"] = payload.pop("metadata_")
        await self.dal.upsert(self.table_name, payload, merge_keys=["id"])
        return entity

    async def delete(self, entity_id: Union[str, UUID]) -> bool:
        eid = str(entity_id)
        await self.dal.delete(self.table_name, f"id == '{eid}'")
        return True



class PostgresEntityRepository(EntityRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, entity_id: Union[str, UUID], user_id: Optional[Union[str, UUID]] = None) -> Optional[Entity]:
        eid = UUID(str(entity_id)) if isinstance(entity_id, str) else entity_id
        query = select(Entity).options(selectinload(Entity.timeline_events))
        if user_id:
            uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
            query = query.where(Entity.user_id == uid, Entity.id == eid)
        else:
            query = query.where(Entity.id == eid)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def list_by_user(self, user_id: Union[str, UUID], order_by: str = "last_updated_at",
                           descending: bool = True, limit: Optional[int] = None) -> list[Entity]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        order_col = getattr(Entity, order_by, Entity.last_updated_at)
        query = (
            select(Entity)
            .where(Entity.user_id == uid)
            .options(selectinload(Entity.timeline_events))
            .order_by(order_col.desc() if descending else order_col.asc())
        )
        if limit:
            query = query.limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create(self, entity: Entity) -> Entity:
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def update(self, entity: Entity) -> Entity:
        entity.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return entity

    async def delete(self, entity_id: Union[str, UUID]) -> bool:
        eid = UUID(str(entity_id)) if isinstance(entity_id, str) else entity_id
        res = await self.db.execute(select(Entity).where(Entity.id == eid))
        ent = res.scalar_one_or_none()
        if ent:
            await self.db.delete(ent)
            await self.db.commit()
            return True
        return False



# ============================================================
# SignalEntityRepository
# ============================================================

class SignalEntityRepository(ABC):
    @abstractmethod
    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalEntity]:
        pass

    @abstractmethod
    async def create(self, signal_entity: SignalEntity) -> SignalEntity:
        pass


class FabricSignalEntityRepository(SignalEntityRepository):
    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "signal_entities"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[SignalEntity]:
        if not data:
            return None
        se_id = data.get("id")
        if isinstance(se_id, str):
            try:
                se_id = UUID(se_id)
            except Exception:
                pass
        sig_id = data.get("signal_id")
        if isinstance(sig_id, str):
            try:
                sig_id = UUID(sig_id)
            except Exception:
                pass
        ent_id = data.get("entity_id")
        if isinstance(ent_id, str):
            try:
                ent_id = UUID(ent_id)
            except Exception:
                pass
        # Column alias: role → relationship_type
        relationship_type = data.get("role") or data.get("relationship_type", "related")

        return SignalEntity(
            id=se_id or uuid.uuid4(),
            signal_id=sig_id or uuid.uuid4(),
            entity_id=ent_id or uuid.uuid4(),
            relationship_type=relationship_type,
            extracted_data={},  # Omitted from Fabric payload
            created_at=data.get("created_at") or datetime.now(timezone.utc),
        )

    def _to_fabric_payload(self, se: SignalEntity) -> dict[str, Any]:
        """Serialize SignalEntity with relationship_type → role mapping. Omits extracted_data."""
        return {
            "id": str(se.id),
            "signal_id": str(se.signal_id),
            "entity_id": str(se.entity_id),
            "role": se.relationship_type or "related",
            "created_at": se.created_at.isoformat() if se.created_at else datetime.now(timezone.utc).isoformat(),
        }

    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalEntity]:
        sid = str(signal_id)
        records = await self.dal.read(self.table_name, filter_expr=f"signal_id == '{sid}'")
        results = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            se = self._to_model(data)
            if se:
                results.append(se)
        return results

    async def create(self, signal_entity: SignalEntity) -> SignalEntity:
        if not signal_entity.id:
            signal_entity.id = uuid.uuid4()
        payload = self._to_fabric_payload(signal_entity)
        await self.dal.insert(self.table_name, payload)
        return signal_entity



class PostgresSignalEntityRepository(SignalEntityRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalEntity]:
        sid = UUID(str(signal_id)) if isinstance(signal_id, str) else signal_id
        res = await self.db.execute(select(SignalEntity).where(SignalEntity.signal_id == sid))
        return list(res.scalars().all())

    async def create(self, signal_entity: SignalEntity) -> SignalEntity:
        self.db.add(signal_entity)
        await self.db.flush()
        return signal_entity


# ============================================================
# EntityTimelineEventRepository
# ============================================================

class EntityTimelineEventRepository(ABC):
    @abstractmethod
    async def get_by_entity_id(self, entity_id: Union[str, UUID]) -> list[EntityTimelineEvent]:
        pass

    @abstractmethod
    async def create(self, event: EntityTimelineEvent) -> EntityTimelineEvent:
        pass


def _timeline_event_to_model(data: Optional[dict[str, Any]]) -> Optional[EntityTimelineEvent]:
    """Shared helper to convert Fabric data dict to EntityTimelineEvent model."""
    if not data:
        return None
    evt_id = data.get("id")
    if isinstance(evt_id, str):
        try:
            evt_id = UUID(evt_id)
        except Exception:
            pass
    ent_id = data.get("entity_id")
    if isinstance(ent_id, str):
        try:
            ent_id = UUID(ent_id)
        except Exception:
            pass
    sig_id = data.get("signal_id")
    if isinstance(sig_id, str):
        try:
            sig_id = UUID(sig_id)
        except Exception:
            pass
    metadata = data.get("metadata")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {}

    # Column aliases: event_title → title, event_summary → description, event_timestamp → event_date, event_type → status
    title = data.get("event_title") or data.get("title", "")
    description = data.get("event_summary") or data.get("description")
    event_date = data.get("event_timestamp") or data.get("event_date")
    status = data.get("event_type") or data.get("status", "completed")

    event_order = data.get("event_order")
    if event_order is not None and not (isinstance(event_order, float) and (event_order != event_order)):
        try:
            event_order = int(event_order)
        except Exception:
            event_order = None
    else:
        event_order = None

    return EntityTimelineEvent(
        id=evt_id or uuid.uuid4(),
        entity_id=ent_id or uuid.uuid4(),
        signal_id=sig_id,
        title=title,
        description=description,
        event_date=event_date,
        status=status,
        event_order=event_order,
        metadata_=metadata or {},
        created_at=data.get("created_at") or datetime.now(timezone.utc),
    )



class FabricEntityTimelineEventRepository(EntityTimelineEventRepository):
    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "entity_timeline_events"

    def _to_fabric_payload(self, event: EntityTimelineEvent) -> dict[str, Any]:
        """Serialize with Fabric column name aliases."""
        return {
            "id": str(event.id),
            "entity_id": str(event.entity_id),
            "signal_id": str(event.signal_id) if event.signal_id else None,
            "event_type": event.status or "completed",
            "event_title": event.title or "",
            "event_summary": event.description,
            "event_timestamp": event.event_date.isoformat() if event.event_date else None,
            "metadata": json.dumps(event.metadata_ or {}),
            "created_at": event.created_at.isoformat() if event.created_at else datetime.now(timezone.utc).isoformat(),
        }

    async def get_by_entity_id(self, entity_id: Union[str, UUID]) -> list[EntityTimelineEvent]:
        eid = str(entity_id)
        records = await self.dal.read(self.table_name, filter_expr=f"entity_id == '{eid}'")
        events = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            evt = _timeline_event_to_model(data)
            if evt:
                events.append(evt)
        events.sort(key=lambda e: e.event_order or 0)
        return events

    async def create(self, event: EntityTimelineEvent) -> EntityTimelineEvent:
        if not event.id:
            event.id = uuid.uuid4()
        payload = self._to_fabric_payload(event)
        await self.dal.insert(self.table_name, payload)
        return event



class PostgresEntityTimelineEventRepository(EntityTimelineEventRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_entity_id(self, entity_id: Union[str, UUID]) -> list[EntityTimelineEvent]:
        eid = UUID(str(entity_id)) if isinstance(entity_id, str) else entity_id
        res = await self.db.execute(
            select(EntityTimelineEvent).where(EntityTimelineEvent.entity_id == eid)
            .order_by(EntityTimelineEvent.event_order)
        )
        return list(res.scalars().all())

    async def create(self, event: EntityTimelineEvent) -> EntityTimelineEvent:
        self.db.add(event)
        await self.db.flush()
        return event


# ============================================================
# Factory Functions
# ============================================================

def get_entity_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> EntityRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricEntityRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresEntityRepository")
        return PostgresEntityRepository(db)
    return FabricEntityRepository()


def get_signal_entity_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> SignalEntityRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricSignalEntityRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresSignalEntityRepository")
        return PostgresSignalEntityRepository(db)
    return FabricSignalEntityRepository()


def get_entity_timeline_event_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> EntityTimelineEventRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricEntityTimelineEventRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresEntityTimelineEventRepository")
        return PostgresEntityTimelineEventRepository(db)
    return FabricEntityTimelineEventRepository()
