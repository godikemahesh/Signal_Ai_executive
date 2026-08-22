"""
Test Phase 3F — Remaining Persistence Migration
Tests SenderProfile, BehaviorInteraction, AskSignalHistory, and GmailAccount.list_active() on Microsoft Fabric OneLake.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
import pytest

sys.path.insert(0, os.path.abspath("."))

from app.core.fabric_dal import get_fabric_dal
from app.models.ai_decision import AskSignalHistory
from app.models.behavior import BehaviorInteraction, SenderProfile
from app.models.gmail import GmailAccount
from app.repositories import (
    FabricAskSignalHistoryRepository,
    FabricBehaviorInteractionRepository,
    FabricGmailAccountRepository,
    FabricSenderProfileRepository,
    get_ask_signal_history_repository,
    get_behavior_interaction_repository,
    get_gmail_account_repository,
    get_sender_profile_repository,
)


@pytest.mark.asyncio
async def test_sender_profile_lifecycle():
    """Test SenderProfile CRUD and list_top on Fabric."""
    repo = FabricSenderProfileRepository()
    test_email = f"test_sender_{uuid.uuid4().hex[:6]}@domain.com"

    profile = SenderProfile(
        email_address=test_email,
        domain="domain.com",
        display_name="Test Sender",
        sender_type="vendor",
        processing_tier=1,
        total_received=15,
        total_opened=12,
        total_replied=4,
        total_ignored=1,
        total_archived=1,
        engagement_score=0.85,
        confidence=0.92,
        consecutive_ignores=0,
    )

    # 1. Create
    created = await repo.create(profile)
    assert created.email_address == test_email

    # 2. Get
    fetched = await repo.get_by_email(test_email)
    assert fetched is not None
    assert fetched.email_address == test_email
    assert fetched.total_received == 15
    assert fetched.processing_tier == 1
    assert abs(fetched.engagement_score - 0.85) < 0.01

    # 3. Update
    fetched.total_opened += 1
    fetched.total_received += 1
    updated = await repo.update(fetched)
    assert updated.total_opened == 13

    # 4. Upsert
    profile.display_name = "Updated Sender Name"
    upserted = await repo.upsert(profile)
    assert upserted.display_name == "Updated Sender Name"

    # 5. List top
    top_senders = await repo.list_top(limit=10)
    assert isinstance(top_senders, list)
    assert len(top_senders) >= 1

    # Cleanup
    dal = get_fabric_dal()
    await dal.delete("sender_profiles", f"email_address == '{test_email}'")
    print("[PASS] SenderProfile lifecycle test passed.")


@pytest.mark.asyncio
async def test_behavior_interaction_lifecycle():
    """Test BehaviorInteraction creation and metadata serialization on Fabric."""
    repo = FabricBehaviorInteractionRepository()
    user_id = uuid.uuid4()
    sig_id = uuid.uuid4()

    interaction = BehaviorInteraction(
        id=uuid.uuid4(),
        user_id=user_id,
        signal_id=sig_id,
        interaction_type="moved_bucket",
        metadata_={"from_bucket": "today", "to_bucket": "do_now"},
    )

    # 1. Create
    created = await repo.create(interaction)
    assert created.id == interaction.id

    # 2. List by user
    user_interactions = await repo.list_by_user(user_id)
    assert len(user_interactions) >= 1
    match = [i for i in user_interactions if str(i.id) == str(interaction.id)]
    assert len(match) == 1
    assert match[0].interaction_type == "moved_bucket"
    assert match[0].metadata_.get("to_bucket") == "do_now"

    # Cleanup
    dal = get_fabric_dal()
    await dal.delete("behavior_interactions", f"id == '{str(interaction.id)}'")
    print("[PASS] BehaviorInteraction lifecycle test passed.")


@pytest.mark.asyncio
async def test_ask_signal_history_lifecycle():
    """Test AskSignalHistory creation and column mappings on Fabric."""
    repo = FabricAskSignalHistoryRepository()
    user_id = uuid.uuid4()
    sig_ids = [uuid.uuid4(), uuid.uuid4()]
    ent_ids = [uuid.uuid4()]

    history = AskSignalHistory(
        id=uuid.uuid4(),
        user_id=user_id,
        query="What meetings do I have today?",
        intent="calendar_query",
        response={"answer": "You have 2 meetings today.", "intent": "calendar_query"},
        response_text="You have 2 meetings today.",
        signals_referenced=sig_ids,
        entities_referenced=ent_ids,
        processing_time_ms=320,
        model_used="gemini",
    )

    # 1. Create
    created = await repo.create(history)
    assert created.id == history.id

    # 2. List by user
    histories = await repo.list_by_user(user_id)
    assert len(histories) >= 1
    match = [h for h in histories if str(h.id) == str(history.id)]
    assert len(match) == 1
    assert match[0].query == "What meetings do I have today?"
    assert match[0].processing_time_ms == 320
    assert len(match[0].signals_referenced) == 2
    assert len(match[0].entities_referenced) == 1

    # Cleanup
    dal = get_fabric_dal()
    await dal.delete("ask_signal_history", f"id == '{str(history.id)}'")
    print("[PASS] AskSignalHistory lifecycle test passed.")


@pytest.mark.asyncio
async def test_gmail_account_list_active_and_poller_wiring():
    """Test GmailAccountRepository.list_active() on Fabric."""
    repo = FabricGmailAccountRepository()
    user_id = uuid.uuid4()
    test_email = f"poller_test_{uuid.uuid4().hex[:6]}@company.com"

    acc = GmailAccount(
        user_id=user_id,
        email=test_email,
        access_token="test_poller_access_token",
        refresh_token="test_poller_refresh_token",
        is_active=True,
    )

    # Create account (tokens encrypted with AES-256-GCM)
    await repo.create(acc)

    # list_active
    active_accounts = await repo.list_active()
    assert isinstance(active_accounts, list)
    matching = [a for a in active_accounts if a.email == test_email]
    assert len(matching) == 1
    assert matching[0].is_active is True
    # Verify decrypted token
    assert matching[0].access_token == "test_poller_access_token"

    # Cleanup
    await repo.delete_by_user_id(user_id)
    print("[PASS] GmailAccount list_active & poller wiring test passed.")


@pytest.mark.asyncio
async def test_repository_factories_phase3f():
    """Test all Phase 3F factory functions."""
    sender_repo = get_sender_profile_repository()
    assert isinstance(sender_repo, FabricSenderProfileRepository)

    behavior_repo = get_behavior_interaction_repository()
    assert isinstance(behavior_repo, FabricBehaviorInteractionRepository)

    ask_repo = get_ask_signal_history_repository()
    assert isinstance(ask_repo, FabricAskSignalHistoryRepository)

    gmail_repo = get_gmail_account_repository()
    assert isinstance(gmail_repo, FabricGmailAccountRepository)
    print("[PASS] Phase 3F repository factories test passed.")


if __name__ == "__main__":
    async def main():
        print("Running Phase 3F Tests...")
        await test_sender_profile_lifecycle()
        await test_behavior_interaction_lifecycle()
        await test_ask_signal_history_lifecycle()
        await test_gmail_account_list_active_and_poller_wiring()
        await test_repository_factories_phase3f()
        print("\nAll Phase 3F Tests Passed Successfully!")

    asyncio.run(main())
