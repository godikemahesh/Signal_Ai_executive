"""
Signal — Base Repository Interfaces
Defines abstract persistence interfaces decoupled from underlying storage (PostgreSQL / Microsoft Fabric).
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar, Union
from uuid import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract Base Repository interface."""

    @abstractmethod
    async def get_by_id(self, entity_id: Union[str, UUID]) -> Optional[T]:
        """Retrieve entity by primary key ID."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """List entities with pagination."""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity record."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity record."""
        pass

    @abstractmethod
    async def delete(self, entity_id: Union[str, UUID]) -> bool:
        """Delete an entity by primary key ID."""
        pass
