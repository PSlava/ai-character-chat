import ssl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.db.models import Base


def _build_engine():
    url = settings.async_database_url
    kwargs: dict = {"echo": False}

    # PostgreSQL (Supabase) needs SSL — but not Docker-internal connections
    is_local = any(h in url for h in ("localhost", "127.0.0.1", "postgres:"))
    if "postgresql" in url and not is_local:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        kwargs["connect_args"] = {"ssl": ssl_ctx}
        kwargs["pool_pre_ping"] = True

    return create_async_engine(url, **kwargs)


engine = _build_engine()
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize DB tables: {e}")
        print("The app will still start — tables may already exist.")

    # Run migrations in separate transactions (PostgreSQL aborts entire
    # transaction on error, so each ALTER needs its own transaction)
    migrations = [
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS max_tokens INTEGER DEFAULT 2048",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS response_length VARCHAR DEFAULT 'long'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'ru'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user'",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS model_used VARCHAR",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS appearance TEXT",
    ]
    for sql in migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(sql))
        except Exception:
            pass  # column already exists or DB doesn't support IF NOT EXISTS


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
