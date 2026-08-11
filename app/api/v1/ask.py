"""
Signal — Ask Signal API Endpoints
Natural language query interface over user's digital life.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import UserProfile
from app.schemas.ask import AskSignalRequest, AskSignalResponse
from app.services.ask_signal_service import AskSignalService

router = APIRouter(prefix="/ask", tags=["Ask Signal"])


@router.post("", response_model=AskSignalResponse)
async def ask_signal(
    body: AskSignalRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query your entire digital life using natural language."""
    return await AskSignalService.ask(db, user.id, body.query)
