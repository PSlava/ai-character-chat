# AI Character Roleplay Chat — Текущий статус

## Деплой

| Сервис | URL | Статус |
|--------|-----|--------|
| Frontend (Vercel) | https://ai-character-chat-murex.vercel.app | Работает |
| Backend (Render) | https://ai-character-chat-vercel.onrender.com | Работает |
| Database (Supabase) | PostgreSQL через connection pooler | Работает |
| GitHub | https://github.com/PSlava/ai-character-chat | main branch |

## Env-переменные в Render

| Переменная | Задана | Работает |
|------------|--------|----------|
| DATABASE_URL | Да (Supabase pooler) | Да |
| JWT_SECRET | Да (auto-generated) | Да |
| OPENROUTER_API_KEY | Да | **Да** |
| DEEPSEEK_API_KEY | Нужно задать | Прямой API (api.deepseek.com) |
| QWEN_API_KEY | Нужно задать | Прямой API (dashscope-intl.aliyuncs.com) |
| ANTHROPIC_API_KEY | Да | Нет (нужны API-кредиты, Claude Pro не даёт доступа к API) |
| OPENAI_API_KEY | Да | Нет (нет кредитов) |
| GEMINI_API_KEY | Да | Нет (квота = 0, регион заблокирован) |
| DEFAULT_MODEL | qwen | Работает |
| PROXY_URL | Да | Да |
| CORS_ORIGINS | Да | Да |
| ENVIRONMENT | production | Да |

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
- **Выбор AI-модели** — OpenRouter модели + прямые провайдеры (DeepSeek, Qwen) с оценкой качества
- **API реестра моделей** — `GET /api/models/openrouter` отдаёт список моделей с метаданными

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
  - Выбор модели (карточки с категориями: бесплатные / прямые API / платные)
  - Temperature (0–2)
  - Top-P (0–1)
  - Top-K (0–100)
  - Frequency penalty (0–2)
  - Макс. токенов (256–4096)
- **Смена модели mid-chat** — сохраняется в БД на чате
- **Синхронизация ID сообщений** — фронтенд обновляет локальные UUID на реальные из БД (фикс удаления)
- **Фильтрация thinking-токенов** — `<think>...</think>` блоки вырезаются из стриминга (Qwen3, DeepSeek R1)

### LLM-провайдеры (6 штук)

| Провайдер | Модель по умолчанию | API | Статус |
|-----------|---------------------|-----|--------|
| **OpenRouter** | gemma-3-27b-it:free | openrouter.ai/api/v1 | **Работает** — 8 бесплатных моделей |
| **DeepSeek** | deepseek-chat | api.deepseek.com/v1 | **Готов** — нужен DEEPSEEK_API_KEY |
| **Qwen (DashScope)** | qwen3-32b | dashscope-intl.aliyuncs.com | **Готов** — нужен QWEN_API_KEY |
| Gemini | gemini-2.0-flash | generativelanguage.googleapis.com | Не работает (квота = 0) |
| Claude | claude-sonnet-4-5 | api.anthropic.com | Не работает (нужны API-кредиты) |
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

**Прямые провайдеры (обходят лимиты OpenRouter):**

| Провайдер | Модели | Бесплатный доступ |
|-----------|--------|-------------------|
| DeepSeek | `deepseek-chat`, `deepseek-reasoner` (thinking) | 5M токенов при регистрации |
| Qwen | `qwen3-32b`, `qwen3-235b-a22b`, `qwen3-14b`, `qwen3-8b` | Free tier через DashScope |

**Режимы выбора модели:**
- **OpenRouter Auto** — автоматический перебор топ-3 по качеству с разных провайдеров (Gemma 27B → Nemotron 9B → DeepSeek R1)
- **Конкретная OpenRouter модель** — только выбранная, без фолбэков
- **Прямой провайдер** (DeepSeek, Qwen) — напрямую через API, минуя OpenRouter

**Особенности провайдеров:**
- Gemma (Google AI Studio) — не поддерживает `system` role, мерджится в `user`
- Nemotron/DeepSeek R1 — thinking-модели, ответ в поле `reasoning`/`reasoning_content`
- DeepSeek-reasoner — thinking-модель, ответ в `reasoning_content`
- Venice — нестабилен, все модели через него возвращают 429
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
- Выбор AI-модели: OpenRouter (с оценками качества) + DeepSeek + Qwen + платные
- Настройки генерации (модалка с моделью + 5 слайдеров)
- Управление сообщениями: удаление, перегенерация, очистка чата
- Автоматическое пробуждение Render (wake-up) с индикатором статуса

### Инфраструктура
- SQLAlchemy ORM (SQLite локально / PostgreSQL в проде)
- Авто-миграции: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` при старте (отдельные транзакции)
- SSL для подключения к Supabase
- Dockerfile для бэкенда
- render.yaml + vercel.json для автодеплоя
- Прокси для обхода региональных ограничений API

## Что нужно доработать

### Высокий приоритет
- [ ] Задать DEEPSEEK_API_KEY и QWEN_API_KEY в Render
- [ ] Загрузка аватаров персонажей (сейчас только URL, нет загрузки файлов)

### Средний приоритет
- [ ] Пагинация в каталоге персонажей (бэкенд есть, фронтенд подгружает только первые 20)
- [ ] Адаптивный дизайн для мобильных устройств
- [ ] Уведомления/тосты при ошибках и успехах
- [ ] Валидация форм (минимальная длина, обязательные поля)

### Низкий приоритет (будущее)
- [ ] OAuth авторизация (Google, GitHub)
- [ ] Загрузка файлов через Supabase Storage
- [ ] Модерация контента
- [ ] Аналитика (популярные персонажи, активность)
- [ ] Экспорт/импорт персонажей
- [ ] WebSocket вместо SSE для двустороннего общения
- [ ] Групповые чаты (несколько персонажей)
- [ ] Голосовые сообщения (TTS)
- [ ] Система отзывов/рейтингов персонажей

## Стек технологий

```
Backend:  Python 3.12 + FastAPI + SQLAlchemy + PyJWT + bcrypt
Frontend: React 18 + TypeScript + Vite + Tailwind CSS + Zustand
Database: PostgreSQL (Supabase) / SQLite (локально)
AI:       OpenRouter + DeepSeek + Qwen/DashScope + Anthropic + OpenAI + Google GenAI
Streaming: SSE (Server-Sent Events)
Deploy:   Vercel (фронт) + Render (бэк) + Supabase (БД)
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
│   │   ├── llm/                     # 6 провайдеров + реестр + модели
│   │   │   ├── base.py              # BaseLLMProvider, LLMConfig, LLMMessage
│   │   │   ├── registry.py          # init_providers + get_provider
│   │   │   ├── openrouter_provider.py  # OpenRouter (8 бесплатных моделей)
│   │   │   ├── openrouter_models.py    # Реестр моделей с quality scores
│   │   │   ├── deepseek_provider.py    # DeepSeek прямой API
│   │   │   ├── qwen_provider.py        # Qwen/DashScope прямой API
│   │   │   ├── anthropic_provider.py   # Claude
│   │   │   ├── openai_provider.py      # GPT-4o
│   │   │   ├── gemini_provider.py      # Gemini
│   │   │   ├── thinking_filter.py      # ThinkingFilter для <think> блоков
│   │   │   └── router.py              # GET /api/models/openrouter
│   │   ├── users/                   # Профиль, избранное
│   │   └── db/                      # Модели, сессии, миграции
│   │       ├── models.py            # User, Character, Chat, Message, Favorite
│   │       └── session.py           # Engine, init_db + auto-migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                     # HTTP клиент, API функции
│   │   │   ├── client.ts            # Axios с JWT
│   │   │   ├── characters.ts        # CRUD + generate + wake-up
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
│   │   │   │   └── GenerationSettingsModal.tsx  # Модель + 5 слайдеров
│   │   │   ├── characters/
│   │   │   │   └── CharacterForm.tsx     # Форма (name, personality, response_length, max_tokens, model, etc.)
│   │   │   └── ui/                       # Button, Input, Avatar
│   │   ├── lib/                     # Утилиты (localStorage)
│   │   └── types/                   # TypeScript типы
│   ├── vercel.json
│   └── package.json
├── render.yaml
├── CLAUDE.md
└── CURRENT_STAGE.md
```
