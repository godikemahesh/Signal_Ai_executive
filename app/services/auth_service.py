"""
Signal — Auth Service
Google OAuth flow, token verification, and user session management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import create_jwt_token
from app.models.gmail import GmailAccount
from app.models.user import UserProfile
from app.repositories import get_gmail_account_repository, get_user_repository

settings = get_settings()


class AuthService:
    """Authentication and Google OAuth service."""

    @staticmethod
    def get_google_auth_url() -> str:
        """Generate Google OAuth login URL."""
        scopes = [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        scope_str = "%20".join(scopes)
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.google_client_id}&"
            f"redirect_uri={settings.google_redirect_uri}&"
            f"response_type=code&"
            f"scope={scope_str}&"
            f"access_type=offline&"
            f"prompt=select_account"
        )
        return auth_url

    @staticmethod
    async def process_google_callback(code: str, db: AsyncSession) -> dict[str, Any]:
        """Exchange auth code for Google tokens and create/update user."""
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise RuntimeError(f"Failed to exchange Google OAuth code: {token_resp.text}")

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)

            user_info_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_info_resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch user info: {user_info_resp.text}")

            user_info = user_info_resp.json()
            email = user_info["email"]
            google_id = user_info.get("sub")
            display_name = user_info.get("name")
            avatar_url = user_info.get("picture")

        # 1. Get or create user profile via repository abstraction
        user_repo = get_user_repository(db=db)
        user = await user_repo.get_by_email(email)

        if not user:
            user = UserProfile(
                email=email,
                google_id=google_id,
                display_name=display_name,
                avatar_url=avatar_url,
            )
            user = await user_repo.create(user)
        else:
            user.display_name = display_name or user.display_name
            user.avatar_url = avatar_url or user.avatar_url
            user.google_id = google_id or user.google_id
            user = await user_repo.update(user)

        # 2. Update connected Gmail account via repository abstraction
        gmail_repo = get_gmail_account_repository(db=db)
        gmail_acc = await gmail_repo.get_by_user_id(user.id)

        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        if not gmail_acc:
            gmail_acc = GmailAccount(
                user_id=user.id,
                email=email,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
            )
            await gmail_repo.create(gmail_acc)
        else:
            gmail_acc.access_token = access_token
            if refresh_token:
                gmail_acc.refresh_token = refresh_token
            gmail_acc.token_expires_at = token_expires_at
            await gmail_repo.update(gmail_acc)

        # 3. Generate app JWT token
        jwt_token = create_jwt_token(
            data={"sub": str(user.id), "email": user.email},
            secret_key=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            expires_delta=timedelta(hours=settings.jwt_expiration_hours),
        )

        return {
            "access_token": jwt_token,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours),
            "user": user,
        }
