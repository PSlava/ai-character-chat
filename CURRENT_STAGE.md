# AI Character Roleplay Chat — Текущий статус

## Деплой

### Текущий (облачный)

| Сервис | URL | Статус |
|--------|-----|--------|
| Frontend (Vercel) | https://ai-character-chat-murex.vercel.app | Работает |
| Backend (Render) | https://ai-character-chat-vercel.onrender.com | Работает |
| Database (Supabase) | PostgreSQL через connection pooler | Работает |
| GitHub | https://github.com/PSlava/ai-character-chat | main branch |

### VPS-деплой (Docker Compose) — ПРОВЕРЕН

Docker Compose сборка протестирована локально — все 4 образа собираются, контейнеры postgres/backend/webhook стартуют, healthcheck проходит.

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
- **GitHub Actions** — SSH на VPS → `deploy/deploy.sh` при push в main
- **Webhook** — Flask-сервер на порту 9000, проверяет secret, запускает `deploy/deploy.sh`
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

### Аутентификация
- Регистрация и логин по email/username/пароль
- JWT-токены (30 дней), bcrypt хеширование
- Защищённые эндпоинты через middleware
- Опциональная авторизация (`get_current_user_optional`) для публичных эндпоинтов
- Хранение токена в localStorage

### Персонажи
- Полный CRUD: создание, просмотр, редактирование, удаление (с cascade на чаты)
- Каталог публичных персонажей с поиском и фильтрацией по тегам
- Приватные персонажи видны только владельцу в каталоге
- Страница персонажа со статистикой (чаты, лайки)
- Избранное (лайки)
- Рейтинг контента (SFW / Moderate / NSFW)
- **Длина ответа** — настройка на персонаже: короткий / средний / длинный / очень длинный
- **Макс. токенов** — настраиваемый лимит (256–4096, дефолт 2048)
- **Генерация персонажа из текста** — вставляешь рассказ, AI создаёт профиль
- **Выбор AI-модели** — OpenRouter, Groq, Cerebras + прямые провайдеры (DeepSeek, Qwen)
- **API реестра моделей** — `GET /api/models/{openrouter,groq,cerebras}`

### Чат
- Создание чат-сессий с персонажами
- SSE-стриминг ответов (токен за токеном)
- Контекстное окно (sliding window ~24K токенов, до 50 сообщений)
- System prompt с динамическими инструкциями по длине ответа (short/medium/long/very_long)
- История сообщений сохраняется в БД
- **Удаление чатов** и **очистка истории** (приветственное сообщение сохраняется)
- **Удаление отдельных сообщений** (кроме приветственного)
- **Перегенерация ответа** — кнопка на hover + постоянная кнопка под последним ответом
- **Ошибки в чате** — красные баблы с текстом ошибки вместо пустых сообщений
- **Настройки генерации** — модалка «Модель и настройки» с:
  - Выбор модели (карточки с категориями: OpenRouter / Groq / Cerebras / Прямой API / Платные)
  - Temperature (0–2)
  - Top-P (0–1)
  - Top-K (0–100)
  - Frequency penalty (0–2)
  - Макс. токенов (256–4096)
- **Смена модели mid-chat** — сохраняется в БД на чате
- **Синхронизация ID сообщений** — фронтенд обновляет локальные UUID на реальные из БД (в т.ч. при ошибках)
- **Фильтрация thinking-токенов** — `<think>...</think>` блоки вырезаются из стриминга (Qwen3, DeepSeek R1)

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

**Бесплатные модели через OpenRouter (с оценкой качества):**

| Модель | Качество | Провайдер | Статус |
|--------|----------|-----------|--------|
| Gemma 3 27B | 9/10 | Google AI Studio | Стабильная |
| Gemma 3 12B | 8/10 | Google AI Studio | Стабильная, быстрая |
| Nemotron 9B | 7/10 | Nvidia | Быстрая, thinking-модель |
| DeepSeek R1 | 7/10 | DeepSeek | Умная, но медленная (>30с) |
| Hermes 3 405B | 6/10 | Venice | Нестабилен |
| Llama 3.3 70B | 6/10 | Venice | Нестабилен |
| Qwen3 4B | 5/10 | Venice | Нестабилен |
| Llama 3.2 3B | 4/10 | Venice | Нестабилен |

**Бесплатные модели через Groq:**

| Модель | Качество | Примечание |
|--------|----------|------------|
| Llama 3.3 70B | 9/10 | Основная |
| Qwen QwQ 32B | 8/10 | Thinking-модель |
| GPT-OSS 120B | 8/10 | Большая |
| Llama 4 Scout | 7/10 | Новая |
| DeepSeek R1 Distill 70B | 7/10 | Thinking-модель |
| Llama 3.1 8B | 5/10 | Быстрая |

**Бесплатные модели через Cerebras:**

| Модель | Качество | Примечание |
|--------|----------|------------|
| Qwen 3 235B | 9/10 | Самая большая бесплатная |
| GPT-OSS 120B | 8/10 | Большая |
| Llama 3.1 8B | 5/10 | Быстрая |

**Режимы выбора модели:**
- **Auto (OpenRouter / Groq / Cerebras)** — автоматический перебор топ-3 по качеству
- **Конкретная модель** — выбор конкретной модели провайдера (напр. `groq:llama-3.3-70b-versatile`)
- **Прямой провайдер** (DeepSeek, Qwen) — напрямую через API, минуя агрегаторы

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
- Все провайдеры поддерживают HTTP-прокси с авторизацией, generation settings (temperature, top_p, top_k, frequency_penalty)
- **ThinkingFilter** — стриминговый фильтр для `<think>...</think>` блоков
- **Render wake-up** — автоматическое пробуждение сервера перед генерацией (free tier засыпает)

### Фронтенд
- React + TypeScript + Vite + Tailwind CSS
- Тёмная тема
- Zustand для стейт-менеджмента
- 7 страниц: главная, авторизация, персонаж, чат, создание, редактирование, профиль
- Стриминг сообщений в реальном времени
- Русский интерфейс
- Выбор AI-модели: OpenRouter / Groq / Cerebras (с оценками) + DeepSeek + Qwen + платные
- Настройки генерации (модалка с моделью + 5 слайдеров)
- Управление сообщениями: удаление, перегенерация, очистка чата
- Автоматическое пробуждение Render (wake-up) с индикатором статуса

### Инфраструктура
- SQLAlchemy ORM (SQLite локально / PostgreSQL в проде)
- Авто-миграции: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` при старте (отдельные транзакции)
- SSL для подключения к Supabase
- **Docker Compose** — полный VPS-деплой (PostgreSQL + Backend + Nginx + Webhook)
- **Multi-stage Docker build** — frontend собирается в node:20, раздаётся через nginx:alpine
- **GitHub Actions** — автодеплой через SSH при push в main
- **GitHub Webhook** — альтернативный автодеплой через webhook-сервер
- **setup.sh** — установка на Ubuntu VPS (интерактивный + `--auto` режим с предзаполненным `.env`)
- render.yaml + vercel.json для облачного деплоя
- Прокси для обхода региональных ограничений API

## Что нужно доработать

### Высокий приоритет
- [x] Протестировать Docker Compose сборку локально — все образы собираются, контейнеры стартуют
- [ ] Развернуть на VPS и протестировать в проде
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
Frontend: React 18 + TypeScript + Vite + Tailwind CSS + Zustand
Database: PostgreSQL 16 (Docker) / Supabase (облако) / SQLite (локально)
AI:       OpenRouter + Groq + Cerebras + DeepSeek + Qwen/DashScope + Anthropic + OpenAI + Google GenAI
Streaming: SSE (Server-Sent Events)
Deploy:   Docker Compose (VPS) / Vercel + Render + Supabase (облако)
CI/CD:    GitHub Actions (SSH deploy) / Webhook server
```

## Структура проекта

```
chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI, CORS, lifespan
│   │   ├── config.py                # Настройки из env
│   │   ├── auth/                    # JWT аутентификация
│   │   │   ├── router.py            # register, login
│   │   │   └── middleware.py        # get_current_user, get_current_user_optional
│   │   ├── characters/              # CRUD + генерация из текста
│   │   │   ├── router.py            # API endpoints
│   │   │   ├── service.py           # Бизнес-логика
│   │   │   ├── schemas.py           # Pydantic модели
│   │   │   └── serializers.py       # ORM → dict
│   │   ├── chat/                    # SSE стриминг, контекст
│   │   │   ├── router.py            # send_message (SSE), delete, clear
│   │   │   ├── service.py           # Контекстное окно, сохранение
│   │   │   ├── schemas.py           # SendMessageRequest (model, temp, top_p, etc.)
│   │   │   └── prompt_builder.py    # Динамический system prompt
│   │   ├── llm/                     # 8 провайдеров + реестр + модели + кулдаун
│   │   │   ├── base.py              # BaseLLMProvider, LLMConfig, LLMMessage
│   │   │   ├── registry.py          # init_providers + get_provider
│   │   │   ├── model_cooldown.py    # 15-мин кулдаун для неработающих моделей
│   │   │   ├── openrouter_provider.py  # OpenRouter (auto-fallback)
│   │   │   ├── openrouter_models.py    # Реестр моделей с quality scores
│   │   │   ├── groq_provider.py        # Groq (auto-fallback)
│   │   │   ├── groq_models.py          # Реестр моделей Groq
│   │   │   ├── cerebras_provider.py    # Cerebras (auto-fallback)
│   │   │   ├── cerebras_models.py      # Реестр моделей Cerebras
│   │   │   ├── deepseek_provider.py    # DeepSeek прямой API
│   │   │   ├── qwen_provider.py        # Qwen/DashScope + модерация
│   │   │   ├── anthropic_provider.py   # Claude
│   │   │   ├── openai_provider.py      # GPT-4o
│   │   │   ├── gemini_provider.py      # Gemini
│   │   │   ├── thinking_filter.py      # ThinkingFilter для <think> блоков
│   │   │   └── router.py              # GET /api/models/{openrouter,groq,cerebras}
│   │   ├── users/                   # Профиль, избранное
│   │   └── db/                      # Модели, сессии, миграции
│   │       ├── models.py            # User, Character, Chat, Message, Favorite
│   │       └── session.py           # Engine, init_db + auto-migrations
│   ├── requirements.txt
│   ├── Dockerfile                   # gunicorn + uvicorn workers
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                     # HTTP клиент, API функции
│   │   │   ├── client.ts            # Axios с JWT
│   │   │   ├── characters.ts        # CRUD + generate + wake-up + models
│   │   │   └── chat.ts              # chats, messages, delete, clear
│   │   ├── hooks/
│   │   │   ├── useAuth.ts           # Авторизация
│   │   │   └── useChat.ts           # SSE стриминг + GenerationSettings
│   │   ├── store/                   # Zustand (auth, chat)
│   │   ├── pages/                   # 7 страниц
│   │   │   ├── ChatPage.tsx         # Чат + настройки + модель
│   │   │   ├── CreateCharacterPage.tsx  # Создание (ручное + из текста)
│   │   │   ├── EditCharacterPage.tsx    # Редактирование персонажа
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx        # Список сообщений + перегенерация
│   │   │   │   ├── ChatInput.tsx         # Ввод + стоп
│   │   │   │   ├── MessageBubble.tsx     # Сообщение + delete + regenerate
│   │   │   │   └── GenerationSettingsModal.tsx  # Модель (5 групп) + 5 слайдеров
│   │   │   ├── characters/
│   │   │   │   └── CharacterForm.tsx     # Форма (name, personality, model, etc.)
│   │   │   └── ui/                       # Button, Input, Avatar
│   │   ├── lib/                     # Утилиты (localStorage)
│   │   └── types/                   # TypeScript типы
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
├── .github/workflows/deploy.yml     # GitHub Actions SSH deploy
├── render.yaml
├── CLAUDE.md
└── CURRENT_STAGE.md
```
