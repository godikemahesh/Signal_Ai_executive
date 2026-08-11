"""
Signal — Gmail Webhook Receiver
Endpoint for Gmail Push Pub/Sub notifications.
"""

import base64
import json
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.gmail_service import GmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/gmail")
async def gmail_push_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Receive Google Pub/Sub push notification for new emails."""
    try:
        body = await request.json()
        message = body.get("message", {})
        data_b64 = message.get("data")

        if data_b64:
            decoded_json = json.loads(base64.b64decode(data_b64).decode("utf-8"))
            email_address = decoded_json.get("emailAddress")
            logger.info(f"Received Gmail push notification for email: {email_address}")

            # Schedule async sync task in background
            # For simplicity, triggers sync for active account
            background_tasks.add_task(GmailService.sync_recent_messages, db, email_address, 20)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error handling Gmail push webhook: {e}")
        return {"status": "error", "message": str(e)}
