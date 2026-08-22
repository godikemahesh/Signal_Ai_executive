import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.fabric_dal import get_fabric_dal


@pytest.mark.asyncio
async def test_fabric_authentication():
    """Verify that Fabric DAL can acquire a valid storage token."""
    dal = get_fabric_dal()
    token = dal.get_storage_token()
    assert token is not None
    assert len(token) > 50
    print("PASS: Fabric authentication and token acquisition")


@pytest.mark.asyncio
async def test_fabric_read_known_domains():
    """Verify read operation on seeded dbo.known_domains table."""
    dal = get_fabric_dal()
    domains = await dal.read("known_domains", limit=10)
    assert len(domains) > 0
    assert "domain" in domains[0]
    print(f"PASS: Fabric read ({len(domains)} known domains retrieved)")


@pytest.mark.asyncio
async def test_fabric_write_upsert_delete_lifecycle():
    """Verify full CRUD lifecycle: insert -> read back -> upsert -> delete."""
    dal = get_fabric_dal()
    test_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()

    # 1. Insert test user profile
    test_record = {
        "id": test_id,
        "email": f"test_dal_{test_id[:8]}@signal.ai",
        "display_name": "Phase 1 Test User",
        "avatar_url": "https://lh3.googleusercontent.com/test",
        "google_id": f"google_{test_id[:8]}",
        "timezone": "UTC",
        "last_visit_at": now_str,
        "preferences": {"notifications_enabled": True, "test_mode": True},
        "created_at": now_str,
        "updated_at": now_str,
    }

    await dal.insert("user_profile", test_record)
    print("PASS: Fabric insert")

    # 2. Read back
    fetched = await dal.get_by_id("user_profile", test_id)
    assert fetched is not None
    assert fetched["id"] == test_id
    assert fetched["email"] == test_record["email"]
    print("PASS: Fabric read-after-insert")

    # 3. Upsert (update display name)
    test_record["display_name"] = "Phase 1 Test User UPDATED"
    await dal.upsert("user_profile", test_record, merge_keys=["id"])

    updated = await dal.get_by_id("user_profile", test_id)
    assert updated is not None
    assert updated["display_name"] == "Phase 1 Test User UPDATED"
    print("PASS: Fabric upsert / merge")

    # 4. Delete
    await dal.delete("user_profile", f"id = '{test_id}'")
    deleted = await dal.get_by_id("user_profile", test_id)
    assert deleted is None
    print("PASS: Fabric delete")


@pytest.mark.asyncio
async def test_app_startup_with_fabric_dal():
    """Verify application starts and FastAPI master router loads cleanly."""
    from app.main import app
    assert app is not None
    assert app.title == "Signal"
    print("PASS: Application startup with Fabric DAL")


if __name__ == "__main__":
    asyncio.run(test_fabric_authentication())
    asyncio.run(test_fabric_read_known_domains())
    asyncio.run(test_fabric_write_upsert_delete_lifecycle())
    asyncio.run(test_app_startup_with_fabric_dal())
    print("\nALL PHASE 1 FABRIC DAL TESTS PASSED SUCCESSFULLY!")
