import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.llm.registry import init_providers
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set proxy env vars so all httpx clients (Gemini, etc.) pick them up
    if settings.proxy_url:
        os.environ["HTTP_PROXY"] = settings.proxy_url
        os.environ["HTTPS_PROXY"] = settings.proxy_url

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
        proxy_url=settings.proxy_url,
    )
    yield


app = FastAPI(title="AI Character Chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _git_commit() -> str:
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


from app.auth.router import router as auth_router  # noqa: E402
from app.characters.router import router as characters_router  # noqa: E402
from app.chat.router import router as chat_router  # noqa: E402
from app.users.router import router as users_router  # noqa: E402
from app.llm.router import router as models_router  # noqa: E402

app.include_router(auth_router)
app.include_router(characters_router)
app.include_router(chat_router)
app.include_router(users_router)
app.include_router(models_router)
