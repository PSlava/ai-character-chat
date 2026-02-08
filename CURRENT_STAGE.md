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
| ANTHROPIC_API_KEY | Да | Нет (нет кредитов) |
| OPENAI_API_KEY | Да | Нет (нет кредитов) |
| GEMINI_API_KEY | Да | Нет (квота = 0) |
| OPENROUTER_API_KEY | Да | **Да** |
| DEEPSEEK_API_KEY | Нужно задать | Прямой API (обходит лимиты OpenRouter) |
| QWEN_API_KEY | Нужно задать | Прямой API через DashScope |
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
- **Генерация персонажа из текста** — вставляешь рассказ, AI создаёт профиль (с выбором рейтинга контента)
- **Выбор AI-модели** — каждая OpenRouter модель доступна индивидуально с оценкой качества (0-10)
- **API реестра моделей** — `GET /api/models/openrouter` отдаёт список моделей с метаданными

### Чат
- Создание чат-сессий с персонажами
- SSE-стриминг ответов (токен за токеном)
- Контекстное окно (sliding window ~12K токенов, до 50 сообщений)
- System prompt собирается из полей персонажа (personality, scenario, examples, content_rating)
- История сообщений сохраняется в БД
- Удаление чатов

### LLM-провайдеры (6 штук)
| Провайдер | Модель по умолчанию | Ключ в Render | Работает |
|-----------|---------------------|---------------|----------|
| OpenRouter | google/gemma-3-27b-it:free | Да | **Да** |
| DeepSeek | deepseek-chat | Нужен | Прямой API (api.deepseek.com) |
| Qwen (DashScope) | qwen3-32b | Нужен | Прямой API (dashscope-intl) |
| Gemini | gemini-2.0-flash | Да | Нет (квота = 0, регион заблокирован) |
| Claude (Anthropic) | claude-sonnet-4-5 | Да | Нет (нет API-кредитов) |
| OpenAI | gpt-4o | Да | Нет (нет кредитов) |

**Рабочие бесплатные модели через OpenRouter:**

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

**Режимы выбора модели:**
- **OpenRouter Auto** — автоматический перебор топ-3 моделей по качеству (с разных провайдеров: Gemma 27B → Nemotron 9B → DeepSeek R1)
- **Конкретная модель** — используется только выбранная, без фолбэков

**Особенности провайдеров:**
- Gemma (Google AI Studio) — не поддерживает `system` role, мерджится в `user`
- Nemotron/DeepSeek — thinking-модели, ответ в поле `reasoning`
- Venice — нестабилен, все модели через него возвращают 429
- Все провайдеры поддерживают HTTP-прокси с авторизацией (настроен)
- Абстракция провайдеров — легко добавить новый
- **Render wake-up** — автоматическое пробуждение сервера перед генерацией (free tier засыпает)

### Фронтенд
- React + TypeScript + Vite + Tailwind CSS
- Тёмная тема
- Zustand для стейт-менеджмента
- 6 страниц: главная, авторизация, персонаж, чат, создание, профиль
- Стриминг сообщений в реальном времени
- Русский интерфейс
- Выбор AI-модели с оценками качества в формах создания персонажа и чата
- Автоматическое пробуждение Render (wake-up) с индикатором статуса

### Инфраструктура
- SQLAlchemy ORM (SQLite локально / PostgreSQL в проде)
- SSL для подключения к Supabase
- Dockerfile для бэкенда
- render.yaml + vercel.json для автодеплоя
- Прокси для обхода региональных ограничений API

## Что нужно доработать

### Высокий приоритет
- [ ] Загрузка аватаров персонажей (сейчас только URL, нет загрузки файлов)
- [ ] Улучшить обработку ошибок на фронтенде
- [ ] Валидация форм (минимальная длина, обязательные поля)

### Средний приоритет
- [ ] Редактирование персонажей через UI (бэкенд есть, фронтенд-страницы нет)
- [ ] Пагинация в каталоге персонажей (бэкенд есть, фронтенд подгружает только первые 20)
- [ ] Кнопка "Удалить чат" в сайдбаре
- [ ] Адаптивный дизайн для мобильных устройств
- [ ] Уведомления/тосты при ошибках и успехах

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
AI:       Anthropic SDK + OpenAI SDK + Google GenAI + OpenRouter
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
│   │   ├── llm/                     # 4 провайдера + реестр
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
