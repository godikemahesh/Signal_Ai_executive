"""
Signal — Gmail Account Repository
Provides abstract, Fabric, and PostgreSQL implementations for GmailAccount OAuth credential and sync state persistence.
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
from app.core.security import decrypt_credential, encrypt_credential
from app.core.serialization import deserialize_from_fabric, serialize_for_fabric
from app.models.gmail import GmailAccount


class GmailAccountRepository(ABC):
    """Abstract Gmail Account repository interface."""

    @abstractmethod
    async def get_by_user_id(self, user_id: Union[str, UUID]) -> Optional[GmailAccount]:
        """Fetch connected Gmail account for a given user ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[GmailAccount]:
        """Fetch Gmail account by email address."""
        pass

    @abstractmethod
    async def list_active(self) -> list[GmailAccount]:
        """List all active Gmail accounts."""
        pass

    @abstractmethod
    async def create(self, account: GmailAccount) -> GmailAccount:
        """Create a new Gmail account record."""
        pass


    @abstractmethod
    async def update(self, account: GmailAccount) -> GmailAccount:
        """Update tokens, expiration, or sync state."""
        pass

    @abstractmethod
    async def upsert(self, account: GmailAccount) -> GmailAccount:
        """Upsert Gmail account by user_id / email."""
        pass

    @abstractmethod
    async def delete_by_user_id(self, user_id: Union[str, UUID]) -> bool:
        """Disconnect/delete Gmail account for a user."""
        pass


class FabricGmailAccountRepository(GmailAccountRepository):
    """Microsoft Fabric Lakehouse Gmail Account Repository."""

    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "gmail_account"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[GmailAccount]:
        """Converts Fabric row dict into GmailAccount model instance."""
        if not data:
            return None

        # Clean IDs
        acc_id = data.get("id")
        if isinstance(acc_id, str):
            try:
                acc_id = UUID(acc_id)
            except Exception:
                pass

        user_id = data.get("user_id")
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except Exception:
                pass

        # Handle token expiration alias
        token_expires = data.get("token_expires_at") or data.get("token_expiration")

        # Decrypt sensitive tokens transparently
        plain_access_token = decrypt_credential(data.get("access_token"))
        plain_refresh_token = decrypt_credential(data.get("refresh_token"))

        account = GmailAccount(
            id=acc_id or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            email=data.get("email", ""),
            access_token=plain_access_token,
            refresh_token=plain_refresh_token,
            token_expires_at=token_expires,
            scopes=data.get("scopes") or [
                "openid",
                "email",
                "profile",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
            ],
            history_id=data.get("history_id"),
            last_full_sync_at=data.get("last_full_sync_at"),
            last_sync_at=data.get("last_sync_at"),
            sync_status=data.get("sync_status", "idle"),
            sync_error=data.get("sync_error"),
            watch_expiration=data.get("watch_expiration"),
            watch_resource_id=data.get("watch_resource_id"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at") or datetime.now(timezone.utc),
            updated_at=data.get("updated_at") or datetime.now(timezone.utc),
        )
        return account

    async def get_by_user_id(self, user_id: Union[str, UUID]) -> Optional[GmailAccount]:
        uid_str = str(user_id)
        raw = await self.dal.get_one(self.table_name, {"user_id": uid_str})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def get_by_email(self, email: str) -> Optional[GmailAccount]:
        clean_email = email.lower().strip()
        raw = await self.dal.get_one(self.table_name, {"email": clean_email})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def list_active(self) -> list[GmailAccount]:
        records = await self.dal.read(self.table_name, filter_expr="is_active == True")
        accounts = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            acc = self._to_model(data)
            if acc and acc.is_active:
                accounts.append(acc)
        return accounts

    async def create(self, account: GmailAccount) -> GmailAccount:
        if not account.id:
            import uuid
            account.id = uuid.uuid4()
        payload = serialize_for_fabric(account, table_name=self.table_name)
        # Encrypt OAuth tokens before writing to Fabric Lakehouse
        if payload.get("access_token"):
            payload["access_token"] = encrypt_credential(payload["access_token"])
        if payload.get("refresh_token"):
            payload["refresh_token"] = encrypt_credential(payload["refresh_token"])
        # Ensure token_expiration is set for Fabric schema compatibility
        if "token_expires_at" in payload and payload["token_expires_at"]:
            payload["token_expiration"] = payload["token_expires_at"]
        await self.dal.insert(self.table_name, payload)
        return account


    async def update(self, account: GmailAccount) -> GmailAccount:
        account.updated_at = datetime.now(timezone.utc)
        payload = serialize_for_fabric(account, table_name=self.table_name)
        # Encrypt OAuth tokens before writing to Fabric Lakehouse
        if payload.get("access_token"):
            payload["access_token"] = encrypt_credential(payload["access_token"])
        if payload.get("refresh_token"):
            payload["refresh_token"] = encrypt_credential(payload["refresh_token"])
        if "token_expires_at" in payload and payload["token_expires_at"]:
            payload["token_expiration"] = payload["token_expires_at"]
        await self.dal.upsert(self.table_name, payload, merge_keys=["id"])
        return account

    async def upsert(self, account: GmailAccount) -> GmailAccount:
        existing = await self.get_by_user_id(account.user_id)
        if not existing:
            return await self.create(account)
        account.id = existing.id
        return await self.update(account)

    async def delete_by_user_id(self, user_id: Union[str, UUID]) -> bool:
        uid_str = str(user_id)
        await self.dal.delete(self.table_name, f"user_id = '{uid_str}'")
        return True


class PostgresGmailAccountRepository(GmailAccountRepository):
    """PostgreSQL Gmail Account Repository (Reference / Fallback)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: Union[str, UUID]) -> Optional[GmailAccount]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(select(GmailAccount).where(GmailAccount.user_id == uid))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[GmailAccount]:
        clean_email = email.lower().strip()
        res = await self.db.execute(select(GmailAccount).where(GmailAccount.email == clean_email))
        return res.scalar_one_or_none()

    async def list_active(self) -> list[GmailAccount]:
        res = await self.db.execute(select(GmailAccount).where(GmailAccount.is_active == True))
        return list(res.scalars().all())

    async def create(self, account: GmailAccount) -> GmailAccount:

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def update(self, account: GmailAccount) -> GmailAccount:
        account.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def upsert(self, account: GmailAccount) -> GmailAccount:
        existing = await self.get_by_user_id(account.user_id)
        if not existing:
            return await self.create(account)
        existing.access_token = account.access_token or existing.access_token
        existing.refresh_token = account.refresh_token or existing.refresh_token
        existing.token_expires_at = account.token_expires_at or existing.token_expires_at
        existing.sync_status = account.sync_status
        existing.sync_error = account.sync_error
        return await self.update(existing)

    async def delete_by_user_id(self, user_id: Union[str, UUID]) -> bool:
        acc = await self.get_by_user_id(user_id)
        if acc:
            await self.db.delete(acc)
            await self.db.commit()
            return True
        return False


def get_gmail_account_repository(
    db: Optional[AsyncSession] = None,
    backend: Optional[str] = None,
) -> GmailAccountRepository:
    """Factory yielding configured GmailAccountRepository (Fabric default, Postgres fallback)."""
    settings = get_settings()
    active_backend = backend or settings.database_backend

    if active_backend == "fabric":
        return FabricGmailAccountRepository()
    elif active_backend == "postgres":
        if db is None:
            raise ValueError("AsyncSession (db) required for PostgresGmailAccountRepository")
        return PostgresGmailAccountRepository(db)
    else:
        return FabricGmailAccountRepository()
