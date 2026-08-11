"""
Signal — Auth Schemas
Token and User Profile Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: "UserProfileResponse"


class UserProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    last_visit_at: datetime
    preferences: dict[str, Any]

    class Config:
        from_attributes = True
