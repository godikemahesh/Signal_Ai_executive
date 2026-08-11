"""
Signal — Timeline Service
Retrieves life event entities and their chronological timeline events.
"""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entity import Entity


class TimelineService:
    """Timeline view service."""

    @staticmethod
    async def get_all_entities(db: AsyncSession, user_id: UUID) -> list[Entity]:
        """Fetch active life entities with their timeline events."""
        res = await db.execute(
            select(Entity)
            .where(Entity.user_id == user_id)
            .options(selectinload(Entity.timeline_events))
            .order_by(Entity.last_updated_at.desc())
        )
        return list(res.scalars().all())

    @staticmethod
    async def get_entity_by_id(db: AsyncSession, user_id: UUID, entity_id: UUID) -> Entity:
        """Fetch a single entity by ID."""
        res = await db.execute(
            select(Entity)
            .where(Entity.user_id == user_id, Entity.id == entity_id)
            .options(selectinload(Entity.timeline_events))
        )
        return res.scalar_one_or_none()
