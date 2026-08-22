"""
Signal — Signal Core Repositories
Provides abstract, Fabric, and PostgreSQL implementations for Signal, SignalThread, and SignalAttachment persistence.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.fabric_dal import FabricDAL, get_fabric_dal
from app.core.serialization import deserialize_from_fabric, serialize_for_fabric
from app.models.signal import Signal, SignalAttachment, SignalThread


# ============================================================
# SIGNAL COLUMNS that exist in the app model but NOT in Fabric
# These are omitted from Fabric writes (approved architecture decision)
# ============================================================
SIGNAL_FABRIC_OMIT_FIELDS = {
    "thread_id",          # FK resolved by gmail_thread_id
    "sender_profile_id",  # FK resolved by sender_email
    "to_recipients",      # Display-only, not queried
    "cc_recipients",      # Display-only, not queried
    "bcc_recipients",     # Display-only, not queried
    "pii_mapping",        # Ephemeral processing artifact
}


# ============================================================
# SignalRepository
# ============================================================

class SignalRepository(ABC):
    """Abstract Signal repository interface."""

    @abstractmethod
    async def get_by_id(self, signal_id: Union[str, UUID]) -> Optional[Signal]:
        pass

    @abstractmethod
    async def get_by_gmail_message_id(self, gmail_message_id: str) -> Optional[Signal]:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: Union[str, UUID], is_deleted: bool = False,
                           order_by: str = "received_at", descending: bool = True,
                           limit: Optional[int] = None, offset: Optional[int] = None) -> list[Signal]:
        pass

    @abstractmethod
    async def list_by_bucket(self, user_id: Union[str, UUID], bucket: str,
                             is_deleted: bool = False) -> list[Signal]:
        pass

    @abstractmethod
    async def list_by_thread(self, user_id: Union[str, UUID], gmail_thread_id: str) -> list[Signal]:
        pass

    @abstractmethod
    async def count_by_bucket(self, user_id: Union[str, UUID]) -> dict[str, int]:
        pass

    @abstractmethod
    async def count_total(self, user_id: Union[str, UUID], is_deleted: bool = False) -> int:
        pass

    @abstractmethod
    async def count_filtered(self, user_id: Union[str, UUID], is_archived: bool = None,
                             bucket: Optional[str] = None, is_deleted: bool = False) -> int:
        pass

    @abstractmethod
    async def create(self, signal: Signal) -> Signal:
        pass

    @abstractmethod
    async def update(self, signal: Signal) -> Signal:
        pass

    @abstractmethod
    async def bulk_update(self, signals: list[Signal]) -> None:
        pass

    @abstractmethod
    async def delete(self, signal_id: Union[str, UUID]) -> bool:
        """Delete a signal record."""
        pass



class FabricSignalRepository(SignalRepository):
    """Microsoft Fabric Lakehouse Signal Repository."""

    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "signals"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[Signal]:
        if not data:
            return None

        sig_id = data.get("id")
        if isinstance(sig_id, str):
            try:
                sig_id = UUID(sig_id)
            except Exception:
                pass

        user_id = data.get("user_id")
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except Exception:
                pass

        # Deserialize JSONB fields
        detected_actions = data.get("detected_actions")
        if isinstance(detected_actions, str):
            try:
                detected_actions = json.loads(detected_actions)
            except Exception:
                detected_actions = []

        detected_deadlines = data.get("detected_deadlines")
        if isinstance(detected_deadlines, str):
            try:
                detected_deadlines = json.loads(detected_deadlines)
            except Exception:
                detected_deadlines = []

        extracted_metadata = data.get("extracted_metadata")
        if isinstance(extracted_metadata, str):
            try:
                extracted_metadata = json.loads(extracted_metadata)
            except Exception:
                extracted_metadata = {}

        gmail_label_ids = data.get("gmail_label_ids")
        if isinstance(gmail_label_ids, str):
            try:
                gmail_label_ids = json.loads(gmail_label_ids)
            except Exception:
                gmail_label_ids = []

        gmail_internal_date = data.get("gmail_internal_date")
        if isinstance(gmail_internal_date, str):
            try:
                gmail_internal_date = int(gmail_internal_date)
            except Exception:
                gmail_internal_date = None

        priority_score = data.get("priority_score")
        if priority_score is not None and not (isinstance(priority_score, float) and (priority_score != priority_score)):
            try:
                priority_score = int(priority_score)
            except Exception:
                priority_score = 50
        else:
            priority_score = 50

        tier = data.get("processing_tier")
        if tier is not None and not (isinstance(tier, float) and (tier != tier)):
            try:
                processing_tier = int(tier)
            except Exception:
                processing_tier = 2
        else:
            processing_tier = 2

        signal = Signal(
            id=sig_id or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            gmail_message_id=data.get("gmail_message_id", ""),
            gmail_thread_id=data.get("gmail_thread_id"),
            sender_email=data.get("sender_email", ""),
            sender_name=data.get("sender_name"),
            subject=data.get("subject"),
            snippet=data.get("snippet"),
            body_plain=data.get("body_plain"),
            body_html=data.get("body_html"),
            body_sanitized=data.get("body_sanitized"),
            summary=data.get("summary"),
            detected_actions=detected_actions or [],
            detected_deadlines=detected_deadlines or [],
            extracted_metadata=extracted_metadata or {},
            pii_mapping={},
            processing_tier=processing_tier,

            processing_status=data.get("processing_status", "pending"),
            skip_reason=data.get("skip_reason"),
            priority_score=priority_score,
            bucket=data.get("bucket", "today"),
            bucket_reason=data.get("bucket_reason"),
            is_read=data.get("is_read", False),
            is_starred=data.get("is_starred", False),
            is_archived=data.get("is_archived", False),
            is_snoozed=data.get("is_snoozed", False),
            snoozed_until=data.get("snoozed_until"),
            is_deleted=data.get("is_deleted", False),
            gmail_link=data.get("gmail_link"),
            received_at=data.get("received_at") or datetime.now(timezone.utc),
            processed_at=data.get("processed_at"),
            opened_at=data.get("opened_at"),
            interacted_at=data.get("interacted_at"),
            has_attachments=data.get("has_attachments", False),
            gmail_label_ids=gmail_label_ids,
            gmail_internal_date=gmail_internal_date,
            created_at=data.get("created_at") or datetime.now(timezone.utc),
            updated_at=data.get("updated_at") or datetime.now(timezone.utc),
        )
        return signal

    def _to_fabric_payload(self, signal: Signal) -> dict[str, Any]:
        """Serialize Signal to Fabric payload, omitting app-only columns."""
        payload = serialize_for_fabric(signal, table_name=self.table_name)
        for field in SIGNAL_FABRIC_OMIT_FIELDS:
            payload.pop(field, None)
        # Ensure boolean defaults
        payload["is_deleted"] = bool(payload.get("is_deleted") or False)
        payload["is_archived"] = bool(payload.get("is_archived") or False)
        payload["is_read"] = bool(payload.get("is_read") or False)
        payload["is_starred"] = bool(payload.get("is_starred") or False)
        payload["is_snoozed"] = bool(payload.get("is_snoozed") or False)
        payload["has_attachments"] = bool(payload.get("has_attachments") or False)
        # Ensure gmail_internal_date is string
        if "gmail_internal_date" in payload and payload["gmail_internal_date"] is not None:
            payload["gmail_internal_date"] = str(payload["gmail_internal_date"])
        return payload

    async def get_by_id(self, signal_id: Union[str, UUID]) -> Optional[Signal]:
        raw = await self.dal.get_by_id(self.table_name, str(signal_id))
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def get_by_gmail_message_id(self, gmail_message_id: str) -> Optional[Signal]:
        raw = await self.dal.get_one(self.table_name, {"gmail_message_id": gmail_message_id})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def list_by_user(self, user_id: Union[str, UUID], is_deleted: bool = False,
                           order_by: str = "received_at", descending: bool = True,
                           limit: Optional[int] = None, offset: Optional[int] = None) -> list[Signal]:
        uid = str(user_id)
        filter_expr = f"user_id == '{uid}'"
        records = await self.dal.read(
            self.table_name, filter_expr=filter_expr,
            order_by=order_by, descending=descending,
        )
        results = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            s = self._to_model(data)
            if s and (bool(s.is_deleted) == is_deleted):
                results.append(s)
        if offset is not None:
            results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results

    async def list_by_bucket(self, user_id: Union[str, UUID], bucket: str,
                             is_deleted: bool = False) -> list[Signal]:
        uid = str(user_id)
        filter_expr = f"user_id == '{uid}' and bucket == '{bucket}'"
        records = await self.dal.read(
            self.table_name, filter_expr=filter_expr,
            order_by="priority_score", descending=True,
        )
        results = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            s = self._to_model(data)
            if s and (bool(s.is_deleted) == is_deleted):
                results.append(s)
        # Secondary sort by received_at descending
        results.sort(key=lambda x: (x.priority_score or 0, x.received_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return results

    async def list_by_thread(self, user_id: Union[str, UUID], gmail_thread_id: str) -> list[Signal]:
        uid = str(user_id)
        filter_expr = f"user_id == '{uid}' and gmail_thread_id == '{gmail_thread_id}'"
        records = await self.dal.read(self.table_name, filter_expr=filter_expr)
        results = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            s = self._to_model(data)
            if s:
                results.append(s)
        return results

    async def count_by_bucket(self, user_id: Union[str, UUID]) -> dict[str, int]:
        uid = str(user_id)
        filter_expr = f"user_id == '{uid}'"
        records = await self.dal.read(self.table_name, filter_expr=filter_expr, columns=["user_id", "bucket", "is_deleted"])
        counts: dict[str, int] = {}
        for r in records:
            if not bool(r.get("is_deleted")):
                b = r.get("bucket", "today")
                counts[b] = counts.get(b, 0) + 1
        return counts

    async def count_total(self, user_id: Union[str, UUID], is_deleted: bool = False) -> int:
        uid = str(user_id)
        filter_expr = f"user_id == '{uid}'"
        records = await self.dal.read(self.table_name, filter_expr=filter_expr, columns=["user_id", "id", "is_deleted"])
        return sum(1 for r in records if bool(r.get("is_deleted")) == is_deleted)

    async def count_filtered(self, user_id: Union[str, UUID], is_archived: bool = None,
                             bucket: Optional[str] = None, is_deleted: bool = False) -> int:
        uid = str(user_id)
        filter_expr = f"user_id == '{uid}'"
        records = await self.dal.read(self.table_name, filter_expr=filter_expr, columns=["user_id", "id", "is_archived", "bucket", "is_deleted"])
        count = 0
        for r in records:
            if bool(r.get("is_deleted")) != is_deleted:
                continue
            if is_archived is not None and bool(r.get("is_archived")) != is_archived:
                continue
            if bucket is not None and r.get("bucket") != bucket:
                continue
            count += 1
        return count



    async def create(self, signal: Signal) -> Signal:
        if not signal.id:
            signal.id = uuid.uuid4()
        payload = self._to_fabric_payload(signal)
        await self.dal.insert(self.table_name, payload)
        return signal


    async def update(self, signal: Signal) -> Signal:
        signal.updated_at = datetime.now(timezone.utc)
        payload = self._to_fabric_payload(signal)
        await self.dal.upsert(self.table_name, payload, merge_keys=["id"])
        return signal

    async def bulk_update(self, signals: list[Signal]) -> None:
        for signal in signals:
            await self.update(signal)

    async def delete(self, signal_id: Union[str, UUID]) -> bool:
        sid = str(signal_id)
        await self.dal.delete(self.table_name, f"id == '{sid}'")
        return True



class PostgresSignalRepository(SignalRepository):
    """PostgreSQL Signal Repository (Fallback)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, signal_id: Union[str, UUID]) -> Optional[Signal]:
        sid = UUID(str(signal_id)) if isinstance(signal_id, str) else signal_id
        res = await self.db.execute(select(Signal).where(Signal.id == sid))
        return res.scalar_one_or_none()

    async def get_by_gmail_message_id(self, gmail_message_id: str) -> Optional[Signal]:
        res = await self.db.execute(select(Signal).where(Signal.gmail_message_id == gmail_message_id))
        return res.scalar_one_or_none()

    async def list_by_user(self, user_id: Union[str, UUID], is_deleted: bool = False,
                           order_by: str = "received_at", descending: bool = True,
                           limit: Optional[int] = None, offset: Optional[int] = None) -> list[Signal]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        query = select(Signal).where(Signal.user_id == uid, Signal.is_deleted == is_deleted)
        order_col = getattr(Signal, order_by, Signal.received_at)
        query = query.order_by(order_col.desc() if descending else order_col.asc())
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_by_bucket(self, user_id: Union[str, UUID], bucket: str,
                             is_deleted: bool = False) -> list[Signal]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(
            select(Signal).where(Signal.user_id == uid, Signal.bucket == bucket, Signal.is_deleted == is_deleted)
            .order_by(Signal.priority_score.desc(), Signal.received_at.desc())
        )
        return list(res.scalars().all())

    async def list_by_thread(self, user_id: Union[str, UUID], gmail_thread_id: str) -> list[Signal]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(
            select(Signal).where(Signal.user_id == uid, Signal.gmail_thread_id == gmail_thread_id)
        )
        return list(res.scalars().all())

    async def count_by_bucket(self, user_id: Union[str, UUID]) -> dict[str, int]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(
            select(Signal.bucket, func.count(Signal.id))
            .where(Signal.user_id == uid, Signal.is_deleted == False)
            .group_by(Signal.bucket)
        )
        return dict(res.all())

    async def count_total(self, user_id: Union[str, UUID], is_deleted: bool = False) -> int:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(
            select(func.count(Signal.id)).where(Signal.user_id == uid, Signal.is_deleted == is_deleted)
        )
        return res.scalar() or 0

    async def count_filtered(self, user_id: Union[str, UUID], is_archived: bool = None,
                             bucket: Optional[str] = None, is_deleted: bool = False) -> int:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        query = select(func.count(Signal.id)).where(Signal.user_id == uid, Signal.is_deleted == is_deleted)
        if is_archived is not None:
            query = query.where(Signal.is_archived == is_archived)
        if bucket is not None:
            query = query.where(Signal.bucket == bucket)
        res = await self.db.execute(query)
        return res.scalar() or 0

    async def create(self, signal: Signal) -> Signal:
        self.db.add(signal)
        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def update(self, signal: Signal) -> Signal:
        signal.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def bulk_update(self, signals: list[Signal]) -> None:
        for s in signals:
            s.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def delete(self, signal_id: Union[str, UUID]) -> bool:
        sid = UUID(str(signal_id)) if isinstance(signal_id, str) else signal_id
        res = await self.db.execute(select(Signal).where(Signal.id == sid))
        sig = res.scalar_one_or_none()
        if sig:
            await self.db.delete(sig)
            await self.db.commit()
            return True
        return False



# ============================================================
# SignalThreadRepository
# ============================================================

class SignalThreadRepository(ABC):
    @abstractmethod
    async def get_by_gmail_thread_id(self, user_id: Union[str, UUID], gmail_thread_id: str) -> Optional[SignalThread]:
        pass

    @abstractmethod
    async def create(self, thread: SignalThread) -> SignalThread:
        pass

    @abstractmethod
    async def update(self, thread: SignalThread) -> SignalThread:
        pass

    @abstractmethod
    async def upsert(self, thread: SignalThread) -> SignalThread:
        pass


class FabricSignalThreadRepository(SignalThreadRepository):
    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "signal_threads"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[SignalThread]:
        if not data:
            return None
        tid = data.get("id")
        if isinstance(tid, str):
            try:
                tid = UUID(tid)
            except Exception:
                pass
        user_id = data.get("user_id")
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except Exception:
                pass
        participants = data.get("participants")
        if isinstance(participants, str):
            try:
                participants = json.loads(participants)
            except Exception:
                participants = []

        sc = data.get("signal_count")
        sig_count = 0
        if sc is not None and not (isinstance(sc, float) and (sc != sc)):
            try:
                sig_count = int(sc)
            except Exception:
                sig_count = 0

        return SignalThread(
            id=tid or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            gmail_thread_id=data.get("gmail_thread_id", ""),
            subject=data.get("subject"),
            signal_count=sig_count,
            last_signal_at=data.get("last_signal_at"),
            participants=participants or [],
            is_active=data.get("is_active", True),
            created_at=data.get("created_at") or datetime.now(timezone.utc),
            updated_at=data.get("updated_at") or datetime.now(timezone.utc),
        )

    async def get_by_gmail_thread_id(self, user_id: Union[str, UUID], gmail_thread_id: str) -> Optional[SignalThread]:
        raw = await self.dal.get_one(self.table_name, {"gmail_thread_id": gmail_thread_id, "user_id": str(user_id)})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def create(self, thread: SignalThread) -> SignalThread:
        payload = serialize_for_fabric(thread, table_name=self.table_name)
        await self.dal.insert(self.table_name, payload)
        return thread

    async def update(self, thread: SignalThread) -> SignalThread:
        thread.updated_at = datetime.now(timezone.utc)
        payload = serialize_for_fabric(thread, table_name=self.table_name)
        await self.dal.upsert(self.table_name, payload, merge_keys=["id"])
        return thread

    async def upsert(self, thread: SignalThread) -> SignalThread:
        existing = await self.get_by_gmail_thread_id(thread.user_id, thread.gmail_thread_id)
        if not existing:
            return await self.create(thread)
        thread.id = existing.id
        return await self.update(thread)


class PostgresSignalThreadRepository(SignalThreadRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_gmail_thread_id(self, user_id: Union[str, UUID], gmail_thread_id: str) -> Optional[SignalThread]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(
            select(SignalThread).where(SignalThread.gmail_thread_id == gmail_thread_id, SignalThread.user_id == uid)
        )
        return res.scalar_one_or_none()

    async def create(self, thread: SignalThread) -> SignalThread:
        self.db.add(thread)
        await self.db.commit()
        await self.db.refresh(thread)
        return thread

    async def update(self, thread: SignalThread) -> SignalThread:
        thread.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(thread)
        return thread

    async def upsert(self, thread: SignalThread) -> SignalThread:
        existing = await self.get_by_gmail_thread_id(thread.user_id, thread.gmail_thread_id)
        if not existing:
            return await self.create(thread)
        existing.signal_count = thread.signal_count
        existing.last_signal_at = thread.last_signal_at
        existing.subject = thread.subject or existing.subject
        return await self.update(existing)


# ============================================================
# SignalAttachmentRepository
# ============================================================

class SignalAttachmentRepository(ABC):
    @abstractmethod
    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalAttachment]:
        pass

    @abstractmethod
    async def create(self, attachment: SignalAttachment) -> SignalAttachment:
        pass

    @abstractmethod
    async def create_batch(self, attachments: list[SignalAttachment]) -> list[SignalAttachment]:
        pass


class FabricSignalAttachmentRepository(SignalAttachmentRepository):
    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "signal_attachments"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[SignalAttachment]:
        if not data:
            return None
        att_id = data.get("id")
        if isinstance(att_id, str):
            try:
                att_id = UUID(att_id)
            except Exception:
                pass
        sig_id = data.get("signal_id")
        if isinstance(sig_id, str):
            try:
                sig_id = UUID(sig_id)
            except Exception:
                pass
        sz = data.get("size_bytes")
        size_bytes = None
        if sz is not None and not (isinstance(sz, float) and (sz != sz)):
            try:
                size_bytes = int(sz)
            except Exception:
                size_bytes = None

        return SignalAttachment(
            id=att_id or uuid.uuid4(),
            signal_id=sig_id or uuid.uuid4(),
            filename=data.get("filename"),
            mime_type=data.get("mime_type"),
            size_bytes=size_bytes,
            gmail_attachment_id=data.get("gmail_attachment_id"),
            created_at=data.get("created_at") or datetime.now(timezone.utc),
        )


    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalAttachment]:
        sid = str(signal_id)
        records = await self.dal.read(self.table_name, filter_expr=f"signal_id == '{sid}'")
        results = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            a = self._to_model(data)
            if a:
                results.append(a)
        return results

    async def create(self, attachment: SignalAttachment) -> SignalAttachment:
        payload = serialize_for_fabric(attachment, table_name=self.table_name)
        await self.dal.insert(self.table_name, payload)
        return attachment

    async def create_batch(self, attachments: list[SignalAttachment]) -> list[SignalAttachment]:
        if not attachments:
            return []
        payloads = [serialize_for_fabric(a, table_name=self.table_name) for a in attachments]
        await self.dal.insert(self.table_name, payloads)
        return attachments


class PostgresSignalAttachmentRepository(SignalAttachmentRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> list[SignalAttachment]:
        sid = UUID(str(signal_id)) if isinstance(signal_id, str) else signal_id
        res = await self.db.execute(select(SignalAttachment).where(SignalAttachment.signal_id == sid))
        return list(res.scalars().all())

    async def create(self, attachment: SignalAttachment) -> SignalAttachment:
        self.db.add(attachment)
        await self.db.commit()
        await self.db.refresh(attachment)
        return attachment

    async def create_batch(self, attachments: list[SignalAttachment]) -> list[SignalAttachment]:
        for a in attachments:
            self.db.add(a)
        await self.db.commit()
        return attachments


# ============================================================
# Factory Functions
# ============================================================

def get_signal_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> SignalRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricSignalRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresSignalRepository")
        return PostgresSignalRepository(db)
    return FabricSignalRepository()


def get_signal_thread_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> SignalThreadRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricSignalThreadRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresSignalThreadRepository")
        return PostgresSignalThreadRepository(db)
    return FabricSignalThreadRepository()


def get_signal_attachment_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> SignalAttachmentRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricSignalAttachmentRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresSignalAttachmentRepository")
        return PostgresSignalAttachmentRepository(db)
    return FabricSignalAttachmentRepository()
