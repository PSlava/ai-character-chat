# Продвижение SweetSin + GrimQuill

---

## ЧАСТЬ 1: SweetSin (sweetsin.cc) — Текущий SEO

### Технический SEO ✅ (всё сделано)
- [x] hreflang + language prefixes (7 языков)
- [x] Sitemap с alternates (статика + персонажи × 7 языков)
- [x] JSON-LD: CreativeWork, FAQPage, BreadcrumbList, Organization, WebSite
- [x] Prerender для ботов (nginx user-agent match → backend HTML)
- [x] OG + Twitter Cards, meta description на всех страницах
- [x] robots.txt (Disallow /api/, /chat/, /profile, /admin/, /auth, /create)
- [x] RSS `/feed.xml` (30 последних персонажей)
- [x] Code splitting (React.lazy, 11 страниц), WebP, lazy loading
- [x] Кнопки "Поделиться" (X, Telegram, WhatsApp, Reddit, Copy)
- [x] Лендинги `/en/tags/{tag}` (fantasy, romance, anime, modern)
- [x] Внутренняя перелинковка ("Похожие" + "Популярные" в футере)
- [x] Google Search Console — sitemap отправлен
- [x] SEO softening (NSFW скрыт от ботов, `rating: adult`, priority 0.4)

### Не сделано (SweetSin)
- [ ] Welcome email с популярными персонажами
- [ ] Рейтинги персонажей + AggregateRating JSON-LD
- [ ] Telegram канал + автопостинг
- [ ] Twitter/X бот
- [ ] Каталоги AI (подача)
- [ ] Reddit посты

---

## ЧАСТЬ 2: GrimQuill (grimquill.io) — Анализ конкурентов

### Рынок
- Interactive fiction: **$4.3B (2025) → $7.8B (2032)**, 12% CAGR
- AI story generator: **$1.5B (2025) → $7.5B (2033)**, 25% CAGR

### Конкуренты

| Платформа | Цена | Трафик | Ключевые фичи | Угроза |
|-----------|------|--------|---------------|--------|
| **Perchance AI RPG** | Бесплатно, без регистрации | Растёт +3.4%/мес | Zero friction, creator ecosystem | **ВЫСОКАЯ** |
| **Friends & Fables** | $15-40/мес | Растёт | Full D&D 5e, multiplayer (6 игроков), карты | **ПРЯМАЯ** (D&D) |
| **AI Dungeon** | $10-50/мес | Падает -60% | Первопроходец, сценарии, мобильные приложения | Средняя (вакуум!) |
| **NovelAI** | $10-25/мес | ~8M/мес | Lorebook (эталон), Erato 70B, приватность | Средняя |
| **Character.AI** | Бесплатно/$10 | ~153M/мес | Stories (ноя 2025), 20M+ MAU | Средняя |
| **AI Game Master** | $15-25/мес | Растёт | Mobile native (iOS/Android), free-text combat | Средняя |
| **DreamGen** | $8-30/мес | Растёт | Без цензуры, story steering, open-source | Низкая |
| **RPGGO** | Freemium (coins) | Растёт | Геймификация (daily tasks, coins), creator tool | Низкая |
| **FictionLab** | Бесплатно | Новый | 70B модели, без цензуры, unlimited | Растущая |
| **Hidden Door** | Free (EA) | Новый | Card collecting, лицензированные миры | Низкая |

### Что пользователи хотят больше всего (Reddit, отзывы)
1. **Долгосрочная память** — 73% жалуются на потерю контекста
2. **Без цензуры** — AI Dungeon "Filtergate", Character.AI "lobotomization"
3. **Качественная проза** — без "smiles softly", без AI-клише
4. **Доступная цена** — $10-15/мес sweet spot, $30+ = "gouging"
5. **Приватность** — без модераторов, без обучения на данных
6. **Multiplayer** — огромный gap в рынке
7. **Картинки в повествовании** — сцены, не только аватары
8. **RPG механики** — дайсы, чарлисты, левелинг, HP

### Козыри GrimQuill
1. **Бесплатно** (конкуренты $15-40/мес за D&D)
2. **7 языков** (ни один конкурент не предлагает больше 1-2)
3. **27 curated adventures** в 12+ жанрах
4. **Server-side dice rolling** + encounter state
5. **Литературное качество** (anti-AI, anti-repetition rules)
6. **9 LLM провайдеров** с auto-fallback

### Критические gaps
1. **Нет character sheet UI** (данные есть на бэке в [STATE], нет визуализации)
2. **Нет save points / branching** (линейный чат)
3. **Нет картинок в повествовании** (только аватары)
4. **Нет геймификации** (ни ачивок, ни стриков, ни челленджей)
5. **Нет UGC** (все истории от админа, нет контентного маховика)
6. **Не индексируется Google** (`site:grimquill.io` = 0 результатов)

---

## ЧАСТЬ 3: SEO-стратегия GrimQuill

### КРИТИЧНО: Индексация Google
`site:grimquill.io` = 0 результатов. Без этого ничего не работает.
- [ ] Google Search Console — верификация + sitemap
- [ ] Проверить robots.txt на блокировки
- [ ] Request indexing для ключевых страниц
- [ ] Backlinks от директорий для запуска crawl

### Ключевые слова

| Кластер | Объём/мес | Конкуренция | Приоритет |
|---------|----------|-------------|-----------|
| `AI dungeon alternative` | 100K-300K+ | Высокая | **Критический** |
| `AI text adventure` | 10K-30K | Средняя | **Высокий** |
| `AI interactive fiction` | 2K-5K | Низкая | **Высокий** (goldmine) |
| `AI dungeon master` / `AI DM` | 5K-15K | Средняя | **Высокий** |
| `play D&D with AI` | 3K-8K | Низкая | **Высокий** |
| `free text adventure game online` | 3K-8K | Низкая | **Высокий** |
| `AI story generator` | 30K-50K | Высокая | Высокий |
| `choose your own adventure AI` | 5K-10K | Средняя | Средний |

**Мультиязычные** (LOW competition, untapped):
- ES: `aventura interactiva IA gratis`, `IA master de mazmorra`
- FR: `fiction interactive IA`, `jeu de role IA gratuit`
- DE: `KI Textabenteuer`, `KI Dungeon Master`
- RU: `AI текстовая игра`, `интерактивная фантастика ИИ`
- PT/IT: аналогично

### AI директории (подать немедленно)

**Tier 1 (DA 70+)**:
- There's An AI For That (DR 76)
- Futurepedia (DR 69+)
- Product Hunt (launch day)
- AlternativeTo (как AI Dungeon alternative)

**Tier 2**: TopAI.tools, Toolify.ai, AI Scout, StartupAITools
**Нишевые**: IFDB, itch.io, intfiction.org

### Listicle Outreach (email авторам)
- DreamGen: "11 Best AI Dungeon Alternatives"
- Maestra: "Top 6 AI Dungeon Alternatives"
- RigorousThemes: "13 Best AI Dungeon Alternatives"
- Mockey: "26 Best AI Dungeon Alternatives"
- CyberNews: "Top 10 AI Story Generators"
- AllAboutAI: "Best AI Tools for Interactive Fiction"

### Контент-маркетинг (блог)

**Tier 1**: "Best AI Dungeon Alternatives 2026", "10 Best AI Text Adventure Games Free"
**Tier 2**: "How to Play D&D Solo with AI", "Can AI Be a Good Dungeon Master?"
**Tier 3**: "Best Dark Fantasy AI Adventures", "Cyberpunk Interactive Fiction AI"

### Сообщества

| Платформа | Приоритет | Где |
|-----------|-----------|-----|
| Reddit | **#1** | r/AIDungeon, r/Solo_Roleplaying, r/DnD, r/interactivefiction |
| YouTube | **#2** | Let's play видео, туториалы |
| TikTok | **#3** | Короткие клипы драматических моментов |
| Discord | #4 | Свой сервер |

### Schema Markup (добавить)
```json
{
  "@type": ["VideoGame", "SoftwareApplication"],
  "name": "GrimQuill - AI Interactive Fiction",
  "applicationCategory": "GameApplication",
  "offers": {"price": "0", "priceCurrency": "USD"},
  "genre": ["Interactive Fiction", "Role-playing Game", "Text Adventure"],
  "playMode": "SinglePlayer",
  "inLanguage": ["en", "es", "ru", "fr", "de", "pt", "it"]
}
```

---

## ЧАСТЬ 4: План фич GrimQuill (по приоритету)

### Tier 1: High Impact, 1-3 месяца

| # | Фича | Усилие | Эффект | Референс |
|---|------|--------|--------|----------|
| A | **Visual Character Sheet** (HP, статы, инвентарь из [STATE]) | Среднее | **Высокий** | Friends & Fables |
| B | **Story Checkpoints** ("Save Your Fate" — bookmark + fork) | Среднее | **Высокий** | StoryPlay X |
| C | **Undo/Retry** ("Rewrite Fate" — регенерация с другим исходом) | Низкое | **Средний** | AI Dungeon |
| D | **Achievement System** (бейджи, прогресс, завершённые истории) | Низкое | **Высокий** | RPGGO, Hidden Door |
| E | **Guided Onboarding** (3 шага: жанр → история → играть) | Низкое | **Средний** | Индустрия |

### Tier 2: Medium Impact, 3-6 месяцев

| # | Фича | Усилие | Эффект | Референс |
|---|------|--------|--------|----------|
| F | **Mid-Story Scene Illustrations** (DALL-E на драматических моментах) | Среднее | **Высокий** | AI Dungeon, AI GM |
| G | **User-Created Adventures** (шаблоны, которые играют другие) | Среднее | **Высокий** | AI Dungeon, RPGGO |
| H | **Daily Challenges** (тематические мини-приключения, XP) | Низкое | **Средний** | RPGGO, Duolingo |
| I | **Campaign Journal** (авто-извлечение NPC, локаций, предметов) | Среднее | **Средний** | Archivist |
| J | **Adventure Ratings** (завершение + 1-5 звёзд) | Низкое | **Средний** | StoryNight |

### Tier 3: Ambitious, 6-12 месяцев

| # | Фича | Усилие | Эффект | Референс |
|---|------|--------|--------|----------|
| K | **Voice Narration** (Web Speech API / ElevenLabs) | Среднее | **Средний** | RPGGO |
| L | **Multiplayer Co-op** (2-4 игрока + AI GM) | Высокое | **Средний** | Friends & Fables |
| M | **Ambient Audio** (атмосферные лупы по сцене) | Среднее | **Низкий** | EndlessVN |
| N | **Collectible Cards** ("Fate Cards" — NPC/предметы за завершение) | Низкое | **Средний** | Hidden Door |
