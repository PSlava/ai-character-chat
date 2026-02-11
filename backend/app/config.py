from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data.db"
    jwt_secret: str = "dev-secret-change-in-production"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    openrouter_api_key: str | None = None
    deepseek_api_key: str | None = None
    qwen_api_key: str | None = None
    groq_api_key: str | None = None
    cerebras_api_key: str | None = None
    together_api_key: str | None = None
    default_model: str = "auto"
    auto_provider_order: str = "groq,cerebras,openrouter"
    proxy_url: str | None = None  # e.g. http://user:pass@host:port
    admin_emails: str = ""  # comma-separated list of admin emails
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "*"
    upload_dir: str = "data/uploads"
    max_avatar_size: int = 4 * 1024 * 1024  # 4MB default, override via MAX_AVATAR_SIZE env
    environment: str = "development"  # development | production

    class Config:
        env_file = ".env"

    @property
    def async_database_url(self) -> str:
        """Convert postgres:// to postgresql+asyncpg:// if needed."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()

# Block startup with default JWT secret in production
if settings.environment == "production" and settings.jwt_secret == "dev-secret-change-in-production":
    raise RuntimeError(
        "CRITICAL: JWT_SECRET must be changed in production! "
        "Set JWT_SECRET environment variable to a random 256-bit secret."
    )
