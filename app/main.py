"""
Signal — AI Executive Assistant Backend Entrypoint
FastAPI application with CORS, route assembly, WebSocket handler, and lifespan events.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from sqlalchemy import select
from app.api.v1.router import api_v1_router
from app.api.websocket import router as websocket_router
from app.config import get_settings
from app.database import async_session_factory, close_db, init_db
from app.models.gmail import GmailAccount
from app.services.gmail_service import GmailService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("signal")
settings = get_settings()


async def periodic_gmail_poller():
    """Background task that continuously syncs emails for all connected accounts independent of frontend."""
    logger.info("Starting background Gmail poller...")
    while True:
        try:
            await asyncio.sleep(settings.gmail_poll_interval_seconds)
            async with async_session_factory() as db:
                res = await db.execute(
                    select(GmailAccount).where(GmailAccount.is_active == True)
                )
                accounts = list(res.scalars().all())
                for acc in accounts:
                    if acc.access_token:
                        logger.info(f"Background worker syncing emails for: {acc.email}")
                        await GmailService.sync_recent_messages(db, acc.user_id, 20)
        except asyncio.CancelledError:
            logger.info("Background Gmail poller stopped.")
            break
        except Exception as e:
            logger.error(f"Error in background Gmail poller: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context."""
    logger.info("Initializing Signal application...")
    await init_db()
    logger.info("Database connection established.")

    # Start background poller task (runs independently of frontend session)
    poller_task = asyncio.create_task(periodic_gmail_poller())

    yield

    poller_task.cancel()
    logger.info("Shutting down Signal application...")
    await close_db()
    logger.info("Database connection closed.")


app = FastAPI(
    title=settings.app_name,
    description="Signal — Your AI Executive Assistant Backend (147 signals → 4 decisions)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(api_v1_router)
app.include_router(websocket_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "primary_llm": settings.primary_llm_provider,
        "fallback_llm": settings.fallback_llm_provider,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
    )
