import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
import pytest

sys.path.insert(0, os.path.abspath("."))

from app.core.fabric_dal import get_fabric_dal

from app.models.category import SignalCategory
from app.models.entity import Entity, EntityTimelineEvent, SignalEntity
from app.models.signal import Signal, SignalAttachment, SignalEmbedding, SignalThread
from app.repositories.signal_category_repo import FabricSignalCategoryRepository
from app.repositories.signal_embedding_repo import FabricSignalEmbeddingRepository
from app.repositories.signal_entity_repo import (
    FabricEntityRepository,
    FabricEntityTimelineEventRepository,
    FabricSignalEntityRepository,
)
from app.repositories.signal_repo import (
    FabricSignalAttachmentRepository,
    FabricSignalRepository,
    FabricSignalThreadRepository,
)


@pytest.mark.asyncio
async def test_signal_lifecycle():
    """Test full Signal lifecycle on Fabric Lakehouse."""
    repo = FabricSignalRepository()
    test_user_id = uuid.uuid4()
    msg_id = f"test_msg_{uuid.uuid4().hex[:8]}"

    sig = Signal(
        id=uuid.uuid4(),
        user_id=test_user_id,
        gmail_message_id=msg_id,
        gmail_thread_id=f"thread_{uuid.uuid4().hex[:8]}",
        sender_email="alice@company.com",
        sender_name="Alice Engineer",
        subject="Sprint Planning Notes",
        snippet="Here are the sprint planning notes...",
        body_plain="Here are the sprint planning notes from today's meeting.",
        body_sanitized="Here are the sprint planning notes from today's meeting.",
        summary="Sprint planning notes summarized",
        detected_actions=[{"action": "Review PR", "due": "tomorrow"}],
        detected_deadlines=[{"deadline": "2026-08-25T10:00:00Z"}],
        extracted_metadata={"topic": "engineering"},
        processing_tier=2,
        processing_status="completed",
        priority_score=85,
        bucket="today",
        bucket_reason="High priority engineering update",
        is_read=False,
        is_starred=False,
        is_archived=False,
        is_deleted=False,
        gmail_link=f"https://mail.google.com/mail/u/0/#inbox/{msg_id}",
        received_at=datetime.now(timezone.utc),
        gmail_label_ids=["INBOX", "IMPORTANT"],
        gmail_internal_date=1724256000000,
    )

    # 1. Create
    created = await repo.create(sig)
    assert created.id == sig.id

    # 2. Get by ID
    fetched = await repo.get_by_id(sig.id)
    assert fetched is not None
    assert fetched.gmail_message_id == msg_id
    assert fetched.priority_score == 85
    assert fetched.bucket == "today"
    assert len(fetched.detected_actions) == 1
    assert fetched.detected_actions[0]["action"] == "Review PR"

    # 3. Get by Gmail Message ID
    by_msg = await repo.get_by_gmail_message_id(msg_id)
    assert by_msg is not None
    assert by_msg.id == sig.id

    # 4. List by user & bucket
    bucket_signals = await repo.list_by_bucket(test_user_id, "today")
    assert len(bucket_signals) >= 1
    assert any(s.id == sig.id for s in bucket_signals)

    # 5. Count by bucket
    counts = await repo.count_by_bucket(test_user_id)
    assert counts.get("today", 0) >= 1

    # 6. Update (Archive)
    fetched.is_archived = True
    fetched.bucket = "completed"
    await repo.update(fetched)

    updated = await repo.get_by_id(sig.id)
    assert updated.is_archived is True
    assert updated.bucket == "completed"

    # Clean up
    dal = get_fabric_dal()
    await dal.delete("signals", f"id == '{str(sig.id)}'")
    print("[PASS] Signal lifecycle test passed.")


@pytest.mark.asyncio
async def test_signal_thread_lifecycle():
    """Test SignalThread lifecycle on Fabric."""
    repo = FabricSignalThreadRepository()
    test_user_id = uuid.uuid4()
    thread_id = f"gthread_{uuid.uuid4().hex[:8]}"

    thread = SignalThread(
        id=uuid.uuid4(),
        user_id=test_user_id,
        gmail_thread_id=thread_id,
        subject="Project Alpha Discussion",
        signal_count=1,
        last_signal_at=datetime.now(timezone.utc),
        participants=["alice@test.com", "bob@test.com"],
        is_active=True,
    )

    created = await repo.create(thread)
    assert created.id == thread.id

    fetched = await repo.get_by_gmail_thread_id(test_user_id, thread_id)
    assert fetched is not None
    assert fetched.subject == "Project Alpha Discussion"
    assert len(fetched.participants) == 2

    # Upsert
    thread.signal_count = 3
    upserted = await repo.upsert(thread)
    assert upserted.signal_count == 3

    # Clean up
    dal = get_fabric_dal()
    await dal.delete("signal_threads", f"id == '{str(thread.id)}'")
    print("[PASS] SignalThread lifecycle test passed.")


@pytest.mark.asyncio
async def test_signal_attachments():
    """Test SignalAttachment batch creation and retrieval on Fabric."""
    repo = FabricSignalAttachmentRepository()
    sig_id = uuid.uuid4()

    att1 = SignalAttachment(
        id=uuid.uuid4(),
        signal_id=sig_id,
        filename="report.pdf",
        mime_type="application/pdf",
        size_bytes=1048576,
        gmail_attachment_id="att_1",
    )
    att2 = SignalAttachment(
        id=uuid.uuid4(),
        signal_id=sig_id,
        filename="image.png",
        mime_type="image/png",
        size_bytes=524288,
        gmail_attachment_id="att_2",
    )

    await repo.create_batch([att1, att2])

    attachments = await repo.get_by_signal_id(sig_id)
    assert len(attachments) == 2
    filenames = {a.filename for a in attachments}
    assert "report.pdf" in filenames
    assert "image.png" in filenames

    # Clean up
    dal = get_fabric_dal()
    await dal.delete("signal_attachments", f"signal_id == '{str(sig_id)}'")
    print("[PASS] SignalAttachment batch test passed.")


@pytest.mark.asyncio
async def test_signal_categories():
    """Test SignalCategory mapping (is_primary ↔ assigned_by) on Fabric."""
    repo = FabricSignalCategoryRepository()
    sig_id = uuid.uuid4()
    cat_id = uuid.uuid4()

    sc = SignalCategory(
        id=uuid.uuid4(),
        signal_id=sig_id,
        category_id=cat_id,
        confidence=0.95,
        is_primary=True,
    )

    await repo.create(sc)

    fetched = await repo.get_by_signal_id(sig_id)
    assert len(fetched) == 1
    assert fetched[0].is_primary is True
    assert abs(fetched[0].confidence - 0.95) < 0.01

    # Clean up
    dal = get_fabric_dal()
    await dal.delete("signal_categories", f"signal_id == '{str(sig_id)}'")
    print("[PASS] SignalCategory mapping test passed.")


@pytest.mark.asyncio
async def test_entity_graph_linkages():
    """Test Entity, SignalEntity, and EntityTimelineEvent on Fabric."""
    ent_repo = FabricEntityRepository()
    sig_ent_repo = FabricSignalEntityRepository()
    timeline_repo = FabricEntityTimelineEventRepository()

    user_id = uuid.uuid4()
    sig_id = uuid.uuid4()

    # 1. Create Entity
    entity = Entity(
        id=uuid.uuid4(),
        user_id=user_id,
        name="Acme Corp Interview",
        entity_type="job_application",
        status="active",
        current_state="Interview scheduled",
        next_action="Prepare system design",
        metadata_={"company": "Acme Corp", "round": "Technical"},
    )
    await ent_repo.create(entity)

    # 2. Link Signal to Entity (SignalEntity)
    sig_ent = SignalEntity(
        id=uuid.uuid4(),
        signal_id=sig_id,
        entity_id=entity.id,
        relationship_type="updated",
    )
    await sig_ent_repo.create(sig_ent)

    # 3. Add Timeline Event
    event = EntityTimelineEvent(
        id=uuid.uuid4(),
        entity_id=entity.id,
        signal_id=sig_id,
        title="Technical Interview",
        description="Interview scheduled for 2 PM",
        event_date=datetime.now(timezone.utc),
        status="action_required",
    )
    await timeline_repo.create(event)

    # 4. Verify Entity retrieval with timeline events
    fetched_ent = await ent_repo.get_by_id(entity.id, user_id=user_id)
    assert fetched_ent is not None
    assert fetched_ent.name == "Acme Corp Interview"
    assert len(fetched_ent.timeline_events) == 1
    assert fetched_ent.timeline_events[0].title == "Technical Interview"

    # 5. Verify SignalEntity retrieval
    sig_links = await sig_ent_repo.get_by_signal_id(sig_id)
    assert len(sig_links) == 1
    assert sig_links[0].entity_id == entity.id
    assert sig_links[0].relationship_type == "updated"

    # Clean up
    dal = get_fabric_dal()
    await dal.delete("entity_timeline_events", f"entity_id == '{str(entity.id)}'")
    await dal.delete("signal_entities", f"signal_id == '{str(sig_id)}'")
    await dal.delete("entities", f"id == '{str(entity.id)}'")
    print("[PASS] Entity graph linkages test passed.")


@pytest.mark.asyncio
async def test_signal_embedding_storage():
    """Test 384-dimensional vector embedding storage and retrieval on Fabric."""
    repo = FabricSignalEmbeddingRepository()
    sig_id = uuid.uuid4()

    dummy_vector = [0.05 * (i % 20) for i in range(384)]

    emb = SignalEmbedding(
        id=uuid.uuid4(),
        signal_id=sig_id,
        embedding_model="tfidf-vectorizer",
        embedding=dummy_vector,
    )

    await repo.create(emb)

    fetched = await repo.get_by_signal_id(sig_id)
    assert fetched is not None
    assert fetched.embedding_model == "tfidf-vectorizer"
    assert fetched.embedding is not None
    assert len(fetched.embedding) == 384
    assert abs(fetched.embedding[10] - dummy_vector[10]) < 1e-4

    # Clean up
    dal = get_fabric_dal()
    await dal.delete("signal_embeddings", f"signal_id == '{str(sig_id)}'")
    print("[PASS] SignalEmbedding vector round-trip test passed.")


if __name__ == "__main__":
    async def main():
        print("Running Phase 3E Tests...")
        await test_signal_lifecycle()
        await test_signal_thread_lifecycle()
        await test_signal_attachments()
        await test_signal_categories()
        await test_entity_graph_linkages()
        await test_signal_embedding_storage()
        print("\nAll Phase 3E Tests Passed Successfully!")

    asyncio.run(main())
