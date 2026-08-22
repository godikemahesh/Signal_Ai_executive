"""
Signal — Model Compatibility & Serialization Layer
Converts between Python application objects (UUID, dict, list, datetime, float vectors)
and Microsoft Fabric Lakehouse Delta table representations (strings, JSON text, ISO-8601).
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID

from dateutil import parser as date_parser

# Column definitions that store JSON structures in Fabric
JSON_COLUMNS = {
    "preferences",
    "metadata",
    "metadata_",
    "decision_data",
    "interaction_metadata",
    "pattern_data",
    "extracted_data",
    "extracted_metadata",
    "detected_actions",
    "detected_deadlines",
    "pii_mapping",
    "response",
}

# Column definitions that store Arrays in Fabric
ARRAY_COLUMNS = {
    "to_recipients",
    "cc_recipients",
    "bcc_recipients",
    "scopes",
    "participants",
    "gmail_label_ids",
    "signals_referenced",
    "entities_referenced",
    "referenced_signal_ids",
    "referenced_entity_ids",
}

# Column definitions that store Datetime / Timestamps
DATETIME_COLUMNS = {
    "created_at",
    "updated_at",
    "received_at",
    "processed_at",
    "opened_at",
    "interacted_at",
    "last_visit_at",
    "last_signal_at",
    "last_engagement_at",
    "last_calculated_at",
    "last_triggered_at",
    "last_full_sync_at",
    "last_sync_at",
    "token_expires_at",
    "token_expiration",
    "watch_expiration",
    "first_seen_at",
    "last_updated_at",
    "next_deadline",
    "snoozed_until",
    "feedback_at",
    "event_date",
    "event_timestamp",
}

# Column definitions that store UUIDs
UUID_COLUMNS = {
    "id",
    "user_id",
    "signal_id",
    "thread_id",
    "sender_profile_id",
    "entity_id",
    "source_entity_id",
    "target_entity_id",
    "category_id",
}


def serialize_for_fabric(
    data: Union[dict[str, Any], Any],
    table_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Serializes a Python dict or SQLAlchemy model instance into a Fabric-compatible row dict.
    - UUID -> str(UUID)
    - dict/list in JSON/ARRAY fields -> json.dumps()
    - datetime -> ISO-8601 string
    - embedding list[float] -> json.dumps()
    """
    if hasattr(data, "__dict__") and not isinstance(data, dict):
        # Extract fields from SQLAlchemy model instance
        raw_dict = {
            k: v for k, v in data.__dict__.items()
            if not k.startswith("_") and not callable(v)
        }
    elif isinstance(data, dict):
        raw_dict = dict(data)
    else:
        raise ValueError(f"Cannot serialize object of type {type(data)}")

    serialized: dict[str, Any] = {}
    for key, value in raw_dict.items():
        # Handle field alias (e.g. metadata_ -> metadata)
        dest_key = "metadata" if key == "metadata_" else key

        if value is None:
            serialized[dest_key] = None
            continue

        if isinstance(value, UUID):
            serialized[dest_key] = str(value)
        elif isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            serialized[dest_key] = value.isoformat()
        elif isinstance(value, (dict, list)):
            serialized[dest_key] = json.dumps(value)
        elif key in ("embedding", "embedding_vector") and isinstance(value, (list, tuple)):
            serialized[dest_key] = json.dumps(list(value))
        else:
            serialized[dest_key] = value

    return serialized


def deserialize_from_fabric(
    row: dict[str, Any],
    table_name: Optional[str] = None,
    parse_uuids: bool = False,
) -> dict[str, Any]:
    """
    Deserializes a Fabric Lakehouse row dict back into Python application types.
    - JSON strings -> dict / list
    - Array strings -> list
    - ISO-8601 strings -> datetime (UTC)
    - embedding_vector strings -> list[float]
    """
    if not row:
        return {}

    deserialized: dict[str, Any] = {}
    for key, value in row.items():
        if value is None:
            # Map standard defaults
            if key in JSON_COLUMNS:
                deserialized[key] = {}
            elif key in ARRAY_COLUMNS:
                deserialized[key] = []
            else:
                deserialized[key] = None
            continue

        # 1. JSON and ARRAY Deserialization
        if key in JSON_COLUMNS or key in ARRAY_COLUMNS or key in ("embedding", "embedding_vector"):
            if isinstance(value, str):
                trimmed = value.strip()
                if (trimmed.startswith("{") and trimmed.endswith("}")) or (
                    trimmed.startswith("[") and trimmed.endswith("]")
                ):
                    try:
                        deserialized[key] = json.loads(trimmed)
                        continue
                    except Exception:
                        pass
                elif trimmed == "":
                    deserialized[key] = [] if key in ARRAY_COLUMNS else {}
                    continue

        # 2. Datetime Deserialization
        if key in DATETIME_COLUMNS and isinstance(value, str):
            try:
                dt = date_parser.isoparse(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                deserialized[key] = dt
                continue
            except Exception:
                pass

        # 3. UUID Deserialization (optional based on caller)
        if parse_uuids and key in UUID_COLUMNS and isinstance(value, str) and len(value) == 36:
            try:
                deserialized[key] = UUID(value)
                continue
            except Exception:
                pass

        deserialized[key] = value

    return deserialized
