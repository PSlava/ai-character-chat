# AI Character Roleplay Chat — Текущий статус

## Деплой

### Текущий (облачный)

| Сервис | URL | Статус |
|--------|-----|--------|
| Frontend (Vercel) | https://ai-character-chat-murex.vercel.app | Работает |
| Backend (Render) | https://ai-character-chat-vercel.onrender.com | Работает |
| Database (Supabase) | PostgreSQL через connection pooler | Работает |
| GitHub | https://github.com/PSlava/ai-character-chat | main branch |

### VPS-деплой (Docker Compose) — РАБОТАЕТ

VPS развёрнут на `45.33.60.244`. Docker Compose: 4 контейнера, автодеплой через GitHub webhook.

```bash
# Вариант 1 — Интерактивная установка (спросит ключи):
git clone https://github.com/PSlava/ai-character-chat.git /opt/ai-chat
cd /opt/ai-chat
bash deploy/setup.sh

# Вариант 2 — Автоматическая (заранее заполнить .env):
git clone https://github.com/PSlava/ai-character-chat.git /opt/ai-chat
cd /opt/ai-chat
cp .env.example .env
nano .env                    # заполнить API-ключи
bash deploy/setup.sh --auto

# После установки — изменить конфиг и применить:
nano .env
docker compose up -d
```

| Контейнер | Назначение | Порт |
|-----------|------------|------|
| postgres | PostgreSQL 16, хранение данных | 5432 (internal) |
| backend | FastAPI + gunicorn + uvicorn workers | 8000 (internal) |
| nginx | Static frontend + reverse proxy /api → backend | 80, 443 |
| webhook | GitHub webhook → auto-deploy | 9000 |

Автодеплой:
- **GitHub Webhook** — Flask-сервер на порту 9000, при push в main → `git pull && docker compose up -d --build`
- **Health endpoint** — `GET :9000/health` возвращает commit, started_at, last_deploy
- **SSL** — опциональный Certbot (Let's Encrypt) через setup.sh

## Env-переменные

| Переменная | Render | VPS (.env) | Описание |
|------------|--------|------------|----------|
| DATABASE_URL | Supabase pooler | Авто (postgres контейнер) | PostgreSQL |
| JWT_SECRET | auto-generated | auto-generated | JWT-токены |
| OPENROUTER_API_KEY | Да | Вручную | OpenRouter |
| GROQ_API_KEY | — | Вручную | Groq |
| CEREBRAS_API_KEY | — | Вручную | Cerebras |
| DEEPSEEK_API_KEY | — | Вручную | DeepSeek |
| QWEN_API_KEY | — | Вручную | Qwen/DashScope |
| ANTHROPIC_API_KEY | Да | Вручную | Claude (нужны кредиты) |
| OPENAI_API_KEY | Да | Вручную | GPT (нужны кредиты) |
| GEMINI_API_KEY | Да | Вручную | Gemini (квота=0) |
| DEFAULT_MODEL | qwen | Настраиваемый | Модель по умолчанию |
| PROXY_URL | Да | Вручную | HTTP прокси |
| DOMAIN | — | Вручную | Домен для SSL |
| POSTGRES_PASSWORD | — | auto-generated | Пароль PostgreSQL |
| WEBHOOK_SECRET | — | auto-generated | GitHub webhook secret |

## Что сделано

### Аутентификация и роли
- Регистрация и логин по email/пароль
- **Автогенерация username** при регистрации (`user_XXXXXX`), можно сменить в профиле
- JWT-токены (30 дней) с ролью, bcrypt хеширование
- **Роли пользователей**: admin и user
- Защищённые эндпоинты через middleware
- Опциональная авторизация (`get_current_user_optional`) для публичных эндпоинтов
- Хранение токена и роли в localStorage

### Персонажи
- Полный CRUD: создание, просмотр, редактирование, удаление (с cascade на чаты)
- **Админ может редактировать и удалять персонажей всех пользователей**
- Каталог публичных персонажей с поиском и фильтрацией по тегам
- Приватные персонажи видны только владельцу в каталоге
- Страница персонажа со статистикой (чаты, лайки), **username создателя как @username**
- Избранное (лайки)
- Рейтинг контента (SFW / Moderate / NSFW)
- **NSFW-фильтрация моделей** — модели без поддержки NSFW отключены в UI и исключены из auto-selection
- **Длина ответа** — настройка на персонаже: короткий / средний / длинный / очень длинный
- **Макс. токенов** — настраиваемый лимит (256–4096, дефолт 2048)
- **Генерация персонажа из текста** — вставляешь рассказ, AI создаёт профиль
- **Выбор AI-модели** — OpenRouter, Groq, Cerebras + прямые провайдеры (DeepSeek, Qwen)
- **API реестра моделей** — `GET /api/models/{openrouter,groq,cerebras}`

### Чат
- Создание чат-сессий с персонажами
- SSE-стриминг ответов (токен за токеном)
- Контекстное окно (sliding window, настраиваемый размер: 4K/8K/16K/∞)
- System prompt с динамическими инструкциями по длине ответа (short/medium/long/very_long)
- **Отслеживание модели** — каждое сообщение сохраняет `model_used` (напр. `openrouter:google/gemma-3-27b-it:free`)
- **Показ модели для админа** — под каждым ответом ассистента (10px серый текст, только для admin)
- История сообщений сохраняется в БД
- **Удаление чатов** и **очистка истории** (приветственное сообщение сохраняется)
- **Удаление отдельных сообщений** (кроме приветственного)
- **Перегенерация ответа** — кнопка на hover + постоянная кнопка под последним ответом
- **Ошибки в чате** — красные баблы с текстом ошибки вместо пустых сообщений
- **Настройки генерации** — модалка «Модель и настройки» с:
  - Выбор модели (карточки с категориями: OpenRouter / Groq / Cerebras / Прямой API / Платные)
  - Temperature (0–2), Top-P (0–1), Top-K (0–100)
  - Frequency penalty (0–2), Presence penalty (0–2)
  - Макс. токенов (256–4096)
  - **Память** (контекст): 4K / 8K / 16K / ∞
- **Сохранение настроек** — настройки генерации сохраняются в localStorage per-chat, восстанавливаются при перезагрузке
- **Смена модели mid-chat** — сохраняется в БД на чате
- **Синхронизация ID сообщений** — фронтенд обновляет локальные UUID на реальные из БД (в т.ч. при ошибках)
- **Фильтрация thinking-токенов** — `<think>...</think>` блоки вырезаются из стриминга (Qwen3, DeepSeek R1)

### Админ-панель
- **Шаблоны промптов** — админ может редактировать любой кусок system prompt через UI
  - Defaults хранятся в коде (`prompt_builder.py`), overrides — в БД (`prompt_templates`)
  - Override перекрывает дефолт; кнопка «Сбросить» удаляет override → возврат к дефолту
  - In-memory кэш (60 сек TTL) для минимизации запросов к БД
  - 20 ключей × 2 языка (ru/en): вступление, правила контента, длина ответа, формат, правила и др.
  - Страница `/admin/prompts` с табами RU/EN, expandable карточки, метки «Изменён»/«По умолчанию»
- Ссылка в сайдбаре видна только админу

### LLM-провайдеры (8 штук)

| Провайдер | Модели | API | Статус |
|-----------|--------|-----|--------|
| **OpenRouter** | 8 бесплатных моделей (auto-fallback) | openrouter.ai/api/v1 | **Работает** |
| **Groq** | 6 моделей (auto-fallback) | api.groq.com/openai/v1 | **Работает** |
| **Cerebras** | 3 модели (auto-fallback) | api.cerebras.ai/v1 | **Работает** |
| **DeepSeek** | deepseek-chat, deepseek-reasoner | api.deepseek.com/v1 | **Готов** — нужен ключ |
| **Qwen (DashScope)** | qwen3-32b, qwen3-235b и др. | dashscope-intl.aliyuncs.com | **Готов** — нужен ключ |
| Gemini | gemini-2.0-flash | generativelanguage.googleapis.com | Не работает (квота=0) |
| Claude | claude-sonnet-4-5 | api.anthropic.com | Не работает (нужны кредиты) |
| OpenAI | gpt-4o | api.openai.com | Не работает (нет кредитов) |

**Бесплатные модели через OpenRouter (с оценкой качества для RP):**

| Модель | Качество | NSFW | Примечание |
|--------|----------|------|------------|
| Hermes 3 405B | 9/10 | Да | Лучшая для RP |
| Llama 3.3 70B | 8/10 | Да | Хорошая для RP |
| Gemma 3 27B | 7/10 | Нет | Стабильная, слабый RP на русском |
| Gemma 3 12B | 6/10 | Нет | Быстрая |
| DeepSeek R1 | 5/10 | Нет | Умная, но медленная (>30с) |
| Nemotron 9B | 4/10 | Да | Thinking-модель, мешает языки |
| Qwen3 4B | 4/10 | Да | Маленькая |
| Llama 3.2 3B | 3/10 | Да | Маленькая |

**Бесплатные модели через Groq (авто-обновление из API):**

| Модель | Качество | Примечание |
|--------|----------|------------|
| Llama 3.3 70B | 9/10 | Основная |
| Qwen3 32B | 8/10 | Хорошая для RP |
| Llama 4 Scout/Maverick | 7/10 | Новые |
| DeepSeek R1 Distill 70B | 7/10 | Thinking-модель |
| GPT-OSS 120B | 6/10 | Строгая модерация, NSFW заблокирован |
| GPT-OSS 20B | 5/10 | Строгая модерация, NSFW заблокирован |

**Бесплатные модели через Cerebras (авто-обновление из API):**

| Модель | Качество | Примечание |
|--------|----------|------------|
| Llama 3.3 70B | 9/10 | Основная |
| Qwen 3 32B | 8/10 | Хорошая для RP |
| ZAI GLM 4.7 | 7/10 | — |
| GPT-OSS 120B | 6/10 | Строгая модерация, NSFW заблокирован |

**Режимы выбора модели:**
- **Auto (OpenRouter / Groq / Cerebras)** — автоматический перебор топ-3 по качеству, с NSFW-фильтрацией
- **Конкретная модель** — выбор конкретной модели провайдера (напр. `groq:llama-3.3-70b-versatile`)
- **Прямой провайдер** (DeepSeek, Qwen) — напрямую через API, минуя агрегаторы
- **Авто-обновление реестров** — модели Groq и Cerebras обновляются из API каждый час
- **NSFW-фильтрация** — модели без поддержки NSFW исключаются из auto-selection для NSFW-персонажей
- **`last_model_used`** — провайдеры с auto-fallback отслеживают какая модель реально ответила

**Кулдаун неработающих моделей:**
- Если модель вернула ошибку (429, 402, 404, rate limit) — она исключается из auto-перебора на 15 минут
- Работает для всех трёх агрегаторов: OpenRouter, Groq, Cerebras
- Реализация: `backend/app/llm/model_cooldown.py`

**Особенности провайдеров:**
- Gemma (Google AI Studio) — не поддерживает `system` role, мерджится в `user`
- Nemotron/DeepSeek R1 — thinking-модели, ответ в поле `reasoning`/`reasoning_content`
- DeepSeek-reasoner — thinking-модель, ответ в `reasoning_content`
- Venice — нестабилен, все модели через него возвращают 429
- **Qwen/DashScope модерация** — DashScope применяет модерацию Alibaba (`data_inspection_failed`), обрабатывается с user-friendly сообщением
- Все провайдеры поддерживают HTTP-прокси с авторизацией, generation settings (temperature, top_p, top_k, frequency_penalty, presence_penalty)
- **ThinkingFilter** — стриминговый фильтр для `<think>...</think>` блоков
- **Render wake-up** — автоматическое пробуждение сервера перед генерацией (free tier засыпает)

### i18n (интернационализация)
- Двуязычный интерфейс: русский (по умолчанию) и английский
- i18next + react-i18next
- Переключатель языков в профиле
- Язык пользователя сохраняется в БД и передаётся в system prompt
- **Промпты на выбранном языке** — при выборе English все части system prompt берутся из английского набора, включая строгое указание «Write ONLY in English»

### Фронтенд
- React + TypeScript + Vite + Tailwind CSS
- Тёмная тема
- Zustand для стейт-менеджмента
- 9 страниц: главная, авторизация, персонаж, чат, создание, редактирование, профиль, **админ-промпты**
- Стриминг сообщений в реальном времени
- Выбор AI-модели: OpenRouter / Groq / Cerebras (с оценками) + DeepSeek + Qwen + платные
- **NSFW-модели визуально отключены** в настройках для NSFW-персонажей
- Настройки генерации (модалка с моделью + 6 слайдеров + память)
- Управление сообщениями: удаление, перегенерация, очистка чата
- Автоматическое пробуждение Render (wake-up) с индикатором статуса
- **Профиль**: смена display name, username (с валидацией), языка

### Инфраструктура
- SQLAlchemy ORM (SQLite локально / PostgreSQL в проде)
- Авто-миграции: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` при старте (отдельные транзакции)
- SSL для подключения к Supabase
- **Docker Compose** — полный VPS-деплой (PostgreSQL + Backend + Nginx + Webhook)
- **Multi-stage Docker build** — frontend собирается в node:20, раздаётся через nginx:alpine
- **GitHub Webhook** — автодеплой при push в main (Flask на порту 9000)
- **Health endpoints** — `/api/health` и `:9000/health` с commit hash, started_at, last_deploy
- **setup.sh** — установка на Ubuntu VPS (интерактивный + `--auto` режим с предзаполненным `.env`)
- **SSL** — опциональный Certbot через setup.sh, поддержка добавления домена позже
- render.yaml + vercel.json для облачного деплоя
- Прокси для обхода региональных ограничений API

## Что нужно доработать

### Высокий приоритет
- [x] Протестировать Docker Compose сборку локально — все образы собираются, контейнеры стартуют
- [x] Развернуть на VPS (45.33.60.244) — работает, автодеплой через webhook
- [x] Настроить GitHub webhook для автодеплоя
- [x] Роли пользователей (admin/user) + админ-панель промптов
- [ ] Задать GROQ_API_KEY и CEREBRAS_API_KEY в Render
- [ ] Загрузка аватаров персонажей (сейчас только URL, нет загрузки файлов)

### Средний приоритет
- [ ] Пагинация в каталоге персонажей (бэкенд есть, фронтенд подгружает только первые 20)
- [ ] Адаптивный дизайн для мобильных устройств
- [ ] Уведомления/тосты при ошибках и успехах
- [ ] Валидация форм (минимальная длина, обязательные поля)

### Низкий приоритет (будущее)
- [ ] OAuth авторизация (Google, GitHub)
- [ ] Загрузка файлов через Storage
- [ ] Модерация контента
- [ ] Аналитика (популярные персонажи, активность)
- [ ] Экспорт/импорт персонажей
- [ ] WebSocket вместо SSE для двустороннего общения
- [ ] Групповые чаты (несколько персонажей)
- [ ] Голосовые сообщения (TTS)
- [ ] Система отзывов/рейтингов персонажей

## Стек технологий

```
Backend:  Python 3.12 + FastAPI + SQLAlchemy + PyJWT + bcrypt + gunicorn + uvicorn
Frontend: React 18 + TypeScript + Vite + Tailwind CSS + Zustand + i18next
Database: PostgreSQL 16 (Docker) / Supabase (облако) / SQLite (локально)
AI:       OpenRouter + Groq + Cerebras + DeepSeek + Qwen/DashScope + Anthropic + OpenAI + Google GenAI
Streaming: SSE (Server-Sent Events)
Deploy:   Docker Compose (VPS) / Vercel + Render + Supabase (облако)
CI/CD:    GitHub Webhook (auto-deploy on push to main)
```

## Структура проекта

```
chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI, CORS, lifespan
│   │   ├── config.py                # Настройки из env
│   │   ├── auth/                    # JWT аутентификация + роли
│   │   │   ├── router.py            # register (auto-username), login
│   │   │   └── middleware.py        # get_current_user (с role), get_current_user_optional
│   │   ├── admin/                   # Админ-панель
│   │   │   └── router.py            # CRUD промпт-шаблонов (admin only)
│   │   ├── characters/              # CRUD + генерация из текста
│   │   │   ├── router.py            # API endpoints (admin bypass)
│   │   │   ├── service.py           # Бизнес-логика (is_admin)
│   │   │   ├── schemas.py           # Pydantic модели
│   │   │   └── serializers.py       # ORM → dict (username в profiles)
│   │   ├── chat/                    # SSE стриминг, контекст
│   │   │   ├── router.py            # send_message (SSE + model_used), delete, clear
│   │   │   ├── service.py           # Контекстное окно, сохранение (model_used)
│   │   │   ├── schemas.py           # SendMessageRequest (model, temp, top_p, context_limit, etc.)
│   │   │   └── prompt_builder.py    # Defaults + DB overrides, async, 60s cache
│   │   ├── llm/                     # 8 провайдеров + реестр + модели + кулдаун
│   │   │   ├── base.py              # BaseLLMProvider, LLMConfig (+ content_rating)
│   │   │   ├── registry.py          # init_providers + get_provider
│   │   │   ├── model_cooldown.py    # 15-мин кулдаун для неработающих моделей
│   │   │   ├── openrouter_provider.py  # OpenRouter (auto-fallback, last_model_used)
│   │   │   ├── openrouter_models.py    # Реестр моделей с quality + nsfw
│   │   │   ├── groq_provider.py        # Groq (auto-fallback, last_model_used)
│   │   │   ├── groq_models.py          # Реестр моделей Groq + NSFW_BLOCKED
│   │   │   ├── cerebras_provider.py    # Cerebras (auto-fallback, last_model_used)
│   │   │   ├── cerebras_models.py      # Реестр моделей Cerebras + NSFW_BLOCKED
│   │   │   ├── deepseek_provider.py    # DeepSeek прямой API
│   │   │   ├── qwen_provider.py        # Qwen/DashScope + модерация
│   │   │   ├── anthropic_provider.py   # Claude
│   │   │   ├── openai_provider.py      # GPT-4o
│   │   │   ├── gemini_provider.py      # Gemini
│   │   │   ├── thinking_filter.py      # ThinkingFilter для <think> блоков
│   │   │   └── router.py              # GET /api/models/{openrouter,groq,cerebras}
│   │   ├── users/                   # Профиль (username update), избранное
│   │   └── db/                      # Модели, сессии, миграции
│   │       ├── models.py            # User (role), Character, Chat, Message (model_used), Favorite, PromptTemplate
│   │       └── session.py           # Engine, init_db + auto-migrations
│   ├── requirements.txt
│   ├── Dockerfile                   # gunicorn + uvicorn workers
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                     # HTTP клиент, API функции
│   │   │   ├── client.ts            # Axios с JWT
│   │   │   ├── admin.ts             # Промпт-шаблоны (admin)
│   │   │   ├── characters.ts        # CRUD + generate + wake-up + models
│   │   │   ├── users.ts             # Profile (username, role)
│   │   │   └── chat.ts              # chats, messages, delete, clear
│   │   ├── hooks/
│   │   │   ├── useAuth.ts           # Авторизация
│   │   │   └── useChat.ts           # SSE стриминг + GenerationSettings + model_used
│   │   ├── store/                   # Zustand (auth с role, chat)
│   │   ├── pages/                   # 9 страниц
│   │   │   ├── ChatPage.tsx         # Чат + настройки + модель + isAdmin
│   │   │   ├── AdminPromptsPage.tsx # Админ: редактор промптов
│   │   │   ├── CreateCharacterPage.tsx  # Создание (ручное + из текста)
│   │   │   ├── EditCharacterPage.tsx    # Редактирование персонажа
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx        # Список сообщений + перегенерация + isAdmin
│   │   │   │   ├── ChatInput.tsx         # Ввод + стоп
│   │   │   │   ├── MessageBubble.tsx     # Сообщение + delete + regenerate + model_used (admin)
│   │   │   │   └── GenerationSettingsModal.tsx  # Модель (5 групп) + 6 слайдеров + память
│   │   │   ├── characters/
│   │   │   │   └── CharacterForm.tsx     # Форма (name, personality, model, NSFW disable)
│   │   │   └── ui/                       # Button, Input, Avatar, LanguageSwitcher
│   │   ├── lib/                     # Утилиты (localStorage с role)
│   │   ├── locales/                 # i18n: en.json, ru.json
│   │   └── types/                   # TypeScript типы (Message с model_used)
│   ├── vercel.json
│   └── package.json
├── deploy/
│   ├── setup.sh                     # Установка на VPS (--auto для non-interactive)
│   ├── deploy.sh                    # Автодеплой (git pull + rebuild)
│   ├── nginx/
│   │   ├── Dockerfile               # Multi-stage: node build → nginx serve
│   │   ├── nginx.conf               # Reverse proxy + SSE support
│   │   └── certs/                   # SSL сертификаты (gitignored)
│   └── webhook/
│       ├── Dockerfile               # Python + docker CLI
│       ├── server.py                # Flask webhook server
│       └── requirements.txt
├── docker-compose.yml               # PostgreSQL + Backend + Nginx + Webhook
├── .env.example                     # Шаблон переменных (cp → .env → nano → setup --auto)
├── render.yaml
├── CLAUDE.md
└── CURRENT_STAGE.md
```
