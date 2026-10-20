from functools import lru_cache
from typing import Annotated, Literal, Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-insecure-jwt-secret-do-not-use-in-production"  # noqa: S105
# A fixed 32-byte key for development only; production refuses to start with it.
DEV_FIELD_KEY = "ZGV2LW9ubHktZmllbGQta2V5LTMyLWJ5dGVzLWxvbmc="


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (and `.env` in development)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = "postgresql+asyncpg://mindguard:mindguard@localhost:5432/mindguard"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    jwt_secret: SecretStr = SecretStr(DEV_JWT_SECRET)
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    cookie_secure: bool = False

    auth_rate_limit_per_minute: int = 30

    field_encryption_key: SecretStr = SecretStr(DEV_FIELD_KEY)

    llm_provider: Literal["mock", "ollama", "anthropic"] = "mock"
    llm_model: str = "llama3.2:3b"
    ollama_base_url: str = "http://localhost:11434"
    anthropic_api_key: SecretStr | None = None
    chat_rate_limit_per_minute: int = 20
    chat_history_turns: int = 10

    # Layer 2 of the safety engine; see app/safety/engine.py.
    safety_classifier: Literal["embedding", "hashed", "none"] = "embedding"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _refuse_insecure_production(self) -> Self:
        if not self.is_production:
            return self
        secret = self.jwt_secret.get_secret_value()
        if secret == DEV_JWT_SECRET or len(secret) < 32:
            raise ValueError("JWT_SECRET must be set to a random value of 32+ characters")
        if self.field_encryption_key.get_secret_value() == DEV_FIELD_KEY:
            raise ValueError("FIELD_ENCRYPTION_KEY must be set to a random 32-byte key")
        if not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production (HTTPS only)")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
