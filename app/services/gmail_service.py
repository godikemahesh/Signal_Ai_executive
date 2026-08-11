"""
Signal — Gmail API Service & Sync Service
Wraps Google Gmail API for message listing, fetching, and syncing.
"""

import logging
from typing import Any, Optional
from uuid import UUID
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.gmail import GmailAccount
from app.services.signal_processor import SignalProcessor

logger = logging.getLogger(__name__)
settings = get_settings()


class GmailService:
    """Gmail API wrapper service."""

    @staticmethod
    def get_gmail_client(access_token: str, refresh_token: Optional[str] = None):
        """Construct Google API client instance."""
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )
        return build("gmail", "v1", credentials=creds)

    @staticmethod
    async def sync_recent_messages(db: AsyncSession, user_id: UUID, max_results: int = 50) -> int:
        """Fetch and process recent unread/inbox messages."""
        res = await db.execute(select(GmailAccount).where(GmailAccount.user_id == user_id))
        acc = res.scalar_one_or_none()

        if not acc or not acc.access_token:
            logger.warning(f"No active Gmail token for user {user_id}")
            return 0

        try:
            client = GmailService.get_gmail_client(acc.access_token, acc.refresh_token)
            results = client.users().messages().list(userId="me", maxResults=max_results, q="in:inbox OR label:SENT").execute()
            messages = results.get("messages", [])

            processed_count = 0
            for msg_item in messages:
                msg_id = msg_item["id"]
                try:
                    msg_full = client.users().messages().get(userId="me", id=msg_id, format="full").execute()
                    await SignalProcessor.process_raw_message(db, user_id, msg_full)
                    processed_count += 1
                except Exception as msg_err:
                    logger.warning(f"Failed processing Gmail message {msg_id}: {msg_err}")
                    await db.rollback()

            acc.sync_status = "idle"
            acc.last_sync_at = func.now()
            await db.commit()
            return processed_count

        except Exception as e:
            logger.error(f"Gmail sync failed for user {user_id}: {e}")
            acc.sync_status = "error"
            acc.sync_error = str(e)
            await db.commit()
            return 0
