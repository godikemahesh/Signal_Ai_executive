"""
Signal — Timeline API Endpoints
Returns entity timelines (Life Events like job applications, orders, bills).
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import UserProfile
from app.schemas.timeline import EntityResponse
from app.services.timeline_service import TimelineService

router = APIRouter(prefix="/timeline", tags=["Timeline"])


@router.get("", response_model=list[EntityResponse])
async def get_timeline(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all active entity timelines."""
    entities = await TimelineService.get_all_entities(db, user.id)
    return [EntityResponse.model_validate(e) for e in entities]


from uuid import UUID

@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID = Path(...),
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single entity by ID with its timeline events."""
    entity = await TimelineService.get_entity_by_id(db, user.id, entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return EntityResponse.model_validate(entity)
