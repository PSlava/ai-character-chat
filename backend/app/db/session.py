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
        # Supabase uses self-signed certs in their pooler chain
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
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS structured_tags VARCHAR DEFAULT ''",
        "ALTER TABLE chats ADD COLUMN IF NOT EXISTS persona_id VARCHAR REFERENCES personas(id) ON DELETE SET NULL",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS message_counts JSONB DEFAULT '{}'",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS original_language VARCHAR DEFAULT 'ru'",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS translations JSONB DEFAULT '{}'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS chat_count INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS base_chat_count JSONB DEFAULT '{}'",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS base_like_count JSONB DEFAULT '{}'",
        "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS slug VARCHAR UNIQUE",
        # Indexes for character browse performance
        "CREATE INDEX IF NOT EXISTS idx_characters_public_created ON characters (is_public, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_characters_creator ON characters (creator_id)",
        "CREATE INDEX IF NOT EXISTS idx_characters_public_chatcount ON characters (is_public, chat_count DESC)",
        "ALTER TABLE page_views ADD COLUMN IF NOT EXISTS country VARCHAR(2)",
        # Indexes for analytics
        "CREATE INDEX IF NOT EXISTS idx_pageviews_created ON page_views (created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_pageviews_ip_date ON page_views (ip_hash, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_pageviews_path ON page_views (path)",
        # Voting, forking, highlights
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS vote_score INTEGER DEFAULT 0",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS fork_count INTEGER DEFAULT 0",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS forked_from_id VARCHAR REFERENCES characters(id) ON DELETE SET NULL",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS highlights JSONB DEFAULT '[]'",
        # Indexes for relations
        "CREATE INDEX IF NOT EXISTS idx_character_relations_char ON character_relations (character_id)",
        "CREATE INDEX IF NOT EXISTS idx_votes_character ON votes (character_id)",
        # Chat memory / summarization
        "ALTER TABLE chats ADD COLUMN IF NOT EXISTS summary TEXT",
        "ALTER TABLE chats ADD COLUMN IF NOT EXISTS summary_up_to_id VARCHAR",
        # Persona snapshot in chat
        "ALTER TABLE chats ADD COLUMN IF NOT EXISTS persona_name VARCHAR(50)",
        "ALTER TABLE chats ADD COLUMN IF NOT EXISTS persona_description TEXT",
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
