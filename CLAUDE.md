# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI character roleplay chat platform. Users create characters with personalities and scenarios; other users chat with them via LLM-powered responses. Multilingual UI (EN/ES/RU/FR/DE/PT/IT) with i18n.

## Stack

- **Backend**: Python 3.12+ / FastAPI — `backend/`
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS — `frontend/`
- **Database**: SQLite locally, PostgreSQL (Supabase) in production — via SQLAlchemy async
- **Auth**: Local JWT (bcrypt passwords, PyJWT tokens)
- **AI**: Multi-provider with cross-provider auto-fallback — OpenRouter (8 free models), Groq (6 free), Cerebras (4 free), Together (paid), DeepSeek, Qwen/DashScope, OpenAI, Gemini
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

- **`config.py`** — `pydantic-settings`. `async_database_url` property auto-converts `postgres://` to `postgresql+asyncpg://`. `autonomous_provider_order` setting: paid models first (default `openai,gemini,deepseek,together,groq,cerebras,openrouter`).
- **`db/models.py`** — SQLAlchemy models: `User` (with `role`, `oauth_provider`, `oauth_id`, nullable `password_hash`, `tier` (free/premium/admin), `tokens_used_today`, `tokens_used_month`, `tokens_reset_date`), `Character`, `Chat` (with `persona_name`, `persona_description` snapshot fields), `Message` (with `model_used`, `prompt_tokens`, `completion_tokens`), `Favorite`, `Vote` (user_id + character_id composite PK, value +1/-1), `Persona` (user_id, slug, name, description, is_default), `CharacterRelation` (character_id, related_id, relation_type, label_ru/en/es/fr/de/pt/it), `PromptTemplate`, `Report` (reporter_id, character_id, reason, details, status). `RelationType` enum: rival/ex/friend/sibling/enemy/lover/ally. Character has `appearance`, `speech_pattern` (speech style description), `structured_tags` (comma-separated tag IDs), `response_length` (short/medium/long/very_long), `max_tokens` (default 2048), `base_chat_count` and `base_like_count` (JSONB, per-language fake engagement counters), `vote_score` (net upvotes-downvotes), `fork_count`, `forked_from_id` (FK self-ref), `highlights` (JSONB array of {text, lang}).
- **`db/session.py`** — Async engine + session factory. `init_db()` creates tables on startup + runs ALTER TABLE migrations in separate transactions with `IF NOT EXISTS`.
- **`auth/router.py`** — `POST /api/auth/register`, `/api/auth/login`, `/api/auth/forgot-password`, `/api/auth/reset-password`, `GET /api/auth/challenge` (PoW). Google OAuth: `GET /api/auth/google` (redirect to Google), `GET /api/auth/google/callback` (create/link user, redirect with JWT). Uses bcrypt directly, authlib for OAuth. `ADMIN_EMAILS` env var: auto-assigns admin role on register; syncs role on login. Anti-bot: honeypot field, PoW verification, registration rate limit (3/hr per IP), header-based bot delay (2s if missing Accept-Language/Referer).
- **`auth/pow.py`** — Proof-of-Work challenge system. `create_challenge()` generates random hex, `verify_pow()` checks SHA256 with 4 leading hex zeros. Single-use challenges, 5-min TTL, auto-cleanup.
- **`auth/rate_limit.py`** — In-memory sliding window rate limiter. Limiters: `auth_limiter` (10/min per IP), `register_limiter` (3/hr per IP), `message_limiter` (20/min per user), `message_interval_limiter` (1 per 5s per user), `reset_limiter` (3/5min per IP), `reset_hourly_limiter` (10/hr per IP), `reset_email_limiter` (1/2min per email).
- **`auth/middleware.py`** — `get_current_user` dependency. `get_current_user_optional` returns None instead of 401.
- **`llm/`** — Provider abstraction layer with 8 providers:
  - `base.py` — `BaseLLMProvider` ABC with `generate_stream()`/`generate()`/`generate_with_usage()`. `LLMConfig` includes model, temperature, max_tokens, top_p, top_k, frequency_penalty. `LLMResult` dataclass: `content`, `prompt_tokens`, `completion_tokens`, `model`. `last_model_used` tracks actual model in auto-fallback.
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
  - `thinking_filter.py` — `ThinkingFilter` strips `<think>...</think>` blocks from streaming output. `strip_thinking()` for non-stream. `has_foreign_chars()` detects CJK/Vietnamese characters (Qwen artifact). `has_mixed_languages(text, lang)` detects English words mixed into ru/es text. Used in groq/together/cerebras providers' `generate()` to retry on bad responses.
  - `model_cooldown.py` — Failed models excluded from auto-fallback for 15 minutes.
  - `openai_provider.py`, `gemini_provider.py` — Standard provider implementations.
  - `router.py` — `GET /api/models/{openrouter,groq,cerebras,together}` returns model lists with quality scores.
- **`admin/router.py`** — Admin-only CRUD for prompt template overrides. `require_admin` dependency checks JWT role. GET/PUT/DELETE `/api/admin/prompts`. Admin settings: `GET/PUT /api/admin/settings` (key-value in `prompt_templates` with `setting.` prefix). Settings: `notify_registration`, `notify_errors`, `paid_mode`, `cost_mode` (quality/balanced/economy), `daily_message_limit`, `max_personas`, `anon_message_limit`.
- **`chat/prompt_builder.py`** — Dynamic system prompt from character fields. Two-layer system: `_DEFAULTS` (code) + DB overrides. `load_overrides(engine)` caches for 60s. `get_all_keys()` for admin UI. 23 keys × 7 languages (ru/en/es/fr/de/pt/it). Includes structured tags snippets (between personality and appearance), appearance section, speech_pattern section (between appearance and scenario), `{{char}}`/`{{user}}` template variable replacement in example dialogues. Response length instructions vary by `response_length` setting. Literary prose format per language: narration as plain text, dialogue via hyphen `-` (ru/es/fr/pt/it), quotes `"..."` (en/de). `*asterisks*` only for inner thoughts. **Third-person narration** enforced per language: she/he (en), она/он (ru), ella/él (es), elle/il (fr), sie/er (de), ela/ele (pt), lei/lui (it). Show-don't-tell, physical sensations, anti-template rules. **Anti-repetition rules**: no echo/paraphrase of user words, require new physical action in every response, advance plot forward, ban crutch words. **Anti-AI rules**: banned AI-marker words per language (RU: пронизан, гобелен, поистине, многогранный, etc.; EN: delve, tapestry, testament, realm, landscape, etc.), sentence length variation required. **DnD GM prompts** (`_DND_PROMPTS`): 7 languages, sections: intro, rules_summary, gm_rules, choices_rules, format_rules, character_creation. DnD detection: `campaign_id` OR 'dnd' in character tags. GM instructed to write `[ROLL]` at END of response as cliffhanger (no outcome narration), `[STATE {json}]` for encounter tracking. **Note**: never use German typographic quotes `„"` (U+201E) in Python source — causes SyntaxError.
- **`chat/service.py`** — `get_or_create_chat(force_new=False)` returns existing chat or creates new; `force_new=True` always creates new chat. Copies persona snapshot (name+description) into Chat at creation time. `get_chat_messages(limit, before_id)` supports cursor pagination with `has_more`. Context window (sliding window ~24k tokens, 50 messages). `build_conversation_messages(max_context_messages=None)` constructs LLM message list with system prompt, accepts tier-based context message limit. `save_message()` accepts `prompt_tokens` and `completion_tokens` for token tracking. `_POST_HISTORY` / `_DND_POST_HISTORY` / `_FICTION_POST_HISTORY` — post-history reminders (7 languages) injected as last system message. DnD post-history instructs GM to use dice results first. **Dice result injection**: `_format_dice_injection()` formats previous turn's dice results as system message; injected before post-history when last assistant message has `dice_rolls` JSONB. Closest to generation = strongest effect.
- **`chat/summarizer.py`** — Auto-summarize older messages when chat exceeds 25 messages (was 40). Keeps 15 most recent unsummarized (was 20). Summary must track current location and end with clear statement of where characters are. Providers: Groq → Cerebras → OpenRouter, 30s timeout. Fire-and-forget after each assistant response.
- **`group_chat/router.py`** — Group chat API: `POST/GET/DELETE /api/group-chats`, `POST /api/group-chats/{id}/message`. Characters respond sequentially via SSE. Each character gets own system prompt + group context. Other characters' messages sent as user role with `[Name]:` prefix (prevents continuation of other's text). `max_tokens=600`, `MAX_MEMBERS=3`.
- **`chat/anon.py`** — Anonymous (guest) chat support. System user `anonymous@system.local` for FK compliance. `get_anon_user_id(db)` lazily creates/caches system user. `get_anon_message_limit()` reads `setting.anon_message_limit` (0=disabled, >0=limit, default 20). `check_anon_limit(session_id)` raises 403 if exceeded. `count_anon_messages()` counts user messages across all chats with matching `anon_session_id`.
- **`chat/daily_limit.py`** — Generic `_get_setting_int(key, default)` with 60s TTL cache. Exports `check_daily_limit()`, `get_max_personas()`, `get_cost_mode()`, `get_user_tier()`, `get_tier_limits()`, `cap_max_tokens()`. Reads from `prompt_templates` table with `setting.*` prefix. **Tier system**: `TIER_LIMITS` dict with 4 levels — anon (20 msg/day, 1024 max_tokens, 10 ctx msgs), free (200/day, 2048, 30 ctx), premium (unlimited, 4096, 50 ctx), admin (unlimited, 4096, 50 ctx). `cap_max_tokens(requested, tier)` enforces tier max_tokens ceiling.
- **`chat/router.py`** — SSE streaming via `StreamingResponse`. Events: `{type: "token"}`, `{type: "done", message_id, user_message_id, anon_messages_left?, dice_rolls?, encounter_state?}`, `{type: "error"}`. **DnD parsing**: `_parse_dice_rolls()` extracts `[ROLL NdM+X desc]`, rolls dice server-side; `_parse_encounter_state()` extracts `[STATE {json}]` (greedy regex for nested JSON); `_save_dice_on_message()` persists dice results on Message JSONB for next-turn injection. `is_dnd` flag: `campaign_id` OR 'dnd' in character tags. **Anonymous chat**: `POST /chats`, `GET /chats/{id}`, `GET /chats/{id}/messages`, `POST /chats/{id}/message` use `get_current_user_optional`; anonymous users identified by `X-Anon-Session` header; chat created under system anon user with `anon_session_id`. `GET /chats/anon-limit` returns limit/remaining/enabled. `POST /chats` supports `force_new` for multiple chats per character. `DELETE` endpoints require auth. `POST /chats/{id}/generate-persona-reply` — admin-only, non-streaming LLM call that ghostwrites a reply as the user's persona (returns text, doesn't save, counts toward daily limit). Cross-provider auto-fallback when `model_name == "auto"`. **cost_mode**: `get_cost_mode()` with 60s cache — `quality` (paid_mode behavior), `balanced` (paid for registered, free for anon), `economy` (free providers only). Tier-based `max_tokens` capping via `cap_max_tokens()`. Tier's `max_context_messages` passed to `build_conversation_messages()`. Token usage estimated and saved on messages (`prompt_tokens`, `completion_tokens`). Error sanitization: non-admin users see generic error, admin sees full details, moderation errors shown to all. **frequency_penalty defaults**: 0.5 for NSFW characters, 0.3 for others (when user doesn't override).
- **`reports/router.py`** — Report system: `POST /api/characters/{id}/report` (rate limit 5/hr), `GET /api/admin/reports?status=` (admin), `PUT /api/admin/reports/{id}` (admin). Reasons: inappropriate, spam, impersonation, underage, other. Statuses: pending, reviewed, dismissed.
- **`characters/export_import.py`** — SillyTavern character card v1/v2 support. `character_to_card(char)` exports to card v2 JSON (includes speech_pattern in `extensions.sweetsin`). `card_to_character_data(card)` imports from v1/v2, mapping SillyTavern fields to SweetSin fields. SweetSin-specific data in `extensions.sweetsin`.
- **`characters/`** — CRUD + AI generation from text + SillyTavern export/import + voting + forking. Tags as comma-separated string. `structured_tags.py` — registry of 33 predefined tags in 5 categories with labels and prompt snippets in all 7 languages (ru/en/es/fr/de/pt/it). `get_snippets_for_ids()` uses `snippet_{lang}` with fallback to `snippet_en`. Public characters require an avatar (400 error on create/update without one). `language_preferences.py` — per-language affinity weights for settings/tags/ratings, used for initial base counts and daily growth. `slugify.py` — `validate_slug()` (normalize, validate 3-50 chars), `generate_slug(name, short_id)` (transliterate + UUID suffix). Shared by both Character and Persona. `serializers.py` for ORM→dict with `getattr` fallbacks for new columns, inflated counters (`real + base[lang]`), `vote_score`, `fork_count`, `forked_from_id`, `highlights`. Admin sees `real_chat_count`/`real_like_count`. Admin bypass for edit/delete via `is_admin` param. `router.py` includes `POST /{id}/vote` (upvote/downvote/remove), `POST /{id}/fork` (clone public char as private draft), `GET /{id}/relations` (character connections).
- **`seo/router.py`** — SEO prerender endpoints for bots: `/api/seo/home`, `/api/seo/c/{slug}`, `/api/seo/tags/{slug}`, `/api/seo/faq`, `/api/seo/about`, `/api/seo/terms`, `/api/seo/privacy`, `/api/seo/sitemap.xml`, `/api/seo/robots.txt`, `/api/seo/feed.xml` (RSS). Anti-template variability (slug-hash section rotation, 6 heading/CTA variants). Quality gates for sitemap. noindex for thin pages.
- **`seo/jsonld.py`** — JSON-LD generators: `character_jsonld()` (real counts only, inLanguage, isPartOf, author, UTC dates), `website_jsonld()`, `faq_jsonld()`, `breadcrumb_jsonld()`, `collection_jsonld()`.
- **`stats/router.py`** — `GET /api/stats` — public endpoint, returns inflated users (+1200), messages (+45000), characters, online_now (15–45 pseudo-random, stable per 5-min window via MD5 hash). Excludes admins, @sweetsin, and anonymous system user from all counts.
- **`autonomous/model_monitor.py`** — Daily model monitoring. Checks Groq/Cerebras/Together via `client.models.list()`, OpenRouter via httpx (`:free` models only). Stores state in `prompt_templates` (`models.*` keys as JSON). First run saves baseline silently. On changes (added/removed/changed) — emails all ADMIN_EMAILS. Registered as task #6 in `scheduler.py`.
- **`utils/email.py`** — Async email sender with 3-tier fallback: Resend API (httpx) → SMTP (aiosmtplib, Gmail etc.) → console (dev). `_get_provider()` selects based on env vars.
- **`utils/error_notifier.py`** — Automatic error monitoring. `AdminEmailHandler(logging.Handler)` on root logger captures ERROR/CRITICAL, buffers in `deque(maxlen=50)`, sends batched email digest every 5 min (CRITICAL = immediate). Dedup, self-filtering (ignores own logger + email logger), thread-safe. Toggle: `setting.notify_errors`. Installed in `main.py` lifespan.
- **`autonomous/`** — Autonomous server tasks (no cron/Celery):
  - `scheduler.py` — Hourly check loop via `asyncio.create_task()` in lifespan. State stored in `prompt_templates` with `scheduler.*` keys. 5-min startup delay, 24h task intervals.
  - `providers.py` — Shared provider order for all autonomous tasks. Reads `AUTONOMOUS_PROVIDER_ORDER` env var (default: `openai,gemini,deepseek,together,groq,cerebras,openrouter`). Paid models first, free as fallback.
  - `text_humanizer.py` — Anti-AI post-processing. Replaces ~30 AI cliché words (RU+EN) with natural alternatives (e.g. "пронизан"→"наполнен", "delve"→"explore", "tapestry"→"blend"). `humanize_text(str)` and `humanize_character_data(dict)`.
  - `character_generator.py` — Daily character generation: weighted categories (~90% NSFW, 50% erotic fantasy based on sexual fantasy research — Lehmiller/Kinsey — with 70% male fantasies generating female chars, 30% female fantasies generating male chars, 6 erotic CATEGORIES + 16 `_EXAMPLE_THEMES`), LLM invents unique concept + avatar prompt (provider order from `providers.py`, temp=0.95), DALL-E 3 avatar ($0.04/day), anti-AI humanizer on output, auto-translation to EN/ES/FR/DE/PT/IT, saves under @sweetsin user. Prompts require psychological depth (1-2 internal contradictions), concrete habits, speech_pattern field, physical details in greeting. NSFW rule: no sexual behavior in personality field.
  - `counter_growth.py` — Daily bump of `base_chat_count`/`base_like_count` JSONB on all public characters, scaled by language preferences.
  - `highlight_generator.py` — Daily: generates 2 editorial highlight phrases per language (ru/en/es/fr/de/pt/it) for up to 10 characters without highlights. Provider order from `providers.py`. NOT fake reviews — editorial descriptive phrases.
  - `relationship_builder.py` — Weekly: finds character pairs with 2+ shared tags, LLM determines relation type (rival/ex/friend/sibling/enemy/lover/ally), creates bidirectional relations with 7-lingual labels (ru/en/es/fr/de/pt/it). Max 3 relations per character, 20 pairs per run. Provider order from `providers.py`.
  - `cleanup.py` — Daily cleanup: page_views >90 days, orphan avatar files (not referenced by any character/user).

### Frontend (`frontend/src/`)

- **`lib/supabase.ts`** — NOT Supabase SDK. Just localStorage helpers for token/user.
- **`lib/pow.ts`** — Browser-side Proof-of-Work solver using SubtleCrypto API. `solveChallenge(challenge, difficulty=4)` finds nonce where SHA256 starts with N hex zeros (~65k iterations, ~100ms).
- **`lib/utils.ts`** — Includes `isCharacterOnline(characterId)` — deterministic ~33% online status based on `hash(id + currentHour) % 3 === 0`.
- **`api/client.ts`** — Axios with JWT auto-injection from localStorage.
- **`api/characters.ts`** — `wakeUpServer()` pings `/health` every 3s for up to 3 min. `getOpenRouterModels()` fetches model registry. `voteCharacter()`, `getUserVotes()`, `forkCharacter()`, `getCharacterRelations()`.
- **`api/chat.ts`** — `createChat(characterId, model?, personaId?, forceNew?)`, `deleteChat()`, `clearChatMessages()`, `deleteChatMessage()`, `getOlderMessages(chatId, beforeId)` for infinite scroll. `generatePersonaReply(chatId)` for ghostwriting as persona.
- **`api/personas.ts`** — `getPersonas()`, `createPersona()`, `updatePersona()`, `deletePersona()`, `getPersonaLimit()` (used/limit), `checkPersonaSlug()` (debounced availability check).
- **`api/reports.ts`** — `createReport(characterId, reason, details?)`, `getReports(status?)`, `updateReport(reportId, status)`.
- **`api/export.ts`** — `getExportUrl(characterId)` for download, `importCharacter(card)` for SillyTavern card import.
- **`api/stats.ts`** — `getStats()` fetches public site statistics (users, messages, characters, online_now).
- **`hooks/useChat.ts`** — SSE streaming via `@microsoft/fetch-event-source`. `GenerationSettings` includes model, temperature, top_p, top_k, frequency_penalty, max_tokens. Updates user message ID from `done` event.
- **`api/admin.ts`** — Admin API client: getPrompts, updatePrompt, resetPrompt.
- **`store/`** — Zustand: `authStore` (with role, clears votes+favorites on logout), `chatStore`, `favoritesStore`, `votesStore` (optimistic updates, loaded on login).
- **`locales/`** — i18n via react-i18next. `en.json`, `es.json`, `ru.json`, `fr.json`, `de.json`, `pt.json`, `it.json` (~540 keys each). Default: English. Language stored in localStorage.
- **`pages/`** — Home (tag filters, gender filter pills, featured character), Chat (+ new chat button), CharacterPage (online dot, report, export, vote, fork, highlights, connections), CreateCharacter (manual + story + SillyTavern import), EditCharacter, Auth (+ Google OAuth), OAuthCallbackPage, Profile, AdminPromptsPage, AdminUsersPage, AdminReportsPage, AboutPage (10 feature cards), TermsPage, PrivacyPage, FAQPage (12 Q&A, JSON-LD).
- **`components/layout/Footer.tsx`** — Site footer with links to About, Terms, Privacy, FAQ, contact email, copyright, and "Popular Characters" section (8 top characters, module-level cache). In Layout.tsx inside `<main>` with `min-h-full flex` wrapper.
- **`components/landing/HeroSection.tsx`** — Landing hero with stats bar (users/messages/online), fetched from `/api/stats` on mount.
- **`components/chat/GenerationSettingsModal.tsx`** — Modal with model card grid (auto, openrouter, groq, cerebras, together, direct, paid groups) + 6 sliders + context memory. Per-model settings stored in `localStorage model-settings:{modelId}`. `loadModelSettings()` exported for ChatPage. Switching model in modal loads saved params for that model. **Per-provider parameter limits** (`PROVIDER_LIMITS`): dynamic slider ranges and visibility per provider — Cerebras/Claude/Gemini hide penalty sliders, Claude limits temperature to 1.0, OpenAI allows penalty up to 2.0, others max 1.0. `clampToLimits()` auto-adjusts values on model switch.
- **`components/chat/MessageBubble.tsx`** — Message with delete/regenerate/copy buttons on hover. Markdown rendering (react-markdown + rehype-sanitize) for assistant messages. Error messages in red. Admin sees `model_used` under assistant messages. Wrapped in `React.memo` with custom comparator to prevent re-rendering during streaming.
- **`components/characters/ReportModal.tsx`** — Modal with 5 radio button reasons + details textarea. Handles duplicate report (409).
- **`components/ui/CookieConsent.tsx`** — Cookie consent banner (bottom, localStorage `cookie-consent`, link to Privacy Policy).
- **`components/ui/Skeleton.tsx`** — Pulse animation skeleton helper for loading states.
- **`components/chat/ChatInput.tsx`** — Input textarea with auto-resize, send/stop buttons. When `personaName` prop is set, shows Sparkles button for generating reply as persona (calls `onGeneratePersonaReply`, puts result in textarea).
- **`components/chat/ChatWindow.tsx`** — Message list with infinite scroll (loads older messages on scroll-to-top, preserves scroll position). Persistent regenerate button below last assistant message. Streaming scroll uses `requestAnimationFrame`-batched instant `scrollTop` (not `scrollIntoView`) to prevent jank.
- **`components/characters/CharacterForm.tsx`** — Full character form with appearance, speech_pattern, structured tag pills (fetched from API, grouped by category), `{{char}}`/`{{user}}` hint in example dialogues placeholder, hint props on greeting/example dialogues Textareas, and estimated token budget display (~N tokens, amber >2000, red >3000). Admin-only fields: preferred_model, max_tokens slider, system_prompt_suffix. Response length dropdown visible to all users.

## Key Patterns

- **DB driver**: SQLite (`sqlite+aiosqlite://`) locally, PostgreSQL (`postgresql+asyncpg://`) in prod. Same SQLAlchemy models.
- **DB migrations**: `init_db()` runs `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in separate transactions (PostgreSQL aborts entire transaction on error). New nullable columns with defaults.
- **Enum handling**: SQLite stores enums as strings. Use `hasattr(x, 'value')` in serializers.
- **Tags**: Comma-separated string in DB, split to array in API responses. Two kinds: free-form `tags` (for search/categorization) and `structured_tags` (predefined IDs that inject prompt snippets).
- **New LLM providers**: Implement `BaseLLMProvider`, register in `registry.py`, add env key to `config.py`, pass in `main.py`.
- **Model selection in routers**: If model is `"auto"` → cross-provider fallback (Groq → Cerebras → OpenRouter, configurable via `AUTO_PROVIDER_ORDER`). **Paid mode** overrides auto order to `["groq", "openrouter"]` (Groq with flex tier, OpenRouter as fallback). **Free mode**: `["openrouter"]` only. If model contains `/` → OpenRouter direct ID. If `"openrouter"` → auto-fallback. Prefix routing: `groq:model_id`, `cerebras:model_id`, `together:model_id`. Otherwise → provider name (deepseek, qwen, openai, gemini, etc.) with default model.
- **Admin settings**: Key-value pairs stored in `prompt_templates` with `setting.` prefix. `GET/PUT /api/admin/settings`. Settings: `notify_registration` (email on new user), `paid_mode` (paid LLM providers for chat), `daily_message_limit` (per-user daily cap), `max_personas` (persona count cap), `anon_message_limit` (guest message limit, 0=disabled). Toggle/input buttons on AdminUsersPage.
- **Thinking models**: DeepSeek-reasoner uses `reasoning_content` field; Nemotron uses `reasoning` field. Extract when `content` is empty. `ThinkingFilter` strips `<think>` tags from streaming.
- **Gemma models**: Don't support `system` role via Google AI Studio. Must merge system into first user message.
- **Render free tier**: Sleeps after inactivity. Frontend calls `wakeUpServer()` before generation requests.
- **Proxy**: All providers accept `proxy_url` param, create `httpx.AsyncClient(proxy=...)` for HTTP clients.
- **Message ID sync**: Frontend creates messages with `crypto.randomUUID()`. Backend returns real IDs in SSE `done` event (`message_id` for assistant, `user_message_id` for user). Frontend updates IDs so delete/regenerate work correctly.
- **User message dedup**: Backend checks if last message in chat is same user text before saving (prevents duplicates on page reload after generation error).
- **Response length**: Character setting (`short`/`medium`/`long`/`very_long`) controls system prompt instructions about response format and length. Separate from `max_tokens` which is a hard token limit.
- **Literary prose format**: Prompts instruct the model to write as literary prose — **third-person narration** per language (she/he, elle/il, ella/él, sie/er, ela/ele, lei/lui). Dialogue format: hyphen `- Text` (ru/es/fr/pt/it), quotes `"..."` (en/de). Em-dashes `—` explicitly banned (AI marker). `*asterisks*` only for inner thoughts. Show-don't-tell, physical sensations, paragraph breaks for rhythm. Explicit ban on template pattern `*does X* text *does Y*`. **Anti-AI rules**: banned cliché words per language, sentence length variation enforced.
- **Generation settings**: Per-request overrides (model, temperature, top_p, top_k, frequency_penalty, max_tokens) sent in `SendMessageRequest`. Character's `max_tokens` used as default. Settings stored per-model in localStorage (`model-settings:{modelId}`), model choice stored per-chat (`chat-model:{chatId}`).
- **User roles**: `admin` or `user` (default). Stored in User model, embedded in JWT. Admin can edit/delete any character, access `/admin/prompts`. Auto-assigned via `ADMIN_EMAILS` env var (comma-separated, case-insensitive, synced on login).
- **Model tracking**: `model_used` stored on each Message as `{provider}:{model_id}`. Auto-fallback providers set `last_model_used` in for-loop. Visible to admin in chat UI.
- **Auto-generated usernames**: Registration creates `user_{hex(3)}` if username not provided. Changeable in profile with `^[a-zA-Z0-9_]{3,20}$` validation.
- **Prompt template overrides**: Defaults in code (`_DEFAULTS`), overrides in `prompt_templates` DB table. Admin edits via UI, "Reset" deletes override → falls back to code default. Cache TTL 60s, invalidated on PUT/DELETE.
- **Gender filter**: `GET /api/characters?gender=male|female` filters by structured_tags (male/female). HomePage shows gender filter pills (All/Male/Female) in purple (`bg-purple-600`), separate from tag filter pills in rose.
- **Structured tags**: 33 predefined tags in 5 categories (gender, role, personality, setting, style). Each tag has multilingual label and prompt snippet. Stored as comma-separated IDs on Character. Injected into system prompt between personality and appearance sections. Registry in `characters/structured_tags.py`, API at `GET /api/characters/structured-tags`.
- **Appearance field**: Separate character field for physical description. Included in system prompt between structured tags and scenario sections.
- **Template variables**: `{{char}}` and `{{user}}` in example dialogues are replaced with actual character and user names in system prompt.
- **Cerebras limitations**: API does not support `frequency_penalty`/`presence_penalty` — params silently ignored. UI hides penalty sliders when Cerebras model selected.
- **Per-provider parameter limits**: Frontend `PROVIDER_LIMITS` enforces provider-specific slider ranges. Cerebras/Claude/Gemini: no penalties. Claude: temp max 1.0. OpenAI: penalty max 2.0. Others: penalty max 1.0. Values clamped on model switch via `clampToLimits()`.
- **NSFW anti-repetition**: Prompts instruct to pick 1-2 senses per response and ROTATE them between responses. Explicit ban on repeating sensation descriptions from previous responses (all 7 languages).
- **i18n**: react-i18next with `en.json`/`es.json`/`ru.json`/`fr.json`/`de.json`/`pt.json`/`it.json` locale files (~540 keys each). Default language: English. Language stored in localStorage, applied to prompts via `language` param. LanguageSwitcher: EN | ES | RU | FR | DE | PT | IT.
- **Fake engagement counters**: `base_chat_count`/`base_like_count` are JSONB `{"ru": N, "en": M, "es": K, "fr": F, "de": D, "pt": P, "it": I}`. Serializer inflates: `displayed = real + base[lang]`. Admin gets extra `real_chat_count`/`real_like_count` fields. Values scaled by language preferences (`language_preferences.py`): dark romance → higher RU, anime → higher EN, romantic → higher ES, fantasy → higher FR, modern → higher DE. Daily growth also preference-aware. Characters sorted by displayed count (real + base) on homepage. Featured = top 5 by current language.
- **Character translation**: Card fields (name, tagline, tags) translated in batch via LLM. Description fields (scenario, appearance, greeting_message) translated per-character on single character page (`include_descriptions=True`). All cached in JSONB `translations` column. Cache invalidated on edit of any translatable field.
- **Email providers**: 3-tier fallback — Resend API (if `RESEND_API_KEY` set) → SMTP (if `SMTP_HOST` + `SMTP_FROM_EMAIL` set) → console (prints to logs). Config: `resend_api_key`, `resend_from_email`, `smtp_host/port/user/password/from_email`.
- **Online status (fake)**: `isCharacterOnline(id)` in `lib/utils.ts` — deterministic hash of `id + currentHour`, ~33% show green dot. Used on CharacterCard and CharacterPage.
- **Static pages**: About, Terms, Privacy, FAQ — pure i18n content, routes at `/about`, `/terms`, `/privacy`, `/faq`. Footer links to all four.
- **Google OAuth**: authlib backend. Flow: AuthPage → `GET /api/auth/google` → Google consent → callback → find/create user (link by email) → JWT → redirect to `/auth/oauth-callback?token=...` → OAuthCallbackPage stores token → redirect to `/`. `password_hash` nullable for OAuth-only users. Env: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
- **Anti-bot protection** (no CAPTCHA, 5 layers): (1) **Honeypot** — hidden `website` field on registration, bots auto-fill it → 400. (2) **Proof-of-Work** — `GET /api/auth/challenge` → client solves SHA256 puzzle (difficulty=4, ~100ms in browser) → sends solution with registration. (3) **Registration rate limit** — 3 per hour per IP. (4) **Message interval** — minimum 5s between messages per user. (5) **Header validation** — 2s delay for requests missing Accept-Language or Referer headers.
- **Report system**: `Report` model with reason enum (inappropriate/spam/impersonation/underage/other), status (pending/reviewed/dismissed). Rate limit 5/hr per user. Admin management at `/admin/reports`. Frontend: ReportModal with radio buttons, AdminReportsPage with status filter tabs.
- **Multiple chats per character**: `force_new: true` on `POST /api/chats` skips existing chat lookup. Sidebar groups chats by character with `#N` numbering. "New Chat" button on CharacterPage and ChatPage header.
- **Group chats**: 1 user + 2-3 AI characters. Models: `GroupChat`, `GroupChatMember`, `GroupMessage`. API: `POST/GET/DELETE /api/group-chats`, `POST /api/group-chats/{id}/message` (SSE). Characters respond sequentially — each sees others' messages as `[Name]: text` (user role), own messages as assistant role. Group-specific system prompt addition with localized instructions (7 langs): "respond ONLY as {name}", "STRICTLY 1-2 paragraphs". Post-history reminder injected. Auto-fallback providers. Frontend: `CreateGroupChatModal` (character picker with search), `GroupChatPage` (SSE streaming with typing indicators per character), sidebar section. `max_tokens=600` for shorter responses. `is_regenerate` flag skips 5s message interval rate limit.
- **SillyTavern export/import**: Character card v2 format (`spec: "chara_card_v2"`). Export: `GET /api/characters/{id}/export` with Content-Disposition. Import: `POST /api/characters/import` from JSON card (v1/v2). SweetSin-specific fields in `extensions.sweetsin`. Import tab on CreateCharacterPage (file upload or JSON paste).
- **Markdown in chat**: react-markdown + rehype-sanitize for assistant messages. Custom styled components (bold, italic, code, lists, blockquote). User messages remain plain text.
- **Toast notifications**: react-hot-toast, bottom-center, dark theme. Used for: like/unlike, delete, copy, report, import, errors.
- **PWA**: vite-plugin-pwa with registerType autoUpdate, standalone display, NetworkFirst for `/api/` via workbox. `navigateFallbackDenylist` excludes `/sitemap.xml`, `/robots.txt`, `/feed.xml` from SPA fallback.
- **Skeleton loading**: Detailed skeletons matching real component shapes for character cards, character page, and chat page.
- **GeoIP**: Local MMDB database (DB-IP Lite Country, ~5MB) via `maxminddb`. Downloaded at Docker build time, auto-refreshed on app startup if >30 days old. `GEOIP_DB_PATH` env var. Country stored on `page_views`, displayed as flag emojis on analytics dashboard.
- **RSS feed**: `/feed.xml` — RSS 2.0, 30 latest characters with avatar enclosures and EN translations for names/descriptions. NSFW characters included but taglines/scenarios hidden. Nginx proxies to `/api/seo/feed.xml`. `<link rel="alternate">` in index.html.
- **JSON-LD schemas**: WebSite + Organization (@graph) on home, CreativeWork on characters (real counts only, no fake base_chat_count; `inLanguage`, `isPartOf: WebSite`, author attribution, UTC dates), FAQPage on /faq, BreadcrumbList on characters and tags, CollectionPage on tag pages (with `inLanguage`).
- **SEO anti-AI measures**: Anti-template prerender variability (6 heading variants per section, slug-hash-based section order rotation, 6 CTA variants), personality section in body, avatar `<img>` with alt text, creator attribution with `<time>` tag, `og:locale` on all pages. Quality gates for sitemap (scenario + personality >= 100 chars). `noindex` for thin character pages (< 100 chars total content). Fake counters removed from JSON-LD. See `ANTIAI.md` for full audit.
- **og:image**: PNG 1200x630 (`frontend/public/og-image.png`). SVG not supported by social platforms.
- **Character slug**: Auto-generated only from character name via `generate_slug(name, id)` (transliterate + UUID suffix). Unique per creator (`UniqueConstraint('creator_id', 'slug')`). Regenerated when name changes. Not user-editable. Used in SEO URLs (`/c/{slug}`).
- **Persona slug**: User-editable, optional, unique per user (`UniqueConstraint('user_id', 'slug')`). Validated via `validate_slug()` (3-50 chars, lowercase alphanumeric + hyphens). Frontend: debounced 500ms availability check in ProfilePage. Backend: `GET /personas/check-slug`.
- **Performance**: React.memo on CharacterCard and MessageBubble (custom comparator prevents re-render during streaming), explicit img width/height (CLS), request dedup in chatStore (module-level promise), stale-while-revalidate, sidebar skeleton + useMemo for grouping. Code splitting via React.lazy (11 pages). Inter font with Google Fonts preconnect. Streaming scroll: `requestAnimationFrame`-batched instant `scrollTop` (not `scrollIntoView` which causes jank).
- **Admin-only UI**: CharacterForm hides preferred_model, max_tokens, system_prompt_suffix from non-admin users. Response length is visible to all. Persona generation (Sparkles button) is admin-only in ChatPage.
- **SEO prerender**: Nginx user-agent match (Googlebot, Bingbot etc.) → backend HTML for /:lang/c/:slug, /:lang/tags/:slug, /:lang/faq, /:lang/about, /:lang/terms, /:lang/privacy, /:lang (home). Languages: `(en|es|ru|fr|de|pt|it)` in nginx regex.
- **SEO softening**: No "NSFW"/"uncensored" in meta tags or prerender content. NSFW characters shown on homepage/tags/RSS as name-only links (no taglines). NSFW character pages: `<meta name="rating" content="adult">`, truncated personality/scenario (100 chars), no appearance/greeting. Sitemap: priority 0.4 for NSFW vs 0.7 for sfw/moderate. `robots.txt`: `Disallow: /*nsfw*` blocks NSFW image URLs.
- **Tag landing pages**: `/en/tags/{fantasy,romance,anime,modern}` with SEO, JSON-LD, prerender, sitemap. All 7 languages supported.
- **Anonymous (guest) chat**: Unauthenticated users can chat with characters up to a configurable message limit (admin setting `anon_message_limit`, default 20, 0=disabled). Frontend generates UUID `anon_session_id` in localStorage, sends as `X-Anon-Session` header. Backend creates chats under system user `anonymous@system.local` with `anon_session_id` on Chat model. Message count enforced server-side (403 `anon_limit_reached`). Frontend shows remaining messages counter and registration prompt modal on limit. Anonymous users can't delete/clear chats, use personas, or see sidebar.
- **Autonomous scheduler**: `asyncio.create_task(run_scheduler())` in lifespan. Hourly check, 24h intervals (weekly for relations). State in `prompt_templates` with `scheduler.*` keys. Tasks: daily character generation (LLM + DALL-E avatar + auto-translate to all 6 non-RU languages), counter growth, highlights generation, cleanup; weekly: relationship building. `warmup_translations.py` translates to `["en", "es", "fr", "de", "pt", "it"]`. Email admin on character generation failure. Config: `AUTO_CHARACTER_ENABLED` env var.

### Scripts

- **`backend/scripts/rewrite_characters.py`** — One-time script to rewrite all @sweetsin character descriptions via paid LLM models (Claude→OpenAI→Gemini→... fallback). Rewrites personality, appearance, scenario, greeting_message + generates speech_pattern if missing + applies humanizer + clears translation cache. Run: `docker compose exec -T backend python scripts/rewrite_characters.py`
- **`scripts/`** — WetDreams.io auto-chat bot and utilities. See `scripts/CLAUDE.md` for details.

### Backup (`deploy/backup/`)

- **`backup.sh`** — Daily backup to Yandex Disk via rclone. Cron: `0 4 * * *`
  - **DB**: 3 rotating slots (`slot-0/1/2.sql.gz`), `day_of_year % 3` — always last 3 days
  - **Uploads**: `rclone sync` (incremental — only transfers new/changed files)
  - **rclone** configured with Yandex Disk OAuth token on production server (`/root/.config/rclone/rclone.conf`)
  - Structure on Yandex Disk: `ai-chat-backups/db/slot-{0,1,2}.sql.gz` + `ai-chat-backups/uploads/`

## API Routes

Auth: `POST /api/auth/register` (username optional, PoW required), `POST /api/auth/login`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`, `GET /api/auth/challenge` (PoW challenge), `GET /api/auth/providers` (available OAuth), `GET /api/auth/google` (OAuth redirect), `GET /api/auth/google/callback` — JWT includes role
Characters: `GET/POST /api/characters` (GET supports `gender` query param for male/female filter), `GET/PUT/DELETE /api/characters/{id}`, `GET /api/characters/my`, `GET /api/characters/structured-tags`, `POST /api/characters/generate-from-story`, `GET /api/characters/{id}/export` (SillyTavern card), `POST /api/characters/import` (SillyTavern card), `POST /api/characters/{id}/vote` (upvote/downvote), `POST /api/characters/{id}/fork` (clone as draft), `GET /api/characters/{id}/relations` (character connections)
Chats: `POST /api/chats` (get-or-create, `force_new` for multiple chats, supports anon via `X-Anon-Session`), `GET /api/chats`, `GET /api/chats/anon-limit` (public — limit/remaining/enabled), `GET /api/chats/daily-usage`, `GET/DELETE /api/chats/{id}`, `GET /api/chats/{id}/messages?before=ID&limit=20` (pagination), `POST /api/chats/{id}/message` (SSE, supports anon), `POST /api/chats/{id}/generate-persona-reply` (ghostwrite as persona), `DELETE /api/chats/{id}/messages` (clear), `DELETE /api/chats/{id}/messages/{msg_id}`
Group Chats: `POST /api/group-chats` (2-3 character_ids), `GET /api/group-chats`, `GET /api/group-chats/{id}` (last 30 messages), `DELETE /api/group-chats/{id}`, `POST /api/group-chats/{id}/message` (SSE: user_saved → character_start/token/character_done per character → all_done)
Personas: `GET /api/personas`, `POST /api/personas`, `PUT /api/personas/{id}`, `DELETE /api/personas/{id}`, `GET /api/personas/limit` (used/limit), `GET /api/personas/check-slug?slug=` (slug availability)
Users: `GET/PUT /api/users/me` (includes role, username), `GET /api/users/me/favorites`, `POST/DELETE /api/users/me/favorites/{id}`, `GET /api/users/me/votes` (user vote dict)
Reports: `POST /api/characters/{id}/report` (rate limit 5/hr), `GET /api/admin/reports?status=` (admin), `PUT /api/admin/reports/{id}` (admin)
Admin: `GET /api/admin/prompts`, `PUT /api/admin/prompts/{key}`, `DELETE /api/admin/prompts/{key}`, `GET /api/admin/settings`, `PUT /api/admin/settings/{key}` — admin role required
Models: `GET /api/models/openrouter`, `GET /api/models/groq`, `GET /api/models/cerebras`, `GET /api/models/together`
Analytics: `POST /api/analytics/pageview` (public, rate-limited), `GET /api/admin/analytics/overview?days=7` (admin — traffic, countries, devices, models, traffic_sources, os, bot_views, anon_stats), `GET /api/admin/analytics/costs?days=7` (admin — daily token usage, by provider, top users, totals)
SEO: `GET /api/seo/sitemap.xml`, `GET /api/seo/robots.txt`, `GET /api/seo/feed.xml` (RSS 2.0), `GET /api/seo/c/{slug}` (prerender), `GET /api/seo/tags/{slug}` (prerender), `GET /api/seo/faq` (prerender), `GET /api/seo/home` (prerender), `GET /api/seo/about` (prerender), `GET /api/seo/terms` (prerender), `GET /api/seo/privacy` (prerender)
Uploads: `POST /api/upload/avatar` (multipart, auth required), `POST /api/upload/generate-avatar` (admin-only, DALL-E 3 generation from prompt, 512x512 WebP)
Stats: `GET /api/stats` — public, returns inflated counters + online_now (excludes admins/system users)
Health: `GET /api/health`
