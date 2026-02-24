# AI Bot Battle Arena — полное исследование

## Оглавление
1. [Анализ CATS: Crash Arena Turbo Stars](#1-анализ-cats)
2. [Аналоги и конкуренты](#2-аналоги-и-конкуренты)
3. [AI-driven battle games — текущий рынок](#3-ai-driven-battle-games)
4. [Анализ рынка и востребованности](#4-анализ-рынка-и-востребованности)
5. [Web vs Mobile App — сравнительный анализ](#5-web-vs-mobile-app)
6. [Расширенный функционал](#6-расширенный-функционал)
7. [Концепция веб-игры с AI](#7-концепция-веб-игры-с-ai)
8. [Техническая архитектура](#8-техническая-архитектура)
9. [Монетизация](#9-монетизация)
10. [MVP план](#10-mvp-план)
11. [Оценка целесообразности](#11-оценка-целесообразности)

---

## 1. Анализ CATS

### Суть игры
CATS (ZeptoLab, 2017) — асинхронный авто-баттлер. Игроки собирают боевые машины из запчастей и выставляют на автоматические бои. **Ноль управления во время боя** — весь скилл в фазе сборки. 200M+ скачиваний, #1 в 20 странах.

### Система сборки

| Компонент | Количество | Роль |
|-----------|-----------|------|
| **Шасси** (8 типов) | 1 | Форма, HP, слоты, физика (центр тяжести, клин, стабильность) |
| **Оружие** (13 типов) | 1-3 | Урон: melee (blade, drill, chainsaw) и ranged (rocket, laser, minigun) |
| **Колёса** (10 типов) | 2-3 | Подвижность, HP колеса, сцепление |
| **Гаджеты** (9 типов) | 0-1 | Утилита: booster, repulse, lifter, harpoon, shield, freeze |

Ключевое: **форма шасси определяет физику боя**. Клиновидный Pyramid заезжает под высокий Titan и переворачивает; круглый Boulder хаотично прыгает; низкий Sneaky трудно перевернуть.

### Механика боя
- **2D физика сбоку**, реалистичные столкновения (гравитация, импульс, трение)
- Машины стартуют с двух сторон, едут навстречу
- Оружие активируется автоматически (melee при контакте, ranged по таймеру)
- **Победа**: HP до 0 ИЛИ противник касается стены. Арена сужается при затягивании
- **Длительность боя: 3-15 секунд**

### Прогрессия
1. **Championship** — 24 стадии, брекеты по 15 игроков
2. **Quick Battles** — PvP лестница, серии побед, рейтинг
3. **Leagues** — 7 тиров (Wood -> Platinum), 3-дневные циклы
4. **Prestige** — сброс + новый контент, до 250 раз

### Что делает аддиктивной
1. **Ультра-короткие бои** (3-15 сек) -> "ещё один"
2. **Голова > пальцы** — нет twitch-скилла, широкая аудитория
3. **Рандомность физики** — одинаковые билды дают слегка разные результаты
4. **Комбинаторика**: 8 x 13 x 10 x 9 = сотни билдов
5. **Асинхронный PvP** — не нужно ждать оппонента
6. **Визуальный спектакль** — машины переворачиваются, прыгают, взрываются
7. **Clash Royale таймеры** — лутбоксы на таймере создают привычку

### Текущее состояние CATS (2025)
- Доход: **~$160K/мес** (iOS $100K + Android $60K), ~140K скачиваний/мес
- **ZeptoLab продала CATS + King of Thieves компании Nazara за $7.7M** (январь 2025)
- Игра на закате, но модель доказана: 200M+ скачиваний за жизненный цикл

---

## 2. Аналоги и конкуренты

### 2.1 Авто-баттлеры (Configure -> Watch)

| Игра | Фаза сборки | Фаза боя | Длительность | MAU |
|------|------------|----------|-------------|-----|
| **TFT** (Riot) | Покупка юнитов, позиция на гексах, аугменты | Авто ~30с | 30-40 мин | **33M MAU** |
| **HS Battlegrounds** | Набор миньонов из таверны | Авто ~10-15с | 20-30 мин | **2.2-2.6M MAU** |
| **Super Auto Pets** | Покупка питомцев/еды, порядок | Лево-vs-право ~5с | 10-15 мин | ~540 concurrent (Steam) |
| **Mechabellum** | Расстановка мехов | Марш + бой ~30-60с | 20-30 мин | ~7.8K peak |
| **Backpack Battles** | Тетрис-инвентарь | Авто ~10-15с | 15-20 мин | Вышла 1.0 (июнь 2025) |
| **CATS** | Drag-drop запчастей | Физика 3-15с | Секунды | ~140K downloads/мес |

### 2.2 Игры с программированием ботов

| Игра | Механика | Платформа |
|------|---------|-----------|
| **Gladiabots** | Визуальное программирование деревьев поведения | PC/Mobile/Web |
| **Battlesnake** | HTTP API, 500мс на ход, любой язык | Web |
| **Screeps** | JavaScript MMO RTS | Web |
| **CodinGame** | Бот-программирование, лиги | Web |
| **Yare.io** | JavaScript RTS в браузере | Web |

### 2.3 AI/LLM батл-игры (новая категория)

| Игра | Механика | Статус |
|------|---------|--------|
| **TextBattle** | Предложение -> SD генерит персонажа -> LLM бой | Mobile/Web |
| **LLM Fighter** | Два LLM-агента дерутся (5 скиллов, tool calls) | Open source |
| **Prompt Wars** | Промпты конкурируют за контроль LLM | Web |
| **Tensor Trust** | Prompt injection атака/защита | Web, 1M+ игроков |

### 2.4 Состояние конкуренции

**Winner-take-most консолидация**: TFT (33M MAU) и HS Battlegrounds доминируют. Standalone провалы: Dota Underlords (заброшена, -93% игроков), Auto Chess (снижение).

**Суб-жанр "build your bot" (CATS-like) пуст**. CATS продана за $7.7M (низкая оценка), значимого преемника нет. С 200M+ скачиваниями за жизнь — спрос доказан, но ниша свободна.

---

## 3. AI-driven battle games

### Где AI добавляет ценность

| Применение | Тип AI | Задержка | Целесообразность |
|-----------|--------|---------|-----------------|
| **Нарратив/комментарий боя** | LLM | 500мс-3с | Высокая — уникальный опыт |
| **Генерация ботов/контента** | LLM | 2-5с | Высокая — бесконечный контент |
| **Определение исхода** | Физика/правила | <1мс | Обязательно — детерминированность |
| **Советы по сборке** | LLM | 1-3с | Средняя — premium фича |
| **NL стратегия бота** | LLM -> параметры | 1-2с | Высокая — уникальная механика |
| **Адаптивные боссы** | LLM + анализ меты | 5-10с | Средняя — еженедельные ивенты |

### Критический инсайт: отношение игроков к AI

**85% геймеров негативно относятся к "генеративному AI" в играх** (Quantic Foundry, 2025). 62% — "очень негативно". Хуже, чем блокчейн (79% негатива).

**НО**: конкретные AI-фичи принимаются хорошо:
- Динамическая сложность — **>50% позитивно** (единственная "позитивная" AI-фича)
- Умные/адаптивные NPC — 34% хотят
- Мир, который "живёт" — 37% хотят

**Вывод**: использовать AI под капотом, **никогда не маркетировать как "AI-powered"**. Продавать опыт, не технологию.

---

## 4. Анализ рынка и востребованности

### 4.1 Размер рынков

| Рынок | 2024-2025 | Прогноз | CAGR |
|-------|----------|---------|------|
| **Авто-баттлеры** | $2.47B | $7.87B (2033) | 14.2% |
| **Мобильные игры** | $144-307B | Рост | 8-12% |
| **HTML5/Web игры** | $1.89-5.66B | $3.92-10.42B (2034) | 6.3-16.7% |
| **AI в играх** | $3.28-5.85B | $37-51B (2033) | 20.5-42.3% |
| **PWA рынок** | $2.08-3.53B | $21.24B (2033) | **29.9%** |
| **Casual online** | $20.57B | Рост | ~5% |

### 4.2 Web-гейминг платформы (трафик 2025-2026)

| Платформа | Трафик/мес | Ключевые метрики |
|----------|-----------|-----------------|
| **Poki** | 150M визитов, 100M MAU | 1B gameplays/мес, рост дохода 50%/год |
| **itch.io** | 118.7M визитов | 8:27 средняя сессия |
| **CrazyGames** | 77.9M визитов | 14:15 сессия, рост 100%+/год, прибыльна |

**Топ разработчики на Poki зарабатывают до $1M/год**. Средний диапазон: $50K-$1M/год.

### 4.3 Демография игроков

| Метрика | Значение |
|---------|---------|
| Основная группа | **18-34** (36% US геймеров) |
| Гендер (overall) | 47% женщин, 52% мужчин |
| Strategy/competitive скью | Мужчины +13.6% к Action |
| Медиана сессии (mobile) | **5-6 минут** |
| Медиана daily playtime | **22 минуты** |
| Casual сессии (2025) | 26 мин (+15% YoY) |

### 4.4 Ретеншн бенчмарки (mobile, 2025)

| Метрика | Медиана | Top 25% | Лучшие |
|---------|---------|---------|--------|
| **D1** | 25-27% | 31-33% | 40-50% |
| **D7** | 3.4-3.9% | 7-8% | 15-20% |
| **D28** | <3% | ~5% | 8-10% |

**Gamification elements (стрики, бейджи, лидерборды) увеличивают D30 на 15-30%.**

### 4.5 Рыночные возможности (gap analysis)

| Ниша | Статус | Возможность |
|------|--------|------------|
| Web/browser авто-баттлер | **Пусто** | Нет ни одного значимого конкурента |
| Bot-building (CATS-like) | **Пусто** после ухода CATS | 200M+ downloads доказали спрос |
| Short-session авто-баттлер | Мало (TFT=30-40 мин, слишком долго) | Sweet spot: 5-15 мин |
| AI-enhanced игры | **Пусто** в consumer space | TextBattle ближайший, но без глубины |
| Async PvP web game | **Очень мало** | Идеален для web (нет realtime) |

---

## 5. Web vs Mobile App

### 5.1 Ключевые метрики

| Фактор | Web | Mobile Native |
|--------|-----|---------------|
| **Стоимость привлечения** | $0.10-$1.00 CPC | **$2.97-$5.50 CPI** |
| **100K юзеров UA бюджет** | $10K-$50K | **$300K+** |
| **Время клик→игра** | **2-5 секунд** | 2-10 минут |
| **Конверсия клик→игра** | ~100% (page load) | **4.47%** (app store median) |
| **Комиссия платформы** | 2.9% (Stripe) | **15-30%** (Apple/Google) |
| **Кодовых баз** | **1** | 2-3 (iOS + Android + API) |
| **Деплой/хотфикс** | **Минуты** | Дни (store review) |
| **Push уведомления** | Слабые на iOS | Сильные |
| **Ad eCPM (rewarded)** | $5-$20 | **$10-$50** |
| **ARPU** | $5-$30/год (ad-supported) | **$60-$124/год** |
| **Стоимость разработки** | **$50K-$150K** | $100K-$300K |
| **Time to MVP** | **2-3 месяца** | 4-6 месяцев |

### 5.2 Преимущества Web

1. **Zero-friction sharing**: ссылка = игра. В Discord/Reddit/Twitter/Telegram — клик и играешь. Mobile теряет 95%+ между кликом и установкой
2. **В 5-50x дешевле UA**: не нужно платить за установки. Органический трафик через SEO, порталы (Poki, CrazyGames), социальные платформы
3. **Нет 30% налога**: Stripe 2.9% vs Apple/Google 15-30%. На $100K дохода разница = $27K
4. **Мгновенные обновления**: без app store review. Критично для баланс-патчей и live-ops
5. **Один кодовая база**: web работает на всех устройствах. Экономия 50% на разработке и поддержке
6. **Стриминг-дружественность**: Twitch/YouTube зритель может сразу играть по ссылке (Super Auto Pets взлетела именно так)
7. **Telegram Mini Apps**: 900M+ юзеров Telegram, нулевая стоимость дистрибуции
8. **Facebook Instant Games**: 250M+ MAU

### 5.3 Преимущества Mobile Native

1. **Push уведомления**: критично для PvP ("Твой бой готов!", "Тебя атаковали!"). На iOS PWA — только если добавлен на home screen (4+ тапа)
2. **Более высокий ARPU**: привычка платить в app store, one-tap покупки, подписки с авто-продлением
3. **Более высокий ad CPM**: mobile rewarded video $10-$50 vs web $5-$20
4. **Лучший retention**: push + app icon на рабочем столе = напоминание вернуться
5. **App Store visibility**: discovery через чарты и featuring (хотя organic discovery = ~35%)
6. **Haptics**: тактильная обратная связь при боях (вибрация при столкновении)

### 5.4 Прецеденты: Web-first успехи

| Игра | Путь | Результат |
|------|------|-----------|
| **Agar.io** | Browser -> mobile | Миллионы игроков, куплена Miniclip |
| **Slither.io** | Browser -> mobile | Top-10 mobile charts |
| **Vampire Survivors** | itch.io -> Steam -> mobile | **~$50M+** выручки |
| **Super Auto Pets** | itch.io -> Steam -> mobile | 1M+ Google Play, стримеры (Northernlion, Ludwig) |
| **Krunker.io** | Browser | **1.2M daily**, полная esports сцена |
| **Hordes.io** | Browser | Solo dev живёт с дохода |

**Паттерн**: web = engine discovery/virality, затем mobile = engine monetization.

### 5.5 Рекомендация: Web-First + Capacitor Wrapper

```
Фаза 1 (мес 1-6): Web Launch
├── TypeScript + WASM + WebGL/Canvas
├── Дистрибуция: порталы, Reddit, Discord, Telegram
├── Монетизация: Stripe IAP (2.9%) + rewarded ads
├── Итерация: мгновенные деплои
└── Стоимость: $50K-$150K (2-4 чел)

Фаза 2 (мес 6-9): Mobile App Store
├── Обёртка через Capacitor (iOS + Android)
├── Push уведомления через Capacitor plugins
├── App store IAP как вторичный канал
├── DTC web store = основной revenue driver
└── Одна кодовая база для всего

Фаза 3 (мес 9-12): Расширение
├── Telegram Mini App (900M+ юзеров)
├── Facebook Instant Games (250M+ MAU)
├── TikTok Instant Games
└── Одна кодовая база = все платформы
```

**Почему web-first побеждает для авто-баттлера**:
- Жанр НЕ требует twitch-reaction — производительности браузера достаточно
- Session-based (не always-on) — подходит под PWA usage patterns
- Highly shareable — "посмотри моего бота" ссылки дают органический рост
- Прецедент: Super Auto Pets доказала этот путь для авто-баттлеров

---

## 6. Расширенный функционал

### 6.1 Боевые режимы

#### Основной: 1v1 Ranked (async PvP)
- Бой против сохранённого бота другого игрока
- Glicko-2 рейтинг, сезонные сбросы
- 3-15 секунд на бой

#### Team Battles (2v2)
Каждый игрок выставляет 2 ботов. Синергия-бонусы когда боты одной "фракции" или с одинаковыми типами оружия (+10% к урону, +15% HP). Добавляет мета-слой "командной композиции".

#### Boss Raids (PvE, кооператив)
- Еженедельный **Mega Boss** — гильдия коллективно дамажит
- Босс с несколькими уязвимыми точками (разные типы оружия для разных частей)
- Contribution leaderboard внутри гильдии
- Уникальные rewards за участие
- **AI-generated**: LLM анализирует мету и генерирует босса, который контрит популярные билды

#### Draft Mode
- Оба игрока по очереди выбирают из общего пула случайных запчастей
- Собирают бота из задрафченного и дерутся
- Тестирует скилл сборки, не коллекцию

#### Build Challenges (PvE паззлы)
- **"Budget Build"** — собери лучшего бота только из Common запчастей
- **"Counter This"** — дан вражеский бот, собери контр
- **"Mirror Match"** — одинаковые шасси, различайся оружием/гаджетами
- **"Speed Build"** — случайные запчасти, 60 секунд на сборку
- **"Gauntlet"** — бой с 5 противниками подряд без починки

#### Sandbox / Training
- Все запчасти доступны, без стоимости
- Тест против AI-противников разной сложности
- "What-if" лаборатория: загрузи replay, измени бота, посмотри что было бы

### 6.2 Арены / Окружение

| Арена | Механика | Эффект |
|-------|---------|--------|
| **Standard** | Плоская | Чистый тест билда |
| **Lava Pit** | Лава в центре | Бои на краях |
| **Moving Platforms** | Пол сдвигается | Наказывает нестабильных |
| **EMP Zone** | Периодически отключает гаджеты на 3с | Снижает зависимость от гаджетов |
| **Gravity Shift** | Арена наклоняется | Награждает тяжёлых |
| **Shrinking Ring** | Стены сужаются (CATS-style) | Предотвращает ничьи |
| **Destructible** | Колонны/стены можно разрушить | Тактический cover |
| **Conveyor** | Пол двигает к опасности | Требует мобильность |

Арены вращаются еженедельно в ranked. Draft и challenges используют специфические арены.

### 6.3 Social / Community

#### Гильдии (Guild System)
- 20-50 членов, guild level (коллективный XP)
- **Guild Boss** (еженедельный кооперативный PvE)
- **Guild Wars** (межгильдийные турниры, bracket)
- Guild chat + шаринг blueprint'ов внутри гильдии
- Guild perks (XP бонус, доп. слоты, эксклюзивные косметики)

Факт: **~70% top-grossing mobile games имеют guild features**. Гильдии = главный драйвер долгосрочного retention.

#### Blueprint Workshop
- Публикация билдов для сообщества
- "Copy & Modify" — чужой blueprint как стартовая точка
- Рейтинг, trending, "Hall of Fame"
- Builder profiles (билды, winrate, фолловеры)
- **"Challenge the Builder"** — сразиться с создателем популярного билда

Факт: **UGC платформы расширяют active user base на 10-20% ежегодно** (Bain, 2025).

#### Спектатор режим
- Live просмотр боёв гильдии
- Автоматический highlight reel
- Slow-motion replay с оверлеем урона/статов
- Турнирный spectating с чатом

#### Лидерборды (множественные)
- Global ranked (сезонный сброс)
- Guild leaderboard
- "Inventor" — самые скопированные/лайкнутые билды
- Weekly challenge leaderboard
- Friends leaderboard

Факт: **Хорошие лидерборды = +40% retention, +60% session time**.

#### Emotes & Chat
- 4 battle emotes (Wow, GG, Oops, Taunt)
- Коллекционные emotes через Battle Pass
- Post-battle "GG" обмен (бонус обоим)

### 6.4 AI-уникальные фичи

#### Natural Language Bot Strategy (ключевой differentiator)
Игрок описывает стратегию текстом:
- "Держись на дистанции и стреляй ракетами"
- "Если HP < 30%, щит и отступление"
- "Атакуй слабейшего первым"

LLM переводит в набор behavioral параметров (aggression, target priority, movement pattern, ability triggers). Бой остаётся детерминированным — AI только **конфигурирует**, не управляет в реалтайме.

**Ни одна существующая игра этого не делает.**

#### AI Coaching / Training Mode
- Анализ слабостей бота ("Твой бот переворачивается при боковых ударах — расширь колёсную базу")
- Предложение контр-билда против конкретного противника
- Replay review — идентификация момента проигрыша
- "Build challenges" для обучения механикам

Прецедент: **trophi.ai** — 1.5M+ coaching sessions, +0.7с к времени круга после 20 мин AI коучинга.

#### AI-Generated Boss Enemies
- LLM анализирует текущую мету (какие билды популярны)
- Генерирует босса специально контрящего мету
- Уникальное имя, backstory, визуал
- Сообщество коллективно ищет контр-стратегию

#### AI Battle Narrator
- LLM стримит эпичный комментарий поверх визуализации боя
- Стиль комментирования настраивается (эпический, юморной, спортивный)
- Post-battle story: нарративное описание ключевых моментов
- Шарится как текст/пост в социальных сетях
- **Без premium**: простой лог событий. **С premium**: полный AI-нарратив

#### AI Personality Evolution
- Бот развивает "характер" на основе истории боёв
- Частые close wins -> "Clutch Fighter" trait
- Победы над крупными -> "Giant Killer"
- Traits дают мини-бонусы (+2% к определённому стату)
- Бот "учится" на боях с определённым типом оружия (+2% effectiveness после 50 боёв)

### 6.5 Прогрессия и Retention

#### Progression System

| Уровень | Механика | Retention impact |
|---------|---------|-----------------|
| **Запчасти** | Rarity: Common -> Rare -> Epic -> Legendary | Коллекционирование |
| **Bot Level** | XP от боёв, уровень бота = minor stat bonuses | Attachment |
| **Player Level** | Глобальный XP, открывает features/modes | Progression feeling |
| **League** | Bronze -> Silver -> Gold -> Platinum -> Diamond | Competitive drive |
| **Prestige** | Scrap collection -> restart с бонусом + exclusive parts | Infinite endgame |
| **Season Rank** | Сезонные очки, exclusive rewards | FOMO + return |

#### Daily/Weekly Structure

**3 daily missions** (easy/medium/hard) + **3 weekly** (encourage mode variety) + **Monthly "Master Challenge"**. Daily login streak (7-day cycle, escalating rewards).

Факт: **Gamification увеличивает D30 retention на 15-30%**.

#### Achievement System (6 категорий)
1. **Builder** — разнообразие билдов
2. **Fighter** — победы, лиги, серии
3. **Social** — гильдии, шаринг, coop
4. **Explorer** — все арены, все режимы
5. **Secret** — скрытые достижения за необычное
6. **Seasonal** — time-limited, стимулирует новый контент

Факт: **Achievements увеличивают retention на ~20%, делают 68% более вероятным продолжение игры**.

#### Battle Pass (4-8 недельные сезоны)
- Free + Premium треки (50+ тиров)
- Привлекательные rewards в начале И в конце (filler в середине)
- Exclusive seasonal cosmetics (FOMO)
- $8-12 sweet spot

#### Seasonal Content
- **Еженедельная ротация запчастей** (Super Auto Pets style) — каждую неделю доступны разные запчасти в draft/shop, меняет мету
- **Ежемесячная тема** с 1-2 новыми запчастями + battle pass
- **Квартальный "meta reset"** — ребаланс, новая механика (тип арены или категория запчастей)
- **Новое оружие**: CATS добавляет оружие с принципиально новой механикой (Squid Cannon отключает гаджеты щупальцами)

---

## 7. Концепция веб-игры с AI

### Pitch
**"Bot Arena"** — web-игра где игроки собирают боевых роботов, описывают стратегию на естественном языке, и выставляют на автоматические бои с AI-комментариями.

### Рекомендуемый вариант: Гибрид (физика + AI)

**Фаза сборки:**
- Визуальный конструктор (шасси + оружие + колёса + гаджет)
- Behavior preset (6 стратегий) ИЛИ natural language описание стратегии
- AI personality: battle cry, taunts, traits (из текстового описания)
- Stats вычисляются из компонентов (не произвольно)

**Фаза боя:**
- Детерминированная симуляция (stats + behavior + seed)
- 2D визуализация (спрайты + анимации)
- AI-комментатор стримит через SSE
- AI post-battle анализ
- Длительность: 10-30с

**Core Loop:**
```
СБОРКА (30с-2мин) -> БОЙ (10-30с) -> НАГРАДА (мгновенно) -> СБОРКА
```

AI как enhancement: если LLM недоступен — бой работает. AI добавляет flavor.

---

## 8. Техническая архитектура

### Frontend

| Слой | Технология | Альтернатива |
|------|-----------|-------------|
| **Физика** | Rapier.js (WASM, детерминированная) | Planck.js (pure JS) |
| **Рендеринг** | PixiJS + WebGL | Phaser 4 |
| **UI** | React + TypeScript + Tailwind | -- |
| **Реалтайм** | WebSocket (бои) + SSE (AI) | -- |

WASM (Rapier.js) в **10% от нативной C++ производительности**. WebGPU = **85-90% от нативного рендеринга**. Для авто-баттлера — более чем достаточно.

### Backend

| Слой | Технология |
|------|-----------|
| **API** | FastAPI (Python) |
| **БД** | PostgreSQL |
| **AI** | Groq/Together/OpenAI (существующий стек) |
| **Рейтинг** | Glicko-2 |
| **Очередь** | Redis / in-memory |

### Async PvP архитектура

```
Client                    Server                     DB
  |-- Save bot config ---->|-- Store config --------->|
  |-- Request battle ----->|-- Select opponent ------>|
  |                        |-- Generate seed          |
  |<-- Configs + seed -----|-- Store result --------->|
  |-- Run simulation       |                         |
  |-- AI commentary (SSE)->|-- LLM generates         |
  |<-- Commentary stream --|                         |
  |-- Confirm result ----->|-- Update ratings ------->|
```

Симуляция детерминированная. Клиент показывает replay. Сервер — authority.

### Модели данных

```python
class Bot:
    id, user_id, name, avatar_url
    chassis_type, weapon_type, wheel_type, gadget_type
    hp, attack, defense, speed  # из компонентов
    personality_text, battle_cry, behavior_preset
    strategy_text  # NL описание стратегии
    rating, rd, volatility, wins, losses

class Battle:
    id, bot1_id, bot2_id, winner_id
    seed, replay_data, ai_commentary
    arena_type, mode  # ranked/draft/challenge
    rating_change_1, rating_change_2

class BotPart:
    id, type, subtype, tier, stars
    stats  # JSONB
    user_id

class Guild:
    id, name, level, xp
    members  # FK to users

class Season:
    id, name, start_date, end_date
    available_parts  # JSONB — weekly rotation
    battle_pass_rewards  # JSONB
```

---

## 9. Монетизация

### Модель

| Источник | Описание | Ожидаемая доля |
|---------|---------|---------------|
| **Cosmetics** | Скины ботов, эффекты, арены, эмоции | 35% |
| **Battle Pass** | $8-12/сезон, free + premium | 30% |
| **Rewarded Ads** | 30с = бонус | 20% |
| **Premium AI** | AI-анализ, AI-coaching, NL стратегия, нарратор | 15% |

### Web vs Mobile монетизация

| Метрика | Web (Stripe) | Mobile (App Store) |
|---------|-------------|-------------------|
| Комиссия | **2.9%** | 15-30% |
| На $100K дохода | Чистыми $97.1K | Чистыми $70-85K |
| Rewarded ad eCPM | $5-$20 | $10-$50 |
| Способы оплаты | Stripe, PayPal, crypto | Только IAP |
| Ценообразование | Любое | Фиксированные тиры Apple |

**DTC web stores для mobile games выросли на 46% YoY в 2025**. Топ-200 mobile publishers теряют $41M/день на комиссиях app stores.

### Premium AI фичи (уникальное УТП)

1. **AI Battle Analyst**: развёрнутый анализ + рекомендации
2. **AI Coaching**: персональные советы по улучшению
3. **NL Strategy**: описание стратегии текстом (free: 5 preset'ов, premium: NL)
4. **AI Narrator**: эпичный комментарий (free: простой лог, premium: полный нарратив)
5. **Custom Taunts**: LLM генерирует фразы для бота

Стоимость AI: ~200-500 токенов/бой = **~$0.001** через Groq/Together. Premium = маржинальный продукт.

---

## 10. MVP план

### Фаза 1: Core (3-4 недели)
- [ ] Система компонентов: 4 шасси, 6 оружий, 4 колёс, 3 гаджета
- [ ] Визуальный конструктор (slot-система)
- [ ] Stat-based бой (HP, Attack, Defense, Speed + behavior preset)
- [ ] 2D визуализация (Canvas, спрайты)
- [ ] Детерминированный алгоритм (stats + behavior + seed)
- [ ] API: CRUD ботов, запрос боя, результат
- [ ] Auth (переиспользование JWT стека)

### Фаза 2: Multiplayer + AI (3-4 недели)
- [ ] Async PvP против сохранённых ботов
- [ ] Glicko-2 рейтинг + matchmaking
- [ ] AI-комментатор (LLM через SSE)
- [ ] Лутбоксы с запчастями
- [ ] Тиры запчастей (Common -> Legendary)
- [ ] NL стратегия бота (LLM -> parameters)

### Фаза 3: Social + Retention (3-4 недели)
- [ ] Лиги + лидерборды
- [ ] Гильдии (создание, chat, blueprint sharing)
- [ ] Daily/weekly challenges
- [ ] Achievement system
- [ ] Replay + шаринг
- [ ] Blueprint Workshop

### Фаза 4: Scale + Monetize (3-4 недели)
- [ ] Battle Pass
- [ ] Cosmetics магазин
- [ ] Rewarded Ads
- [ ] Premium AI фичи
- [ ] Capacitor wrapper (iOS + Android)
- [ ] Guild Boss + Guild Wars
- [ ] Турниры (weekly automated)

### Фаза 5: Polish + Expand (3-4 недели)
- [ ] Физическая симуляция (Rapier.js вместо stat-based)
- [ ] Дополнительные арены (8 типов)
- [ ] Draft mode
- [ ] Team battles (2v2)
- [ ] AI-generated weekly bosses
- [ ] Telegram Mini App / Facebook Instant Games

---

## 11. Оценка целесообразности

### Аргументы ЗА

| Фактор | Данные |
|--------|--------|
| **Рынок растёт** | Авто-баттлеры $2.47B -> $7.87B (14.2% CAGR) |
| **Ниша пуста** | Нет web авто-баттлеров. Нет CATS-like преемника |
| **Спрос доказан** | CATS: 200M+ downloads. Super Auto Pets: viral web-first |
| **Дешёвый UA на web** | 5-50x дешевле mobile. Organic через порталы/social |
| **Низкая стоимость разработки** | $50K-$150K для MVP (2-4 чел, 3-4 мес) |
| **AI = differentiator** | NL стратегия + AI нарратив = нет аналогов |
| **Переиспользование стека** | FastAPI, PostgreSQL, LLM провайдеры, auth — уже есть |
| **Web-first путь доказан** | Vampire Survivors ($50M+), Super Auto Pets, Agar.io |
| **Монетизация без 30% налога** | Stripe DTC = +27% чистого дохода vs app stores |

### Аргументы ПРОТИВ

| Фактор | Данные |
|--------|--------|
| **Winner-take-most** | TFT (33M MAU) доминирует; indie auto-battlers обычно проваливаются |
| **0.5% success rate** | Только ~300 из 20K Steam games зарабатывают >$1M |
| **Web ARPU ниже** | $5-30/год vs mobile $60-124/год |
| **Web ad CPM ниже** | $5-20 vs mobile $10-50 |
| **iOS PWA ограничения** | Push notifications только с home screen; Apple враждебна |
| **85% негатив к AI** | Нельзя маркетировать как "AI-powered" |
| **Сложность балансировки** | Комбинаторика запчастей требует постоянного tuning |
| **Отвлечение от основного проекта** | Ресурсы уходят от SweetSin/GrimQuill |

### Риски и митигация

| Риск | Вероятность | Митигация |
|------|------------|-----------|
| Не наберём аудиторию | Высокая (70%) | Web = минимальные затраты на UA. Быстрый pivot если D7 < 5% |
| Low monetization | Средняя (50%) | Hybrid model: ads + IAP + battle pass. DTC Stripe |
| AI costs scale badly | Низкая (20%) | AI необязателен для core loop. Free tier без AI |
| Technical complexity | Средняя (40%) | Start stat-based, add physics later. Proven stack |
| Balance issues | Высокая (60%) | Weekly meta data analysis. Small part pool in MVP |

### Финальная оценка

| Критерий | Оценка |
|---------|--------|
| Рыночная возможность | **8/10** — пустая ниша, доказанный спрос |
| Техническая реализуемость | **9/10** — стек существует, MVP за 3-4 мес |
| Конкурентные преимущества | **7/10** — AI features уникальны, но "winner-take-most" жанр |
| Монетизация потенциал | **6/10** — web ARPU ниже, но DTC + AI premium компенсируют |
| Ресурсозатратность | **7/10** — $50K-$150K, 2-4 чел, НО отвлекает от основного проекта |
| **Итого** | **7.4/10** — стоит попробовать как side project с минимальным MVP |

### Рекомендация

**Делать как side project**, не вместо SweetSin/GrimQuill:
1. MVP за 3-4 недели (1 dev, stat-based, без физики)
2. Запустить на Poki/CrazyGames/itch.io + Reddit/Discord
3. Измерить D1/D7 retention
4. Если D7 > 8% — инвестировать в Фазу 2-3
5. Если D7 < 5% — свернуть, потери минимальны ($5-10K времени)

**Web-first однозначно** — mobile через Capacitor wrapper после product-market fit.

---

## Источники

### Рынок
- [DataIntelo — Auto-Battler Games Market](https://dataintelo.com/report/auto-battler-games-market)
- [Business Research Insights — HTML5 Games Market](https://www.businessresearchinsights.com/market-reports/html5-games-market-122374)
- [Grand View Research — AI in Gaming](https://www.grandviewresearch.com/industry-analysis/ai-gaming-market-report)
- [Straits Research — PWA Market](https://straitsresearch.com/report/progressive-web-apps-market)
- [GameAnalytics — 2025 Mobile Gaming Benchmarks](https://www.gameanalytics.com/reports/2025-mobile-gaming-benchmarks)

### Игроки и поведение
- [Quantic Foundry — Gen AI Sentiment (85% negative)](https://quanticfoundry.com/2025/12/18/gen-ai/)
- [Naavik — Web Gaming Strikes Back](https://naavik.co/digest/web-gaming-strikes-back/)
- [Mobidictum — Poki Interview](https://mobidictum.com/pokis-web-gaming-interview-michiel-van-amerongen/)
- [OneEsports — TFT 33M Monthly Players](https://www.oneesports.gg/teamfight-tactics/riot-teamfight-tactics-has-more-than-33-million-players-per-month/)

### Web vs Mobile
- [Mapendo — Mobile Games CPI 2025](https://mapendo.co/blog/mobile-games-cpi-2025)
- [Appcharge — DTC Revenue ($500M+)](https://www.appcharge.com/blog/from-0-to-500-m-building-the-dtc-infrastructure-for-the-next-era-of-mobile-games)
- [Business of Apps — Mobile Game Conversion Rates](https://www.businessofapps.com/data/mobile-game-conversion-rates/)
- [Brainhub — PWA on iOS](https://brainhub.eu/library/pwa-on-ios)

### Технологии
- [Rapier.js](https://github.com/dimforge/rapier.js) | [PixiJS](https://pixijs.com/) | [Glicko-2](https://glicko.net/glicko/glicko2.pdf)
- [ByteIota — WebGPU 2026](https://byteiota.com/webgpu-2026-70-browser-support-15x-performance-gains/)
- [Playgama — WASM Game Performance](https://playgama.com/blog/2025/04/03/boost-html5-game-performance-with-webassembly/)

### Game Design
- [trophi.ai — AI Gaming Coach (1.5M sessions)](https://www.trophi.ai/)
- [GameMakers — Battle Pass Design](https://www.gamemakers.com/p/understanding-battle-pass-game-design)
- [GameRefinery — Guild Systems](https://www.gamerefinery.com/casual-games-guilding-up/)
- [Bain — UGC +10-20% User Growth](https://www.bain.com/insights/user-generated-content/)

### CATS и конкуренты
- [CATS Official](https://www.catsthegame.com/) | [CATS Wiki](https://catsthegame.fandom.com/)
- [PocketGamer — Making of CATS](https://www.pocketgamer.biz/interview/66379/feline-fighters-the-making-of-zeptolabs-cats/)
- [Wikipedia — ZeptoLab sold CATS for $7.7M](https://en.wikipedia.org/wiki/ZeptoLab)
- [Wikipedia — Vampire Survivors (~$50M)](https://en.wikipedia.org/wiki/Vampire_Survivors)
- [LLM Fighter (GitHub)](https://github.com/neutree-ai/llm-fighter)
- [Gladiabots](https://gladiabots.com/) | [Battlesnake](https://play.battlesnake.com/)
