"""
Signal — Timeline Service
Retrieves life event entities and their chronological timeline events.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.repositories import get_entity_repository


class TimelineService:
    """Timeline view service."""

    @staticmethod
    async def get_all_entities(db: AsyncSession, user_id: UUID) -> list[Entity]:
        """Fetch active life entities with their timeline events."""
        entity_repo = get_entity_repository(db=db)
        return await entity_repo.list_by_user(user_id, order_by="last_updated_at", descending=True)

    @staticmethod
    async def get_entity_by_id(db: AsyncSession, user_id: UUID, entity_id: UUID) -> Entity:
        """Fetch a single entity by ID."""
        entity_repo = get_entity_repository(db=db)
        return await entity_repo.get_by_id(entity_id, user_id=user_id)

