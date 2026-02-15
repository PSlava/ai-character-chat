# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI character roleplay chat platform. Users create characters with personalities and scenarios; other users chat with them via LLM-powered responses. Bilingual UI (Russian/English) with i18n.

## Stack

- **Backend**: Python 3.12+ / FastAPI — `backend/`
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS — `frontend/`
- **Database**: SQLite locally, PostgreSQL (Supabase) in production — via SQLAlchemy async
- **Auth**: Local JWT (bcrypt passwords, PyJWT tokens)
- **AI**: Multi-provider with cross-provider auto-fallback — OpenRouter (8 free models), Groq (6 free), Cerebras (4 free), Together (paid), DeepSeek, Qwen/DashScope, Anthropic, OpenAI, Gemini
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
4. Env vars: `DATABASE_URL`, `JWT_SECRET`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `QWEN_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `TOGETHER_API_KEY`, `CORS_ORIGINS`, `PROXY_URL`
5. Optional: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`

### Vercel (frontend)
1. Connect GitHub repo, set root directory to `frontend`
2. Edit `vercel.json` — replace `YOUR-RENDER-APP.onrender.com` with actual Render URL
3. Framework: Vite, build: `npm run build`, output: `dist`

## Architecture

### Backend (`backend/app/`)

- **`config.py`** — `pydantic-settings`. `async_database_url` property auto-converts `postgres://` to `postgresql+asyncpg://`.
- **`db/models.py`** — SQLAlchemy models: `User` (with `role`, `oauth_provider`, `oauth_id`, nullable `password_hash`), `Character`, `Chat`, `Message` (with `model_used`), `Favorite`, `PromptTemplate`, `Report` (reporter_id, character_id, reason, details, status). Character has `appearance`, `structured_tags` (comma-separated tag IDs), `response_length` (short/medium/long/very_long), `max_tokens` (default 2048), `base_chat_count` and `base_like_count` (JSONB, per-language fake engagement counters).
- **`db/session.py`** — Async engine + session factory. `init_db()` creates tables on startup + runs ALTER TABLE migrations in separate transactions with `IF NOT EXISTS`.
- **`auth/router.py`** — `POST /api/auth/register`, `/api/auth/login`, `/api/auth/forgot-password`, `/api/auth/reset-password`. Google OAuth: `GET /api/auth/google` (redirect to Google), `GET /api/auth/google/callback` (create/link user, redirect with JWT). Uses bcrypt directly, authlib for OAuth. `ADMIN_EMAILS` env var: auto-assigns admin role on register; syncs role on login.
- **`auth/middleware.py`** — `get_current_user` dependency. `get_current_user_optional` returns None instead of 401.
- **`llm/`** — Provider abstraction layer with 9 providers:
  - `base.py` — `BaseLLMProvider` ABC with `generate_stream()`/`generate()`. `LLMConfig` includes model, temperature, max_tokens, top_p, top_k, frequency_penalty. `last_model_used` tracks actual model in auto-fallback.
  - `registry.py` — `init_providers()` creates instances from env keys; `get_provider(name)` resolves.
  - `openrouter_provider.py` — OpenRouter with auto-fallback (top-3 by quality), system role merge for Gemma, thinking model support.
  - `openrouter_models.py` — Registry of 8 free models with quality scores (0-10). `get_fallback_models()` diversifies by provider.
  - `groq_provider.py` — Groq with auto-fallback. OpenAI-compatible at `api.groq.com/openai/v1`. 6 free models.
  - `groq_models.py` — Model registry with quality scores, NSFW support flags.
  - `cerebras_provider.py` — Cerebras with auto-fallback. OpenAI-compatible at `api.cerebras.ai/v1`. 3 free models.
  - `cerebras_models.py` — Model registry with quality scores. Note: Cerebras API does NOT support frequency/presence penalty.
  - `together_provider.py` — Together AI with auto-fallback. OpenAI-compatible at `api.together.xyz/v1`. Paid (pay-per-token), no NSFW moderation.
  - `together_models.py` — Model registry with quality scores, type-based filtering (chat/language only).
  - `deepseek_provider.py` — Direct DeepSeek API (`api.deepseek.com/v1`). Supports `deepseek-reasoner` thinking model.
  - `qwen_provider.py` — Direct Qwen/DashScope API (`dashscope-intl.aliyuncs.com`). Default: `qwen3-32b`. Thinking disabled via `enable_thinking: False`.
  - `thinking_filter.py` — `ThinkingFilter` strips `<think>...</think>` blocks from streaming output. `strip_thinking()` for non-stream.
  - `model_cooldown.py` — Failed models excluded from auto-fallback for 15 minutes.
  - `anthropic_provider.py`, `openai_provider.py`, `gemini_provider.py` — Standard provider implementations.
  - `router.py` — `GET /api/models/{openrouter,groq,cerebras,together}` returns model lists with quality scores.
- **`admin/router.py`** — Admin-only CRUD for prompt template overrides. `require_admin` dependency checks JWT role. GET/PUT/DELETE `/api/admin/prompts`.
- **`chat/prompt_builder.py`** — Dynamic system prompt from character fields. Two-layer system: `_DEFAULTS` (code) + DB overrides. `load_overrides(engine)` caches for 60s. `get_all_keys()` for admin UI. Bilingual: 21 keys × 2 languages (ru/en). Includes structured tags snippets (between personality and appearance), appearance section, `{{char}}`/`{{user}}` template variable replacement in example dialogues. Response length instructions vary by `response_length` setting. Literary prose format: narration as plain text, dialogue via em-dash (ru) / quotes (en), `*asterisks*` only for inner thoughts. **Third-person narration** enforced (intro + format_rules + rules). Show-don't-tell, physical sensations, anti-template rules.
- **`chat/service.py`** — `get_or_create_chat(force_new=False)` returns existing chat or creates new; `force_new=True` always creates new chat. `get_chat_messages(limit, before_id)` supports cursor pagination with `has_more`. Context window (sliding window ~24k tokens, 50 messages). `build_conversation_messages()` constructs LLM message list with system prompt (always loads all messages).
- **`chat/router.py`** — SSE streaming via `StreamingResponse`. Events: `{type: "token"}`, `{type: "done", message_id, user_message_id}`, `{type: "error"}`. `POST /chats` supports `force_new` for multiple chats per character. `GET /chats/{id}` returns last 20 messages + `has_more`. `GET /chats/{id}/messages?before=ID&limit=20` for infinite scroll. `DELETE /chats/{id}/messages` clears all except greeting. Cross-provider auto-fallback when `model_name == "auto"`. Error sanitization: non-admin users see generic error, admin sees full details, moderation errors shown to all.
- **`reports/router.py`** — Report system: `POST /api/characters/{id}/report` (rate limit 5/hr), `GET /api/admin/reports?status=` (admin), `PUT /api/admin/reports/{id}` (admin). Reasons: inappropriate, spam, impersonation, underage, other. Statuses: pending, reviewed, dismissed.
- **`characters/export_import.py`** — SillyTavern character card v1/v2 support. `character_to_card(char)` exports to card v2 JSON. `card_to_character_data(card)` imports from v1/v2, mapping SillyTavern fields to SweetSin fields. SweetSin-specific data in `extensions.sweetsin`.
- **`characters/`** — CRUD + AI generation from text + SillyTavern export/import. Tags as comma-separated string. `structured_tags.py` — registry of 33 predefined tags in 5 categories with bilingual labels and prompt snippets. `serializers.py` for ORM→dict with `getattr` fallbacks for new columns, inflated counters (`real + base[lang]`), admin sees `real_chat_count`/`real_like_count`. Admin bypass for edit/delete via `is_admin` param.
- **`stats/router.py`** — `GET /api/stats` — public endpoint, returns inflated users (+1200), messages (+45000), characters, online_now (15–45 pseudo-random, stable per 5-min window via MD5 hash).
- **`utils/email.py`** — Async email sender with 3-tier fallback: Resend API (httpx) → SMTP (aiosmtplib, Gmail etc.) → console (dev). `_get_provider()` selects based on env vars.

### Frontend (`frontend/src/`)

- **`lib/supabase.ts`** — NOT Supabase SDK. Just localStorage helpers for token/user.
- **`lib/utils.ts`** — Includes `isCharacterOnline(characterId)` — deterministic ~33% online status based on `hash(id + currentHour) % 3 === 0`.
- **`api/client.ts`** — Axios with JWT auto-injection from localStorage.
- **`api/characters.ts`** — `wakeUpServer()` pings `/health` every 3s for up to 3 min. `getOpenRouterModels()` fetches model registry.
- **`api/chat.ts`** — `createChat(characterId, model?, personaId?, forceNew?)`, `deleteChat()`, `clearChatMessages()`, `deleteChatMessage()`, `getOlderMessages(chatId, beforeId)` for infinite scroll.
- **`api/reports.ts`** — `createReport(characterId, reason, details?)`, `getReports(status?)`, `updateReport(reportId, status)`.
- **`api/export.ts`** — `getExportUrl(characterId)` for download, `importCharacter(card)` for SillyTavern card import.
- **`api/stats.ts`** — `getStats()` fetches public site statistics (users, messages, characters, online_now).
- **`hooks/useChat.ts`** — SSE streaming via `@microsoft/fetch-event-source`. `GenerationSettings` includes model, temperature, top_p, top_k, frequency_penalty, max_tokens. Updates user message ID from `done` event.
- **`api/admin.ts`** — Admin API client: getPrompts, updatePrompt, resetPrompt.
- **`store/`** — Zustand: `authStore` (with role), `chatStore`.
- **`locales/`** — i18n via react-i18next. `en.json`, `es.json`, `ru.json` (~391 keys each). Default: English. Language stored in localStorage.
- **`pages/`** — Home (tag filters, featured character), Chat (+ new chat button), CharacterPage (online dot, report, export), CreateCharacter (manual + story + SillyTavern import), EditCharacter, Auth (+ Google OAuth), OAuthCallbackPage, Profile, AdminPromptsPage, AdminUsersPage, AdminReportsPage, AboutPage, TermsPage, PrivacyPage, FAQPage.
- **`components/layout/Footer.tsx`** — Site footer with links to About, Terms, Privacy, FAQ, contact email, copyright, and "Popular Characters" section (8 top characters, module-level cache). In Layout.tsx inside `<main>` with `min-h-full flex` wrapper.
- **`components/landing/HeroSection.tsx`** — Landing hero with stats bar (users/messages/online), fetched from `/api/stats` on mount.
- **`components/chat/GenerationSettingsModal.tsx`** — Modal with model card grid (auto, openrouter, groq, cerebras, together, direct, paid groups) + 6 sliders + context memory. Per-model settings stored in `localStorage model-settings:{modelId}`. `loadModelSettings()` exported for ChatPage. Switching model in modal loads saved params for that model.
- **`components/chat/MessageBubble.tsx`** — Message with delete/regenerate/copy buttons on hover. Markdown rendering (react-markdown + rehype-sanitize) for assistant messages. Error messages in red. Admin sees `model_used` under assistant messages.
- **`components/characters/ReportModal.tsx`** — Modal with 5 radio button reasons + details textarea. Handles duplicate report (409).
- **`components/ui/CookieConsent.tsx`** — Cookie consent banner (bottom, localStorage `cookie-consent`, link to Privacy Policy).
- **`components/ui/Skeleton.tsx`** — Pulse animation skeleton helper for loading states.
- **`components/chat/ChatWindow.tsx`** — Message list with infinite scroll (loads older messages on scroll-to-top, preserves scroll position). Persistent regenerate button below last assistant message.
- **`components/characters/CharacterForm.tsx`** — Full character form with appearance, structured tag pills (fetched from API, grouped by category), response_length dropdown, max_tokens slider, and `{{char}}`/`{{user}}` hint in example dialogues placeholder.

## Key Patterns

- **DB driver**: SQLite (`sqlite+aiosqlite://`) locally, PostgreSQL (`postgresql+asyncpg://`) in prod. Same SQLAlchemy models.
- **DB migrations**: `init_db()` runs `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in separate transactions (PostgreSQL aborts entire transaction on error). New nullable columns with defaults.
- **Enum handling**: SQLite stores enums as strings. Use `hasattr(x, 'value')` in serializers.
- **Tags**: Comma-separated string in DB, split to array in API responses. Two kinds: free-form `tags` (for search/categorization) and `structured_tags` (predefined IDs that inject prompt snippets).
- **New LLM providers**: Implement `BaseLLMProvider`, register in `registry.py`, add env key to `config.py`, pass in `main.py`.
- **Model selection in routers**: If model is `"auto"` → cross-provider fallback (Groq → Cerebras → OpenRouter, configurable via `AUTO_PROVIDER_ORDER`). If model contains `/` → OpenRouter direct ID. If `"openrouter"` → auto-fallback. Prefix routing: `groq:model_id`, `cerebras:model_id`, `together:model_id`. Otherwise → provider name (deepseek, qwen, claude, etc.) with default model.
- **Thinking models**: DeepSeek-reasoner uses `reasoning_content` field; Nemotron uses `reasoning` field. Extract when `content` is empty. `ThinkingFilter` strips `<think>` tags from streaming.
- **Gemma models**: Don't support `system` role via Google AI Studio. Must merge system into first user message.
- **Render free tier**: Sleeps after inactivity. Frontend calls `wakeUpServer()` before generation requests.
- **Proxy**: All providers accept `proxy_url` param, create `httpx.AsyncClient(proxy=...)` for HTTP clients.
- **Message ID sync**: Frontend creates messages with `crypto.randomUUID()`. Backend returns real IDs in SSE `done` event (`message_id` for assistant, `user_message_id` for user). Frontend updates IDs so delete/regenerate work correctly.
- **Response length**: Character setting (`short`/`medium`/`long`/`very_long`) controls system prompt instructions about response format and length. Separate from `max_tokens` which is a hard token limit.
- **Literary prose format**: Prompts instruct the model to write as literary prose — **third-person narration** (she/he, not "I"), dialogue via em-dash (ru) / quotes (en), `*asterisks*` only for inner thoughts. Show-don't-tell, physical sensations, paragraph breaks for rhythm. Explicit ban on template pattern `*does X* text *does Y*`.
- **Generation settings**: Per-request overrides (model, temperature, top_p, top_k, frequency_penalty, max_tokens) sent in `SendMessageRequest`. Character's `max_tokens` used as default. Settings stored per-model in localStorage (`model-settings:{modelId}`), model choice stored per-chat (`chat-model:{chatId}`).
- **User roles**: `admin` or `user` (default). Stored in User model, embedded in JWT. Admin can edit/delete any character, access `/admin/prompts`. Auto-assigned via `ADMIN_EMAILS` env var (comma-separated, case-insensitive, synced on login).
- **Model tracking**: `model_used` stored on each Message as `{provider}:{model_id}`. Auto-fallback providers set `last_model_used` in for-loop. Visible to admin in chat UI.
- **Auto-generated usernames**: Registration creates `user_{hex(3)}` if username not provided. Changeable in profile with `^[a-zA-Z0-9_]{3,20}$` validation.
- **Prompt template overrides**: Defaults in code (`_DEFAULTS`), overrides in `prompt_templates` DB table. Admin edits via UI, "Reset" deletes override → falls back to code default. Cache TTL 60s, invalidated on PUT/DELETE.
- **Structured tags**: 33 predefined tags in 5 categories (gender, role, personality, setting, style). Each tag has bilingual label and prompt snippet. Stored as comma-separated IDs on Character. Injected into system prompt between personality and appearance sections. Registry in `characters/structured_tags.py`, API at `GET /api/characters/structured-tags`.
- **Appearance field**: Separate character field for physical description. Included in system prompt between structured tags and scenario sections.
- **Template variables**: `{{char}}` and `{{user}}` in example dialogues are replaced with actual character and user names in system prompt.
- **Cerebras limitations**: API does not support `frequency_penalty`/`presence_penalty` — params silently ignored. UI shows amber warning when Cerebras model selected.
- **i18n**: react-i18next with `en.json`/`es.json`/`ru.json` locale files (~391 keys each). Default language: English. Language stored in localStorage, applied to prompts via `language` param. LanguageSwitcher: EN | ES | RU.
- **Fake engagement counters**: `base_chat_count`/`base_like_count` are JSONB `{"ru": N, "en": M}`. Serializer inflates: `displayed = real + base[lang]`. Admin gets extra `real_chat_count`/`real_like_count` fields. Seed characters initialized with random(300-3000) chats, random(100-800) likes. Characters sorted by displayed count (real + base) on homepage.
- **Character translation**: Card fields (name, tagline, tags) translated in batch via LLM. Description fields (scenario, appearance, greeting_message) translated per-character on single character page (`include_descriptions=True`). All cached in JSONB `translations` column. Cache invalidated on edit of any translatable field.
- **Email providers**: 3-tier fallback — Resend API (if `RESEND_API_KEY` set) → SMTP (if `SMTP_HOST` + `SMTP_FROM_EMAIL` set) → console (prints to logs). Config: `resend_api_key`, `resend_from_email`, `smtp_host/port/user/password/from_email`.
- **Online status (fake)**: `isCharacterOnline(id)` in `lib/utils.ts` — deterministic hash of `id + currentHour`, ~33% show green dot. Used on CharacterCard and CharacterPage.
- **Static pages**: About, Terms, Privacy, FAQ — pure i18n content, routes at `/about`, `/terms`, `/privacy`, `/faq`. Footer links to all four.
- **Google OAuth**: authlib backend. Flow: AuthPage → `GET /api/auth/google` → Google consent → callback → find/create user (link by email) → JWT → redirect to `/auth/oauth-callback?token=...` → OAuthCallbackPage stores token → redirect to `/`. `password_hash` nullable for OAuth-only users. Env: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
- **Report system**: `Report` model with reason enum (inappropriate/spam/impersonation/underage/other), status (pending/reviewed/dismissed). Rate limit 5/hr per user. Admin management at `/admin/reports`. Frontend: ReportModal with radio buttons, AdminReportsPage with status filter tabs.
- **Multiple chats per character**: `force_new: true` on `POST /api/chats` skips existing chat lookup. Sidebar groups chats by character with `#N` numbering. "New Chat" button on CharacterPage and ChatPage header.
- **SillyTavern export/import**: Character card v2 format (`spec: "chara_card_v2"`). Export: `GET /api/characters/{id}/export` with Content-Disposition. Import: `POST /api/characters/import` from JSON card (v1/v2). SweetSin-specific fields in `extensions.sweetsin`. Import tab on CreateCharacterPage (file upload or JSON paste).
- **Markdown in chat**: react-markdown + rehype-sanitize for assistant messages. Custom styled components (bold, italic, code, lists, blockquote). User messages remain plain text.
- **Toast notifications**: react-hot-toast, bottom-center, dark theme. Used for: like/unlike, delete, copy, report, import, errors.
- **PWA**: vite-plugin-pwa with registerType autoUpdate, standalone display, NetworkFirst for `/api/` via workbox.
- **Skeleton loading**: Detailed skeletons matching real component shapes for character cards, character page, and chat page.
- **GeoIP**: Local MMDB database (DB-IP Lite Country, ~5MB) via `maxminddb`. Downloaded at Docker build time, auto-refreshed on app startup if >30 days old. `GEOIP_DB_PATH` env var. Country stored on `page_views`, displayed as flag emojis on analytics dashboard.
- **RSS feed**: `/feed.xml` — RSS 2.0, 30 latest characters with avatar enclosures. Nginx proxies to `/api/seo/feed.xml`. `<link rel="alternate">` in index.html.
- **JSON-LD schemas**: WebSite + Organization (@graph) on home, CreativeWork on characters, FAQPage on /faq, BreadcrumbList on characters and tags, CollectionPage on tag pages.
- **Performance**: React.memo on CharacterCard, explicit img width/height (CLS), request dedup in chatStore (module-level promise), stale-while-revalidate, sidebar skeleton + useMemo for grouping. Code splitting via React.lazy (11 pages). Inter font with Google Fonts preconnect.
- **SEO prerender**: Nginx user-agent match (Googlebot, Bingbot etc.) → backend HTML for /:lang/c/:slug, /:lang/tags/:slug, /:lang/faq, /:lang (home).
- **Tag landing pages**: `/en/tags/{fantasy,romance,anime,modern}` with SEO, JSON-LD, prerender, sitemap.

## API Routes

Auth: `POST /api/auth/register` (username optional), `POST /api/auth/login`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`, `GET /api/auth/providers` (available OAuth), `GET /api/auth/google` (OAuth redirect), `GET /api/auth/google/callback` — JWT includes role
Characters: `GET/POST /api/characters`, `GET/PUT/DELETE /api/characters/{id}`, `GET /api/characters/my`, `GET /api/characters/structured-tags`, `POST /api/characters/generate-from-story`, `GET /api/characters/{id}/export` (SillyTavern card), `POST /api/characters/import` (SillyTavern card)
Chats: `POST /api/chats` (get-or-create, `force_new` for multiple chats), `GET /api/chats`, `GET/DELETE /api/chats/{id}`, `GET /api/chats/{id}/messages?before=ID&limit=20` (pagination), `POST /api/chats/{id}/message` (SSE), `DELETE /api/chats/{id}/messages` (clear), `DELETE /api/chats/{id}/messages/{msg_id}`
Users: `GET/PUT /api/users/me` (includes role, username), `GET /api/users/me/favorites`, `POST/DELETE /api/users/me/favorites/{id}`
Reports: `POST /api/characters/{id}/report` (rate limit 5/hr), `GET /api/admin/reports?status=` (admin), `PUT /api/admin/reports/{id}` (admin)
Admin: `GET /api/admin/prompts`, `PUT /api/admin/prompts/{key}`, `DELETE /api/admin/prompts/{key}` — admin role required
Models: `GET /api/models/openrouter`, `GET /api/models/groq`, `GET /api/models/cerebras`, `GET /api/models/together`
Analytics: `POST /api/analytics/pageview` (public, rate-limited), `GET /api/admin/analytics/overview?days=7` (admin — traffic, countries, devices, models)
SEO: `GET /api/seo/sitemap.xml`, `GET /api/seo/robots.txt`, `GET /api/seo/feed.xml` (RSS 2.0), `GET /api/seo/c/{slug}` (prerender), `GET /api/seo/tags/{slug}` (prerender), `GET /api/seo/faq` (prerender), `GET /api/seo/home` (prerender)
Stats: `GET /api/stats` — public, returns inflated counters + online_now
Health: `GET /api/health`
