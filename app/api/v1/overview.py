"""
Signal — Overview API Endpoints
Returns the live state-based command center overview.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import UserProfile
from app.schemas.overview import OverviewResponse
from app.services.overview_service import OverviewService

router = APIRouter(prefix="/overview", tags=["Overview"])


@router.get("", response_model=OverviewResponse)
async def get_overview(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch live command center overview ("147 signals → 4 decisions")."""
    return await OverviewService.get_overview(db, user)
