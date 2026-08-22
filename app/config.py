"""
Signal — Application Configuration
Loads all settings from environment variables via pydantic-settings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Signal"
    app_env: Literal["development", "production", "testing"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:5173"

    # --- Database & Persistence ---
    database_backend: Literal["fabric", "postgres"] = "fabric"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/signal"
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # --- Microsoft Fabric ---
    fabric_workspace_id: str = "60a962ae-2d89-4881-8dbd-f6b5b843d72b"
    fabric_lakehouse_id: str = "ac486cd1-8dd5-40fe-b770-fe16d6f4a5d3"
    fabric_sql_endpoint_id: str = "639815ab-55c7-444f-a7d5-f3d053b8b8bf"
    fabric_sql_connection_string: str = "iix2bcztutkuvpnlaeb2dpc7uu-vzrksyejfwaurdn56223qq6xfm.datawarehouse.fabric.microsoft.com"
    fabric_client_id: str = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
    fabric_authority: str = "https://login.microsoftonline.com/common"
    fabric_token_cache_path: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # --- Google OAuth ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # --- JWT ---
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 720  # 30 days persistent login session

    # --- LLM Providers ---
    primary_llm_provider: Literal["gemini", "groq"] = "gemini"
    fallback_llm_provider: Literal["gemini", "groq"] = "groq"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"

    # --- Embeddings ---
    embedding_provider: Literal["minilm", "tfidf"] = "minilm"
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # --- Gmail Sync ---
    gmail_sync_mode: Literal["polling", "push"] = "polling"
    gmail_poll_interval_seconds: int = 60
    gmail_push_webhook_url: str = ""
    gmail_pubsub_topic: str = ""

    # --- App Settings ---
    initial_sync_max_emails: int = 500
    behavior_min_sample_size: int = 5
    sender_auto_demote_threshold: int = 10

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
