# SFW-ответвления: глубокое исследование AI-продуктов (февраль 2026)

Какой продукт создать на базе текущего стека (FastAPI + React + multi-provider LLM + character system).
Рассматриваемые домены: **chatsensei.app**, **chatsensei.ai**.

## Зачем SFW-домен

| Проблема NSFW | SFW решает |
|---------------|------------|
| SEO: пессимизация, "Discovered but not crawled" | Нормальная индексация |
| Stripe/PayPal запрещены | Без ограничений |
| App Store отклоняет | Можно публиковать |
| AdSense/рекламодатели не идут | Google Ads, спонсоры |
| TikTok/YouTube блокируют промо | Свободная раскрутка |

---

## Сводная таблица всех вариантов (16 штук)

| # | Продукт | Рынок | Конкур. | Код reuse | Stripe | SEO | Юр. риски | MVP | Потолок MRR (solo) |
|---|---------|-------|---------|-----------|--------|-----|-----------|-----|-------------------|
| 1 | AI DnD/TTRPG Game Master | $2.15B TTRPG | **Низкая** | 70% | 10/10 | Высок | Нулев | 3-5 мес | $10-30K |
| 2 | AI Social Skills Trainer | $37B companion | Низкая | 95% | 10/10 | Высок | Низк | 2 нед | $15-25K |
| 3 | AI Interview Prep Coach | $5B career | Средн | 85% | 10/10 | Средн | Нулев | 2 нед | $15-30K |
| 4 | Interactive Fiction / CYOA | $1.4B IF | Средн | 90% | 10/10 | Высок | Нулев | 2 нед | $10-50K |
| 5 | Anime SFW Character Chat | $36B anime | Высок | 95% | 9/10 | Высок | Средн (IP) | 1 нед | $5-25K |
| 6 | Japanese через Anime (Language) | $2.6B apps | Высок | 90% | 10/10 | Высок | Нулев | 1 мес | $5-15K |
| 7 | AI Sales Training Simulator | $13B CS | Средн | 85% | 10/10 | Низк | Нулев | 1 мес | $20-40K |
| 8 | AI Creative Writing Mentor | $2.5B writing | Средн | 80% | 10/10 | Средн | Нулев | 3 нед | $5-15K |
| 9 | White-label Chat Platform | $22B conv.AI | Высок | 90% | 10/10 | Низк | Нулев | 2 мес | $15-30K |
| 10 | AI Dating Coach | $11B dating | Средн | 75% | 8/10 | Средн | Низк | 3 нед | $10-100K |
| 11 | AI Journaling Companion | $12.8B wellness | Средн | 75% | 10/10 | Высок | Низк | 3 нед | $3-8K |
| 12 | AI Language Tutor (general) | $2.6B apps | Жёстк | 90% | 10/10 | Высок | Нулев | 1 мес | $3-10K |
| 13 | AI Visual Novel Engine | $1.3B VN | **Низкая** | 70% | 10/10 | Средн | Низк | 2 мес | $5-15K |
| 14 | AI VTuber / Virtual Idol | $3B VTuber | **Низкая** | 20% | 6/10 | Низк | Низк | 3 мес | $2K-400K |
| 15 | AI CoC/Horror RPG | $2.15B TTRPG | **Нулевая** | 75% | 10/10 | Высок | Нулев | 2 мес | $5-20K |
| 16 | AI Kids Stories | $1.12B | Низкая | 60% | 10/10 | Высок | Высок (COPPA) | 1 мес | $5-30K |

---

## 1. AI DnD/TTRPG Game Master (ГЛУБОКИЙ АНАЛИЗ)

### Обзор рынка

- **TTRPG глобально**: $2.15B (2025) -> $6.59B (2035), CAGR 11.84%
- **D&D игроков**: ~50M worldwide, ~13.7M активных за столом
- **60% D&D revenue = digital** (в основном D&D Beyond)
- **44% используют виртуальные столы** (VTT), **27% хотят AI NPC**
- **VTT поддерживают 55%+ кампаний** (было 29% в 2020)
- **Solo TTRPG**: 2.5-7.5M игроков (5-15% от всех), растущий рынок
- **r/lfg** (250-300K подписчиков): огромный разрыв между желающими играть и доступными DM

### Конкуренты: детальный разбор

#### AI Dungeon (Latitude) — пионер, но ослабевший
- **Revenue**: не раскрыт, оценочно low single-digit millions/год
- **Users**: пик 1.5M MAU (2020-2021), сейчас значительно меньше. Steam: 109 -> 52 concurrent
- **Funding**: $3.3M seed (2021, NFX)
- **Team**: ~10 человек
- **Pricing**: Free -> $9.99/мес (Adventurer) -> $14.99 (Champion) -> $29.99 (Legend) -> $49.99 (Mythic, GPT-4 Turbo + DALL-E 3)
- **Tech**: MythoMax (Llama 2 13B, free), Mixtral (premium), GPT-4 Turbo (ultra). Было GPT-2 -> GPT-3 -> AI21 Labs
- **Что хорошо**: multi-model, мультиплеер co-writing, глубокий контекст (32K на топ-тире), name recognition
- **Что плохо**: **НЕ D&D** — нет правил, костей, стат-блоков, боевой системы. Это interactive fiction, не TTRPG. Репутация подорвана скандалом 2021 (чтение приватных историй + модерация). Ушёл из Steam (март 2024)
- **Сентимент**: ~70% позитив на Reddit, но trust deficit остаётся

#### Friends & Fables (fables.gg) — самая серьёзная попытка "настоящего D&D с AI"
- **Revenue**: не раскрыт
- **Users**: 10,100+ Discord members
- **Funding**: не раскрыт
- **Team**: маленькая инди-команда
- **Pricing**: Free (3 игрока, 25 ходов/день) -> $19.95/мес (4 игрока, безлимит) -> $29.95 (5 игроков) -> $39.95 (6 игроков)
- **Tech**: предположительно GPT-4 или frontier model
- **AI GM "Franz"**: реальные механики (HP, leveling, spell casting, inventory)
- **Что хорошо**: ближе всех к "настоящему D&D" с механиками, мультиплеер до 6 игроков, community module sharing, long-term memory
- **Что плохо**: дорого ($20-40/мес), текстовый (без карт/токенов), маленькое community (10K Discord), мобильные приложения ещё не вышли
- **2025 Roadmap**: combat polish, free tier, iOS/Android apps (март-апрель 2025)

#### RPGGO — платформа для создания AI RPG
- **Revenue**: не раскрыт
- **Funding**: не раскрыт
- **Team**: маленькая (US + China)
- **Pricing**: Free чат с NPC. GG Coins: $4.99 = 500 coins. Image gen = 4 coins, voice = 8 coins/session
- **Tech**: проприетарный AI engine
- **Что хорошо**: creator economy (30% revenue share авторам), мультимодальность (голос, изображения), group chat с AI NPC
- **Что плохо**: не D&D-специфичен, coin-gated features, мало публичных данных о traction

#### LitRPG Adventures — solo dev, DM prep tool
- **Creator**: Paul Bellow — LitRPG-автор, solo dev
- **Revenue**: не раскрыт, нишевая аудитория
- **Pricing**: $6 starter (one-time) -> $5/мес Bronze -> $50/год
- **Tech**: GPT-3.5 + DALL-E 3
- **Что хорошо**: самый дешёвый ($5/мес), 36+ генераторов, 250K+ RPG-элементов в библиотеке, commercial license
- **Что плохо**: solo dev bus factor, GPT-3.5 качество, не игровая платформа (только prep tool), устаревший UI

#### Hidden Door — самый funded, самый амбициозный
- **Revenue**: $1.7M за ~5 лет (скромно для VC-backed)
- **Funding**: $2M pre-seed (Northzone). Angels: CTO Roblox, founder del.icio.us
- **Team**: ~23 человека
- **Founder**: Hilary Mason — ex-Chief Data Scientist at Bitly, AI ветеран
- **Tech**: custom AI narrative engine + licensed IP
- **Что хорошо**: сильнейшая команда/фандинг, лицензированные миры (Wizard of Oz, Pride and Prejudice, Call of Cthulhu, The Crow), card collection = retention
- **Что плохо**: очень медленный (анонс 2022, public launch август 2025), $1.7M revenue за 5 лет, НЕ D&D (narrative fiction, другое позиционирование), IP licensing дорого

#### AI Game Master (aigamemaster.app) — мобильный D&D
- **Funding**: нет ($0)
- **Team**: 2 человека
- **Pricing**: Free (5 tokens/4 hours) -> token packs (~$0.99-$4.99) -> Game Master sub $25/мес
- **Tech**: GPT-based, D&D-inspired rules
- **Что хорошо**: мобильный, D&D-инспирированные механики, AI portraits
- **Что плохо**: token-gated, мало функций vs полноценные VTT

### Конкурентный ландшафт: сводная таблица

| Продукт | Тип | Цена | Мультиплеер | D&D Rules | Фандинг | Команда |
|---------|-----|------|-------------|-----------|---------|---------|
| AI Dungeon | Interactive Fiction | $0-50/мес | Да | **Нет** | $3.3M | ~10 |
| Friends & Fables | D&D 5e AI GM | $0-40/мес | Да (2-6) | **Да** | ? | Малая |
| RPGGO | Creator Platform | Free + coins | Да | Нет | ? | Малая |
| LitRPG Adventures | DM Prep Tool | $5-50/мес | Нет | Compatible | $0 | Solo |
| Hidden Door | Narrative Fiction | TBD | Да | Нет | $2M | ~23 |
| AI Game Master | Mobile RPG | Free + tokens | Local | Inspired | $0 | 2 |

### КРИТИЧЕСКИЕ ПРОБЕЛЫ НА РЫНКЕ

1. **Никто не совмещает AI GM + реальные D&D 5e механики + визуальные карты + мультиплеер**. Friends & Fables ближе всех, но text-only
2. **VTT-интеграция = практически ноль**. Roll20 = 0 AI фич. Foundry VTT = только community модули
3. **Persistence кампаний** решён плохо. Большинство tool'ов = session-by-session
4. **Качество AI-текста** = жалоба #1 по всем продуктам ("AI slop")
5. **"DM assistant" (помощник DM, не замена)** — категория недообслужена и менее контроверсионная
6. **Никто не добился масштаба**. AI Dungeon пик 1.5M, потом крах. Все остальные < 100K

### Что D&D-игроки реально хотят от AI

**Хотят**:
1. DM prep: генерация NPC, локаций, энкаунтеров, лора
2. **Solo play GM** — #1 драйвер спроса (r/lfg: сотни тысяч хотят играть, но нет DM)
3. Session notes/recaps
4. Генерация арта (портреты, карты)
5. AI rules lookup
6. Естественный NPC dialogue
7. Worldbuilding brainstorming

**Жалобы на существующие AI DM**:
1. Repetitive, generic output ("AI slop")
2. Не понимает D&D правил, не ведёт бой правильно
3. Теряет контекст через 5 ходов, противоречит установленным фактам
4. Choices feel meaningless
5. Token/paywall frustration mid-session
6. Не может обработать multi-character combat
7. Hallucination правил

### Лицензирование D&D 5e: что безопасно

**SRD 5.1** (январь 2023): лицензирован под **Creative Commons CC-BY-4.0** — **безотзывный**:
- 403 страницы core rules, 12 классов (1 подкласс каждый), 9 рас, сотни заклинаний, 300+ монстров
- Полностью коммерческое использование с простой атрибуцией
- Без роялти

**SRD 5.2** (апрель 2025): также CC-BY-4.0, обновлён для 2024 rules revision

**Что безопасно**: все механики, классы, большинство монстров/заклинаний из SRD
**Нельзя**: "Dungeons & Dragons", "D&D", "Dungeon Master" (trademark'и); Beholder, Mind Flayer (Product Identity); именные NPC (Strahd, Tiamat)
**Можно**: "Game Master", "d20 fantasy RPG", "compatible with 5th edition"

**WotC / Hasbro позиция по AI**:
- Официально: запрет AI-арта в опубликованных D&D продуктах
- CEO Chris Cocks (лично): активно pro-AI, использует ChatGPT для приключений, планирует "liberally deploy AI"
- Третьи стороны: **WotC никогда не подавал иски** против third-party D&D контента. Единственная попытка ограничить (OGL 1.1, 2023) привела к массовому бунту и полному отступлению

### Adjacent Tools (DM помощники)

| Инструмент | Тип | Цена | Ключевая фишка |
|------------|-----|------|-----------------|
| Archivist AI | Session recorder | $10-60/мес | Превращает сессии в организованную memory |
| Vellum AI (TTRPG) | Worldbuilding | $10/мес | Fine-tuned AI для сторителлинга |
| LoreKeeper | Campaign manager | Free + premium | Мультисистемный, AI генерация NPC/локаций |
| Foundry VTT RPGX | VTT AI module | Free | AI NPC dialogue через Ollama |

### VTT рынок (виртуальные столы)

| Платформа | Модель | Цена | AI фичи |
|-----------|--------|------|---------|
| Roll20 | Subscription | Free/$5.99/$9.99/мес | **Нет** (12M+ accounts) |
| Foundry VTT | One-time | $50 | Community AI modules |
| D&D Beyond | Subscription | $2.99/$5.99/мес | "Rules Assistant" (не AI GM) |
| Owlbear Rodeo | Freemium | Free/$3.99/мес | Нет |
| Fantasy Grounds | Purchase | $39-$149 + DLC | Нет |

### Solo TTRPG — целевая аудитория

- **2.5-7.5M мировая аудитория** (5-15% от 50M+ TTRPG игроков)
- Текущие инструменты: Mythic GME ($14.95 PDF), Ironsworn (free, CC-BY), случайные таблицы
- **Что отсутствует**: интегрированный опыт (сейчас жонглируют 3-5 инструментами), persistent world memory, enforcement правил, динамические NPC, adaptive difficulty

### Соответствие текущей кодовой базы

**Можно переиспользовать напрямую (70% кодовой базы)**:
- Multi-provider LLM orchestration (9 провайдеров + auto-fallback)
- Group chat (1 user + 2-3 AI = TTRPG партия)
- Character/NPC creation и storage (personality, appearance, speech_pattern)
- Streaming SSE infrastructure
- Multilingual prompt system (7 языков)
- User auth, tier system, token tracking, cost management
- Message summarization + context window management
- Admin settings framework

**Нужна модификация (20%)**:
- Prompt builder: добавить GM-specific templates, encounter context injection
- Chat service: turn management, dice roll integration, encounter state
- Character model: добавить stats_block (JSON), character_type (pc/npc/monster)
- Frontend: combat HUD overlay, initiative tracker, dice roller UI

**Нужно построить заново (10%)**:
- Dice roll system (middleware: перехват действия -> бросок -> результат в промпт)
- Encounter manager (state machine: раунды, ходы, эффекты)
- Campaign model (группировка сессий, NPC continuity)
- Character sheets (ability scores, spell slots, inventory)
- Progression system (XP, level-up)

### Новые DB модели

- **Campaign**: creator_id, name, description, system (D&D 5e / Pathfinder / etc.), status
- **CampaignSession**: campaign_id, number, summary, status
- **Encounter**: campaign_id, encounter_data (JSON), status
- **DiceRoll**: chat_id, roll_expression, result (audit trail)
- **InventoryItem**: persona_id, name, quantity, weight, description
- **NPCMemory**: npc_id, pc_id, memory_text, importance (NPC "помнит" игроков)

Расширения существующих моделей:
- Character: + `character_type` (pc/npc/monster), + `stats_block` (JSON: AC, HP, abilities)
- Persona: + `stats_block`, `level`, `hit_points_current`, `spells_known`
- Chat: + `encounter_state` (JSON: initiative, conditions, round)
- Message: + `dice_rolls` (JSON array)

### Фазы разработки

| Фаза | Что | Срок |
|------|-----|------|
| 1 | DB модели (Campaign, Encounter), GM промпты, NPCs в group chat | 2-3 нед |
| 2 | Turn management, initiative tracking, encounter state | 2-3 нед |
| 3 | Dice roll integration (structured output + fallback parsing) | 2-4 нед |
| 4 | Conditions, spell effects, status tracking | 2-3 нед |
| 5 | Character sheets, inventory, leveling | 2-3 нед |
| 6 | Polish: tactical map, NPC memory, campaign continuity | 2-3 нед |
| **Итого MVP (фазы 1-3)** | Рабочий AI GM с костями и ходами | **6-10 нед** |
| **Полный продукт** | Все 6 фаз | **12-19 нед** |

### Pricing sweet spot

- **Free tier**: 3-5 сессий/день (acquisition)
- **Core**: $9.99-14.99/мес (между AI Dungeon $9.99 и F&F $19.95)
- **Premium**: $19.99-24.99/мес (premium models, image gen, longer context)
- **Дополнительно**: one-time campaign/adventure packs

### Риски

| Риск | Импакт | Митигация |
|------|--------|-----------|
| Structured output не у всех провайдеров | Высокий | JSON fallback parsing; начать с OpenAI/Anthropic |
| Сложность campaign state | Высокий | Начать с single-encounter; JSONB для гибкости |
| LLM costs с длинными промптами | Средний | Кэш encounter context; дешёвые провайдеры для exploration |
| Community anti-AI hostility | Средний | Позиционирование "DM assistant", не "replacement" |

---

## 2. AI Social Skills Trainer

Персонажи = собеседники для тренировки: собеседование, свидание, конфликтный начальник, сложный сосед.

- **Рынок**: $37.7B AI companion (2025) -> $435B (2034), 31% CAGR
- **Конкуренты**: Flir (10K+), Sociabl (voice), Bearwith (Hume emotion detection), Charisme (CBT), EaseTalk — все ранние стадии, ни один не доминирует
- **Почему топ**: низкая конкуренция + самый высокий code reuse (95%). Post-COVID социальная тревожность = эпидемия
- **Code reuse**: character system = типы собеседников, persona = практикующий, SSE streaming = диалог
- **Монетизация**: $9.99-19.99/мес B2C, B2B $50-200/user/мес
- **Юр. риски**: низкие. "Practice conversations" -- не терапия

---

## 3. AI Interview Prep Coach

Персонажи = интервьюеры (жёсткий CTO, дружелюбный HR, агрессивный VP). Персона = кандидат.

- **Рынок**: $5.0B (2025) -> $23.5B (2034), 18.7% CAGR. 35% improvement performance
- **Конкуренты**: Final Round AI (realtime подсказки), LockedIn AI, Huru, InterviewBee — большинство дают подсказки (borderline cheating), не практику
- **Почему сильный**: самая высокая willingness to pay ($14.99-29.99/мес), urgent need ("ищу работу сейчас")
- **Code reuse**: 85%. Добавить: scoring, feedback, session recording
- **Монетизация**: $14.99-29.99/мес или per-session
- **Юр. риски**: нулевые

---

## 4. Interactive Fiction / CYOA

Чат-интерфейс = already interactive fiction. Добавить кнопки выбора, трекинг состояния, публикацию историй.

- **Рынок**: $1.42B (2024) -> $4.12B (2033), 13.7% CAGR. AI story tools: $1.4B -> $14.7B (2030), 34.2% CAGR
- **Конкуренты**:
  - **AI Dungeon**: $9.99-49.99/мес, ~10 чел, $3.3M seed, declining
  - **Episode Interactive**: $32.2M annual, 125M+ installs, 210-250 employees, Pocket Gems (Sequoia/Tencent)
  - **Choices (Pixelberry)**: $35-60.9M annual, acquired by Series Entertainment (2024)
  - **Choice of Games**: 150+ interactive novels, ChoiceScript (open-source), "world's largest IF publisher"
  - **Inkle**: Heaven's Vault ~$390K Steam gross, "ink" scripting language (free, widely adopted)
- **Ключевой инсайт от Episode**: 70%+ female audience, romance/drama доминирует, FOMO microtransactions ($32M/год), UGC scales supply
- **Почему сильный**: 90% code reuse, literary prose prompts переносятся напрямую
- **Code reuse**: добавить choice buttons, state tracking, "publish story", marketplace
- **Монетизация**: freemium $4.99-14.99/мес + creator revenue share
- **Юр. риски**: нулевые (если не копировать IP)
- **Пересечение с SweetSin**: romance/drama female audience — естественное расширение

---

## 5. Anime SFW Character Chat (ГЛУБОКИЙ АНАЛИЗ)

### Конкуренты: детальные метрики

| Платформа | Revenue | MAU/визиты | Фандинг | Команда | Цена |
|-----------|---------|------------|---------|---------|------|
| Character.AI | $32.2M (2024), прогноз $50M | 20M MAU | $193M | 225 | $9.99/мес |
| Chai AI | $40M ARR -> $70M | 2M DAU | $55M | 21 (11 eng) | Freemium |
| Janitor AI | ? | 135M визитов/мес | ? (North Equity, Sky9) | Малая | BYOK + sub |
| Candy.AI | **$25M ARR, bootstrap** | 10M+ US | **$0 funded** | Малая (Мальта) | $12.99/мес + tokens |
| CrushOn.AI | ? | 20.6M визитов | $0 funded | ~25 | $5.99-14.99/мес |
| SpicyChat | ? | 73.9M визитов | ? | ? | **Free** |
| Replika | ~$300K/мес (companion cat.) | 30M+ total | $11M | ~115 | $14.99/мес |
| SillyTavern | $0 (open source) | 500K+ active | $0 | Community | Free (BYOK) |

**Candy.AI — proof case для solo dev**: $25M ARR без единого доллара VC, маленькая команда. Гибрид sub ($12.99/мес) + token packs ($9.99-$299.99)

**Chai AI — efficiency benchmark**: $2.5M revenue на сотрудника. 21 человек = $40M ARR

**Moemate (ЗАКРЫЛСЯ февраль 2025)**: из-за GPU/API costs. Все данные юзеров потеряны безвозвратно. **Наш стек с бесплатными провайдерами = конкурентное преимущество**

### Демография и возможность BL/Husbando

- **Janitor AI**: 70% female users (по одним данным), 63.7% male (SemRush traffic). Вероятно: трафик = male, heavy users/creators = female
- **Только 13 "boyfriend" apps vs 57 "girlfriend" apps** — supply gap 4:1
- **Otome games**: $5.69B в 2025, $8.88B к 2030. Love & Deepspace: **$826M за 15 месяцев**
- **Female ARPU**: $16-17 в otome (выше среднего mobile gaming)
- **BL/Yaoi рынок**: Таиланд ~$150M к 2025, глобально -> $1B к 2030+

**Ключевой инсайт**: женщины ГОТОВЫ ПЛАТИТЬ БОЛЬШЕ за romance/companion контент, но рынок массово недообслуживает их

### Юридические риски (IP)

- **Disney C&D to Character.AI** (сент. 2025): удаление Elsa, Moana, Spider-Man, Darth Vader
- **Disney vs ByteDance** (февр. 2026): C&D за Seedance 2.0
- **Japan CODA vs OpenAI**: требование не использовать anime/manga
- **Суды**: Character.AI settled wrongful death lawsuits (янв. 2026), FTC investigation

**Безопасный подход**: оригинальные архетипы (tsundere, yandere, kuudere), НЕ конкретные IP. DMCA compliance обязателен

### Потенциал solo dev

- **Month 1-6**: $0-500/мес (building, beta)
- **Month 6-12**: $1K-5K/мес (BL/husbando niche wide open)
- **Month 12-24**: $5K-20K/мес (retention + word-of-mouth)
- **Year 2-3**: $20K-100K/мес (если рост компаундится)
- **Потолок solo dev**: ~$50K-100K/мес (потом нужна помощь)
- **Риск**: Moemate сценарий. При 100K messages/day = $100-1000/day API costs

---

## 6. Japanese через Anime (Language Tutor)

"Учи японский, общаясь с аниме-персонажами". Идеальный fit для ChatSensei.

### Конкуренты: детальные метрики

| Компания | Revenue | Users | Фандинг | Фишка |
|----------|---------|-------|---------|-------|
| Duolingo | **$1.03B forecast 2025** | 130M MAU | IPO ($14B) | Gamification, AI Roleplay, Video Call |
| Speak | **$100M+ ARR** | 10M learners | $162M ($1B val.) | Speech-first, OpenAI-backed |
| Praktika | $20M ARR | 14M downloads | $35.5M | AI avatar tutors, GPT-5.2 |
| ELSA Speak | $32.5M (2023) | 50M+ | $60M (Google) | Best-in-class pronunciation |
| TalkPal | ~$1.7M ARR | 6M learners | Bootstrap | 57 languages, $5-10/мес |
| Babbel | $147.8M | 16M+ subs lifetime | ~$50M | Structured curriculum |
| Rosetta Stone | $182.7M (IXL) | ? | Acquired | Legacy brand |

### Gap в рынке

Никто не совмещает anime character chat + structured JLPT progression. Duolingo Roleplay ограничен. Anime-specific tutors (Hanashi, SakuraSpeak, Amiko) — все ранние стадии.

### Научное обоснование

Мета-анализ 31 исследования: chatbots = medium effect на L2 learning (g = 0.608). GenAI-powered значительно эффективнее rule-based. Сильнее всего: speaking и writing.

### Технические требования

| Компонент | Стоимость | Решение |
|-----------|-----------|---------|
| Speech-to-Text | $0.006/мин | OpenAI Whisper API (cheapest, best accuracy) |
| Text-to-Speech | $0.011/1K chars | Speechmatics / Google Cloud TTS |
| Pronunciation scoring | ? | Azure Speech Assessment API |
| LLM conversation | ~$0.001-0.01/msg | Groq/OpenRouter free tier |

### Профитабельные языки для обучения

1. **English** — 1.5B learners, largest demand
2. **Japanese** — fastest growing (+33%), culture-driven (anime/manga). **Best fit для ChatSensei**
3. **Korean** — +35% growth, K-pop/K-drama
4. **Spanish** — massive in US
5. **French** — Africa (growing population)
6. **German** — business-motivated (higher WTP)

### Можно ли конкурировать с Duolingo?

**Лобовая конкуренция = самоубийство**. Viable angles:
- Single language pair: "Japanese for English speakers via anime"
- Niche use case: "Conversational Japanese for anime fans"
- Price undercut: free + $5-7/мес vs Speak's $14/мес
- Target: 1,000 paying users x $7/мес = $7,000/мес

---

## 7. AI Sales Training Simulator

Персонажи = клиенты ("Скептичный CFO", "Прижимистый закупщик"). Персона = продавец.

- **Рынок**: $13B AI customer service -> $83.8B (2033), 23.2% CAGR
- **Конкуренты (B2B)**: Second Nature AI, SymTrain, Rehearsal, Awarathon, MindTickle
- **Почему высокий потолок**: B2B pricing $50-200/user/мес. 50 компаний x 10 seats x $100 = $50K MRR
- **Code reuse**: 85%. Добавить: scoring/feedback, session recording, manager dashboard
- **Минус**: медленный B2B sales cycle, нужны кейсы и демо
- **Юр. риски**: нулевые

---

## 8. AI Creative Writing Mentor (ГЛУБОКИЙ АНАЛИЗ)

### Конкуренты: детальные метрики

| Компания | Revenue | Фандинг | Команда | Цена |
|----------|---------|---------|---------|------|
| Grammarly | **$700M ARR** | $400M+ ($13B val.) | ~1,000 | Free/$12/мес |
| Jasper AI | **$142.9M** | $125M Series C | ~300 | $49-69/мес |
| Sudowrite | ~$2-5M ARR est. | **$3M** | **5 чел** | $10-44/мес |
| NovelAI | ~$5-15M ARR est. | **$0** | <20 | $10-25/мес |
| Copy.ai | $23.7M | $16.9M | ? | B2B focus |
| ProWritingAid | ~$2.3M/yr | ? | ? | $30/мес, $399 lifetime |
| Novelcrafter | ? growing | **$0** | **Started as 1 person** | $4-20/мес (BYOK) |

### Ключевые инсайты

- **Sudowrite: 5 сотрудников, $3M funding** — proof small works. Launched custom "Muse" model (март 2025)
- **NovelAI: $0 funding, self-funded** — loyal community через NSFW-friendly stance + custom models
- **Novelcrafter: начат одним человеком в 2023** — BYOK model (user brings API key) = near-zero AI costs
- **Fiction vs copywriting**: copywriting ($143M Jasper) более прибылен per-company, но commoditized (ChatGPT бесплатный). Fiction writing = defensible niche

### Что писатели реально платят за

1. Brainstorming/ideation (character development, plot holes)
2. Continuation/drafting assistance (when stuck, maintaining voice)
3. Style analysis (matching voice, identifying repetition)
4. Editing/developmental feedback (pacing, structure)
5. Worldbuilding management (Lorebook/Codex)
6. **НЕ за полную генерацию** — serious writers хотят assistance, не replacement

### Revenue models

- **BYOK** ($4-20/мес + user's API costs): Novelcrafter model, near-zero overhead для dev
- **Freemium subscription**: $10-25/мес (NovelAI, Sudowrite)
- **Lifetime purchase**: $200-400 (ProWritingAid, risky for SaaS)

### Synergy с SweetSin

Literary prose prompts, character depth system, anti-repetition rules — всё напрямую переносится. Genre-specific (romance, LitRPG) = underserved niches.

---

## 9. White-label AI Chat Platform

Strip NSFW, добавить multi-tenancy, billing per client.

- **Рынок**: $22B conv. AI (2026) -> $40B (2030), 21.8% CAGR
- **Конкуренты**: Botpress, Voiceflow, Tidio, Kore.ai, Stammer AI — хорошо funded
- **Code reuse**: 90%. Multi-provider fallback + admin panel = enterprise features. Нужно: tenant isolation, custom branding, API keys per client, usage billing
- **Монетизация**: $200-2000/мес per client
- **Минус**: B2B sales cycle, support burden

---

## 10. AI Dating Coach (ГЛУБОКИЙ АНАЛИЗ)

### Конкуренты

| Продукт | Users | Revenue | Демография |
|---------|-------|---------|------------|
| Rizz (Rizz Labs) | 7.5-10M downloads, 1M+ MAU | **$190K/мес** | 65% male, 18-25 |
| YourMove AI | 1M+ downloads | ? | Younger males |
| Flirtify | ? | ? | Free 5 msgs/day, $5.99/мес |
| Keys AI | ? | ? | Keyboard-based |

### Рынок

- Online dating services: **$11.02B** (2025) -> $19.33B (2033), 7.27% CAGR
- AI in dating: $7.94B (2022) -> $12.37B (2030)
- Мужчины на dating apps: match rate 1-3% на Tinder (pain point реален)

### Этические вопросы

- "Intimate authenticity crisis" — если все используют AI, никто не genuine
- Fine line между self-improvement и manipulation
- Hinge/Bumble борются с AI-assisted messaging
- App Store может отклонить

### Solo dev feasibility: ОЧЕНЬ ВЫСОКАЯ

- Simplest tech stack: LLM API + mobile app
- MVP за дни: screenshot OCR + GPT prompt
- **Rizz: 1.5M downloads, $190K MRR за 4.5 месяца** (маленькая команда)
- Niche angles: non-English markets, specific apps (Grindr, Bumble), 35+ demographic
- Cost: ~$0.01-0.05 per message

---

## 11. AI Journaling Companion

- **Рынок**: $12.87B wellness (2025) -> $45.65B (2034), 15.11% CAGR
- **Конкуренты**: Rosebud ($6.75M raised, $12.99/мес), Day One (15M+ downloads), Reflectly
- **Code reuse**: 75%. Нужно: mood tagging, streak tracking, weekly summaries, export-to-PDF
- **Юр. риски**: НИЗКИЕ если "journaling companion", НЕ "therapy". Illinois запрещает AI в терапии (авг 2025). Безопасные слова: journal, reflection, mindfulness. Опасные: therapy, counselor, treatment
- **ИЗБЕГАТЬ**: AI Therapy/Mental Health. Woebot ($123.5M raised) **закрылся** июнь 2025. Replika оштрафована EUR 5M. FTC investigation. Regulatory landscape = catastrophic для solo dev

---

## 12. AI Language Tutor (general)

- **Рынок**: $2.6B apps (2025) -> $7.2B (2034)
- **Конкуренты**: Duolingo ($1B+, 130M MAU), Speak ($100M+ ARR, $1B), Praktika ($20M ARR)
- **Проблема**: лобовая конкуренция с гигантами ($35-162M funding). Без узкой ниши шансы минимальны
- **Монетизация**: freemium $4.99-9.99/мес

---

## 13. AI Visual Novel Engine (НОВЫЙ)

"Canva для визуальных новелл" — no-code AI visual novel maker с anime art generation.

### Рынок

- Visual novel market: $1.26B (2025), projected $3B (2035), 15% CAGR
- 65% top itch.io visual novels в Q1 2025 используют hybrid Ren'Py + AI workflows
- 45% indie VN devs используют AI tools (cut production time 20%)

### Конкуренты

- **Ren'Py**: free, open source, 8,000+ visual novels. Но **требует кодирования**
- **Rosebud AI**: no-code VN maker, ранний
- **miku.gg**: generative VNs, ранний
- **Storio, Depthtale**: AI-powered VN creation, минимальный traction

**Gap**: НЕТ платного AI-native VN engine. Ren'Py бесплатный но требует Python. Никто не объединил "no-code + AI writing + AI art + publish" в одном продукте

### Монетизация

- Subscription $10-25/мес для creation tool
- Revenue share on published VNs
- Marketplace для AI-generated assets
- Free to play created VNs, pay to create

### Риск

Fanfiction/VN community = price-sensitive. Многие используют бесплатные инструменты. AI value-add должен быть значительным

---

## 14. AI VTuber / Virtual Idol (НОВЫЙ)

### Proof case: Neuro-sama

- **Revenue**: ~$400K/мес от subs, **$2-2.5M/год** включая subathons
- **Users**: **162K active Twitch subs** (#3 most-subscribed ever на Twitch)
- **Team**: **SOLO DEVELOPER** (Vedal987)
- **Tech**: Custom LLM + Azure TTS + Live2D + custom game AI
- **Startup cost**: $500-2000 (avatar + first year API)
- **Monthly cost**: $50-500 (API)

### Рынок

- VTuber market: **$3.06B** (2025) -> $13.62B (2033), CAGR 20.5%
- Virtual goods: 38% VTuber revenue
- Brand partnerships: 56% growth

### Open-source stack

**Open-LLM-VTuber** (GitHub, 8.9K stars): LLM + Live2D + voice, fully offline, cross-platform — ~80% technical foundation бесплатно

### Feasibility

- **Vedal987 доказал**: solo dev -> $2M+/yr
- НО: 12-24 мес минимум для monetizable audience
- "Personality engineering" — hard part (AI должен быть entertaining)
- **Top 1% capture most revenue** (whale dependency)
- Platform risk (Twitch/YouTube ban policies)

### Revenue timeline

- Month 1-3: build stack, $0
- Month 3-6: start streaming, $0-100/мес
- Month 6-12: 50-500 viewers, $500-2K/мес
- Year 2: 500-2000 viewers, $2K-10K/мес
- Moonshot: $100K-400K/мес (Neuro-sama tier, extremely unlikely)

---

## 15. AI Call of Cthulhu / Horror RPG (НОВЫЙ, NICHE TTRPG)

### Почему это лучший TTRPG niche

- **Call of Cthulhu = #2 RPG глобально** (>10% campaigns на Roll20), **#1 в Японии**
- **ZERO dedicated AI tools** для CoC
- Investigation-heavy gameplay = ИДЕАЛЬНО для LLM (текстовая дедукция, разгадывание тайн)
- Horror atmosphere через текст = сильная сторона AI (slow dread, mystery, sanity mechanics)
- Solo horror = compelling product (vs solo D&D combat which is less fun alone)
- Chaosium (издатель CoC) = friendly to third-party content

### Отличия от D&D

| D&D 5e | Call of Cthulhu |
|--------|-----------------|
| Combat-focused | Investigation-focused |
| Power fantasy | Horror / fragility |
| Level progression | Sanity degradation |
| d20 system | d100 percentile |
| Heroes grow stronger | Characters go insane or die |

### Другие underserved системы

- **Vampire: The Masquerade**: social/political intrigue = идеален для AI (conversation-heavy)
- **Ironsworn**: free, designed for solo play, natural AI companion
- **Blades in the Dark**: fiction-first, cult following, zero AI tools
- **FATE**: rules-light, AI handles easily

### Монетизация

$10-15/мес subscription, pay-per-session, или one-time + API pass-through

---

## 16. AI Kids Stories (НОВЫЙ)

Персонализированные AI-сказки на ночь с именем ребёнка и друзей.

### Proof case: Oscar Stories

- **Revenue**: $6K/мес (янв 2025), profitable
- **Users**: 50K+
- **Team**: 2 founders
- Персонализированные истории + TTS audiobook

### Рынок

- Bedtime story apps: **$1.12B** (2024) -> $3.33B (2033), 12.7% CAGR
- AI in childcare: $4.7B (2024) -> $35.2B (2034), 22.4% CAGR

### COPPA (обновлено июнь 2025)

FTC обновил COPPA (compliance deadline: апрель 2026):
- AI training на детских данных = **отдельное** согласие родителей
- Расширено PII: биометрия (voiceprints, facial templates)
- Data retention limits обязательны
- **Штрафы: $53,088 за нарушение**

### Риск: ВЫСОКИЙ

- COPPA compliance: $5-20K на правильную настройку
- Content safety: AI может сгенерировать inappropriate content
- Инцидент = catastrophic для бренда (дети = нулевая толерантность)
- Но Oscar Stories доказал: $6K/мес achievable с 2 founders

### Niche angles

- Конкретные языки/культуры (русские сказки, испанские fairy tales)
- Educational focus (math stories, science adventures)
- Print-on-demand персонализированных книг ($15-30 per book, higher margins)

---

## Рынок AI Character Chat: текущее состояние (2025-2026)

### Ключевые цифры

- **AI companion market**: $37.7B (2025) -> $435.9B (2034), 31% CAGR
- **Mobile AI companion apps**: $120M revenue (2025), 337 active apps, 220M downloads
- **Топ-10% apps** = 89% дохода категории
- **Revenue per download**: $1.18 (рост 127% от $0.52 в 2024)
- **Только ~33 apps из 337 превысили $1M lifetime revenue** (10%)
- **ARK Invest**: AI companion = $150B/год к 2030

### Новые игроки 2025-2026

- **Lollipop Chat** — #1 Character.AI alternative (2026), photorealistic images, voice
- **Moescape** (ex-Yodayo) — anime AI + image generation
- **PepHop AI** — 4600+ персонажей, Stripe payments
- **xAI Companions (Ani/Rudi)** — xAI launched animated AI companions (июль 2025)

---

## Аниме-рынок: deep dive

### Размер

| Сегмент | 2025 | Прогноз | CAGR |
|---------|------|---------|------|
| Глобальный аниме | $36-38B | $77B (2033) | 9.2% |
| Аниме мерч | $29.9B | $46.8B (2030) | 9.1% |
| Gacha (топ-5) | $2.2B+ | N/A | N/A |
| VTuber | $3.06B | $13.62B (2033) | 20.5% |
| Otome games | $5.69B | $8.88B (2030) | N/A |
| BL/Yaoi (глобально) | ~$500M+ | ~$1B (2030+) | 17%+ |

### Gacha revenue (willingness-to-pay proof)

| Игра | Revenue 2025 |
|------|-------------|
| Genshin Impact | ~$800M (mobile), $10B lifetime |
| Honkai: Star Rail | $588M |
| Fate/Grand Order | $321M (9+ лет!) |
| Love & Deepspace | **$826M за 15 мес** (OTOME!) |

### Демография

- 54% Gen Z = фанаты аниме (Crunchyroll 2025)
- Crunchyroll: 17M paying subs (3x от 5M в 2021)
- Пол: 54% M / 46% F (общее). Но active users на anime chat = до 70% F

---

## Монетизация SFW (Stripe-friendly)

### Модели

1. **Гибрид sub + tokens** (ЛУЧШАЯ, 3x прибыльнее): подписка + usage-based кредиты
2. **Tiered subscription** (56% дохода AI companion): Free -> $5-8 -> $10-15 -> $20-30/мес
3. **Freemium + paywall**: free text chat, pay for NSFW/voice/images
4. **Реклама**: только на масштабе (millions MAU)

### Revenue per user benchmarks

- AI companion apps: **$1.18 per download** (2025, +127% YoY)
- Language learning apps ARPU: $3-9/мес
- Replika: 25% free-to-paid conversion (gold standard)
- Education apps: 5-8% conversion (9.4% top performers)

---

## Успешные соло-разработчики в AI (2025-2026)

| Продукт | Revenue | Команда | Модель |
|---------|---------|---------|--------|
| Neuro-sama (VTuber) | **$2-2.5M/год** | **1 чел** | Twitch subs/donations |
| BoredHumans | $733K/мес | 1 чел | 100+ AI tools, реклама |
| HeadshotPro | $300K/мес | 1 чел | AI headshots |
| FormulaBot | $220K/мес | 1 чел (non-dev) | OpenAI wrapper |
| RIZZ | $190K/мес | small team | Dating coach |
| SiteGPT | $95K/мес | 1 чел | Custom chatbots |
| Chatbase | ~$50K MRR | 1 чел | AI chatbot builder |
| Chai Research | $40M ARR | 21 чел | AI companion |
| Candy.AI | **$25M ARR** | small, **bootstrap** | AI companion |
| NovelAI | ~$5M | <20, **$0 funded** | AI writing + anime art |

### Паттерны

1. **Lean**: Chai = $40M ARR / 21 чел. Candy = $25M ARR / bootstrap
2. **Niche down**: RIZZ (dating only), HeadshotPro (headshots only)
3. **Distribution > product**: Chatbase = TikTok, RIZZ = App Store optimization
4. **Hybrid monetization**: sub + tokens = 3x прибыльнее
5. **SFW = Stripe + App Store + Google Ads**: 75% Forbes AI 50 = Stripe

### Реалистичные цели solo dev

- **$1K MRR**: 3-6 мес
- **$5K MRR**: 6-12 мес с сильной нишей
- **$10K+ MRR**: 12+ мес, тысячи юзеров или premium pricing
- **Breakeven LLM**: при 50-200 paying users

---

## РЫНКИ КОТОРЫХ СТОИТ ИЗБЕГАТЬ (solo dev)

### AI Therapy / Mental Health — AVOID

- **Woebot ($123.5M raised) — ЗАКРЫЛСЯ** (июнь 2025). $123.5M НЕ ХВАТИЛО для FDA regulation
- **Replika** — оштрафована EUR 5M (GDPR), FTC complaint, erotic roleplay removed/restored fiasco
- **Pi.ai (Inflection, $1.3B raised)** — effectively dead. Microsoft acqui-hire $650M
- **Illinois**: запрет AI в терапии (авг 2025). Другие штаты следуют
- **Штрафы**: если пользователь причинит себе вред → иски (Character.AI sued after teen suicide)
- **Insurance**: $10-50K/год для health apps

### AI Personal Assistant — AVOID (general)

- **ChatGPT: 59.5% рынка**, $10-12B revenue, 800M users
- **Claude, Copilot, Gemini, Perplexity** = 96.3% рынка у 5 игроков
- **Solo dev building "better ChatGPT" = zero chance**
- Исключение: vertical niche ("AI assistant for immigration lawyers")

### AI Music Generation — AVOID

- **Suno: $375M funded, $2.45B valuation, $147M ARR**
- Ongoing copyright lawsuits (RIAA, Sony)
- Solo dev cannot compete on model quality
- Can only build wrappers with thin margins

---

## Бренд ChatSensei: анализ

| Позиционирование | Fit | Комментарий |
|-----------------|-----|-------------|
| Japanese/Anime Language Learning | **Идеальный** | "Sensei" = учитель по-японски |
| Anime SFW Character Chat | Хороший | "Chat" + японский vibe |
| General AI Tutor | Слабый | "Sensei" не для математики |
| Social Skills / Interview | Средний | Можно, но не ассоциируется |
| DnD Game Master | Слабый | "Sensei" ≠ фэнтези |
| Dating Coach | Слабый | Wrong associations |

### Домены

- **chatsensei.app** / **chatsensei.ai** — рассматриваются
- chatsensei.net — ЗАНЯТ
- Альтернативы: chatsensei.co, chatsensei.io, chatsensei.gg (gaming)

**ChatSensei лучше всего подходит для аниме + японский язык.** Для DnD/Social Skills/Dating нужно другое название.

---

## Unit Economics

| Статья | Стоимость |
|--------|-----------|
| LLM costs per user/мес | $0.20-3.00 |
| Hosting (VPS/Render) | $5-20/мес |
| Домен | $10-50/год |
| TTS (если нужен) | ~$0.30/user/мес |
| STT (Whisper, для lang learning) | ~$0.10/user/мес |
| **Total COGS per user** | **$0.50-3.50/мес** |
| При $9.99/мес | **50-90% gross margin** |

Multi-provider fallback (Groq free -> Cerebras free -> OpenRouter free -> paid) = cost advantage. Funded стартапы платят full price за GPT-5.

---

## Три стратегических пути

### A) ChatSensei — аниме + Japanese learning

- **Максимальный fit бренда**
- Audience proven (Janitor AI 135M, Love & Deepspace $826M)
- 90% code reuse
- Домен: chatsensei.app / chatsensei.ai
- **Потолок**: $5-15K MRR

### B) Другой бренд — высокий MRR

| Продукт | Потолок MRR | MVP | Бренд нужен |
|---------|-------------|-----|-------------|
| DnD Game Master | $10-30K | 6-10 нед | Да (фэнтези) |
| Social Skills Trainer | $15-25K | 2 нед | Да |
| Interview Coach | $15-30K | 2 нед | Да |
| Sales Training (B2B) | $20-40K | 1 мес | Да |
| Dating Coach | $10-100K | 3 нед | Да |
| Interactive Fiction | $10-50K | 2 нед | Да |

### C) Параллельная разработка

Запустить 2 продукта одновременно:
- ChatSensei (аниме/Japanese) — максимальный code reuse, быстрый запуск
- DnD GM / Dating Coach / другой — более высокий потолок MRR, но больше работы

---

## Источники

### TTRPG
- [TTRPG Market $2.15B-$6.59B](https://www.globalgrowthinsights.com/market-reports/tabletop-role-playing-game-ttrpg-market-103239)
- [AI Dungeon Pricing](https://play.aidungeon.com/pricing)
- [AI Dungeon Wikipedia](https://en.wikipedia.org/wiki/AI_Dungeon)
- [Latitude Seed $3.3M - TechCrunch](https://techcrunch.com/2021/02/04/latitude-seed-funding/)
- [Friends & Fables Pricing](https://fables.gg/pricing)
- [Friends & Fables 2024 Year in Review](https://fables.gg/blog/ff-2024-year-in-review-and-2025-preview)
- [Hidden Door Press Kit](https://www.hiddendoor.co/press)
- [Hidden Door Revenue $1.7M](https://getlatka.com/companies/hiddendoor.co)
- [SRD 5.2 CC-BY-4.0](https://www.dndbeyond.com/srd)
- [SRD 5.2 Explainer - ScreenRant](https://screenrant.com/dnd-2024-srd-52-creative-commons-license-explainer/)
- [WotC AI Art Policy](https://dnd-support.wizards.com/hc/en-us/articles/26243094975252-Generative-AI-art-FAQ)
- [Hasbro CEO pro-AI](https://boundingintocomics.com/tabletop-games/hasbro-ceo-confirms-generative-ai-to-play-heavy-role-in-future-of-dungeons-dragons-says-technologys-popularity-is-a-clear-signal-that-we-need-to-be-embracing-it/)
- [Archivist AI](https://www.myarchivist.ai/)
- [Vellum AI TTRPG](https://www.vellum-ai.com/)

### AI Companion Market
- [AI Companion $37.7B-$435B](https://www.precedenceresearch.com/ai-companion-market)
- [AI Companion Apps $120M 2025 - TechCrunch](https://techcrunch.com/2025/08/12/ai-companion-apps-on-track-to-pull-in-120m-in-2025/)
- [Character.AI $50M Revenue](https://completeaitraining.com/news/character-ai-2025-by-the-numbers-20m-maus-322m-revenue-1b/)
- [Character.AI Statistics - Business of Apps](https://www.businessofapps.com/data/character-ai-statistics/)
- [Chai AI $40M ARR](https://finance.yahoo.com/news/chai-reaches-over-30m-arr-123500699.html)
- [Chai AI $55M Funding](https://www.ainvest.com/news/chai-ai-55m-surge-leading-ugai-revolution-booming-mobile-ai-landscape-2507/)
- [Candy.AI $25M ARR](https://tripleminds.co/blogs/strategies/candy-ai-revenue-models/)
- [Janitor AI 135M visits](https://www.semrush.com/website/janitor.ai/overview/)
- [Moemate Shutdown](https://www.softwarecurio.com/blog/moemate-ai-review-the-untold-story-of-its-rise-and-fall/)
- [SillyTavern 500K Users](https://github.com/SillyTavern/SillyTavern)
- [Replika 25% Conversion](https://www.techbuzz.ai/articles/breaking-ai-companion-apps-hit-120m-revenue-run-rate)

### Аниме
- [Anime Market $36-38B](https://www.grandviewresearch.com/industry-analysis/anime-market)
- [54% Gen Z = anime fans](https://www.animenewsnetwork.com/interest/2025-05-23/crunchyroll-research-over-half-of-gen-z-globally-are-anime-fans/.224732)
- [Otome Games $5.69B](https://otome.com/2025/06/06/female-gamers-are-reshaping-the-market/)
- [BL Industry Growth](https://www.dramallama.app/post/bl-industry-growth-how-the-fandom-exploded-in-2024-25)
- [VTuber Market $3.06B](https://www.skyquestt.com/report/vtuber-market)
- [AI Anime Generator $91B](https://www.grandviewresearch.com/industry-analysis/ai-anime-generator-market-report)
- [Disney C&D Character.AI](https://deadline.com/2025/09/disney-cease-and-desist-letter-characterai-copyright-infringement-1236566831/)
- [Character.AI Lawsuits](https://socialmediavictims.org/character-ai-lawsuits/)

### Language Learning
- [Duolingo $1B Revenue](https://chiefaiofficer.com/blog/how-duolingos-ai-first-strategy-drove-51-user-growth-and-1-billion-revenue-forecast/)
- [Speak $100M ARR, $1B Valuation](https://finance.yahoo.com/news/1-billion-ai-startup-backed-144613265.html)
- [Praktika $20M ARR](https://getlatka.com/companies/praktika.ai)
- [ELSA $32.5M](https://getlatka.com/companies/elsaspeak.com)
- [Language Learning Apps $7.36B](https://straitsresearch.com/report/language-learning-apps-market)
- [Meta-analysis chatbots L2 g=0.608](https://onlinelibrary.wiley.com/doi/full/10.1111/ijal.12668)
- [Speech-to-Text Pricing](https://vocafuse.com/blog/best-speech-to-text-api-comparison-2025/)

### Writing Tools
- [Grammarly $700M ARR](https://sacra.com/c/grammarly/)
- [Jasper $142.9M](https://electroiq.com/stats/jasper-ai-statistics/)
- [Sudowrite $3M Funding](https://www.crunchbase.com/organization/sudowrite)
- [NovelAI $5M](https://getlatka.com/companies/novelai.net)
- [Novelcrafter](https://www.novelcrafter.com/pricing)

### Dating Coach
- [Rizz 10M Users $190K MRR](https://www.aibase.com/cases/156)
- [Online Dating $11B](https://straitsresearch.com/report/online-dating-market)
- [AI Dating Ethics](https://reason.com/volokh/2025/07/12/the-role-and-ethics-of-ai-use-in-online-dating/)

### Interactive Fiction
- [Episode Interactive Revenue](https://growjo.com/company/Episode)
- [Interactive Fiction Market $1.42B](https://dataintelo.com/report/interactive-fiction-market)
- [AI Story Generator $1.4B-$14.7B](https://www.statsndata.org/report/interactive-fiction-market-269070)

### VTuber
- [Neuro-sama Revenue](https://starstat.yt/ch/neuro-sama-ch-vedal-ai-net-worth)
- [Neuro-sama 162K Subs](https://streamscharts.com/channels/vedal987/subscribers)
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)
- [AI VTubers Earning Millions](https://www.cnbc.com/2025/07/02/ai-virtual-personality-youtubers-or-vtubers-are-earning-millions.html)

### Kids Stories
- [Bedtime Story Apps $1.12B](https://dataintelo.com/report/bedtime-story-apps-for-kids-market)
- [Oscar Stories $6K/mo](https://www.starterstory.com/oscar-personal-bedtime-stories-for-kids-breakdown)
- [COPPA 2025 Final Rule](https://securiti.ai/ftc-coppa-final-rule-amendments/)

### Mental Health (AVOID)
- [Woebot Shutdown](https://www.statnews.com/2025/07/02/woebot-therapy-chatbot-shuts-down-founder-says-ai-moving-faster-than-regulators/)
- [Replika Fined EUR 5M](https://www.edpb.europa.eu/news/national-news/2025/ai-italian-supervisory-authority-fines-company-behind-chatbot-replika_en)
- [Illinois AI Therapy Ban](https://www.axios.com/local/chicago/2025/08/06/illinois-ai-therapy-ban-mental-health-regulation)

### Solo Dev Success
- [Solo AI SaaS Success Stories 2026](https://crazyburst.com/ai-saas-solo-founder-success-stories-2026/)
- [44% profitable SaaS = solo founders](https://medium.com/@theabhishek.040/solo-developers-building-100k-1m-revenue-micro-saas-2024-110838470a2a)
- [Stripe AI Monetization](https://stripe.com/resources/more/ai-monetization-strategies)
