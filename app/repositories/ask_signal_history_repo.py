"""
Signal — Ask Signal History Repository
Provides abstract, Fabric, and PostgreSQL implementations for AskSignalHistory persistence.
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
from app.models.ai_decision import AskSignalHistory


class AskSignalHistoryRepository(ABC):
    """Abstract repository for AskSignalHistory persistence."""

    @abstractmethod
    async def create(self, history: AskSignalHistory) -> AskSignalHistory:
        """Save a new natural language query history entry."""
        pass

    @abstractmethod
    async def list_by_user(
        self, user_id: Union[str, UUID], limit: int = 20
    ) -> list[AskSignalHistory]:
        """Fetch query history for a user."""
        pass


class FabricAskSignalHistoryRepository(AskSignalHistoryRepository):
    """Microsoft Fabric Lakehouse Ask Signal History Repository."""

    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "ask_signal_history"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[AskSignalHistory]:
        if not data:
            return None

        hist_id = data.get("id")
        if isinstance(hist_id, str):
            try:
                hist_id = UUID(hist_id)
            except Exception:
                pass

        user_id = data.get("user_id")
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except Exception:
                pass

        # Response JSON deserialization
        resp_raw = data.get("response")
        response_dict = {}
        if isinstance(resp_raw, str):
            try:
                response_dict = json.loads(resp_raw)
            except Exception:
                response_dict = {"answer": resp_raw}
        elif isinstance(resp_raw, dict):
            response_dict = resp_raw

        # Signals referenced: referenced_signal_ids -> signals_referenced
        sig_ref_raw = data.get("referenced_signal_ids") or data.get("signals_referenced")
        signals_referenced = []
        if isinstance(sig_ref_raw, str):
            try:
                signals_referenced = [UUID(s) for s in json.loads(sig_ref_raw)]
            except Exception:
                signals_referenced = []
        elif isinstance(sig_ref_raw, list):
            signals_referenced = [UUID(str(s)) for s in sig_ref_raw]

        # Entities referenced: referenced_entity_ids -> entities_referenced
        ent_ref_raw = data.get("referenced_entity_ids") or data.get("entities_referenced")
        entities_referenced = []
        if isinstance(ent_ref_raw, str):
            try:
                entities_referenced = [UUID(e) for e in json.loads(ent_ref_raw)]
            except Exception:
                entities_referenced = []
        elif isinstance(ent_ref_raw, list):
            entities_referenced = [UUID(str(e)) for e in ent_ref_raw]

        # Processing time: execution_time_ms -> processing_time_ms
        exec_ms = data.get("execution_time_ms") or data.get("processing_time_ms")
        processing_time_ms = 0
        if exec_ms is not None and not (isinstance(exec_ms, float) and (exec_ms != exec_ms)):
            try:
                processing_time_ms = int(exec_ms)
            except Exception:
                processing_time_ms = 0

        answer_text = response_dict.get("answer") if isinstance(response_dict, dict) else str(response_dict)

        return AskSignalHistory(
            id=hist_id or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            query=data.get("query", ""),
            intent=response_dict.get("intent", "general_query") if isinstance(response_dict, dict) else "general_query",
            response=response_dict,
            response_text=answer_text,
            signals_referenced=signals_referenced,
            entities_referenced=entities_referenced,
            processing_time_ms=processing_time_ms,
            model_used=data.get("model_used", "gemini"),
            created_at=data.get("created_at") or datetime.now(timezone.utc),
        )

    def _to_fabric_payload(self, history: AskSignalHistory) -> dict[str, Any]:
        """Serialize with Fabric column name aliases."""
        resp_str = json.dumps(history.response or {}) if isinstance(history.response, dict) else str(history.response or "")
        sig_ids_str = json.dumps([str(s) for s in (history.signals_referenced or [])])
        ent_ids_str = json.dumps([str(e) for e in (history.entities_referenced or [])])

        return {
            "id": str(history.id),
            "user_id": str(history.user_id),
            "query": history.query or "",
            "response": resp_str,
            "referenced_signal_ids": sig_ids_str,
            "referenced_entity_ids": ent_ids_str,
            "execution_time_ms": int(history.processing_time_ms or 0),
            "created_at": (
                history.created_at.isoformat()
                if isinstance(history.created_at, datetime)
                else datetime.now(timezone.utc).isoformat()
            ),
        }

    async def create(self, history: AskSignalHistory) -> AskSignalHistory:
        payload = self._to_fabric_payload(history)
        await self.dal.insert(self.table_name, payload)
        return history

    async def list_by_user(
        self, user_id: Union[str, UUID], limit: int = 20
    ) -> list[AskSignalHistory]:
        uid = str(user_id)
        records = await self.dal.read(
            self.table_name,
            filter_expr=f"user_id == '{uid}'",
            order_by="created_at",
            descending=True,
            limit=limit,
        )
        histories = []
        for r in records:
            data = deserialize_from_fabric(r, table_name=self.table_name)
            h = self._to_model(data)
            if h:
                histories.append(h)
        return histories


class PostgresAskSignalHistoryRepository(AskSignalHistoryRepository):
    """PostgreSQL Ask Signal History Repository (Fallback)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, history: AskSignalHistory) -> AskSignalHistory:
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history

    async def list_by_user(
        self, user_id: Union[str, UUID], limit: int = 20
    ) -> list[AskSignalHistory]:
        uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        res = await self.db.execute(
            select(AskSignalHistory)
            .where(AskSignalHistory.user_id == uid)
            .order_by(AskSignalHistory.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())


def get_ask_signal_history_repository(
    db: Optional[AsyncSession] = None,
    backend: Optional[str] = None,
) -> AskSignalHistoryRepository:
    """Factory yielding configured AskSignalHistoryRepository."""
    settings = get_settings()
    active_backend = backend or settings.database_backend
    if active_backend == "fabric":
        return FabricAskSignalHistoryRepository()
    elif active_backend == "postgres":
        if db is None:
            raise ValueError("AsyncSession (db) required for PostgresAskSignalHistoryRepository")
        return PostgresAskSignalHistoryRepository(db)
    return FabricAskSignalHistoryRepository()
