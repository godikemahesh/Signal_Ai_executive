"""
Signal — Signal Embedding Repository
Provides abstract, Fabric, and PostgreSQL implementations for SignalEmbedding persistence.
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
from app.models.signal import SignalEmbedding


class SignalEmbeddingRepository(ABC):
    @abstractmethod
    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> Optional[SignalEmbedding]:
        pass

    @abstractmethod
    async def create(self, embedding: SignalEmbedding) -> SignalEmbedding:
        pass


class FabricSignalEmbeddingRepository(SignalEmbeddingRepository):
    def __init__(self, dal: Optional[FabricDAL] = None):
        self.dal = dal or get_fabric_dal()
        self.table_name = "signal_embeddings"

    def _to_model(self, data: Optional[dict[str, Any]]) -> Optional[SignalEmbedding]:
        if not data:
            return None
        emb_id = data.get("id")
        if isinstance(emb_id, str):
            try:
                emb_id = UUID(emb_id)
            except Exception:
                pass
        sig_id = data.get("signal_id")
        if isinstance(sig_id, str):
            try:
                sig_id = UUID(sig_id)
            except Exception:
                pass

        # Vector parsing from embedding_vector JSON string
        vec_raw = data.get("embedding_vector")
        vec = None
        if isinstance(vec_raw, str):
            try:
                vec = json.loads(vec_raw)
            except Exception:
                vec = None
        elif isinstance(vec_raw, list):
            vec = vec_raw

        return SignalEmbedding(
            id=emb_id or uuid.uuid4(),
            signal_id=sig_id or uuid.uuid4(),
            embedding_model=data.get("embedding_model", "all-MiniLM-L6-v2"),
            embedding=vec,
            content_hash=None,  # Not stored in Fabric
            created_at=data.get("created_at") or datetime.now(timezone.utc),
        )

    def _to_fabric_payload(self, embedding: SignalEmbedding) -> dict[str, Any]:
        """Serialize SignalEmbedding to Fabric payload. Column alias: embedding -> embedding_vector."""
        vec = embedding.embedding
        if isinstance(vec, list):
            vec_str = json.dumps(vec)
        elif hasattr(vec, "tolist"):
            vec_str = json.dumps(vec.tolist())
        elif isinstance(vec, str):
            vec_str = vec
        else:
            vec_str = "[]"

        return {
            "id": str(embedding.id),
            "signal_id": str(embedding.signal_id),
            "embedding_model": embedding.embedding_model or "all-MiniLM-L6-v2",
            "embedding_vector": vec_str,
            "created_at": embedding.created_at.isoformat() if embedding.created_at else datetime.now(timezone.utc).isoformat(),
        }

    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> Optional[SignalEmbedding]:
        sid = str(signal_id)
        raw = await self.dal.get_one(self.table_name, {"signal_id": sid})
        if not raw:
            return None
        data = deserialize_from_fabric(raw, table_name=self.table_name)
        return self._to_model(data)

    async def create(self, embedding: SignalEmbedding) -> SignalEmbedding:
        payload = self._to_fabric_payload(embedding)
        await self.dal.insert(self.table_name, payload)
        return embedding


class PostgresSignalEmbeddingRepository(SignalEmbeddingRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_signal_id(self, signal_id: Union[str, UUID]) -> Optional[SignalEmbedding]:
        sid = UUID(str(signal_id)) if isinstance(signal_id, str) else signal_id
        res = await self.db.execute(select(SignalEmbedding).where(SignalEmbedding.signal_id == sid))
        return res.scalar_one_or_none()

    async def create(self, embedding: SignalEmbedding) -> SignalEmbedding:
        self.db.add(embedding)
        await self.db.commit()
        await self.db.refresh(embedding)
        return embedding


def get_signal_embedding_repository(db: Optional[AsyncSession] = None, backend: Optional[str] = None) -> SignalEmbeddingRepository:
    settings = get_settings()
    active = backend or settings.database_backend
    if active == "fabric":
        return FabricSignalEmbeddingRepository()
    elif active == "postgres":
        if db is None:
            raise ValueError("AsyncSession required for PostgresSignalEmbeddingRepository")
        return PostgresSignalEmbeddingRepository(db)
    return FabricSignalEmbeddingRepository()
