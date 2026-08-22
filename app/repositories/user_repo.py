"""
Signal — User Profile Repository
Provides abstract, Fabric, and PostgreSQL implementations for UserProfile persistence.
"""

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
from app.models.user import UserProfile


class UserRepository(ABC):
    """Abstract User Profile repository interface."""

    @abstractmethod
    async def get_by_id(self, user_id: Union[str, UUID]) -> Optional[UserProfile]:
        """Fetch user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        """Fetch user by email address."""
        pass

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> Optional[UserProfile]:
        """Fetch user by Google ID."""
        pass

    @abstractmethod
    async def create(self, user: UserProfile) -> UserProfile:
        """Create a new user profile."""
        pass

    @abstractmethod
    async def update(self, user: UserProfile) -> UserProfile:
        """Update an existing user profile."""
        pass

    @abstractmethod
    async def upsert(self, user: UserProfile) -> UserProfile:
        """Upsert user profile by ID / email."""
        pass

    @abstractmethod
    async def delete(self, user_id: Union[str, UUID]) -> bool:
        """Delete user profile by ID."""
        pass


class FabricUserRepository(UserRepository):
    """Microsoft Fabric Lakehouse User Profile Repository."""

    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "user_profile"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[UserProfile]:
        """Converts deserialized Fabric row into a UserProfile model instance."""
        if not data:
            return None

        # Clean ID
        user_id = data.get("id")
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except Exception:
                pass

        user = UserProfile(
            id=user_id or uuid.uuid4(),
            email=data.get("email", ""),
            display_name=data.get("display_name"),
            avatar_url=data.get("avatar_url"),
            google_id=data.get("google_id"),
            timezone=data.get("timezone", "Asia/Kolkata"),
            last_visit_at=data.get("last_visit_at") or datetime.now(timezone.utc),
            preferences=data.get("preferences") or {
                "notifications_enabled": True,
                "digest_time": "07:30",
                "auto_archive_threshold": 10,
                "processing_tier_default": 2,
            },
            created_at=data.get("created_at") or datetime.now(timezone.utc),
            updated_at=data.get("updated_at") or datetime.now(timezone.utc),
        )
        return user

    async def get_by_id(self, user_id: Union[str, UUID]) -> Optional[UserProfile]:
        raw = await self.dal.get_by_id(self.table_name, str(user_id))
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        raw = await self.dal.get_one(self.table_name, {"email": email.lower()})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def get_by_google_id(self, google_id: str) -> Optional[UserProfile]:
        raw = await self.dal.get_one(self.table_name, {"google_id": google_id})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def create(self, user: UserProfile) -> UserProfile:
        if not user.id:
            import uuid
            user.id = uuid.uuid4()
        payload = serialize_for_fabric(user, table_name=self.table_name)
        await self.dal.insert(self.table_name, payload)
        return user


    async def update(self, user: UserProfile) -> UserProfile:
        user.updated_at = datetime.now(timezone.utc)
        payload = serialize_for_fabric(user, table_name=self.table_name)
        await self.dal.upsert(self.table_name, payload, merge_keys=["id"])
        return user

    async def upsert(self, user: UserProfile) -> UserProfile:
        return await self.update(user)

    async def delete(self, user_id: Union[str, UUID]) -> bool:
        await self.dal.delete(self.table_name, f"id = '{str(user_id)}'")
        return True


class PostgresUserRepository(UserRepository):
    """PostgreSQL / SQLAlchemy User Profile Repository (Reference / Fallback)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: Union[str, UUID]) -> Optional[UserProfile]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(select(UserProfile).where(UserProfile.id == uid))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        res = await self.db.execute(select(UserProfile).where(UserProfile.email == email.lower()))
        return res.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[UserProfile]:
        res = await self.db.execute(select(UserProfile).where(UserProfile.google_id == google_id))
        return res.scalar_one_or_none()

    async def create(self, user: UserProfile) -> UserProfile:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: UserProfile) -> UserProfile:
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def upsert(self, user: UserProfile) -> UserProfile:
        existing = await self.get_by_email(user.email)
        if not existing:
            return await self.create(user)
        existing.display_name = user.display_name or existing.display_name
        existing.avatar_url = user.avatar_url or existing.avatar_url
        existing.google_id = user.google_id or existing.google_id
        existing.preferences = user.preferences or existing.preferences
        return await self.update(existing)

    async def delete(self, user_id: Union[str, UUID]) -> bool:
        user = await self.get_by_id(user_id)
        if user:
            await self.db.delete(user)
            await self.db.commit()
            return True
        return False


def get_user_repository(
    db: Optional[AsyncSession] = None,
    backend: Optional[str] = None,
) -> UserRepository:
    """
    Factory that yields the configured UserRepository implementation
    (Fabric by default, PostgreSQL as fallback/reference).
    """
    settings = get_settings()
    active_backend = backend or settings.database_backend

    if active_backend == "fabric":
        return FabricUserRepository()
    elif active_backend == "postgres":
        if db is None:
            raise ValueError("AsyncSession (db) required for PostgresUserRepository")
        return PostgresUserRepository(db)
    else:
        # Default to Fabric
        return FabricUserRepository()
