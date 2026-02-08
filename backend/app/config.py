from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data.db"
    jwt_secret: str = "dev-secret-change-in-production"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    default_model: str = "claude"
    cors_origins: str = "http://localhost:5173"
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
