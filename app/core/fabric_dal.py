"""
Signal — Microsoft Fabric Data Access Layer (DAL)
Provides high-performance, ACID-compliant read, write, upsert, and delete operations
against Microsoft Fabric Lakehouse Delta tables via OneLake DFS and Entra ID authentication.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID

import msal
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from app.config import get_settings

logger = logging.getLogger(__name__)

STORAGE_SCOPES = ["https://storage.azure.com/.default"]
FABRIC_SCOPES = ["https://api.fabric.microsoft.com/.default"]


class FabricDAL:
    """Microsoft Fabric Lakehouse Data Access Layer."""

    def __init__(self):
        self.settings = get_settings()
        self.workspace_id = self.settings.fabric_workspace_id
        self.lakehouse_id = self.settings.fabric_lakehouse_id
        self.client_id = self.settings.fabric_client_id
        self.authority = self.settings.fabric_authority
        self._cache_file_path = self._resolve_cache_path()
        self._msal_app: Optional[msal.PublicClientApplication] = None
        self._token_cache: Optional[msal.SerializableTokenCache] = None

    def _resolve_cache_path(self) -> str:
        """Find or create persistent MSAL token cache file."""
        if self.settings.fabric_token_cache_path and os.path.exists(self.settings.fabric_token_cache_path):
            return self.settings.fabric_token_cache_path

        # Candidate paths for persistent token cache
        candidate_paths = [
            Path(r"C:\Users\ganes\.gemini\antigravity-ide\brain\5ef138d2-f236-4b9f-b554-2cf679dc1adc\scratch\msal_token_cache.bin"),
            Path(".fabric_cache") / "token_cache.bin",
            Path.home() / ".fabric" / "token_cache.bin",
        ]

        for p in candidate_paths:
            if p.exists():
                return str(p)

        # Default to local .fabric_cache
        default_dir = Path(".fabric_cache")
        default_dir.mkdir(parents=True, exist_ok=True)
        return str(default_dir / "token_cache.bin")

    def _init_msal(self) -> tuple[msal.PublicClientApplication, msal.SerializableTokenCache]:
        """Initialize or load cached MSAL PublicClientApplication."""
        cache = msal.SerializableTokenCache()
        if os.path.exists(self._cache_file_path):
            try:
                with open(self._cache_file_path, "r", encoding="utf-8") as f:
                    cache.deserialize(f.read())
            except Exception as e:
                logger.warning(f"Could not load MSAL token cache: {e}")

        app = msal.PublicClientApplication(
            self.client_id,
            authority=self.authority,
            token_cache=cache,
        )
        return app, cache

    def _save_cache(self):
        """Save updated MSAL token cache to disk."""
        if self._token_cache and self._token_cache.has_state_changed:
            try:
                os.makedirs(os.path.dirname(self._cache_file_path), exist_ok=True)
                with open(self._cache_file_path, "w", encoding="utf-8") as f:
                    f.write(self._token_cache.serialize())
            except Exception as e:
                logger.warning(f"Could not save MSAL token cache: {e}")

    def get_storage_token(self) -> str:
        """Acquire a valid Azure Storage bearer token for OneLake DFS."""
        if not self._msal_app or not self._token_cache:
            self._msal_app, self._token_cache = self._init_msal()

        accounts = self._msal_app.get_accounts()
        if not accounts:
            raise RuntimeError(
                f"No cached Microsoft Fabric account found in {self._cache_file_path}. Please authenticate first."
            )

        res = self._msal_app.acquire_token_silent(STORAGE_SCOPES, account=accounts[0])
        if res and "access_token" in res:
            self._save_cache()
            return res["access_token"]

        # If silent acquisition failed, attempt refresh
        raise RuntimeError(
            f"Failed to acquire silent token for Microsoft Fabric. Result: {res.get('error_description') if res else 'Unknown error'}"
        )

    def get_table_uri(self, table_name: str) -> str:
        """Get the OneLake ABFSS table URI for a given Lakehouse table."""
        # Normalize table name (strip dbo. if present)
        clean_name = table_name.replace("dbo.", "")
        return f"abfss://{self.workspace_id}@onelake.dfs.fabric.microsoft.com/{self.lakehouse_id}/Tables/dbo/{clean_name}"

    def get_storage_options(self) -> dict[str, str]:
        """Build storage options with current bearer token and Fabric endpoint settings."""
        token = self.get_storage_token()
        return {
            "bearer_token": token,
            "azure_storage_use_azure_fabric_endpoint": "true",
        }

    def _sync_read(
        self,
        table_name: str,
        filter_expr: Optional[str] = None,
        columns: Optional[list[str]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Synchronous implementation of table read."""
        table_uri = self.get_table_uri(table_name)
        storage_options = self.get_storage_options()

        try:
            dt = DeltaTable(table_uri, storage_options=storage_options)
            df = dt.to_pandas(columns=columns)
        except Exception as e:
            logger.error(f"Error reading Delta table {table_name}: {e}")
            raise

        if df.empty:
            return []

        # Apply in-memory filtering if filter_expr is provided
        if filter_expr:
            try:
                df = df.query(filter_expr)
            except Exception as q_err:
                logger.warning(f"DataFrame query filter '{filter_expr}' failed, falling back: {q_err}")

        # Order by
        if order_by and order_by in df.columns:
            df = df.sort_values(by=order_by, ascending=not descending)

        # Offset & Limit
        if offset is not None:
            df = df.iloc[offset:]
        if limit is not None:
            df = df.iloc[:limit]

        return df.to_dict(orient="records")

    async def read(
        self,
        table_name: str,
        filter_expr: Optional[str] = None,
        columns: Optional[list[str]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously read records from a Fabric Delta table."""
        return await asyncio.to_thread(
            self._sync_read,
            table_name=table_name,
            filter_expr=filter_expr,
            columns=columns,
            order_by=order_by,
            descending=descending,
            limit=limit,
            offset=offset,
        )

    async def get_by_id(self, table_name: str, id_value: Union[str, UUID]) -> Optional[dict[str, Any]]:
        """Fetch a single record by its primary key ID."""
        id_str = str(id_value)
        records = await self.read(table_name, filter_expr=f"id == '{id_str}'", limit=1)
        return records[0] if records else None

    async def get_one(self, table_name: str, filter_dict: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Fetch a single record matching key-value pairs."""
        clauses = []
        for k, v in filter_dict.items():
            if isinstance(v, (str, UUID)):
                clauses.append(f"{k} == '{str(v)}'")
            elif isinstance(v, bool):
                clauses.append(f"{k} == {v}")
            elif v is None:
                clauses.append(f"{k}.isnull()")
            else:
                clauses.append(f"{k} == {v}")

        filter_expr = " and ".join(clauses) if clauses else None
        records = await self.read(table_name, filter_expr=filter_expr, limit=1)
        return records[0] if records else None

    def _sync_insert(self, table_name: str, records: list[dict[str, Any]]) -> None:
        """Synchronously append records to a Fabric Delta table."""
        if not records:
            return

        table_uri = self.get_table_uri(table_name)
        storage_options = self.get_storage_options()

        # Sanitize records (UUID to str, dict/list to JSON string)
        clean_records = []
        for r in records:
            clean_r = {}
            for k, v in r.items():
                if isinstance(v, UUID):
                    clean_r[k] = str(v)
                elif isinstance(v, (dict, list)):
                    clean_r[k] = json.dumps(v)
                elif isinstance(v, datetime):
                    clean_r[k] = v.isoformat()
                else:
                    clean_r[k] = v
            clean_records.append(clean_r)

        pa_table = pa.Table.from_pylist(clean_records)
        write_deltalake(
            table_uri,
            pa_table,
            mode="append",
            storage_options=storage_options,
            schema_mode="merge",
        )

    async def insert(self, table_name: str, records: Union[dict[str, Any], list[dict[str, Any]]]) -> None:
        """Asynchronously append one or more records to a Fabric Delta table."""
        if isinstance(records, dict):
            records = [records]
        await asyncio.to_thread(self._sync_insert, table_name, records)

    def _sync_upsert(
        self,
        table_name: str,
        records: list[dict[str, Any]],
        merge_keys: list[str],
    ) -> None:
        """Synchronously upsert records using Delta merge."""
        if not records:
            return

        table_uri = self.get_table_uri(table_name)
        storage_options = self.get_storage_options()

        clean_records = []
        for r in records:
            clean_r = {}
            for k, v in r.items():
                if isinstance(v, UUID):
                    clean_r[k] = str(v)
                elif isinstance(v, (dict, list)):
                    clean_r[k] = json.dumps(v)
                elif isinstance(v, datetime):
                    clean_r[k] = v.isoformat()
                else:
                    clean_r[k] = v
            clean_records.append(clean_r)

        pa_table = pa.Table.from_pylist(clean_records)
        dt = DeltaTable(table_uri, storage_options=storage_options)

        # Build merge predicate: target.key = source.key
        predicate = " AND ".join([f"target.{k} = source.{k}" for k in merge_keys])

        (
            dt.merge(
                source=pa_table,
                predicate=predicate,
                source_alias="source",
                target_alias="target",
            )
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute()
        )

    async def upsert(
        self,
        table_name: str,
        records: Union[dict[str, Any], list[dict[str, Any]]],
        merge_keys: Optional[list[str]] = None,
    ) -> None:
        """Asynchronously upsert records into a Fabric Delta table."""
        if isinstance(records, dict):
            records = [records]
        if not merge_keys:
            merge_keys = ["id"]
        await asyncio.to_thread(self._sync_upsert, table_name, records, merge_keys)

    def _sync_delete(self, table_name: str, filter_predicate: str) -> None:
        """Synchronously delete records matching predicate."""
        table_uri = self.get_table_uri(table_name)
        storage_options = self.get_storage_options()
        dt = DeltaTable(table_uri, storage_options=storage_options)
        dt.delete(filter_predicate)

    async def delete(self, table_name: str, filter_predicate: str) -> None:
        """Asynchronously delete matching records from a Fabric Delta table."""
        await asyncio.to_thread(self._sync_delete, table_name, filter_predicate)

    async def count(self, table_name: str, filter_expr: Optional[str] = None) -> int:
        """Get row count of a Fabric Delta table."""
        records = await self.read(table_name, filter_expr=filter_expr, columns=["id"] if "id" in table_name else None)
        return len(records)


# Global singleton instance
_fabric_dal_instance: Optional[FabricDAL] = None


def get_fabric_dal() -> FabricDAL:
    """Get the global Fabric DAL instance."""
    global _fabric_dal_instance
    if _fabric_dal_instance is None:
        _fabric_dal_instance = FabricDAL()
    return _fabric_dal_instance
