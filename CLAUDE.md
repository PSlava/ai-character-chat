# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI character roleplay chat platform. Users create characters with personalities and scenarios; other users chat with them via LLM-powered responses. Russian-language UI.

## Stack

- **Backend**: Python 3.12+ / FastAPI — `backend/`
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS — `frontend/`
- **Database**: SQLite locally, PostgreSQL (Supabase) in production — via SQLAlchemy async
- **Auth**: Local JWT (bcrypt passwords, PyJWT tokens)
- **AI**: Multi-provider — OpenRouter (8 free models), DeepSeek, Qwen/DashScope, Anthropic, OpenAI, Gemini
- **Deploy**: Vercel (frontend) + Render (backend) + Supabase (PostgreSQL)

## Commands

### Backend (local)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
uvicorn app.main:app --reload  # runs on :8000
```

### Frontend (local)
```bash
cd frontend
npm install
npm run dev    # runs on :5173, proxies /api to :8000
npm run build
```

DB is auto-created on startup. Locally uses SQLite (`data.db`), delete to reset.

## Deployment

### Supabase (database)
1. Create project at supabase.com
2. Copy connection string from Settings > Database > URI
3. Tables auto-create on first backend startup via SQLAlchemy

### Render (backend)
1. Connect GitHub repo, set root directory to `backend`
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Env vars: `DATABASE_URL`, `JWT_SECRET`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `QWEN_API_KEY`, `CORS_ORIGINS`, `PROXY_URL`
5. Optional: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`

### Vercel (frontend)
1. Connect GitHub repo, set root directory to `frontend`
2. Edit `vercel.json` — replace `YOUR-RENDER-APP.onrender.com` with actual Render URL
3. Framework: Vite, build: `npm run build`, output: `dist`

## Architecture

### Backend (`backend/app/`)

- **`config.py`** — `pydantic-settings`. `async_database_url` property auto-converts `postgres://` to `postgresql+asyncpg://`.
- **`db/models.py`** — SQLAlchemy models: `User`, `Character`, `Chat`, `Message`, `Favorite`.
- **`db/session.py`** — Async engine + session factory. `init_db()` creates tables on startup.
- **`auth/router.py`** — `POST /api/auth/register`, `/api/auth/login`. JWT tokens (30-day). Uses bcrypt directly.
- **`auth/middleware.py`** — `get_current_user` dependency. Decodes JWT.
- **`llm/`** — Provider abstraction layer with 6 providers:
  - `base.py` — `BaseLLMProvider` ABC with `generate_stream()`/`generate()`.
  - `registry.py` — `init_providers()` creates instances from env keys; `get_provider(name)` resolves.
  - `openrouter_provider.py` — OpenRouter with auto-fallback (top-3 by quality), system role merge for Gemma, thinking model support.
  - `openrouter_models.py` — Registry of 8 free models with quality scores (0-10). `get_fallback_models()` diversifies by provider.
  - `deepseek_provider.py` — Direct DeepSeek API (`api.deepseek.com/v1`). Supports `deepseek-reasoner` thinking model.
  - `qwen_provider.py` — Direct Qwen/DashScope API (`dashscope-intl.aliyuncs.com`). Default: `qwen3-32b`.
  - `anthropic_provider.py`, `openai_provider.py`, `gemini_provider.py` — Standard provider implementations.
  - `router.py` — `GET /api/models/openrouter` returns model list with quality scores.
- **`chat/prompt_builder.py`** — System prompt from character fields.
- **`chat/service.py`** — Context window (sliding window ~12k tokens).
- **`chat/router.py`** — SSE streaming via `StreamingResponse`. Events: `{type: "token"}`, `{type: "done"}`, `{type: "error"}`.
- **`characters/`** — CRUD + AI generation from text. Tags as comma-separated string. `serializers.py` for ORM→dict.

### Frontend (`frontend/src/`)

- **`lib/supabase.ts`** — NOT Supabase SDK. Just localStorage helpers for token/user.
- **`api/client.ts`** — Axios with JWT auto-injection from localStorage.
- **`api/characters.ts`** — `wakeUpServer()` pings `/health` every 3s for up to 3 min. `getOpenRouterModels()` fetches model registry.
- **`hooks/useChat.ts`** — SSE streaming via `@microsoft/fetch-event-source`.
- **`store/`** — Zustand: `authStore`, `chatStore`.
- **`pages/`** — Home, Chat, CharacterPage, CreateCharacter, Auth, Profile.

## Key Patterns

- **DB driver**: SQLite (`sqlite+aiosqlite://`) locally, PostgreSQL (`postgresql+asyncpg://`) in prod. Same SQLAlchemy models.
- **Enum handling**: SQLite stores enums as strings. Use `hasattr(x, 'value')` in serializers.
- **Tags**: Comma-separated string in DB, split to array in API responses.
- **New LLM providers**: Implement `BaseLLMProvider`, register in `registry.py`, add env key to `config.py`, pass in `main.py`.
- **Model selection in routers**: If model contains `/` → OpenRouter direct ID. If `"openrouter"` → auto-fallback. Otherwise → provider name (deepseek, qwen, claude, etc.) with default model.
- **Thinking models**: DeepSeek-reasoner uses `reasoning_content` field; Nemotron uses `reasoning` field. Extract when `content` is empty.
- **Gemma models**: Don't support `system` role via Google AI Studio. Must merge system into first user message.
- **Render free tier**: Sleeps after inactivity. Frontend calls `wakeUpServer()` before generation requests.
- **Proxy**: All providers accept `proxy_url` param, create `httpx.AsyncClient(proxy=...)` for HTTP clients.

## API Routes

Auth: `POST /api/auth/register`, `POST /api/auth/login`
Characters: `GET/POST /api/characters`, `GET/PUT/DELETE /api/characters/{id}`, `GET /api/characters/my`, `POST /api/characters/generate-from-story`
Chats: `POST /api/chats`, `GET /api/chats`, `GET/DELETE /api/chats/{id}`, `POST /api/chats/{id}/message` (SSE)
Users: `GET/PUT /api/users/me`, `GET /api/users/me/favorites`, `POST/DELETE /api/users/me/favorites/{id}`
Models: `GET /api/models/openrouter`
Health: `GET /api/health`
