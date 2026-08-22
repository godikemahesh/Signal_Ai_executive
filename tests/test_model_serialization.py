"""
Phase 2 Tests: Model Compatibility & Serialization
Validates round-trip serialization between Python application data types
(UUID, JSON dicts, ARRAY lists, datetime, 384-dim float vectors) and Fabric Lakehouse Delta formats.
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
import pytest

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.serialization import serialize_for_fabric, deserialize_from_fabric
from app.core.fabric_dal import get_fabric_dal
from app.models.user import UserProfile
from app.models.signal import Signal, SignalEmbedding
from app.models.entity import Entity
from app.models.behavior import SenderProfile


def test_uuid_roundtrip():
    """Verify UUID serialization and deserialization."""
    test_uuid = uuid.uuid4()
    payload = {"id": test_uuid, "user_id": test_uuid}
    serialized = serialize_for_fabric(payload)
    assert serialized["id"] == str(test_uuid)
    assert isinstance(serialized["id"], str)

    deserialized = deserialize_from_fabric(serialized, parse_uuids=True)
    assert deserialized["id"] == test_uuid
    assert isinstance(deserialized["id"], uuid.UUID)
    print("PASS: UUID round-trip serialization")


def test_json_roundtrip():
    """Verify nested JSON objects/dicts serialization and deserialization."""
    complex_json = {
        "notifications_enabled": True,
        "digest_time": "07:30",
        "nested_stats": {"score": 98.5, "tags": ["priority", "executive"]},
    }
    payload = {"preferences": complex_json, "metadata_": {"company": "Google", "job_id": 123}}
    serialized = serialize_for_fabric(payload)
    assert isinstance(serialized["preferences"], str)
    assert isinstance(serialized["metadata"], str)

    deserialized = deserialize_from_fabric(serialized)
    assert deserialized["preferences"] == complex_json
    assert deserialized["metadata"]["company"] == "Google"
    assert deserialized["metadata"]["job_id"] == 123
    print("PASS: JSON dict round-trip serialization")


def test_array_roundtrip():
    """Verify Array/List serialization and deserialization."""
    recipients = ["ceo@company.com", "cto@company.com", "lead@company.com"]
    payload = {"to_recipients": recipients, "cc_recipients": ["team@company.com"]}
    serialized = serialize_for_fabric(payload)
    assert isinstance(serialized["to_recipients"], str)

    deserialized = deserialize_from_fabric(serialized)
    assert deserialized["to_recipients"] == recipients
    assert deserialized["cc_recipients"] == ["team@company.com"]
    print("PASS: ARRAY list round-trip serialization")


def test_datetime_roundtrip():
    """Verify ISO-8601 UTC timestamp serialization and deserialization."""
    now = datetime(2026, 8, 21, 15, 30, 45, 123456, tzinfo=timezone.utc)
    payload = {"received_at": now, "created_at": now}
    serialized = serialize_for_fabric(payload)
    assert serialized["received_at"] == now.isoformat()

    deserialized = deserialize_from_fabric(serialized)
    assert deserialized["received_at"] == now
    assert deserialized["received_at"].tzinfo is not None
    print("PASS: Datetime ISO-8601 round-trip serialization")


def test_embedding_vector_roundtrip():
    """Verify 384-dimensional float vector serialization and deserialization."""
    vector_384 = [float(i) * 0.001 for i in range(384)]
    payload = {
        "signal_id": uuid.uuid4(),
        "embedding_model": "tfidf-vectorizer",
        "embedding_vector": vector_384,
    }
    serialized = serialize_for_fabric(payload)
    assert isinstance(serialized["embedding_vector"], str)

    deserialized = deserialize_from_fabric(serialized)
    assert len(deserialized["embedding_vector"]) == 384
    assert deserialized["embedding_vector"] == vector_384
    print("PASS: Embedding vector round-trip serialization")


def test_nullable_and_numeric_fields():
    """Verify nullable fields and numeric precision (int, float, bool)."""
    payload = {
        "priority_score": 85,
        "engagement_score": 0.942,
        "is_read": False,
        "is_archived": True,
        "skip_reason": None,
    }
    serialized = serialize_for_fabric(payload)
    assert serialized["priority_score"] == 85
    assert serialized["engagement_score"] == 0.942
    assert serialized["is_read"] is False
    assert serialized["skip_reason"] is None

    deserialized = deserialize_from_fabric(serialized)
    assert deserialized["priority_score"] == 85
    assert deserialized["engagement_score"] == 0.942
    assert deserialized["is_read"] is False
    assert deserialized["skip_reason"] is None
    print("PASS: Nullable and numeric fields serialization")


@pytest.mark.asyncio
async def test_sqlalchemy_model_to_fabric_dal_lifecycle():
    """Verify end-to-end: SQLAlchemy model instance -> Fabric DAL insert -> read back -> deserialize."""
    dal = get_fabric_dal()
    test_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # 1. Create domain model instance
    user = UserProfile(
        id=uuid.UUID(test_id),
        email=f"phase2_model_{test_id[:8]}@signal.ai",
        display_name="Phase 2 Serialization User",
        avatar_url="https://lh3.googleusercontent.com/test",
        google_id=f"google_{test_id[:8]}",
        timezone="Asia/Kolkata",
        last_visit_at=now,
        preferences={"digest_time": "08:00", "notifications_enabled": True},
        created_at=now,
        updated_at=now,
    )

    # 2. Serialize and insert to Fabric Lakehouse
    fabric_row = serialize_for_fabric(user)
    await dal.insert("user_profile", fabric_row)

    # 3. Read back from Fabric Delta table
    raw_read = await dal.get_by_id("user_profile", test_id)
    assert raw_read is not None

    # 4. Deserialize back to domain types
    domain_data = deserialize_from_fabric(raw_read, parse_uuids=True)
    assert domain_data["id"] == uuid.UUID(test_id)
    assert domain_data["email"] == user.email
    assert domain_data["preferences"]["digest_time"] == "08:00"
    assert domain_data["preferences"]["notifications_enabled"] is True
    assert isinstance(domain_data["created_at"], datetime)

    # 5. Cleanup
    await dal.delete("user_profile", f"id = '{test_id}'")
    print("PASS: End-to-end SQLAlchemy model -> Fabric Lakehouse -> Domain Deserialization")


async def run_all_tests_async():
    test_uuid_roundtrip()
    test_json_roundtrip()
    test_array_roundtrip()
    test_datetime_roundtrip()
    test_embedding_vector_roundtrip()
    test_nullable_and_numeric_fields()
    await test_sqlalchemy_model_to_fabric_dal_lifecycle()


def run_all_tests():
    import asyncio
    asyncio.run(run_all_tests_async())
    print("\n============================================================")
    print("ALL PHASE 2 MODEL COMPATIBILITY & SERIALIZATION TESTS PASSED!")
    print("============================================================")


if __name__ == "__main__":
    run_all_tests()
