"""
Signal — Focus API Endpoints
Returns human-readable priority buckets (Do now, Today, This week, Waiting, Completed, Ignored).
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.core.constants import ALL_BUCKETS
from app.database import get_db
from app.dependencies import get_current_user
from app.models.signal import Signal
from app.models.user import UserProfile
from app.repositories import get_signal_repository
from app.schemas.focus import FocusViewResponse, MoveBucketRequest
from app.schemas.signal import SignalResponse
from app.services.behavior_engine import BehaviorEngine
from app.services.focus_service import FocusService

router = APIRouter(prefix="/focus", tags=["Focus"])


@router.get("", response_model=FocusViewResponse)
async def get_focus_buckets(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch summary of all focus buckets."""
    return await FocusService.get_buckets_summary(db, user.id)


@router.get("/{bucket}", response_model=list[SignalResponse])
async def get_bucket_signals(
    bucket: str = Path(...),
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch signals in a specific bucket."""
    if bucket not in ALL_BUCKETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid bucket. Allowed buckets: {ALL_BUCKETS}",
        )
    signals = await FocusService.get_signals_by_bucket(db, user.id, bucket)
    return [SignalResponse.model_validate(s) for s in signals]


@router.patch("/{signal_id}/move", response_model=SignalResponse)
async def move_signal_bucket(
    body: MoveBucketRequest,
    signal_id: UUID = Path(...),
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually move a signal to a different bucket."""
    if body.new_bucket not in ALL_BUCKETS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bucket")

    signal_repo = get_signal_repository(db=db)
    signal = await signal_repo.get_by_id(signal_id)

    if not signal or str(signal.user_id) != str(user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")

    old_bucket = signal.bucket
    signal.bucket = body.new_bucket
    signal.bucket_reason = body.reason

    # Record behavior interaction for learning
    await BehaviorEngine.record_interaction(
        db,
        user.id,
        signal.id,
        "moved_bucket",
        signal.sender_email,
        metadata={"from_bucket": old_bucket, "to_bucket": body.new_bucket},
    )

    updated_signal = await signal_repo.update(signal)
    return SignalResponse.model_validate(updated_signal)

