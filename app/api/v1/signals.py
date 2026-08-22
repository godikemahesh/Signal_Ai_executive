"""
Signal — Signal CRUD & Management API Endpoints
Signal operations: list, get, archive, snooze, trigger sync.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.signal import Signal
from app.models.user import UserProfile
from app.repositories import get_signal_repository
from app.schemas.signal import SignalResponse
from app.services.behavior_engine import BehaviorEngine
from app.services.gmail_service import GmailService

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("", response_model=list[SignalResponse])
async def list_signals(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    bucket: Optional[str] = Query(None),
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List signals with pagination and bucket filtering."""
    signal_repo = get_signal_repository(db=db)
    if bucket:
        signals = await signal_repo.list_by_bucket(user.id, bucket, is_deleted=False)
        signals = signals[offset: offset + limit]
    else:
        signals = await signal_repo.list_by_user(
            user.id, is_deleted=False, order_by="received_at", descending=True, limit=limit, offset=offset
        )
    return [SignalResponse.model_validate(s) for s in signals]


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: UUID = Path(...),
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch single signal by ID."""
    signal_repo = get_signal_repository(db=db)
    signal = await signal_repo.get_by_id(signal_id)
    if not signal or str(signal.user_id) != str(user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")

    # Record open interaction
    await BehaviorEngine.record_interaction(
        db, user.id, signal.id, "opened", signal.sender_email
    )

    return SignalResponse.model_validate(signal)


@router.post("/{signal_id}/archive", response_model=SignalResponse)
async def archive_signal(
    signal_id: UUID = Path(...),
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive a signal."""
    signal_repo = get_signal_repository(db=db)
    signal = await signal_repo.get_by_id(signal_id)
    if not signal or str(signal.user_id) != str(user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")

    signal.is_archived = True

    await BehaviorEngine.record_interaction(
        db, user.id, signal.id, "archived", signal.sender_email
    )

    updated_signal = await signal_repo.update(signal)
    return SignalResponse.model_validate(updated_signal)


@router.post("/sync")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger background Gmail sync."""
    background_tasks.add_task(GmailService.sync_recent_messages, db, user.id, 50)
    return {"message": "Gmail sync scheduled in background"}

