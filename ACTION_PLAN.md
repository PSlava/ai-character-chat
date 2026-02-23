# GrimQuill — Action Plan

## Phase 0: Critical — Get Indexed
- [x] Google Search Console — verify grimquill.io (**done**)
- [x] Bing Webmaster Tools — verify (**done**)
- [x] Fix sitemap — generate slugs for all 27 adventures (**done**, 260 URLs)
- [x] robots.txt — verified, no accidental blocks
- [x] Submit sitemap in GSC + Bing (**done**, grimquill.io/sitemap.xml)
- [x] Indexation monitoring — daily cron, `/opt/ai-chat/indexation.log`
- [x] Favicon — vector SVG (purple quill) + .ico + apple-touch-icon (**done**)
- [ ] Request indexing for key pages (home, /campaigns, top 5 adventures)
- [ ] Submit to AI directories — TAIFT, Futurepedia, AlternativeTo, IFDB

## Phase 1: SEO Foundation (1-2 weeks)
- [ ] VideoGame + SoftwareApplication JSON-LD schema on home page
- [ ] AggregateRating JSON-LD on adventures (when ratings implemented)
- [ ] More tag landing pages (horror, sci-fi, mystery, adventure — currently only fantasy/romance/anime/modern)
- [ ] Multilingual keyword-rich meta descriptions per genre
- [ ] Blog section with first 3 articles (AI Dungeon alternatives, best text adventures, D&D solo with AI)

## Phase 2: Retention Features (1-3 months)
- [ ] Visual Character Sheet UI — display HP, stats, inventory from [STATE] data
- [ ] Undo/Retry ("Rewrite Fate") — regenerate last response with different outcome
- [ ] Achievement System — badges for adventures started/completed, dice rolls
- [ ] Adventure Ratings — completion detection + 1-5 stars

## Phase 3: Growth Features (3-6 months)
- [ ] Mid-story scene illustrations (DALL-E on dramatic moments)
- [ ] Story Checkpoints ("Save Your Fate" — bookmark + fork)
- [ ] Daily Challenges — themed mini-adventures with XP
- [ ] User-Created Adventures — template editor for community content

## Marketing (Ongoing)
- [ ] Reddit presence — r/AIDungeon, r/Solo_Roleplaying, r/interactivefiction
- [ ] Listicle outreach — email "AI Dungeon alternatives" article authors
- [ ] Product Hunt launch — coordinate with feature release
