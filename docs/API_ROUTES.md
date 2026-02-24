# API Routes

## Auth
- `POST /api/auth/register` (username optional, PoW required)
- `POST /api/auth/login`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/auth/challenge` (PoW challenge)
- `GET /api/auth/providers` (available OAuth)
- `GET /api/auth/google` (OAuth redirect)
- `GET /api/auth/google/callback` — JWT includes role

## Characters
- `GET /api/characters` (supports `gender` query param for male/female filter)
- `POST /api/characters`
- `GET /api/characters/{id}`
- `PUT /api/characters/{id}`
- `DELETE /api/characters/{id}`
- `GET /api/characters/my`
- `GET /api/characters/structured-tags`
- `POST /api/characters/generate-from-story`
- `GET /api/characters/{id}/export` (SillyTavern card)
- `POST /api/characters/import` (SillyTavern card)
- `POST /api/characters/{id}/vote` (upvote/downvote)
- `POST /api/characters/{id}/fork` (clone as draft)
- `GET /api/characters/{id}/relations` (character connections)

## Chats
- `POST /api/chats` (get-or-create, `force_new` for multiple chats, supports anon via `X-Anon-Session`)
- `GET /api/chats`
- `GET /api/chats/anon-limit` (public — limit/remaining/enabled)
- `GET /api/chats/daily-usage`
- `GET /api/chats/{id}`
- `DELETE /api/chats/{id}`
- `GET /api/chats/{id}/messages?before=ID&limit=20` (pagination)
- `POST /api/chats/{id}/message` (SSE, supports anon)
- `POST /api/chats/{id}/generate-persona-reply` (ghostwrite as persona)
- `DELETE /api/chats/{id}/messages` (clear)
- `DELETE /api/chats/{id}/messages/{msg_id}`

## Group Chats
- `POST /api/group-chats` (2-3 character_ids)
- `GET /api/group-chats`
- `GET /api/group-chats/{id}` (last 30 messages)
- `DELETE /api/group-chats/{id}`
- `POST /api/group-chats/{id}/message` (SSE: user_saved → character_start/token/character_done per character → all_done)

## Personas
- `GET /api/personas`
- `POST /api/personas`
- `PUT /api/personas/{id}`
- `DELETE /api/personas/{id}`
- `GET /api/personas/limit` (used/limit)
- `GET /api/personas/check-slug?slug=` (slug availability)

## Users
- `GET /api/users/me` (includes role, username)
- `PUT /api/users/me`
- `GET /api/users/me/favorites`
- `POST /api/users/me/favorites/{id}`
- `DELETE /api/users/me/favorites/{id}`
- `GET /api/users/me/votes` (user vote dict)

## Reports
- `POST /api/characters/{id}/report` (rate limit 5/hr)
- `GET /api/admin/reports?status=` (admin)
- `PUT /api/admin/reports/{id}` (admin)

## Admin
- `GET /api/admin/prompts`
- `PUT /api/admin/prompts/{key}`
- `DELETE /api/admin/prompts/{key}`
- `GET /api/admin/settings`
- `PUT /api/admin/settings/{key}`
- `GET /api/admin/provider-status` — admin role required

## Models
- `GET /api/models/openrouter`
- `GET /api/models/groq`
- `GET /api/models/cerebras`
- `GET /api/models/together`

## Analytics
- `POST /api/analytics/pageview` (public, rate-limited)
- `GET /api/admin/analytics/overview?days=7` (admin — traffic, countries, devices, models, traffic_sources, os, bot_views, anon_stats)
- `GET /api/admin/analytics/costs?days=7` (admin — daily token usage, by provider, top users, totals)

## SEO
- `GET /api/seo/sitemap.xml`
- `GET /api/seo/robots.txt`
- `GET /api/seo/feed.xml` (RSS 2.0)
- `GET /api/seo/c/{slug}` (prerender)
- `GET /api/seo/tags/{slug}` (prerender)
- `GET /api/seo/faq` (prerender)
- `GET /api/seo/home` (prerender)
- `GET /api/seo/about` (prerender)
- `GET /api/seo/terms` (prerender)
- `GET /api/seo/privacy` (prerender)
- `GET /api/seo/campaigns` (prerender, DnD adventures)

## Uploads
- `POST /api/upload/avatar` (multipart, auth required)
- `POST /api/upload/generate-avatar` (admin-only, DALL-E 3 generation from prompt, 512x512 WebP)
- Avatars saved as full-size (512px) + thumbnail (160px `_thumb.webp`) via `_save_with_thumb()`
- Auto-fallback in `main.py`: if `_thumb.webp` 404, generates from full-size on demand and caches to disk

## Stats
- `GET /api/stats` — public, returns inflated counters + online_now (excludes admins/system users)

## Health
- `GET /api/health`
