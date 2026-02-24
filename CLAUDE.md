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

## Detailed Documentation

Architecture and patterns are split into thematic files:

- **[Backend Architecture](docs/BACKEND.md)** — all backend modules (`backend/app/`): config, DB, auth, LLM providers, chat, admin, SEO, autonomous tasks
- **[Frontend Architecture](docs/FRONTEND.md)** — all frontend modules (`frontend/src/`): API clients, hooks, stores, pages, components
- **[Key Patterns](docs/PATTERNS.md)** — DB, auth, LLM, prompts, SEO, i18n, performance patterns and conventions
- **[API Routes](docs/API_ROUTES.md)** — complete API reference (auth, characters, chats, admin, SEO, etc.)

## Scripts

- **`backend/scripts/rewrite_characters.py`** — Script to rewrite all @sweetsin character descriptions via paid NSFW-friendly LLM models (Together → OpenAI → Claude). Rewrites personality (behavioral PList), appearance (character-revealing), scenario (clean AI-speak), greeting_message (structured) + always regenerates speech_pattern with examples + applies humanizer + clears translation cache. Run: `docker compose exec -T backend python scripts/rewrite_characters.py`
- **`scripts/`** — WetDreams.io auto-chat bot and utilities. See `scripts/CLAUDE.md` for details.

## Backup (`deploy/backup/`)

- **`backup.sh`** — Daily backup to Yandex Disk via rclone. Cron: `0 4 * * *`
  - **DB**: 3 rotating slots (`slot-0/1/2.sql.gz`), `day_of_year % 3` — always last 3 days
  - **Uploads**: `rclone sync` (incremental — only transfers new/changed files)
  - **rclone** configured with Yandex Disk OAuth token on production server (`/root/.config/rclone/rclone.conf`)
  - Structure on Yandex Disk: `ai-chat-backups/db/slot-{0,1,2}.sql.gz` + `ai-chat-backups/uploads/`
