# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI character roleplay chat platform. Users create characters with personalities and scenarios; other users chat with them via LLM-powered responses. Bilingual UI (Russian/English) with i18n.

## Stack

- **Backend**: Python 3.12+ / FastAPI — `backend/`
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS — `frontend/`
- **Database**: SQLite locally, PostgreSQL (Supabase) in production — via SQLAlchemy async
- **Auth**: Local JWT (bcrypt passwords, PyJWT tokens)
- **AI**: Multi-provider with cross-provider auto-fallback — OpenRouter (8 free models), Groq (6 free), Cerebras (4 free), DeepSeek, Qwen/DashScope, Anthropic, OpenAI, Gemini
- **Deploy**: Docker Compose (VPS) or Vercel (frontend) + Render (backend) + Supabase (PostgreSQL)

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
4. Env vars: `DATABASE_URL`, `JWT_SECRET`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `QWEN_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `CORS_ORIGINS`, `PROXY_URL`
5. Optional: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`

### Vercel (frontend)
1. Connect GitHub repo, set root directory to `frontend`
2. Edit `vercel.json` — replace `YOUR-RENDER-APP.onrender.com` with actual Render URL
3. Framework: Vite, build: `npm run build`, output: `dist`

## Architecture

### Backend (`backend/app/`)

- **`config.py`** — `pydantic-settings`. `async_database_url` property auto-converts `postgres://` to `postgresql+asyncpg://`.
- **`db/models.py`** — SQLAlchemy models: `User` (with `role`), `Character`, `Chat`, `Message` (with `model_used`), `Favorite`, `PromptTemplate`. Character has `appearance`, `response_length` (short/medium/long/very_long) and `max_tokens` (default 2048).
- **`db/session.py`** — Async engine + session factory. `init_db()` creates tables on startup + runs ALTER TABLE migrations in separate transactions with `IF NOT EXISTS`.
- **`auth/router.py`** — `POST /api/auth/register`, `/api/auth/login`. JWT tokens (30-day). Uses bcrypt directly. `ADMIN_EMAILS` env var: auto-assigns admin role on register; syncs role on login.
- **`auth/middleware.py`** — `get_current_user` dependency. `get_current_user_optional` returns None instead of 401.
- **`llm/`** — Provider abstraction layer with 8 providers:
  - `base.py` — `BaseLLMProvider` ABC with `generate_stream()`/`generate()`. `LLMConfig` includes model, temperature, max_tokens, top_p, top_k, frequency_penalty. `last_model_used` tracks actual model in auto-fallback.
  - `registry.py` — `init_providers()` creates instances from env keys; `get_provider(name)` resolves.
  - `openrouter_provider.py` — OpenRouter with auto-fallback (top-3 by quality), system role merge for Gemma, thinking model support.
  - `openrouter_models.py` — Registry of 8 free models with quality scores (0-10). `get_fallback_models()` diversifies by provider.
  - `groq_provider.py` — Groq with auto-fallback. OpenAI-compatible at `api.groq.com/openai/v1`. 6 free models.
  - `groq_models.py` — Model registry with quality scores, NSFW support flags.
  - `cerebras_provider.py` — Cerebras with auto-fallback. OpenAI-compatible at `api.cerebras.ai/v1`. 3 free models.
  - `cerebras_models.py` — Model registry with quality scores. Note: Cerebras API does NOT support frequency/presence penalty.
  - `deepseek_provider.py` — Direct DeepSeek API (`api.deepseek.com/v1`). Supports `deepseek-reasoner` thinking model.
  - `qwen_provider.py` — Direct Qwen/DashScope API (`dashscope-intl.aliyuncs.com`). Default: `qwen3-32b`. Thinking disabled via `enable_thinking: False`.
  - `thinking_filter.py` — `ThinkingFilter` strips `<think>...</think>` blocks from streaming output. `strip_thinking()` for non-stream.
  - `model_cooldown.py` — Failed models excluded from auto-fallback for 15 minutes.
  - `anthropic_provider.py`, `openai_provider.py`, `gemini_provider.py` — Standard provider implementations.
  - `router.py` — `GET /api/models/openrouter` returns model list with quality scores.
- **`admin/router.py`** — Admin-only CRUD for prompt template overrides. `require_admin` dependency checks JWT role. GET/PUT/DELETE `/api/admin/prompts`.
- **`chat/prompt_builder.py`** — Dynamic system prompt from character fields. Two-layer system: `_DEFAULTS` (code) + DB overrides. `load_overrides(engine)` caches for 60s. `get_all_keys()` for admin UI. Bilingual: 20 keys × 2 languages (ru/en). Includes appearance section, `{{char}}`/`{{user}}` template variable replacement in example dialogues. Response length instructions vary by `response_length` setting.
- **`chat/service.py`** — `get_or_create_chat()` returns existing chat or creates new. `get_chat_messages(limit, before_id)` supports cursor pagination with `has_more`. Context window (sliding window ~24k tokens, 50 messages). `build_conversation_messages()` constructs LLM message list with system prompt (always loads all messages).
- **`chat/router.py`** — SSE streaming via `StreamingResponse`. Events: `{type: "token"}`, `{type: "done", message_id, user_message_id}`, `{type: "error"}`. `POST /chats` is get-or-create (one chat per character). `GET /chats/{id}` returns last 20 messages + `has_more`. `GET /chats/{id}/messages?before=ID&limit=20` for infinite scroll. Cross-provider auto-fallback when `model_name == "auto"`.
- **`characters/`** — CRUD + AI generation from text. Tags as comma-separated string. `serializers.py` for ORM→dict with `getattr` fallbacks for new columns. Admin bypass for edit/delete via `is_admin` param.

### Frontend (`frontend/src/`)

- **`lib/supabase.ts`** — NOT Supabase SDK. Just localStorage helpers for token/user.
- **`api/client.ts`** — Axios with JWT auto-injection from localStorage.
- **`api/characters.ts`** — `wakeUpServer()` pings `/health` every 3s for up to 3 min. `getOpenRouterModels()` fetches model registry.
- **`api/chat.ts`** — `deleteChat()`, `deleteChatMessage()`, `getOlderMessages(chatId, beforeId)` for infinite scroll.
- **`hooks/useChat.ts`** — SSE streaming via `@microsoft/fetch-event-source`. `GenerationSettings` includes model, temperature, top_p, top_k, frequency_penalty, max_tokens. Updates user message ID from `done` event.
- **`api/admin.ts`** — Admin API client: getPrompts, updatePrompt, resetPrompt.
- **`store/`** — Zustand: `authStore` (with role), `chatStore`.
- **`locales/`** — i18n via react-i18next. `en.json`, `ru.json`. Language stored in localStorage.
- **`pages/`** — Home, Chat, CharacterPage, CreateCharacter, EditCharacter, Auth, Profile, AdminPromptsPage.
- **`components/chat/GenerationSettingsModal.tsx`** — Modal with model card grid + 5 sliders (temperature, top_p, top_k, frequency_penalty, max_tokens).
- **`components/chat/MessageBubble.tsx`** — Message with delete/regenerate buttons on hover. Error messages in red. Admin sees `model_used` under assistant messages.
- **`components/chat/ChatWindow.tsx`** — Message list with infinite scroll (loads older messages on scroll-to-top, preserves scroll position). Persistent regenerate button below last assistant message.
- **`components/characters/CharacterForm.tsx`** — Full character form with appearance, response_length dropdown, max_tokens slider, and `{{char}}`/`{{user}}` hint in example dialogues placeholder.

## Key Patterns

- **DB driver**: SQLite (`sqlite+aiosqlite://`) locally, PostgreSQL (`postgresql+asyncpg://`) in prod. Same SQLAlchemy models.
- **DB migrations**: `init_db()` runs `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in separate transactions (PostgreSQL aborts entire transaction on error). New nullable columns with defaults.
- **Enum handling**: SQLite stores enums as strings. Use `hasattr(x, 'value')` in serializers.
- **Tags**: Comma-separated string in DB, split to array in API responses.
- **New LLM providers**: Implement `BaseLLMProvider`, register in `registry.py`, add env key to `config.py`, pass in `main.py`.
- **Model selection in routers**: If model is `"auto"` → cross-provider fallback (Groq → Cerebras → OpenRouter, configurable via `AUTO_PROVIDER_ORDER`). If model contains `/` → OpenRouter direct ID. If `"openrouter"` → auto-fallback. Otherwise → provider name (deepseek, qwen, claude, etc.) with default model.
- **Thinking models**: DeepSeek-reasoner uses `reasoning_content` field; Nemotron uses `reasoning` field. Extract when `content` is empty. `ThinkingFilter` strips `<think>` tags from streaming.
- **Gemma models**: Don't support `system` role via Google AI Studio. Must merge system into first user message.
- **Render free tier**: Sleeps after inactivity. Frontend calls `wakeUpServer()` before generation requests.
- **Proxy**: All providers accept `proxy_url` param, create `httpx.AsyncClient(proxy=...)` for HTTP clients.
- **Message ID sync**: Frontend creates messages with `crypto.randomUUID()`. Backend returns real IDs in SSE `done` event (`message_id` for assistant, `user_message_id` for user). Frontend updates IDs so delete/regenerate work correctly.
- **Response length**: Character setting (`short`/`medium`/`long`/`very_long`) controls system prompt instructions about response format and length. Separate from `max_tokens` which is a hard token limit.
- **Generation settings**: Per-request overrides (model, temperature, top_p, top_k, frequency_penalty, max_tokens) sent in `SendMessageRequest`. Character's `max_tokens` used as default.
- **User roles**: `admin` or `user` (default). Stored in User model, embedded in JWT. Admin can edit/delete any character, access `/admin/prompts`. Auto-assigned via `ADMIN_EMAILS` env var (comma-separated, case-insensitive, synced on login).
- **Model tracking**: `model_used` stored on each Message as `{provider}:{model_id}`. Auto-fallback providers set `last_model_used` in for-loop. Visible to admin in chat UI.
- **Auto-generated usernames**: Registration creates `user_{hex(3)}` if username not provided. Changeable in profile with `^[a-zA-Z0-9_]{3,20}$` validation.
- **Prompt template overrides**: Defaults in code (`_DEFAULTS`), overrides in `prompt_templates` DB table. Admin edits via UI, "Reset" deletes override → falls back to code default. Cache TTL 60s, invalidated on PUT/DELETE.
- **Appearance field**: Separate character field for physical description. Included in system prompt between personality and scenario sections.
- **Template variables**: `{{char}}` and `{{user}}` in example dialogues are replaced with actual character and user names in system prompt.
- **Cerebras limitations**: API does not support `frequency_penalty`/`presence_penalty` — params silently ignored. UI shows amber warning when Cerebras model selected.
- **i18n**: react-i18next with `en.json`/`ru.json` locale files. Language stored in localStorage, applied to prompts via `language` param.

## API Routes

Auth: `POST /api/auth/register` (username optional, auto-generated), `POST /api/auth/login` — JWT includes role
Characters: `GET/POST /api/characters`, `GET/PUT/DELETE /api/characters/{id}`, `GET /api/characters/my`, `POST /api/characters/generate-from-story`
Chats: `POST /api/chats` (get-or-create), `GET /api/chats`, `GET/DELETE /api/chats/{id}`, `GET /api/chats/{id}/messages?before=ID&limit=20` (pagination), `POST /api/chats/{id}/message` (SSE), `DELETE /api/chats/{id}/messages` (clear), `DELETE /api/chats/{id}/messages/{msg_id}`
Users: `GET/PUT /api/users/me` (includes role, username), `GET /api/users/me/favorites`, `POST/DELETE /api/users/me/favorites/{id}`
Admin: `GET /api/admin/prompts`, `PUT /api/admin/prompts/{key}`, `DELETE /api/admin/prompts/{key}` — admin role required
Models: `GET /api/models/openrouter`, `GET /api/models/groq`, `GET /api/models/cerebras`
Health: `GET /api/health`
