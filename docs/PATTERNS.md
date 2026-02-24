# Key Patterns

## Database

- **DB driver**: SQLite (`sqlite+aiosqlite://`) locally, PostgreSQL (`postgresql+asyncpg://`) in prod. Same SQLAlchemy models.
- **DB migrations**: `init_db()` runs `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in separate transactions (PostgreSQL aborts entire transaction on error). New nullable columns with defaults.
- **Enum handling**: SQLite stores enums as strings. Use `hasattr(x, 'value')` in serializers.

## Tags & Structured Tags

- **Tags**: Comma-separated string in DB, split to array in API responses. Two kinds: free-form `tags` (for search/categorization) and `structured_tags` (predefined IDs that inject prompt snippets).
- **Structured tags**: 33 predefined tags in 5 categories (gender, role, personality, setting, style). Each tag has multilingual label and prompt snippet. Stored as comma-separated IDs on Character. Injected into system prompt between personality and appearance sections. Registry in `characters/structured_tags.py`, API at `GET /api/characters/structured-tags`.
- **Gender filter**: `GET /api/characters?gender=male|female` filters by structured_tags (male/female). HomePage shows gender filter pills (All/Male/Female) in purple (`bg-purple-600`), separate from tag filter pills in rose.
- **Appearance field**: Separate character field for physical description. Included in system prompt between structured tags and scenario sections.
- **Template variables**: `{{char}}` and `{{user}}` in example dialogues are replaced with actual character and user names in system prompt.

## LLM Providers

- **New LLM providers**: Implement `BaseLLMProvider`, register in `registry.py`, add env key to `config.py`, pass in `main.py`.
- **Model selection in routers**: If model is `"auto"` → cross-provider fallback (Groq → Cerebras → OpenRouter, configurable via `AUTO_PROVIDER_ORDER`). **Paid mode** overrides auto order to `["groq", "openrouter"]` (Groq with flex tier, OpenRouter as fallback). **Free mode**: `["openrouter"]` only. If model contains `/` → OpenRouter direct ID. If `"openrouter"` → auto-fallback. Prefix routing: `groq:model_id`, `cerebras:model_id`, `together:model_id`. Otherwise → provider name (deepseek, qwen, openai, gemini, etc.) with default model.
- **Thinking models**: DeepSeek-reasoner uses `reasoning_content` field; Nemotron uses `reasoning` field. Extract when `content` is empty. `ThinkingFilter` strips `<think>` tags from streaming.
- **Gemma models**: Don't support `system` role via Google AI Studio. Must merge system into first user message.
- **Cerebras limitations**: API does not support `frequency_penalty`/`presence_penalty` — params silently ignored. UI hides penalty sliders when Cerebras model selected.
- **Per-provider parameter limits**: Frontend `PROVIDER_LIMITS` enforces provider-specific slider ranges. Cerebras/Claude/Gemini: no penalties. Claude: temp max 1.0. OpenAI: penalty max 2.0. Others: penalty max 1.0. Values clamped on model switch via `clampToLimits()`.
- **Proxy**: All providers accept `proxy_url` param, create `httpx.AsyncClient(proxy=...)` for HTTP clients.
- **Model tracking**: `model_used` stored on each Message as `{provider}:{model_id}`. Auto-fallback providers set `last_model_used` in for-loop. Visible to admin in chat UI.

## Auth & Admin

- **User roles**: `admin` or `user` (default). Stored in User model, embedded in JWT. Admin can edit/delete any character, access `/admin/prompts`. Auto-assigned via `ADMIN_EMAILS` env var (comma-separated, case-insensitive, synced on login).
- **Admin settings**: Key-value pairs stored in `prompt_templates` with `setting.` prefix. `GET/PUT /api/admin/settings`. Settings: `notify_registration` (email on new user), `paid_mode` (paid LLM providers for chat), `daily_message_limit` (per-user daily cap), `max_personas` (persona count cap), `anon_message_limit` (guest message limit, 0=disabled), `provider_enabled.{name}` (per-provider toggle for 9 providers). Toggle/input buttons on AdminUsersPage. Provider status section shows all providers with color-coded toggles (green=active, amber=auto-blocked 402, red=admin-disabled).
- **Prompt template overrides**: Defaults in code (`_DEFAULTS`), overrides in `prompt_templates` DB table. Admin edits via UI, "Reset" deletes override → falls back to code default. Cache TTL 60s, invalidated on PUT/DELETE.
- **Auto-generated usernames**: Registration creates `user_{hex(3)}` if username not provided. Changeable in profile with `^[a-zA-Z0-9_]{3,20}$` validation.
- **Google OAuth**: authlib backend. Flow: AuthPage → `GET /api/auth/google` → Google consent → callback → find/create user (link by email) → JWT → redirect to `/auth/oauth-callback?token=...` → OAuthCallbackPage stores token → redirect to `/`. `password_hash` nullable for OAuth-only users. Env: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
- **Anti-bot protection** (no CAPTCHA, 5 layers): (1) **Honeypot** — hidden `website` field on registration, bots auto-fill it → 400. (2) **Proof-of-Work** — `GET /api/auth/challenge` → client solves SHA256 puzzle (difficulty=4, ~100ms in browser) → sends solution with registration. (3) **Registration rate limit** — 3 per hour per IP. (4) **Message interval** — minimum 5s between messages per user. (5) **Header validation** — 2s delay for requests missing Accept-Language or Referer headers.
- **Admin-only UI**: CharacterForm hides preferred_model, max_tokens, system_prompt_suffix from non-admin users. Response length is visible to all. Persona generation (Sparkles button) is admin-only in ChatPage.
- **Email providers**: 3-tier fallback — Resend API (if `RESEND_API_KEY` set) → SMTP (if `SMTP_HOST` + `SMTP_FROM_EMAIL` set) → console (prints to logs). Config: `resend_api_key`, `resend_from_email`, `smtp_host/port/user/password/from_email`.

## Prompt System

- **Literary prose format**: Prompts instruct the model to write as literary prose — **third-person narration** per language (she/he, elle/il, ella/el, sie/er, ela/ele, lei/lui). Dialogue format: hyphen `- Text` (ru/es/fr/pt/it), quotes `"..."` (en/de). Em-dashes explicitly banned (AI marker). `*asterisks*` only for inner thoughts. Show-don't-tell, physical sensations, paragraph breaks for rhythm. Explicit ban on template pattern `*does X* text *does Y*`. **Anti-AI rules**: expanded banned cliche words per language (~30 each), sentence length variation enforced. **Anti-structural-repetition**: ban on starting 2+ sentences with same subject (She/He/Her/His per language), banned RP cliche patterns ("eyes widened/sparkled", "bit her lip", "heart raced", "voice filled with warmth", "couldn't help but smile" etc., all 7 languages). **Post-history**: 5 rotating variants (setting/action/dialogue/subtext/personality-driven) x 7 langs, hash-based selection prevents model adaptation. **NSFW-specific**: character voice preserved in intimacy, purple prose metaphors banned, emotions shown through body.
- **NSFW anti-repetition**: Prompts instruct to pick 1-2 senses per response and ROTATE them between responses. Explicit ban on repeating sensation descriptions from previous responses (all 7 languages).
- **Response length**: Character setting (`short`/`medium`/`long`/`very_long`) controls system prompt instructions about response format and length. Separate from `max_tokens` which is a hard token limit.
- **Generation settings**: Per-request overrides (model, temperature, top_p, top_k, frequency_penalty, max_tokens) sent in `SendMessageRequest`. Character's `max_tokens` used as default. Settings stored per-model in localStorage (`model-settings:{modelId}`), model choice stored per-chat (`chat-model:{chatId}`).

## Chat & Messaging

- **Render free tier**: Sleeps after inactivity. Frontend calls `wakeUpServer()` before generation requests.
- **Message ID sync**: Frontend creates messages with `crypto.randomUUID()`. Backend returns real IDs in SSE `done` event (`message_id` for assistant, `user_message_id` for user). Frontend updates IDs so delete/regenerate work correctly.
- **User message dedup**: Backend checks if last message in chat is same user text before saving (prevents duplicates on page reload after generation error).
- **Multiple chats per character**: `force_new: true` on `POST /api/chats` skips existing chat lookup. Sidebar groups chats by character with `#N` numbering. "New Chat" button on ChatPage header (icon) and CharacterPage (secondary button with `MessageSquarePlus` icon, authenticated users only). Anonymous users see only single "Start Chat" button (force_new=false).
- **Group chats**: 1 user + 2-3 AI characters. Models: `GroupChat`, `GroupChatMember`, `GroupMessage`. API: `POST/GET/DELETE /api/group-chats`, `POST /api/group-chats/{id}/message` (SSE). Characters respond sequentially — each sees others' messages as `[Name]: text` (user role), own messages as assistant role. Group-specific system prompt addition with localized instructions (7 langs): "respond ONLY as {name}", "STRICTLY 1-2 paragraphs". Post-history reminder injected. Auto-fallback providers. Frontend: `CreateGroupChatModal` (character picker with search), `GroupChatPage` (SSE streaming with typing indicators per character), sidebar section. `max_tokens=600` for shorter responses. `is_regenerate` flag skips 5s message interval rate limit.
- **Anonymous (guest) chat**: Unauthenticated users can chat with characters up to a configurable message limit (admin setting `anon_message_limit`, default 20, 0=disabled). Frontend generates UUID `anon_session_id` in localStorage, sends as `X-Anon-Session` header. Backend creates chats under system user `anonymous@system.local` with `anon_session_id` on Chat model. Message count enforced server-side (403 `anon_limit_reached`). Frontend shows remaining messages counter and registration prompt modal on limit. Anonymous users can't delete/clear chats, use personas, or see sidebar.
- **Report system**: `Report` model with reason enum (inappropriate/spam/impersonation/underage/other), status (pending/reviewed/dismissed). Rate limit 5/hr per user. Admin management at `/admin/reports`. Frontend: ReportModal with radio buttons, AdminReportsPage with status filter tabs.
- **SillyTavern export/import**: Character card v2 format (`spec: "chara_card_v2"`). Export: `GET /api/characters/{id}/export` with Content-Disposition. Import: `POST /api/characters/import` from JSON card (v1/v2). SweetSin-specific fields in `extensions.sweetsin`. Import tab on CreateCharacterPage (file upload or JSON paste).
- **Markdown in chat**: react-markdown + rehype-sanitize for assistant messages. Custom styled components (bold, italic, code, lists, blockquote). User messages remain plain text.

## Characters & Content

- **Character slug**: Auto-generated only from character name via `generate_slug(name, id)` (transliterate + UUID suffix). Unique per creator (`UniqueConstraint('creator_id', 'slug')`). Regenerated when name changes. Not user-editable. Used in SEO URLs (`/c/{slug}`).
- **Persona slug**: User-editable, optional, unique per user (`UniqueConstraint('user_id', 'slug')`). Validated via `validate_slug()` (3-50 chars, lowercase alphanumeric + hyphens). Frontend: debounced 500ms availability check in ProfilePage. Backend: `GET /personas/check-slug`.
- **Character translation**: Card fields (name, tagline, tags) translated in batch via LLM. Description fields (scenario, appearance, greeting_message) translated per-character on single character page (`include_descriptions=True`). All cached in JSONB `translations` column. Cache invalidated on edit of any translatable field. **Eager translation on edit**: when admin edits translatable fields, `translate_character_all_languages()` fires as background task — translates card + descriptions to all 6 other languages immediately (not lazily). `original_language` is saved on update via `CharacterUpdate` schema, so admin can edit in any UI language and translations go from the correct source.
- **Fake engagement counters**: `base_chat_count`/`base_like_count` are JSONB `{"ru": N, "en": M, "es": K, "fr": F, "de": D, "pt": P, "it": I}`. Serializer inflates: `displayed = real + base[lang]`. Admin gets extra `real_chat_count`/`real_like_count` fields. Values scaled by language preferences (`language_preferences.py`): dark romance → higher RU, anime → higher EN, romantic → higher ES, fantasy → higher FR, modern → higher DE. Daily growth also preference-aware. Characters sorted by displayed count (real + base) on homepage. Featured = top 5 by current language.
- **Online status (fake)**: `isCharacterOnline(id)` in `lib/utils.ts` — deterministic hash of `id + currentHour`, ~33% show green dot. Used on CharacterCard and CharacterPage.
- **Autonomous scheduler**: `asyncio.create_task(run_scheduler())` in lifespan. Hourly check, 24h intervals (weekly for relations). State in `prompt_templates` with `scheduler.*` keys. Tasks: daily character generation (LLM + DALL-E avatar + auto-translate to all 6 non-RU languages), counter growth, highlights generation, cleanup; weekly: relationship building. `warmup_translations.py` translates to `["en", "es", "fr", "de", "pt", "it"]`. Email admin on character generation failure. Config: `AUTO_CHARACTER_ENABLED` env var.

## SEO

- **SEO prerender**: Nginx user-agent match (Googlebot, Bingbot etc.) → backend HTML for /:lang/c/:slug, /:lang/tags/:slug, /:lang/faq, /:lang/about, /:lang/terms, /:lang/privacy, /:lang/campaigns, /:lang (home). Languages: `(en|es|ru|fr|de|pt|it)` in nginx regex. Fiction nginx config has all 8 prerender routes.
- **SEO softening**: No "NSFW"/"uncensored" in meta tags or prerender content. NSFW characters shown on homepage/tags/RSS as name-only links (no taglines). NSFW character pages: `<meta name="rating" content="adult">`, truncated personality/scenario (100 chars), no appearance/greeting. Sitemap: priority 0.4 for NSFW vs 0.7 for sfw/moderate. `robots.txt`: `Disallow: /*nsfw*` only for non-fiction mode (SweetSin).
- **SEO anti-AI measures**: Anti-template prerender variability (6 heading variants per section, slug-hash-based section order rotation, 6 CTA variants), personality section in body, avatar `<img>` with alt text, creator attribution with `<time>` tag, `og:locale` on all pages. Quality gates for sitemap (scenario + personality >= 100 chars). `noindex` for thin character pages (< 100 chars total content). Fake counters removed from JSON-LD. See `ANTIAI.md` for full audit.
- **JSON-LD schemas**: WebSite + Organization (@graph) on home, CreativeWork on characters (real counts only, no fake base_chat_count; `inLanguage`, `isPartOf: WebSite`, author attribution, UTC dates), FAQPage on /faq, BreadcrumbList on characters and tags, CollectionPage on tag pages (with `inLanguage`).
- **Tag landing pages**: `/{lang}/tags/{fantasy,romance,anime,modern}` with SEO, JSON-LD, prerender, sitemap. All 7 languages supported.
- **RSS feed**: `/feed.xml` — RSS 2.0, 30 latest characters with avatar enclosures and EN translations for names/descriptions. NSFW characters included but taglines/scenarios hidden. Nginx proxies to `/api/seo/feed.xml`. `<link rel="alternate">` in index.html.
- **og:image**: PNG 1200x630 (`frontend/public/og-image.png`). SVG not supported by social platforms.

## Frontend Patterns

- **i18n**: react-i18next with `en.json`/`es.json`/`ru.json`/`fr.json`/`de.json`/`pt.json`/`it.json` locale files (~540 keys each). Default language: English. Language stored in localStorage, applied to prompts via `language` param. LanguageSwitcher: EN | ES | RU | FR | DE | PT | IT.
- **Toast notifications**: react-hot-toast, bottom-center, dark theme. Used for: like/unlike, delete, copy, report, import, errors.
- **PWA**: vite-plugin-pwa with registerType autoUpdate, standalone display, NetworkFirst for `/api/` via workbox. `navigateFallbackDenylist` excludes `/sitemap.xml`, `/robots.txt`, `/feed.xml` from SPA fallback.
- **Skeleton loading**: Detailed skeletons matching real component shapes for character cards, character page, and chat page.
- **GeoIP**: Local MMDB database (DB-IP Lite Country, ~5MB) via `maxminddb`. Downloaded at Docker build time, auto-refreshed on app startup if >30 days old. `GEOIP_DB_PATH` env var. Country stored on `page_views`, displayed as flag emojis on analytics dashboard.
- **Static pages**: About, Terms, Privacy, FAQ — pure i18n content, routes at `/about`, `/terms`, `/privacy`, `/faq`. Footer links to all four.
- **Performance**: React.memo on CharacterCard and MessageBubble (custom comparator prevents re-render during streaming), explicit img width/height (CLS), request dedup in chatStore (module-level promise), stale-while-revalidate, sidebar skeleton + useMemo for grouping. Code splitting via React.lazy (11 pages). Inter font with Google Fonts preconnect. Streaming scroll: `requestAnimationFrame`-batched instant `scrollTop` (not `scrollIntoView` which causes jank).
