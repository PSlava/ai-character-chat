# AI Character Roleplay Chat — Текущий статус

## Деплой

| Сервис | URL | Статус |
|--------|-----|--------|
| Frontend (Vercel) | https://ai-character-chat-murex.vercel.app | Работает |
| Backend (Render) | https://ai-character-chat-vercel.onrender.com | Работает |
| Database (Supabase) | PostgreSQL через connection pooler | Работает |
| GitHub | https://github.com/PSlava/ai-character-chat | main branch |

## Текущие данные в БД

- **Пользователи**: 1 (test@example.com / testuser)
- **Персонажи**: 1 (Шерлок Холмс, модель: claude)
- **Чаты**: 0

## Env-переменные в Render

| Переменная | Задана | Работает |
|------------|--------|----------|
| DATABASE_URL | Да (Supabase pooler) | Да |
| JWT_SECRET | Да (auto-generated) | Да |
| ANTHROPIC_API_KEY | Да | Нет (нет кредитов) |
| OPENAI_API_KEY | Да | Нет (нет кредитов) |
| GEMINI_API_KEY | Да | Нет (квота = 0) |
| OPENROUTER_API_KEY | **НЕТ** | — |
| DEFAULT_MODEL | gemini | Нужно сменить на openrouter |
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
- **Генерация персонажа из текста** — вставляешь рассказ, AI создаёт профиль

### Чат
- Создание чат-сессий с персонажами
- SSE-стриминг ответов (токен за токеном)
- Контекстное окно (sliding window ~12K токенов, до 50 сообщений)
- System prompt собирается из полей персонажа (personality, scenario, examples, content_rating)
- История сообщений сохраняется в БД
- Удаление чатов

### LLM-провайдеры (4 штуки)
| Провайдер | Модель | Ключ в Render | Работает |
|-----------|--------|---------------|----------|
| OpenRouter | google/gemini-2.0-flash-exp:free | НЕТ — нужно добавить `OPENROUTER_API_KEY` | Нет |
| Gemini | gemini-2.0-flash | Есть | Нет (квота = 0, регион заблокирован) |
| Claude (Anthropic) | claude-sonnet-4-5 | Есть | Нет (нет кредитов) |
| OpenAI | gpt-4o | Есть | Нет (нет кредитов) |

**Блокер: ни один LLM-провайдер сейчас не работает.** Чат и генерация персонажей из текста недоступны.

Решение: добавить `OPENROUTER_API_KEY` в Render → Environment. Ключ берётся бесплатно на https://openrouter.ai/keys

- Все провайдеры поддерживают HTTP-прокси с авторизацией (настроен)
- Абстракция провайдеров — легко добавить новый

### Фронтенд
- React + TypeScript + Vite + Tailwind CSS
- Тёмная тема
- Zustand для стейт-менеджмента
- 6 страниц: главная, авторизация, персонаж, чат, создание, профиль
- Стриминг сообщений в реальном времени
- Русский интерфейс

### Инфраструктура
- SQLAlchemy ORM (SQLite локально / PostgreSQL в проде)
- SSL для подключения к Supabase
- Dockerfile для бэкенда
- render.yaml + vercel.json для автодеплоя
- Прокси для обхода региональных ограничений API

## Что нужно доработать

### Критический (без этого не работает чат)
- [ ] **Добавить `OPENROUTER_API_KEY` в Render** — зарегистрироваться на https://openrouter.ai, создать ключ, добавить в Environment
- [ ] Установить `DEFAULT_MODEL=openrouter` в Render Environment

### Высокий приоритет
- [ ] Загрузка аватаров персонажей (сейчас только URL, нет загрузки файлов)
- [ ] Обработка ошибок на фронтенде (сейчас минимальная)
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
