"""
Signal — Gmail API Service & Synchronization Pipeline
Handles Google OAuth token refresh, 10-day historical import with full pagination,
incremental new-mail detection with in-process concurrency locking, and Fabric persistence.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Optional
from uuid import UUID

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.gmail import GmailAccount
from app.repositories import get_gmail_account_repository, get_signal_repository
from app.services.signal_processor import SignalProcessor

logger = logging.getLogger(__name__)
settings = get_settings()

# In-process concurrency locks keyed by user_id string to prevent overlapping sync runs
_sync_locks: dict[str, asyncio.Lock] = {}


class GmailService:
    """Gmail API synchronization service."""

    @staticmethod
    def _get_user_lock(user_id: UUID) -> asyncio.Lock:
        """Obtain or initialize in-process sync lock for a given user."""
        uid_str = str(user_id)
        if uid_str not in _sync_locks:
            _sync_locks[uid_str] = asyncio.Lock()
        return _sync_locks[uid_str]

    @staticmethod
    def get_date_filter_query(days: int = 10) -> str:
        """Generate Gmail search query for the last N calendar days."""
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_ts = int(cutoff_dt.timestamp())
        return f"(in:inbox OR label:SENT) after:{cutoff_ts}"

    @staticmethod
    def get_gmail_client(
        access_token: str,
        refresh_token: Optional[str] = None,
        account: Optional[GmailAccount] = None,
        gmail_repo: Optional[Any] = None,
    ):
        """Construct Google API client instance with automatic token refresh support."""
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )

        # Check and handle proactive token refresh if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                if account and gmail_repo and creds.token != access_token:
                    account.access_token = creds.token
                    if creds.expiry:
                        expiry = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry.tzinfo is None else creds.expiry
                        account.token_expires_at = expiry
                    # Note: repository update is async, so callers can await if needed
            except Exception as ref_err:
                logger.warning(f"Token refresh failed during client setup: {ref_err}")

        return build("gmail", "v1", credentials=creds)

    @staticmethod
    async def sync_historical_messages(
        db: AsyncSession,
        user_id: UUID,
        days: int = 10,
        batch_page_size: int = 100,
    ) -> dict[str, Any]:
        """
        Execute full 10-day historical email import with server-side date filter,
        complete pagination, message deduplication, and single-pipeline classification.
        """
        lock = GmailService._get_user_lock(user_id)
        if lock.locked():
            logger.info(f"Historical sync already in progress for user {user_id}. Skipping.")
            return {"status": "in_progress", "processed": 0}

        async with lock:
            gmail_repo = get_gmail_account_repository(db=db)
            signal_repo = get_signal_repository(db=db)
            acc = await gmail_repo.get_by_user_id(user_id)

            if not acc or not acc.access_token:
                logger.warning(f"No active Gmail account or token found for user {user_id}")
                return {"status": "not_connected", "processed": 0}

            acc.sync_status = "initial_sync_running"
            acc.sync_error = None
            await gmail_repo.update(acc)

            discovered_count = 0
            processed_count = 0
            skipped_duplicate = 0
            tier0_count = 0
            tier1_count = 0
            tier2_count = 0
            failures_count = 0

            try:
                client = GmailService.get_gmail_client(
                    acc.access_token,
                    acc.refresh_token,
                    account=acc,
                    gmail_repo=gmail_repo,
                )
                query_str = GmailService.get_date_filter_query(days=days)
                logger.info(f"Starting {days}-day historical Gmail import for {acc.email} with query: {query_str}")

                page_token: Optional[str] = None
                while True:
                    list_args: dict[str, Any] = {
                        "userId": "me",
                        "q": query_str,
                        "maxResults": batch_page_size,
                    }
                    if page_token:
                        list_args["pageToken"] = page_token

                    results = client.users().messages().list(**list_args).execute()
                    messages = results.get("messages", [])
                    page_token = results.get("nextPageToken")

                    if not messages:
                        break

                    for msg_item in messages:
                        msg_id = msg_item.get("id")
                        if not msg_id:
                            continue

                        discovered_count += 1

                        # Deduplication check: do not re-process existing signals
                        existing = await signal_repo.get_by_gmail_message_id(msg_id)
                        if existing:
                            skipped_duplicate += 1
                            continue

                        try:
                            msg_full = client.users().messages().get(
                                userId="me", id=msg_id, format="full"
                            ).execute()
                            signal = await SignalProcessor.process_raw_message(db, user_id, msg_full)
                            if signal:
                                processed_count += 1
                                if signal.processing_tier == 0:
                                    tier0_count += 1
                                elif signal.processing_tier == 1:
                                    tier1_count += 1
                                else:
                                    tier2_count += 1
                            else:
                                # User sent message resolved thread
                                processed_count += 1
                        except Exception as msg_err:
                            failures_count += 1
                            logger.warning(
                                f"Non-blocking error processing Gmail message ID {msg_id} for user {user_id}: {str(msg_err)[:200]}"
                            )

                    # Stop if no next page
                    if not page_token:
                        break

                # Update account status on successful import completion
                now_utc = datetime.now(timezone.utc)
                acc.sync_status = "idle"
                acc.last_sync_at = now_utc
                acc.last_full_sync_at = now_utc
                acc.sync_error = None
                await gmail_repo.update(acc)

                report = {
                    "status": "completed",
                    "discovered": discovered_count,
                    "processed": processed_count,
                    "skipped_duplicate": skipped_duplicate,
                    "tier0": tier0_count,
                    "tier1": tier1_count,
                    "tier2": tier2_count,
                    "failures": failures_count,
                }
                logger.info(
                    f"Historical sync completed for {acc.email}: {processed_count} processed ({tier0_count} T0, {tier1_count} T1, {tier2_count} T2), {skipped_duplicate} skipped, {failures_count} failures."
                )
                return report

            except Exception as e:
                logger.error(f"Historical Gmail import failed for user {user_id}: {e}")
                acc.sync_status = "error"
                acc.sync_error = str(e)[:500]
                await gmail_repo.update(acc)
                return {
                    "status": "error",
                    "error": str(e),
                    "discovered": discovered_count,
                    "processed": processed_count,
                    "skipped_duplicate": skipped_duplicate,
                    "tier0": tier0_count,
                    "tier1": tier1_count,
                    "tier2": tier2_count,
                    "failures": failures_count,
                }

    @staticmethod
    async def sync_recent_messages(
        db: AsyncSession,
        user_id: UUID,
        max_results: int = 50,
    ) -> int:
        """
        Incremental synchronization: fetches newly arrived messages since last sync timestamp.
        If initial historical sync has never run, automatically executes 10-day historical import.
        """
        lock = GmailService._get_user_lock(user_id)
        if lock.locked():
            logger.info(f"Sync already active for user {user_id}. Skipping incremental cycle.")
            return 0

        async with lock:
            gmail_repo = get_gmail_account_repository(db=db)
            signal_repo = get_signal_repository(db=db)
            acc = await gmail_repo.get_by_user_id(user_id)

            if not acc or not acc.access_token:
                logger.warning(f"No active Gmail account or token found for user {user_id}")
                return 0

            # If account has never completed initial sync, run 10-day historical import
            if acc.last_sync_at is None or acc.sync_status in ("pending", "initial_sync_pending"):
                logger.info(f"Initial sync pending for user {user_id}. Running 10-day historical import.")
                res = await GmailService.sync_historical_messages(db, user_id, days=10)
                return res.get("processed", 0)

            # Incremental sync using last_sync_at with a 60s overlap buffer
            try:
                acc.sync_status = "syncing"
                await gmail_repo.update(acc)

                client = GmailService.get_gmail_client(
                    acc.access_token,
                    acc.refresh_token,
                    account=acc,
                    gmail_repo=gmail_repo,
                )

                # Query messages received since (last_sync_at - 60s)
                buffer_dt = acc.last_sync_at - timedelta(seconds=60)
                after_ts = int(buffer_dt.timestamp())
                query_str = f"(in:inbox OR label:SENT) after:{after_ts}"

                results = client.users().messages().list(
                    userId="me", maxResults=max_results, q=query_str
                ).execute()
                messages = results.get("messages", [])

                processed_count = 0
                for msg_item in messages:
                    msg_id = msg_item.get("id")
                    if not msg_id:
                        continue

                    # Deduplication check
                    existing = await signal_repo.get_by_gmail_message_id(msg_id)
                    if existing:
                        continue

                    try:
                        msg_full = client.users().messages().get(
                            userId="me", id=msg_id, format="full"
                        ).execute()
                        await SignalProcessor.process_raw_message(db, user_id, msg_full)
                        processed_count += 1
                    except Exception as msg_err:
                        logger.warning(
                            f"Failed processing new Gmail message {msg_id} for user {user_id}: {str(msg_err)[:200]}"
                        )

                acc.sync_status = "idle"
                acc.last_sync_at = datetime.now(timezone.utc)
                acc.sync_error = None
                await gmail_repo.update(acc)
                return processed_count

            except Exception as e:
                logger.error(f"Incremental Gmail sync failed for user {user_id}: {e}")
                acc.sync_status = "error"
                acc.sync_error = str(e)[:500]
                await gmail_repo.update(acc)
                return 0
