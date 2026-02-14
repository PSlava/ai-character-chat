import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.llm.registry import init_providers
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set proxy env vars so all httpx clients (Gemini, etc.) pick them up
    if settings.proxy_url:
        os.environ["HTTP_PROXY"] = settings.proxy_url
        os.environ["HTTPS_PROXY"] = settings.proxy_url

    # Ensure upload directories exist
    Path(settings.upload_dir, "avatars").mkdir(parents=True, exist_ok=True)

    await init_db()
    init_providers(
        anthropic_key=settings.anthropic_api_key,
        openai_key=settings.openai_api_key,
        gemini_key=settings.gemini_api_key,
        openrouter_key=settings.openrouter_api_key,
        deepseek_key=settings.deepseek_api_key,
        qwen_key=settings.qwen_api_key,
        groq_key=settings.groq_api_key,
        cerebras_key=settings.cerebras_api_key,
        together_key=settings.together_api_key,
        proxy_url=settings.proxy_url,
    )
    yield


app = FastAPI(title="SweetSin", lifespan=lifespan)

# Use a derived key for session middleware (separate from JWT secret)
import hashlib as _hashlib
_session_key = _hashlib.sha256(b"session:" + settings.jwt_secret.encode()).hexdigest()
app.add_middleware(SessionMiddleware, secret_key=_session_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def _git_commit() -> str:
    # Prefer GIT_COMMIT env (baked into Docker image at build time)
    env_commit = os.environ.get("GIT_COMMIT", "").strip()
    if env_commit and env_commit != "unknown":
        return env_commit
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, timeout=5
        ).strip()
    except Exception:
        return "unknown"


_COMMIT = _git_commit()
_STARTED_AT = __import__("datetime").datetime.now(
    __import__("datetime").timezone.utc
).isoformat()


@app.get("/api/health")
async def health():
    return {"status": "ok", "commit": _COMMIT, "started_at": _STARTED_AT}


@app.get("/api/health/db")
async def health_db():
    """Test database connectivity."""
    from app.db.session import engine
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        return {"status": "ok", "db": "connected"}
    except Exception:
        return {"status": "error", "db": "disconnected"}


from app.auth.router import router as auth_router  # noqa: E402
from app.characters.router import router as characters_router  # noqa: E402
from app.chat.router import router as chat_router  # noqa: E402
from app.users.router import router as users_router  # noqa: E402
from app.llm.router import router as models_router  # noqa: E402
from app.admin.router import router as admin_router  # noqa: E402
from app.uploads.router import router as uploads_router  # noqa: E402
from app.personas.router import router as personas_router  # noqa: E402
from app.stats.router import router as stats_router  # noqa: E402
from app.reports.router import router as reports_router  # noqa: E402
from app.seo.router import router as seo_router  # noqa: E402
from app.analytics.router import router as analytics_router  # noqa: E402

app.include_router(auth_router)
app.include_router(characters_router)
app.include_router(chat_router)
app.include_router(users_router)
app.include_router(models_router)
app.include_router(admin_router)
app.include_router(uploads_router)
app.include_router(personas_router)
app.include_router(stats_router)
app.include_router(reports_router)
app.include_router(seo_router)
app.include_router(analytics_router)

# Serve uploaded files (avatars etc.) — must be after routers
# Create directory before mounting (StaticFiles checks at import time)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
