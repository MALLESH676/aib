from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import json


class Settings(BaseSettings):
    # App
    APP_NAME: str = "TrustShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./trustshield.db"

    # LLM
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "template"  # "gemini/gemini-2.0-flash", "gpt-4o-mini", or "template"

    # Demo
    DEMO_MODE: bool = False

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    # Thresholds
    RISK_ALLOW_THRESHOLD: float = 30.0
    RISK_REVIEW_THRESHOLD: float = 70.0
    HIGH_CONFIDENCE_THRESHOLD: float = 0.75

    # Agent weights
    RISK_AGENT_WEIGHT: float = 0.40
    AUTH_AGENT_WEIGHT: float = 0.35
    REVIEW_AGENT_WEIGHT: float = 0.25

    # API Server Settings (avoid validation errors if in .env)
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

