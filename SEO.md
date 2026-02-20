# План продвижения sweetsin.cc

## Tier 1 — Автоматизация (код)

### 1. Технический SEO ✅
- [x] hreflang + language prefixes (3 языка: en/es/ru)
- [x] Sitemap с xhtml:link alternates (статика + все персонажи × 3 языка)
- [x] JSON-LD CreativeWork на персонажах
- [x] Prerender для ботов (nginx user-agent match → backend HTML)
- [x] Open Graph + Twitter Cards мета-теги (SEO компонент + prerender)
- [x] `<meta name="description">` на всех страницах (SEO компонент)
- [x] robots.txt (Disallow /api/, /chat/, /profile, /admin/, /auth, /create)
- [x] JSON-LD: FAQPage (на /faq), BreadcrumbList (на персонажах и тег-страницах)
- [x] JSON-LD: Organization (на главной, @graph с WebSite)

### 2. Лендинги под категории/теги ✅
- [x] Страницы `/en/tags/{tag}` — fantasy, romance, anime, modern
- [x] SEO title/description/JSON-LD CollectionPage + BreadcrumbList
- [x] Nginx prerender для ботов
- [x] Добавлено в sitemap (priority 0.7, weekly)

### 3. Скорость загрузки ✅
- [x] Lazy loading аватаров (native `loading="lazy"` + `decoding="async"`)
- [x] WebP конвертация при загрузке аватаров (Pillow, quality=85, 512x512 max)
- [x] Preload: Inter font (Google Fonts + preconnect), Tailwind fontFamily
- [x] Code splitting — React.lazy для 11 тяжёлых страниц

### 4. Социальные шеры ✅
- [x] Кнопки "Поделиться" на CharacterPage (X, Telegram, WhatsApp, Reddit, Copy)
- [x] Native Web Share API (мобильный share-диалог)
- [x] Текст шера с именем и tagline

### 5. RSS / Atom фид ✅
- [x] `/feed.xml` — RSS 2.0, 30 последних персонажей, enclosure с аватарами

### 6. Email-маркетинг
- [x] Email при регистрации нового пользователя (уведомление админам)
- [ ] Welcome email пользователю при регистрации (3 популярных персонажа)
- [ ] Weekly digest "Новые персонажи" (крон)

### 7. Внутренняя перелинковка ✅
- [x] "Похожие персонажи" блок на CharacterPage (по тегам)
- [x] "Популярные персонажи" блок в футере (8 персонажей, кеш)

### 8. Рейтинги
- [ ] Отзывы/рейтинги на персонажей (1-5 звёзд)
- [ ] AggregateRating в JSON-LD

### 9. Автопостинг
- [ ] Telegram бот — новые персонажи
- [ ] Twitter/X бот (нужен dev account)

### 10. Многоязычный контент ✅
- [x] SEO-тексты на главной для каждого языка (hero section)
- [x] Автоопределение языка из navigator.language
- [x] Переключение языка в AgeGate

---

## Tier 2 — Нужна помощь (аккаунты/доступы)

### 11. Google Search Console + Analytics ✅
- [x] Домен подтверждён, sitemap отправлен
- (Своя аналитика уже есть: pageviews, unique visitors, страны, устройства, модели)

### 12. Bing Webmaster Tools ⚠️
- [x] Submit sitemap — отправлен
- ⚠️ "Discovered but not crawled" — Bing нашёл URL, но не индексирует
- [x] SEO softening (feb 2026): убраны "NSFW"/"uncensored" из мета, NSFW-тэглайны скрыты от ботов, `<meta name="rating" content="adult">` для NSFW-персонажей, sitemap priority 0.4, robots.txt `/*nsfw*`

### 13. Twitter/X dev account
- Нужно: создать аккаунт + API ключи
- Сделаю: бот автопостинга новых персонажей

### 14. Telegram канал
- Нужно: создать канал + бота
- Сделаю: интеграция автопостинга

### 15. Каталоги AI
- theresanaiforthat.com, futurepedia.io, toolify.ai, aitoptools.com
- Сделаю: тексты для подачи

---

## Tier 3 — Ручная работа

### 16. Reddit / форумы
- r/CharacterAI, r/SillyTavern, r/AIDungeon, r/NSFW_AI
- Посты с примерами персонажей, AMA, отзывы

### 17. Контент-маркетинг
- Статьи/гайды на Medium, Dev.to, Habr
- "How to create the perfect AI character", "Best AI roleplay platforms 2026"

### 18. Линкбилдинг
- Гостевые посты, обмен ссылками с AI-блогами

### 19. Платная реклама
- Google Ads, Twitter ads, Reddit ads

---

## Приоритеты — что делать дальше

| # | Задача | Усилие | Эффект | Статус |
|---|--------|--------|--------|--------|
| 1 | **Google Search Console** — submit sitemap | Низкое (нужен доступ) | Высокий | ✅ Готово |
| 2 | **Каталоги AI** — подача на 4-5 платформ | Низкое (ручная) | Высокий | Не начато |
| 3 | **Reddit посты** — r/CharacterAI, r/SillyTavern | Низкое (ручная) | Высокий | Не начато |
| 4 | **Welcome email** с 3 популярными персонажами | Среднее (код) | Средний | Не начато |
| 5 | **Telegram канал** + автопостинг | Среднее (код + канал) | Средний | Нужен канал |
| 6 | **Рейтинги персонажей** + AggregateRating | Среднее (код) | Средний | Не начато |
| 7 | **Preload ресурсов** + code splitting | Низкое (код) | Средний | ✅ Готово |
| 8 | **Блок "Популярные"** в футере | Низкое (код) | Низкий | ✅ Готово |
