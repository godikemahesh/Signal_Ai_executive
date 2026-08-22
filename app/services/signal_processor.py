"""
Signal — Master Signal Processing Pipeline
Orchestrates the 3-tier processing pipeline (Tier 0 Blocklist → Tier 1 Rules → Tier 2 Full AI).
"""

from datetime import datetime, timezone
import logging
from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_manager import get_llm_manager
from app.ai.prompts.signal_analysis import SIGNAL_ANALYSIS_SYSTEM_INSTRUCTION, build_signal_analysis_prompt
from app.core.constants import BUCKET_COMPLETED
from app.models.signal import Signal, SignalEmbedding, SignalThread
from app.models.user import UserProfile
from app.repositories import (
    get_signal_embedding_repository,
    get_signal_repository,
    get_signal_thread_repository,
    get_user_repository,
)

from app.services.embedding_service import EmbeddingService
from app.services.entity_service import EntityService
from app.services.parser_engine import ParserEngine
from app.services.pii_masker import PIIMasker
from app.services.priority_scorer import PriorityScorer
from app.services.rule_engine import RuleEngine
from app.services.sender_classifier import SenderClassifier

logger = logging.getLogger(__name__)


class SignalProcessor:
    """Master signal processing pipeline."""

    @staticmethod
    async def process_raw_message(
        db: AsyncSession,
        user_id: UUID,
        gmail_payload: dict[str, Any],
    ) -> Signal:
        """Process a raw Gmail API message payload through the 3-tier pipeline."""
        signal_repo = get_signal_repository(db=db)
        user_repo = get_user_repository(db=db)
        embedding_repo = get_signal_embedding_repository(db=db)

        # Step 1: Parse raw email payload
        parsed = ParserEngine.parse_gmail_message(gmail_payload)
        gmail_msg_id = parsed["gmail_message_id"]

        # Check if already exists
        existing_signal = await signal_repo.get_by_gmail_message_id(gmail_msg_id)
        if existing_signal:
            logger.info(f"Signal {gmail_msg_id} already processed. Skipping.")
            return existing_signal

        sender_email = parsed["sender_email"]
        sender_name = parsed["sender_name"]
        subject = parsed["subject"]
        body_plain = parsed["body_plain"]
        snippet = parsed["snippet"]
        received_at = datetime.fromtimestamp(parsed["gmail_internal_date"] / 1000.0, tz=timezone.utc)
        gmail_thread_id = parsed["gmail_thread_id"]

        # Step 1.5: If message is sent by user (sent reply), automatically resolve signals in this thread
        user = await user_repo.get_by_id(user_id)
        if user and sender_email.lower() == user.email.lower():
            logger.info(f"Detected sent reply from user {user.email} in thread {gmail_thread_id}. Resolving thread signals.")
            thread_signals = await signal_repo.list_by_thread(user_id, gmail_thread_id)
            for ts in thread_signals:
                ts.bucket = BUCKET_COMPLETED
                ts.is_archived = True
                ts.interacted_at = datetime.now(timezone.utc)
            await signal_repo.bulk_update(thread_signals)

            try:
                from app.api.websocket import ws_manager
                await ws_manager.broadcast({
                    "type": "signal_updated",
                    "user_id": str(user_id),
                    "action": "reply_sent_resolved"
                })
            except Exception:
                pass
            return None

        # Step 2: Get or create sender profile (Tier lookup)
        sender_profile = await SenderClassifier.get_or_create_sender_profile(
            db, sender_email, sender_name
        )

        # Step 3: Check Tier 0 / Tier 1 (Cost Reduction)
        rule_result = RuleEngine.process_tier0_or_1(
            sender_profile, subject, snippet, body_plain
        )

        if rule_result is not None:
            # Signal processed via zero-LLM rules!
            logger.info(f"Signal {gmail_msg_id} processed via Tier {rule_result['processing_tier']} (zero LLM cost)")
            
            signal = Signal(
                user_id=user_id,
                gmail_message_id=gmail_msg_id,
                gmail_thread_id=parsed["gmail_thread_id"],
                sender_email=sender_email,
                sender_name=sender_name,
                sender_profile_id=sender_profile.id if sender_profile else None,
                to_recipients=parsed["to_recipients"],
                cc_recipients=parsed["cc_recipients"],
                subject=subject,
                snippet=snippet,
                body_plain=body_plain,
                summary=rule_result["summary"],
                processing_tier=rule_result["processing_tier"],
                processing_status="completed",
                skip_reason=rule_result.get("skip_reason"),
                priority_score=rule_result["priority_score"],
                bucket=rule_result["suggested_bucket"],
                bucket_reason=rule_result["bucket_reason"],
                is_archived=(rule_result["suggested_bucket"] == "ignored"),
                gmail_link=f"https://mail.google.com/mail/u/0/#inbox/{gmail_msg_id}",
                received_at=received_at,
                processed_at=datetime.now(timezone.utc),
            )
            created_signal = await signal_repo.create(signal)

            if gmail_thread_id:
                try:
                    import uuid
                    thread_repo = get_signal_thread_repository(db=db)
                    th = SignalThread(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        gmail_thread_id=gmail_thread_id,
                        subject=subject,
                        participants=[sender_email] + parsed.get("to_recipients", []),
                        last_signal_at=received_at,
                        signal_count=1,
                        is_active=True,
                    )
                    await thread_repo.upsert(th)
                except Exception as th_err:
                    logger.warning(f"Failed to upsert thread {gmail_thread_id}: {th_err}")


            return created_signal


        # Step 4: Tier 2 — Full AI Processing
        logger.info(f"Signal {gmail_msg_id} sending to Tier 2 AI Processing")

        # Mask PII before LLM call
        sanitized_body, pii_map = PIIMasker.mask(body_plain)

        # Build prompt & call LLM
        prompt = build_signal_analysis_prompt(
            subject=subject,
            sender_email=sender_email,
            sender_name=sender_name,
            body_text=sanitized_body,
            received_at=received_at.isoformat(),
        )

        llm = get_llm_manager()
        ai_res = await llm.generate_structured(
            prompt=prompt,
            system_instruction=SIGNAL_ANALYSIS_SYSTEM_INSTRUCTION,
            temperature=0.2,
        )

        # Step 5: Compute priority & resolve bucket
        priority_score, bucket, bucket_reason = PriorityScorer.calculate_priority(
            ai_priority_score=ai_res.get("priority_score", 50),
            sender_engagement_score=sender_profile.engagement_score if sender_profile else 0.5,
            has_urgent_deadline=bool(ai_res.get("actions")),
            is_marketing=ai_res.get("is_marketing_or_newsletter", False),
        )

        # Create Signal object
        signal = Signal(
            user_id=user_id,
            gmail_message_id=gmail_msg_id,
            gmail_thread_id=parsed["gmail_thread_id"],
            sender_email=sender_email,
            sender_name=sender_name,
            sender_profile_id=sender_profile.id if sender_profile else None,
            to_recipients=parsed["to_recipients"],
            cc_recipients=parsed["cc_recipients"],
            subject=subject,
            snippet=snippet,
            body_plain=body_plain,
            body_sanitized=sanitized_body,
            summary=ai_res.get("summary"),
            detected_actions=ai_res.get("actions", []),
            extracted_metadata=ai_res.get("entities", [{}])[0].get("metadata", {}) if ai_res.get("entities") else {},
            pii_mapping=pii_map,
            processing_tier=2,
            processing_status="completed",
            priority_score=priority_score,
            bucket=bucket,
            bucket_reason=bucket_reason,
            is_archived=(bucket == "ignored"),
            gmail_link=f"https://mail.google.com/mail/u/0/#inbox/{gmail_msg_id}",
            received_at=received_at,
            processed_at=datetime.now(timezone.utc),
        )
        created_signal = await signal_repo.create(signal)

        if gmail_thread_id:
            try:
                import uuid
                thread_repo = get_signal_thread_repository(db=db)
                th = SignalThread(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    gmail_thread_id=gmail_thread_id,
                    subject=subject,
                    participants=[sender_email] + parsed.get("to_recipients", []),
                    last_signal_at=received_at,
                    signal_count=1,
                    is_active=True,
                )
                await thread_repo.upsert(th)
            except Exception as th_err:
                logger.warning(f"Failed to upsert thread {gmail_thread_id}: {th_err}")


        # Step 6: Process Entities & Timeline (Gatekept for meaningful threads: priority_score >= 40)

        is_marketing = ai_res.get("is_marketing_or_newsletter", False)
        suggested_cat = ai_res.get("suggested_category", "")

        if ai_res.get("entities") and bucket != "ignored" and priority_score >= 40 and not is_marketing:
            try:
                await EntityService.process_extracted_entities(
                    db,
                    user_id,
                    created_signal.id,
                    ai_res["entities"],
                    received_at,
                    signal_subject=subject,
                    signal_category=suggested_cat,
                )
            except Exception as e:
                logger.warning(f"Failed to process extracted entities for signal {created_signal.id}: {e}")

        # Step 7: Generate & Store Embeddings for semantic search
        try:
            embed_text = f"{subject}\n{created_signal.summary or ''}\n{body_plain[:500]}"
            vector, model_name = EmbeddingService.get_embedding(embed_text)

            embedding_obj = SignalEmbedding(
                signal_id=created_signal.id,
                embedding_model=model_name,
                embedding=vector,
            )
            await embedding_repo.create(embedding_obj)
        except Exception as e:
            logger.warning(f"Failed to save embedding for signal {created_signal.id}: {e}")

        # Broadcast real-time WebSocket update event to active UI clients
        try:
            from app.api.websocket import ws_manager
            await ws_manager.broadcast({
                "type": "signal_updated",
                "user_id": str(user_id),
                "signal_id": str(created_signal.id),
                "subject": created_signal.subject,
                "bucket": created_signal.bucket,
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket event: {e}")

        return created_signal

