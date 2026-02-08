import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.db.models import Base


def _build_engine():
    url = settings.async_database_url
    kwargs: dict = {"echo": False}

    # PostgreSQL (Supabase) needs SSL
    if "postgresql" in url and "localhost" not in url and "127.0.0.1" not in url:
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


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
