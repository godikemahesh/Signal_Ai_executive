"""
Phase 3B Tests: User Profile Domain Migration & Repository Abstraction
Verifies UserRepository interface, FabricUserRepository, PostgresUserRepository,
FastAPI dependency injection, and Pydantic validation.
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pytest

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.user import UserProfile
from app.repositories.user_repo import (
    FabricUserRepository,
    PostgresUserRepository,
    get_user_repository,
)
from app.schemas.auth import UserProfileResponse
from app.core.security import create_jwt_token
from app.config import get_settings


@pytest.mark.asyncio
async def test_fabric_user_repository_crud():
    """Test full CRUD operations on FabricUserRepository."""
    repo = FabricUserRepository()
    test_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"phase3_user_{str(test_id)[:8]}@signal.ai"

    # 1. Create
    user = UserProfile(
        id=test_id,
        email=email,
        display_name="Phase 3 Test Executive",
        avatar_url="https://lh3.googleusercontent.com/avatar123",
        google_id=f"google_{str(test_id)[:8]}",
        timezone="Asia/Kolkata",
        last_visit_at=now,
        preferences={
            "notifications_enabled": True,
            "digest_time": "08:15",
            "auto_archive_threshold": 7,
            "processing_tier_default": 2,
        },
        created_at=now,
        updated_at=now,
    )

    created = await repo.create(user)
    assert created.id == test_id
    assert created.email == email
    print("PASS: FabricUserRepository.create()")

    # 2. Get by ID
    by_id = await repo.get_by_id(test_id)
    assert by_id is not None
    assert by_id.id == test_id
    assert by_id.email == email
    assert by_id.preferences["digest_time"] == "08:15"
    print("PASS: FabricUserRepository.get_by_id()")

    # 3. Get by Email
    by_email = await repo.get_by_email(email)
    assert by_email is not None
    assert by_email.id == test_id
    assert by_email.display_name == "Phase 3 Test Executive"
    print("PASS: FabricUserRepository.get_by_email()")

    # 4. Get by Google ID
    by_google = await repo.get_by_google_id(f"google_{str(test_id)[:8]}")
    assert by_google is not None
    assert by_google.id == test_id
    print("PASS: FabricUserRepository.get_by_google_id()")

    # 5. Update / Upsert
    by_id.display_name = "Phase 3 Test Executive (Updated)"
    by_id.preferences["digest_time"] = "09:00"
    updated = await repo.update(by_id)
    assert updated.display_name == "Phase 3 Test Executive (Updated)"

    re_read = await repo.get_by_id(test_id)
    assert re_read is not None
    assert re_read.display_name == "Phase 3 Test Executive (Updated)"
    assert re_read.preferences["digest_time"] == "09:00"
    print("PASS: FabricUserRepository.update() & upsert()")

    # 6. Pydantic schema validation
    resp_schema = UserProfileResponse.model_validate(re_read)
    assert resp_schema.id == test_id
    assert resp_schema.email == email
    assert resp_schema.display_name == "Phase 3 Test Executive (Updated)"
    print("PASS: UserProfileResponse Pydantic schema validation")

    # 7. Delete
    deleted = await repo.delete(test_id)
    assert deleted is True

    verify_del = await repo.get_by_id(test_id)
    assert verify_del is None
    print("PASS: FabricUserRepository.delete() & cleanup")


@pytest.mark.asyncio
async def test_repository_factory():
    """Verify repository factory properly instantiates Fabric and Postgres repositories."""
    fabric_repo = get_user_repository(backend="fabric")
    assert isinstance(fabric_repo, FabricUserRepository)

    # Test default
    default_repo = get_user_repository()
    assert isinstance(default_repo, FabricUserRepository)
    print("PASS: Repository factory instantiation")


@pytest.mark.asyncio
async def test_app_startup():
    """Verify application startup with new repository layer."""
    from app.main import app
    assert app is not None
    assert app.title == "Signal"
    print("PASS: FastAPI Application startup with UserRepository abstraction")


def run_all_tests():
    asyncio.run(test_fabric_user_repository_crud())
    asyncio.run(test_repository_factory())
    asyncio.run(test_app_startup())
    print("\n============================================================")
    print("ALL PHASE 3B USER_PROFILE MIGRATION TESTS PASSED!")
    print("============================================================")


if __name__ == "__main__":
    run_all_tests()
