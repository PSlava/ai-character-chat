# SweetSin — AI Character Roleplay Chat

## Бренд

| Параметр | Значение |
|----------|----------|
| **Название** | SweetSin |
| **Домен** | sweetsin.cc (~$10-12/год) |
| **Слоган EN** | Where fantasy comes alive |
| **Слоган RU** | Где фантазии оживают |
| **Подзаголовок EN** | Where fantasy comes alive. Chat with AI characters — no limits, no filters. |
| **Подзаголовок RU** | Где фантазии оживают. ИИ-персонажи без ограничений и фильтров. |
| **Цветовая схема** | Rose (rose-500/600/700) — ранее purple |
| **Иконка** | Flame (lucide-react) |
| **Логотип** | Текстовый: **Sweet** (белый) + **Sin** (rose-500) |

**SEO (index.html):**
- Title: `SweetSin — AI Character Chat | Roleplay & Fantasy`
- Meta description: Chat with AI characters without limits. Immersive roleplay, uncensored conversations, and endless fantasy.
- Keywords: AI chat, AI roleplay, character AI alternative, NSFW AI chat, AI companion, uncensored AI, roleplay chatbot, AI girlfriend, AI boyfriend, fantasy chat, AI characters, SweetSin
- Open Graph: title, description, type, site_name

**Рассматривались домены (feb 2026):**
- .ai зона (~$50-80/год): naughtai.ai, sweetsin.ai, temptai.ai, darkrose.ai, velvetai.ai — все свободны
- .cc зона (~$10-12/год): sweetsin.cc ✓, naughtai.cc, darkdesire.cc, temptai.cc, lustai.cc, hotchat.cc — все свободны
- .fun зона (~$9/год): naughtai.fun, darkdesire.fun, sweetsin.fun — все свободны
- Заняты: lustchat.fun, lustchat.cc, afterdark.cc, spicychat.fun, spicyai.cc

**Конкуренты для справки:**
| Платформа | Домен | Трафик/мес |
|-----------|-------|------------|
| Character.AI | character.ai | ~200M+ |
| CrushOn.AI | crushon.ai | ~100M |
| SpicyChat.AI | spicychat.ai | ~73M |
| JanitorAI | janitor.ai | ~50M+ |
| Candy.AI | candy.ai | — |
| Chub.AI | chub.ai | — |

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
| nginx | Static frontend + reverse proxy /api → backend + uploads | 80, 443 |
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
| TOGETHER_API_KEY | — | Вручную | Together AI (платный, без модерации) |
| ANTHROPIC_API_KEY | Да | Вручную | Claude (нужны кредиты) |
| OPENAI_API_KEY | Да | Вручную | GPT (нужны кредиты) |
| GEMINI_API_KEY | Да | Вручную | Gemini (квота=0) |
| DEFAULT_MODEL | auto | Настраиваемый | Модель по умолчанию (auto = все провайдеры) |
| AUTO_PROVIDER_ORDER | groq,cerebras,openrouter | Настраиваемый | Порядок провайдеров для auto-fallback |
| ADMIN_EMAILS | — | Вручную | Список email-ов админов (через запятую) |
| PROXY_URL | Да | Вручную | HTTP прокси |
| SMTP_HOST | — | Вручную | SMTP сервер (пусто = ссылка в консоль) |
| SMTP_PORT | — | 587 | SMTP порт |
| SMTP_USER | — | Вручную | SMTP логин |
| SMTP_PASSWORD | — | Вручную | SMTP пароль |
| SMTP_FROM_EMAIL | — | Вручную | Email отправителя |
| FRONTEND_URL | — | http://localhost:5173 | URL фронтенда (для ссылок в email) |
| CORS_ORIGINS | — | * | CORS (по умолч. `*`, можно ограничить через env) |
| UPLOAD_DIR | — | data/uploads | Директория для загруженных файлов |
| MAX_AVATAR_SIZE | — | 4194304 | Макс. размер аватара в байтах (4 МБ) |
| DOMAIN | — | Вручную | Домен для SSL |
| POSTGRES_PASSWORD | — | auto-generated | Пароль PostgreSQL |
| WEBHOOK_SECRET | — | auto-generated | GitHub webhook secret |

## Что сделано

### Аутентификация и роли
- Регистрация и логин по email/пароль
- **Автогенерация username** при регистрации (`user_XXXXXX`), можно сменить в профиле
- JWT-токены (7 дней) с ролью, bcrypt хеширование
- **Роли пользователей**: admin и user
- **ADMIN_EMAILS** — автоназначение роли admin по email (при регистрации и синхронизация при логине)
- **Админ-роль проверяется из БД** (не только из JWT) в `require_admin`
- Защищённые эндпоинты через middleware
- Опциональная авторизация (`get_current_user_optional`) для публичных эндпоинтов
- Хранение токена и роли в localStorage
- **Восстановление пароля** — полный флоу:
  - `POST /api/auth/forgot-password` — всегда возвращает одинаковый ответ (не раскрывает наличие email в БД)
  - JWT-based reset token (1 час, одноразовый — привязан к хешу пароля)
  - Отправка email через SMTP (`aiosmtplib`), в dev-режиме — ссылка выводится в консоль
  - `POST /api/auth/reset-password` — валидация токена, смена пароля
  - Фронтенд: «Забыли пароль?» на странице логина, отдельная страница `/auth/reset-password?token=...`
  - Rate limiting: 3 запроса на сброс за 5 минут на IP

### Персонажи
- Полный CRUD: создание, просмотр, редактирование, удаление (с cascade на чаты)
- **Админ может редактировать и удалять персонажей всех пользователей**
- Каталог публичных персонажей с поиском и фильтрацией по тегам
- Приватные персонажи видны только владельцу в каталоге
- Страница персонажа со статистикой (чаты, лайки), **username создателя как @username**
- Избранное (лайки)
- Рейтинг контента (SFW / Moderate / NSFW)
- **NSFW-фильтрация моделей** — модели без поддержки NSFW отключены в UI и исключены из auto-selection
- **Внешность (Appearance)** — отдельное поле для описания внешности персонажа (включается в system prompt)
- **Шаблонные переменные** — `{{char}}` и `{{user}}` в примерах диалогов заменяются на реальные имена
- **Структурированные теги** — 33 предустановленных тега в 5 категориях (пол, роль, характер, сеттинг, стиль ответов). Каждый тег добавляет свой промпт-сниппет в system prompt. Кликабельные pills в форме создания/редактирования
- **Длина ответа** — настройка на персонаже: короткий / средний / длинный / очень длинный
- **Макс. токенов** — настраиваемый лимит (256–4096, дефолт 2048)
- **Генерация персонажа из текста** — вставляешь рассказ, AI создаёт профиль
- **Выбор AI-модели** — OpenRouter, Groq, Cerebras, Together + прямые провайдеры (DeepSeek, Qwen)
- **API реестра моделей** — `GET /api/models/{openrouter,groq,cerebras,together}`
- **API реестра тегов** — `GET /api/characters/structured-tags` — категории и теги для формы

### Чат
- **Один чат на персонажа** — повторный «Начать чат» открывает существующий, не создаёт дубликат
- SSE-стриминг ответов (токен за токеном)
- Контекстное окно (sliding window, настраиваемый размер: 4K/8K/16K/∞)
- **System prompt (литературный формат):**
  - Динамические инструкции по длине ответа (short/medium/long/very_long)
  - **Структурированные теги** — промпт-сниппеты между personality и appearance
  - **Литературный формат прозы** — нарратив обычным текстом, диалоги через тире (ru) / кавычки (en), `*звёздочки*` ТОЛЬКО для внутренних мыслей
  - **Конкретный пример формата** в промпте — модели следуют примерам лучше, чем абстрактным правилам
  - **Нарратив от третьего лица** — «она сказала», а не «я сказала»; правило в intro, format_rules и rules
  - Show-don't-tell, физические ощущения, анти-шаблонность, запрет повторов
  - Обязательные пустые строки между нарративом, диалогом и мыслями
- **Ленивая подгрузка сообщений** — загружаются последние 20, остальные при скролле вверх (infinite scroll)
- **Отслеживание модели** — каждое сообщение сохраняет `model_used` (напр. `openrouter:google/gemma-3-27b-it:free`)
- **Показ модели для админа** — под каждым ответом ассистента (10px серый текст, только для admin)
- История сообщений сохраняется в БД
- **Удаление чатов** — полное удаление с навигацией на главную
- **Очистка чата** — удаление всех сообщений (кроме приветствия), чат начинается заново
- **Удаление отдельных сообщений** (кроме приветственного)
- **Перегенерация ответа** — кнопка на hover + постоянная кнопка под последним ответом
- **Ошибки в чате** — красные баблы; обычные пользователи видят «Ошибка генерации», админы — полный текст; ошибки модерации видны всем
- **Настройки генерации** — модалка «Модель и настройки» с:
  - Выбор модели (карточки с категориями: OpenRouter / Groq / Cerebras / Together / Прямой API / Платные)
  - Temperature (0–2), Top-P (0–1), Top-K (0–100)
  - Frequency penalty (0–2), Presence penalty (0–2)
  - Макс. токенов (256–4096)
  - **Память** (контекст): 4K / 8K / 16K / ∞
- **Сохранение настроек** — настройки генерации сохраняются в localStorage **per-model** (`model-settings:{modelId}`), модель per-chat (`chat-model:{chatId}`). При смене модели в модалке — слайдеры переключаются на сохранённые настройки этой модели
- **Смена модели mid-chat** — сохраняется в БД на чате
- **Синхронизация ID сообщений** — фронтенд обновляет локальные UUID на реальные из БД (в т.ч. при ошибках)
- **Фильтрация thinking-токенов** — `<think>...</think>` блоки вырезаются из стриминга (Qwen3, DeepSeek R1)

### Аватары
- **Загрузка аватаров** — `POST /api/upload/avatar` (multipart, auth required)
- **Безопасность**: проверка Content-Type, magic bytes (JPEG/PNG/WebP/GIF), настраиваемый лимит (MAX_AVATAR_SIZE, дефолт 4 МБ)
- **Обработка**: Pillow — валидация, ресайз до 512×512, конвертация в WebP (quality=85), EXIF удаляется
- **Хранение**: `data/uploads/avatars/{uuid}.webp`, UUID-имена файлов (нет user-controlled имён)
- **Раздача**: FastAPI StaticFiles (dev) + nginx location (prod) с кэшированием 30 дней
- **Docker**: shared volume `uploads` между backend и nginx
- **Фронтенд**: компонент `AvatarUpload` — кликабельный аватар с overlay камеры, загрузка, preview
- **Интеграция**: форма создания/редактирования персонажа, страница профиля
- **Фон на странице персонажа** — размытый растянутый аватар (blur-3xl, opacity-20)
- **Жизненный цикл файлов** — автоматическое удаление старых файлов при замене аватара (персонаж + профиль), при удалении персонажа, при удалении аккаунта
- **Очистка сирот** — `POST /api/admin/cleanup-avatars` сканирует диск, удаляет файлы не привязанные к БД
- **onError fallback** — компонент Avatar показывает инициалы если картинка не загрузилась

### Админ-панель
- **Шаблоны промптов** — админ может редактировать любой кусок system prompt через UI
  - Defaults хранятся в коде (`prompt_builder.py`), overrides — в БД (`prompt_templates`)
  - Override перекрывает дефолт; кнопка «Сбросить» удаляет override → возврат к дефолту
  - In-memory кэш (60 сек TTL) для минимизации запросов к БД
  - 21 ключ × 2 языка (ru/en): вступление, правила контента, длина ответа, формат с примером, структурированные теги, внешность, правила и др.
  - Страница `/admin/prompts` с табами RU/EN, expandable карточки, метки «Изменён»/«По умолчанию»
- **Seed-персонажи** — 30 готовых персонажей от @sweetsin для непустого каталога
  - Основаны на популярных архетипах конкурентов (SpicyChat, CrushOn, JanitorAI, Chub, WetDreams)
  - 25 NSFW, 5 moderate: вампир, суккуб, мафия, яндере, профессор, демон, сосед, цундере, CEO, оборотень, нэко, тёмная эльфийка, фембой, сводный брат, инкуб, якудза, призрак, дракон, сталкер-бывший, андроид, доминатрикс, байкер, эльф-целитель, sugar mommy, рыцарь, Люцифер, ревнивый парень, ведьма, друг детства, пиратка
  - DALL-E 3 аватары (512×512 WebP, ~1.1MB суммарно) — хранятся в `seed_avatars/`
  - При импорте аватары копируются в `data/uploads/avatars/` с UUID-именами
  - Внутренний пользователь `@sweetsin` (`system@sweetsin.cc`) создаётся автоматически
  - `POST /api/admin/seed-characters` — импорт (409 если уже импортированы)
  - `DELETE /api/admin/seed-characters` — удаление всех персонажей @sweetsin
  - Кнопки «Импортировать» / «Удалить все» на странице админки
- **Очистка файлов** — кнопка для удаления сиротских аватаров (не привязанных к персонажам/пользователям)
- Ссылка в сайдбаре видна только админу

### LLM-провайдеры (9 штук)

| Провайдер | Модели | API | Статус |
|-----------|--------|-----|--------|
| **OpenRouter** | 8 бесплатных моделей (auto-fallback) | openrouter.ai/api/v1 | **Работает** |
| **Groq** | 6 моделей (auto-fallback) | api.groq.com/openai/v1 | **Работает** |
| **Cerebras** | 3 модели (auto-fallback) | api.cerebras.ai/v1 | **Работает** |
| **Together AI** | 7+ моделей (auto-fallback) | api.together.xyz/v1 | **Готов** — платный, нужен ключ |
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
| Nemotron 9B | 0/10 | Да | Исключена из auto-fallback — мешает языки |
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
| Llama 3.3 70B | 7/10 | Нет поддержки penalty — качество снижено |
| Qwen 3 32B | 7/10 | Нет поддержки penalty — качество снижено |
| ZAI GLM 4.7 | 6/10 | — |
| GPT-OSS 120B | 5/10 | Строгая модерация, NSFW заблокирован |

**Cerebras ограничения**: API не поддерживает `frequency_penalty` / `presence_penalty`. Параметры игнорируются. В UI предупреждение для пользователя.

**Платные модели через Together AI (авто-обновление из API):**

| Модель | Качество | Примечание |
|--------|----------|------------|
| Llama 4 Maverick | 9/10 | Лучшая для creative writing |
| Llama 3.3 70B Turbo | 8/10 | Быстрая и качественная |
| Qwen 3 32B | 7/10 | Без модерации DashScope |
| Llama 4 Scout | 7/10 | Новая |
| DeepSeek V3 / R1 | 6/10 | Reasoning |

**Together AI**: платный (pay-per-token, от $0.02/M), OpenAI-совместимый. **Без модерации контента** — Qwen и Llama работают без NSFW-ограничений. Поддерживает все параметры генерации.

**Режимы выбора модели:**
- **Auto (Все провайдеры)** — кросс-провайдерный fallback: Groq → Cerebras → OpenRouter (настраиваемый порядок через `AUTO_PROVIDER_ORDER`). Дефолт для новых персонажей
- **Auto (OpenRouter / Groq / Cerebras / Together)** — автоматический перебор топ-3 по качеству внутри одного провайдера, с NSFW-фильтрацией
- **Конкретная модель** — выбор конкретной модели провайдера (напр. `groq:llama-3.3-70b-versatile`)
- **Прямой провайдер** (DeepSeek, Qwen) — напрямую через API, минуя агрегаторы
- **Авто-обновление реестров** — модели Groq, Cerebras и Together обновляются из API каждый час
- **NSFW-фильтрация** — модели без поддержки NSFW исключаются из auto-selection для NSFW-персонажей
- **`last_model_used`** — провайдеры с auto-fallback отслеживают какая модель реально ответила

**Кулдаун неработающих моделей:**
- Если модель вернула ошибку (429, 402, 404, rate limit) — она исключается из auto-перебора на 15 минут
- Работает для всех четырёх агрегаторов: OpenRouter, Groq, Cerebras, Together
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
- Тёмная тема, **цветовая схема rose** (бренд SweetSin)
- Zustand для стейт-менеджмента
- 9 страниц: главная, авторизация, сброс пароля, персонаж (с размытым фоном аватара), чат, создание, редактирование, профиль (аватар), **админ-промпты**
- **Брендинг**: логотип Sweet+Sin с иконкой Flame, SEO мета-теги, Open Graph
- Стриминг сообщений в реальном времени
- Выбор AI-модели: **Auto (все провайдеры)** / OpenRouter / Groq / Cerebras / Together (с оценками) + DeepSeek + Qwen + платные
- **NSFW-модели визуально отключены** в настройках для NSFW-персонажей
- **Предупреждение Cerebras** — жёлтое предупреждение о неподдержке penalty
- Настройки генерации (модалка с моделью + 6 слайдеров + память)
- Управление сообщениями: удаление, перегенерация, очистка чата (кнопка RotateCcw в шапке)
- **Красивые диалоги подтверждения** — ConfirmDialog (danger/warning) для удаления чата, очистки, удаления сообщения, удаления персонажа
- **Мобильные действия с сообщениями** — вертикальное троеточие (⋮) вместо hover-кнопок, dropdown-меню
- **Дизайн сообщений** — header row (аватар + имя + кнопки действий) над баблом, имя пользователя из профиля
- Автоматическое пробуждение Render (wake-up) с индикатором статуса
- **Профиль**: смена display name, username (с валидацией), языка, удаление аккаунта (danger zone с ConfirmDialog)
- **Age gate (18+)** — полноэкранный оверлей с backdrop blur для неавторизованных, подтверждение в localStorage, отказ → google.com
- **Адаптивная вёрстка**: мобильный sidebar-drawer (hamburger + backdrop), responsive padding, responsive message bubbles (85%/75%), compact chat input

### Безопасность
- **Rate limiting** — in-memory (без зависимостей):
  - Auth (login/register): 10 запросов/мин на IP
  - Сброс пароля: 3 запроса/5 мин на IP
  - Сообщения чата: 20/мин на пользователя
- **Input validation** — Pydantic `Field(max_length=...)` на всех входных данных (schemas)
- **Mass assignment protection** — allowlists (`_ALLOWED_FIELDS`) для `setattr` в characters и users
- **ILIKE injection** — экранирование `%`, `_`, `\` при поиске персонажей
- **HTML sanitization** — `strip_html_tags()` на текстовых полях персонажей и профиля
- **Private character access control** — `GET /characters/{id}` проверяет `is_public` для не-владельцев
- **JWT production check** — блокирует запуск с дефолтным секретом в production
- **SSL certificate verification** — включена для Supabase (CERT_REQUIRED, check_hostname=False для Supabase pooler)
- **CORS** — ограничены `allow_methods` и `allow_headers` (вместо `*`); `CORS_ORIGINS` по умолчанию `*`, настраивается через env
- **Avatar URL validation** — блокирует `javascript:` и `data:` URI (фронтенд), принимает только `https://` и `/api/uploads/`
- **Avatar upload security** — magic bytes проверка, Pillow валидация, UUID-имена, настраиваемый лимит (MAX_AVATAR_SIZE, дефолт 4 МБ), WebP-конвертация
- **Age gate (18+)** — полноэкранный оверлей для неавторизованных пользователей, подтверждение возраста сохраняется в localStorage
- **SSE safety** — `JSON.parse` в try/catch, localStorage в try/catch

### Инфраструктура
- SQLAlchemy ORM (SQLite локально / PostgreSQL в проде)
- Авто-миграции: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` при старте (отдельные транзакции)
- SSL для подключения к Supabase (CERT_REQUIRED, check_hostname=False для pooler)
- **Файловое хранилище** — `data/uploads/` с Docker volume, nginx раздача с кэшированием
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
- [x] Структурированные теги — 33 тега в 5 категориях с промпт-сниппетами
- [x] Литературный формат прозы — переписан system prompt с конкретным примером
- [x] Адаптивный дизайн для мобильных устройств (sidebar drawer, responsive padding, compact chat)
- [x] Мобильные действия с сообщениями (tap-friendly menu вместо hover)
- [x] Красивые диалоги подтверждения (ConfirmDialog для всех деструктивных действий)
- [x] Ребрендинг — SweetSin (логотип, цвета, SEO, слоган, OG-теги)
- [ ] Зарегистрировать домен sweetsin.cc
- [ ] Настроить DNS и SSL для sweetsin.cc на VPS
- [x] Загрузка аватаров персонажей и пользователей (POST /api/upload/avatar, Pillow → WebP 512x512)
- [ ] Протестировать качество ответов с новым литературным форматом промпта на разных моделях

### Средний приоритет
- [ ] Пагинация в каталоге персонажей (бэкенд есть, фронтенд подгружает только первые 20)
- [ ] Уведомления/тосты при ошибках и успехах
- [ ] Валидация форм (минимальная длина, обязательные поля)
- [ ] Больше структурированных тегов (расширить реестр, добавить новые категории)
- [ ] Favicon (SVG flame icon в rose цвете)
- [ ] Landing page / hero section с примерами персонажей
- [ ] Социальные мета-теги (og:image — preview card)

### Низкий приоритет (будущее)
- [ ] OAuth авторизация (Google, GitHub)
- [ ] Модерация контента
- [ ] Аналитика (популярные персонажи, активность)
- [ ] Экспорт/импорт персонажей (совместимость с SillyTavern формат)
- [ ] WebSocket вместо SSE для двустороннего общения
- [ ] Групповые чаты (несколько персонажей)
- [ ] Голосовые сообщения (TTS)
- [ ] Система отзывов/рейтингов персонажей
- [ ] Монетизация (подписка, токены)

## Стек технологий

```
Backend:  Python 3.12 + FastAPI + SQLAlchemy + PyJWT + bcrypt + Pillow + gunicorn + uvicorn
Frontend: React 18 + TypeScript + Vite + Tailwind CSS + Zustand + i18next
Database: PostgreSQL 16 (Docker) / Supabase (облако) / SQLite (локально)
AI:       OpenRouter + Groq + Cerebras + Together + DeepSeek + Qwen/DashScope + Anthropic + OpenAI + Google GenAI
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
│   │   ├── auth/                    # JWT аутентификация + роли + rate limiting
│   │   │   ├── router.py            # register, login, forgot-password, reset-password
│   │   │   ├── middleware.py        # get_current_user (с role), get_current_user_optional
│   │   │   └── rate_limit.py        # In-memory rate limiter (auth, messages, reset)
│   │   ├── admin/                   # Админ-панель
│   │   │   ├── router.py            # CRUD промпт-шаблонов + seed import/delete + cleanup-avatars (admin only)
│   │   │   ├── seed_data.py         # 30 seed-персонажей (определения)
│   │   │   └── seed_avatars/        # 30 DALL-E 3 аватаров (00–29.webp, 512×512)
│   │   ├── characters/              # CRUD + генерация из текста + структурированные теги
│   │   │   ├── router.py            # API endpoints (admin bypass) + GET /structured-tags
│   │   │   ├── service.py           # Бизнес-логика (is_admin)
│   │   │   ├── schemas.py           # Pydantic модели
│   │   │   ├── serializers.py       # ORM → dict (username в profiles)
│   │   │   └── structured_tags.py   # Реестр 33 тегов × 5 категорий (с промпт-сниппетами ru/en)
│   │   ├── chat/                    # SSE стриминг, контекст
│   │   │   ├── router.py            # send_message (SSE + model_used), delete, clear
│   │   │   ├── service.py           # Контекстное окно, сохранение (model_used)
│   │   │   ├── schemas.py           # SendMessageRequest (model, temp, top_p, context_limit, etc.)
│   │   │   └── prompt_builder.py    # Defaults + DB overrides, 21 ключ × ru/en, литературный формат с примером, 60s cache
│   │   ├── llm/                     # 9 провайдеров + реестр + модели + кулдаун
│   │   │   ├── base.py              # BaseLLMProvider, LLMConfig (+ content_rating)
│   │   │   ├── registry.py          # init_providers + get_provider
│   │   │   ├── model_cooldown.py    # 15-мин кулдаун для неработающих моделей
│   │   │   ├── openrouter_provider.py  # OpenRouter (auto-fallback, last_model_used)
│   │   │   ├── openrouter_models.py    # Реестр моделей с quality + nsfw
│   │   │   ├── groq_provider.py        # Groq (auto-fallback, last_model_used)
│   │   │   ├── groq_models.py          # Реестр моделей Groq + NSFW_BLOCKED
│   │   │   ├── cerebras_provider.py    # Cerebras (auto-fallback, last_model_used)
│   │   │   ├── cerebras_models.py      # Реестр моделей Cerebras + NSFW_BLOCKED
│   │   │   ├── together_provider.py     # Together AI (auto-fallback, платный, без модерации)
│   │   │   ├── together_models.py       # Реестр моделей Together (7+ моделей, quality scores)
│   │   │   ├── deepseek_provider.py    # DeepSeek прямой API
│   │   │   ├── qwen_provider.py        # Qwen/DashScope + модерация
│   │   │   ├── anthropic_provider.py   # Claude
│   │   │   ├── openai_provider.py      # GPT-4o
│   │   │   ├── gemini_provider.py      # Gemini
│   │   │   ├── thinking_filter.py      # ThinkingFilter для <think> блоков
│   │   │   └── router.py              # GET /api/models/{openrouter,groq,cerebras,together}
│   │   ├── uploads/                 # Загрузка файлов (аватары)
│   │   │   └── router.py            # POST /api/upload/avatar (Pillow, magic bytes, WebP)
│   │   ├── users/                   # Профиль (username update), избранное, удаление аккаунта
│   │   ├── utils/                   # Утилиты
│   │   │   ├── sanitize.py          # HTML strip_tags (defense-in-depth)
│   │   │   └── email.py             # Async email sender (SMTP + dev console fallback)
│   │   └── db/                      # Модели, сессии, миграции
│   │       ├── models.py            # User (role), Character, Chat, Message (model_used), Favorite, PromptTemplate
│   │       └── session.py           # Engine, init_db + auto-migrations
│   ├── scripts/
│   │   └── generate_seed_avatars.py # Генерация аватаров через DALL-E 3
│   ├── requirements.txt
│   ├── Dockerfile                   # gunicorn + uvicorn workers
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                     # HTTP клиент, API функции
│   │   │   ├── client.ts            # Axios с JWT
│   │   │   ├── admin.ts             # Промпт-шаблоны + seed import/delete + cleanup (admin)
│   │   │   ├── characters.ts        # CRUD + generate + wake-up + models
│   │   │   ├── users.ts             # Profile (username, role), deleteAccount
│   │   │   ├── uploads.ts           # uploadAvatar (multipart)
│   │   │   └── chat.ts              # chats, messages, delete, clear
│   │   ├── hooks/
│   │   │   ├── useAuth.ts           # Авторизация
│   │   │   └── useChat.ts           # SSE стриминг + GenerationSettings + model_used
│   │   ├── store/                   # Zustand (auth с role, chat)
│   │   ├── pages/                   # 10 страниц
│   │   │   ├── AuthPage.tsx         # Вход / регистрация / забыли пароль (3 режима)
│   │   │   ├── ResetPasswordPage.tsx # Установка нового пароля (по ссылке из email)
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
│   │   │   │   └── GenerationSettingsModal.tsx  # Модель (7 групп) + 6 слайдеров + память
│   │   │   ├── characters/
│   │   │   │   └── CharacterForm.tsx     # Форма (name, personality, structured tags pills, appearance, model, NSFW disable)
│   │   │   └── ui/                       # Button, Input, Avatar, AvatarUpload, AgeGate, ConfirmDialog, LanguageSwitcher
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
├── docker-compose.yml               # PostgreSQL + Backend + Nginx + Webhook + uploads volume
├── .env.example                     # Шаблон переменных (cp → .env → nano → setup --auto)
├── render.yaml
├── CLAUDE.md
└── CURRENT_STAGE.md
```
