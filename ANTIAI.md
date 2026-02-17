# Anti-AI Detection & SEO Audit

## Google AI Content Detection (2025-2026)

### Как Google обнаруживает AI-контент

**SpamBrain** — основная система, использует:
- Структуру текста и лингвистические паттерны (perplexity, burstiness)
- Глубину и оригинальность контента
- Фактическую последовательность
- Скорость публикации относительно размера команды

**SynthID** — водяные знаки в контенте от моделей Google (Gemini). Не применяется к OpenRouter/Groq/Cerebras.

**Лингвистические отпечатки:**
- Низкая perplexity (предсказуемый текст)
- Низкая burstiness (однообразная длина предложений)
- Артефакты токенизации
- Шаблонные структуры на множестве страниц

### Риски для сайта с LLM-контентом

| Риск | Уровень | Описание |
|------|---------|----------|
| AI-описания персонажей | Средний | generate-from-story и автогенерация создают LLM-текст |
| Шаблонные страницы | Средний | Все страницы персонажей — одинаковая структура |
| Переведённый контент | Средний | 7× страниц с machine-translated текстом |
| Скорость публикации | Средний | Автогенерация 1 персонаж/день |
| Фейковые счётчики | Средний | Inflated stats видны в prerender |
| Тонкие страницы | Средний | Короткие описания без unique value |

### Google Helpful Content Update (Dec 2025)

- Mass-produced AI content без oversight: **87% негативное влияние**
- Тонкий affiliate контент: **71% падение трафика**
- Ключевой принцип: Google оценивает **intent, не method** — контент для пользователей ОК, контент для манипуляции ранжированием — нет

### E-E-A-T сигналы

- **Experience**: реальные пользователи, реальная активность
- **Expertise**: глубокие описания, About/FAQ/Terms
- **Authoritativeness**: внешние ссылки, бренд, социальные сети
- **Trustworthiness**: точная информация, прозрачность, модерация

---

## AI-маркерные слова и фразы

### Запрещённые слова (RU)
«пронизан», «гобелен», «поистине», «бесчисленный», «многогранный», «неотъемлемый», «является», «представляет собой», «в рамках», «стоит отметить», «важно подчеркнуть», «таким образом», «волна [эмоции]», «нахлынувшее чувство», «пронзительный взгляд», «воздух, наполненный [чем-то]», «не смогла сдержать»

### Запрещённые слова (EN)
'delve', 'tapestry', 'testament', 'realm', 'landscape', 'beacon', 'indelible', 'palpable', 'a wave of [emotion]', 'a surge of [feeling]', 'couldn't help but', 'eyes that held [emotion]', 'piercing gaze', 'the air was thick with', 'sent a shiver down'

### Другие маркеры
- Длинное тире `—` (заменено на дефис `-` во всех промптах)
- Единообразная длина предложений (3+ подряд одной длины — запрещено)
- Hedging phrases: "It's important to note that...", "It's worth mentioning..."
- Crutch words: feeling/realizing/understanding, чувствуя/понимая/осознавая
- Overuse of adverbs: meticulously, seamlessly, intricate
- Template pattern: `*does X* text *does Y*`

---

## SEO Audit (Feb 2026)

### Критические проблемы

#### 1. Русский текст на английских prerender-страницах
- **Где**: `/api/seo/home`, `/api/seo/tags/*`
- **Проблема**: Список персонажей в body не переводится. На `/en` Google видит русские имена и tagline
- **Файлы**: `backend/app/seo/router.py`
- **Фикс**: Применить перевод к character list в prerender home и tags

#### 2. og:image — SVG
- **Где**: `frontend/index.html`, `frontend/public/og-image.svg`
- **Проблема**: Facebook, Twitter, WhatsApp не рендерят SVG превью
- **Фикс**: Конвертировать в PNG 1200×630, обновить ссылки

#### 3. Hreflang мисмэтч (3 vs 7 языков)
- **Где**: `frontend/src/components/seo/SEO.tsx` (строки 52-55)
- **Проблема**: Фронтенд генерирует hreflang для en/es/ru, но sitemap и prerender — для 7 языков
- **Фикс**: Добавить fr/de/pt/it в SEO.tsx

#### 4. FAQ prerender неполный (6 из 12)
- **Где**: `backend/app/seo/router.py` (строки 263-269)
- **Проблема**: Prerender FAQ имеет 6 вопросов, фронтенд — 12. Google теряет 6 rich snippets
- **Фикс**: Синхронизировать все 12 вопросов, перевести на все 7 языков

#### 5. Нет prerender для /about, /terms, /privacy
- **Где**: `deploy/nginx/nginx-ssl.conf`, `backend/app/seo/router.py`
- **Проблема**: Страницы в sitemap, но боты видят пустой SPA-shell
- **Фикс**: Добавить prerender endpoints + nginx rules

### Средние проблемы

#### 6. Organization JSON-LD отсутствует в prerender home
- **Где**: `backend/app/seo/router.py` (home endpoint)
- **Фикс**: Добавить Organization в @graph

#### 7. BreadcrumbList отсутствует в prerender персонажей
- **Где**: `backend/app/seo/router.py` (character endpoint)
- **Фикс**: Добавить BreadcrumbList schema

#### 8. Короткие meta description на персонажах
- **Где**: `backend/app/seo/router.py` (строка ~136)
- **Проблема**: Если только tagline — 20-40 символов. Google рекомендует 120-160
- **Фикс**: Конкатенировать tagline + scenario snippet

#### 9. FAQ заголовки h1→h3 (пропущен h2)
- **Где**: `backend/app/seo/router.py` (строка ~323)
- **Фикс**: Заменить h3 на h2

#### 10. Нет og:image на tag-страницах и FAQ
- **Фикс**: Добавить дефолтный og-image

#### 11. Нет twitter tags на главной и FAQ
- **Фикс**: Добавить twitter:title/twitter:description

### Низкоприоритетные (все исправлены)

- ~~og:type `article` для персонажей вместо `website`~~ ✅
- ~~og:locale для языковых версий~~ ✅
- ~~ISO 8601 даты без timezone в JSON-LD~~ ✅ (UTC `Z` suffix)
- ~~Плоская heading structure на персонажах (только h1)~~ ✅
- ~~RSS — русские имена на /en ссылках~~ ✅ (EN translations)
- ~~`<img>` отсутствует в body prerender персонажа~~ ✅

---

## Реализованные меры

### Промпты (prompt_builder.py)
- [x] Замена длинных тире `—` на дефисы `-` (все 7 языков)
- [x] Запрет AI-маркерных слов (RU: 17 слов/фраз, EN: 15)
- [x] Вариация длины предложений (3 подряд одной длины — запрещено)
- [x] Автономность персонажа (не слепо выполняет команды юзера)
- [x] Anti-repetition rules (7 языков)

### Автогенерация (character_generator.py)
- [x] Запрет длинного тире в генерации
- [x] Anti-AI humanizer (text_humanizer.py) — ~30 клише → замены

### Аналитика
- [x] Bot detection (is_bot) — боты исключены из статистики
- [x] OS detection, traffic sources classification

### SEO Anti-AI (prerender для ботов)
- [x] Убраны фейковые счётчики из JSON-LD (только real chat_count, без base_chat_count)
- [x] interactionStatistic скрыт при 0 чатов (нет подозрительных нулей)
- [x] Anti-template: 6 вариантов заголовков h2 для каждой секции (About/Story/Background/...)
- [x] Anti-template: ротация порядка секций на основе hash(slug) — каждый персонаж уникален
- [x] Anti-template: 6 вариантов CTA-текста (Chat with.../Start a conversation.../Talk to...)
- [x] `<img>` аватар в body prerender с alt-текстом
- [x] Personality секция добавлена в prerender body
- [x] Creator attribution в body (Created by + date)
- [x] `og:locale` на всех prerender страницах (home, tags, characters)
- [x] `inLanguage` в JSON-LD (character + collection)
- [x] ISO 8601 с UTC timezone (`Z` suffix) в JSON-LD
- [x] `isPartOf: WebSite` в character JSON-LD (E-E-A-T)
- [x] RSS feed — EN translations для имён и описаний

---

## TODO (SEO фиксы) — все выполнены

- [x] Перевод character list в prerender home и tags
- [x] og:image SVG → PNG 1200×630
- [x] Hreflang 7 языков в SEO.tsx
- [x] FAQ prerender — все 12 вопросов × 7 языков
- [x] Prerender для /about, /terms, /privacy
- [x] Organization JSON-LD в prerender home
- [x] BreadcrumbList в prerender персонажей
- [x] Улучшить meta description персонажей
- [x] FAQ h3 → h2
- [x] og:image на tag pages и FAQ
- [x] twitter tags на главной и FAQ
- [x] noindex для тонких страниц персонажей
- [x] Quality gates для sitemap
- [x] Убрать фейковые счётчики из prerender/JSON-LD
- [x] Anti-template вариативность (заголовки, порядок секций, CTA)
- [x] E-E-A-T сигналы (author, datePublished, isPartOf, inLanguage)
- [x] RSS — EN translations
- [x] og:locale на всех страницах
