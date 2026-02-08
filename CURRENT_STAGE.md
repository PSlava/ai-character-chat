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
| DEFAULT_MODEL | openrouter | Работает (Auto — перебор по качеству) |
| PROXY_URL | Да | Да |
| CORS_ORIGINS | Да | Да |
| ENVIRONMENT | production | Да |

## Что сделано

### Аутентификация
- Регистрация и логин по email/username/пароль
- JWT-токены (30 дней), bcrypt хеширование
- Защищённые эндпоинты через middleware
- Хранение токена в localStorage

### Персонажи
- Полный CRUD: создание, просмотр, редактирование, удаление
- Каталог публичных персонажей с поиском и фильтрацией по тегам
- Страница персонажа со статистикой (чаты, лайки)
- Избранное (лайки)
- Рейтинг контента (SFW / Moderate / NSFW)
- **Генерация персонажа из текста** — вставляешь рассказ, AI создаёт профиль (с выбором рейтинга контента, модели и дополнительных пожеланий)
- **Выбор AI-модели** — все OpenRouter модели + прямые провайдеры (DeepSeek, Qwen) с оценкой качества
- **API реестра моделей** — `GET /api/models/openrouter` отдаёт список моделей с метаданными

### Чат
- Создание чат-сессий с персонажами
- SSE-стриминг ответов (токен за токеном)
- Контекстное окно (sliding window ~12K токенов, до 50 сообщений)
- System prompt собирается из полей персонажа (personality, scenario, examples, content_rating)
- История сообщений сохраняется в БД
- Удаление чатов

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
- Все провайдеры поддерживают HTTP-прокси с авторизацией
- **Render wake-up** — автоматическое пробуждение сервера перед генерацией (free tier засыпает)

### Фронтенд
- React + TypeScript + Vite + Tailwind CSS
- Тёмная тема
- Zustand для стейт-менеджмента
- 6 страниц: главная, авторизация, персонаж, чат, создание, профиль
- Стриминг сообщений в реальном времени
- Русский интерфейс
- Выбор AI-модели: OpenRouter (с оценками качества) + DeepSeek + Qwen + платные
- Автоматическое пробуждение Render (wake-up) с индикатором статуса

### Инфраструктура
- SQLAlchemy ORM (SQLite локально / PostgreSQL в проде)
- SSL для подключения к Supabase
- Dockerfile для бэкенда
- render.yaml + vercel.json для автодеплоя
- Прокси для обхода региональных ограничений API

## Что нужно доработать

### Высокий приоритет
- [ ] Задать DEEPSEEK_API_KEY и QWEN_API_KEY в Render
- [ ] Загрузка аватаров персонажей (сейчас только URL, нет загрузки файлов)
- [ ] Улучшить обработку ошибок на фронтенде

### Средний приоритет
- [ ] Редактирование персонажей через UI (бэкенд есть, фронтенд-страницы нет)
- [ ] Пагинация в каталоге персонажей (бэкенд есть, фронтенд подгружает только первые 20)
- [ ] Кнопка "Удалить чат" в сайдбаре
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
│   │   ├── characters/              # CRUD + генерация из текста
│   │   ├── chat/                    # SSE стриминг, контекст
│   │   ├── llm/                     # 6 провайдеров + реестр + модели
│   │   │   ├── base.py              # BaseLLMProvider (абстракция)
│   │   │   ├── registry.py          # Инициализация и реестр провайдеров
│   │   │   ├── openrouter_provider.py  # OpenRouter (8 бесплатных моделей)
│   │   │   ├── openrouter_models.py    # Реестр моделей с quality scores
│   │   │   ├── deepseek_provider.py    # DeepSeek прямой API
│   │   │   ├── qwen_provider.py        # Qwen/DashScope прямой API
│   │   │   ├── anthropic_provider.py   # Claude
│   │   │   ├── openai_provider.py      # GPT-4o
│   │   │   ├── gemini_provider.py      # Gemini
│   │   │   └── router.py              # GET /api/models/openrouter
│   │   ├── users/                   # Профиль, избранное
│   │   └── db/                      # Модели, сессии
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                     # HTTP клиент, API функции
│   │   ├── hooks/                   # useAuth, useChat (SSE)
│   │   ├── store/                   # Zustand (auth, chat)
│   │   ├── pages/                   # 6 страниц
│   │   ├── components/              # UI, чат, персонажи, layout
│   │   ├── lib/                     # Утилиты
│   │   └── types/                   # TypeScript типы
│   ├── vercel.json
│   └── package.json
├── render.yaml
├── CLAUDE.md
└── CURRENT_STAGE.md
```
