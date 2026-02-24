# Frontend Architecture (`frontend/src/`)

## Libraries & API Clients

- **`lib/supabase.ts`** — NOT Supabase SDK. Just localStorage helpers for token/user.
- **`lib/pow.ts`** — Browser-side Proof-of-Work solver using SubtleCrypto API. `solveChallenge(challenge, difficulty=4)` finds nonce where SHA256 starts with N hex zeros (~65k iterations, ~100ms).
- **`lib/utils.ts`** — Includes `isCharacterOnline(characterId)` — deterministic ~33% online status based on `hash(id + currentHour) % 3 === 0`.
- **`api/client.ts`** — Axios with JWT auto-injection from localStorage.
- **`api/characters.ts`** — `wakeUpServer()` pings `/health` every 3s for up to 3 min. `getOpenRouterModels()` fetches model registry. `voteCharacter()`, `getUserVotes()`, `forkCharacter()`, `getCharacterRelations()`.
- **`api/chat.ts`** — `createChat(characterId, model?, personaId?, forceNew?)`, `deleteChat()`, `clearChatMessages()`, `deleteChatMessage()`, `getOlderMessages(chatId, beforeId)` for infinite scroll. `generatePersonaReply(chatId)` for ghostwriting as persona.
- **`api/personas.ts`** — `getPersonas()`, `createPersona()`, `updatePersona()`, `deletePersona()`, `getPersonaLimit()` (used/limit), `checkPersonaSlug()` (debounced availability check).
- **`api/reports.ts`** — `createReport(characterId, reason, details?)`, `getReports(status?)`, `updateReport(reportId, status)`.
- **`api/export.ts`** — `getExportUrl(characterId)` for download, `importCharacter(card)` for SillyTavern card import.
- **`api/stats.ts`** — `getStats()` fetches public site statistics (users, messages, characters, online_now).
- **`api/admin.ts`** — Admin API client: getPrompts, updatePrompt, resetPrompt, getProviderStatus.

## Hooks & State

- **`hooks/useChat.ts`** — SSE streaming via `@microsoft/fetch-event-source`. `GenerationSettings` includes model, temperature, top_p, top_k, frequency_penalty, max_tokens. Updates user message ID from `done` event. Uses `messagesRef` (always synced via `setMessages` wrapper) for reliable reads in `regenerate`/`resendLast` — avoids React 18 setState batching issues where updater side-effects are deferred.
- **`store/`** — Zustand: `authStore` (with role, clears votes+favorites on logout), `chatStore`, `favoritesStore`, `votesStore` (optimistic updates, loaded on login).
- **`locales/`** — i18n via react-i18next. `en.json`, `es.json`, `ru.json`, `fr.json`, `de.json`, `pt.json`, `it.json` (~540 keys each). Default: English. Language stored in localStorage.

## Pages

- **`pages/`** — Home (tag filters, gender filter pills, featured character, ContinueAdventure CTA), Chat (+ new chat button), CharacterPage (online dot, report, export, vote, fork, highlights, connections), CreateCharacter (manual + story + SillyTavern import), EditCharacter, Auth (+ Google OAuth), OAuthCallbackPage, Profile (stats grid, XP bar, achievements), LeaderboardPage (sort by level/messages/adventures), CampaignsPage, CampaignDetailPage, AdminPromptsPage, AdminUsersPage, AdminReportsPage, AboutPage (10 feature cards), TermsPage, PrivacyPage, FAQPage (12 Q&A, JSON-LD).

## Components

### Layout
- **`components/layout/Footer.tsx`** — Site footer with links to About, Terms, Privacy, FAQ, contact email, copyright, and "Popular Characters" section (8 top characters, module-level cache). In Layout.tsx inside `<main>` with `min-h-full flex` wrapper.
- **`components/landing/HeroSection.tsx`** — Landing hero with stats bar (users/messages/online), fetched from `/api/stats` on mount.

### Chat
- **`components/chat/GenerationSettingsModal.tsx`** — Modal with model card grid (auto, openrouter, groq, cerebras, together, direct, paid groups) + 6 sliders + context memory. Per-model settings stored in `localStorage model-settings:{modelId}`. `loadModelSettings()` exported for ChatPage. Switching model in modal loads saved params for that model. **Per-provider parameter limits** (`PROVIDER_LIMITS`): dynamic slider ranges and visibility per provider — Cerebras/Claude/Gemini hide penalty sliders, Claude limits temperature to 1.0, OpenAI allows penalty up to 2.0, others max 1.0. `clampToLimits()` auto-adjusts values on model switch.
- **`components/chat/MessageBubble.tsx`** — Message with delete/regenerate/copy buttons on hover. Markdown rendering (react-markdown + rehype-sanitize) for assistant messages. Error messages in red. Admin sees `model_used` under assistant messages. Wrapped in `React.memo` with custom comparator to prevent re-rendering during streaming.
- **`components/chat/ChatInput.tsx`** — Input textarea with auto-resize, send/stop buttons. When `personaName` prop is set, shows Sparkles button for generating reply as persona (calls `onGeneratePersonaReply`, puts result in textarea).
- **`components/chat/ChatWindow.tsx`** — Message list with infinite scroll (loads older messages on scroll-to-top, preserves scroll position). Persistent regenerate button below last assistant message. Streaming scroll uses `requestAnimationFrame`-batched instant `scrollTop` (not `scrollIntoView`) to prevent jank.

### Characters
- **`components/characters/CharacterForm.tsx`** — Full character form with appearance, speech_pattern, structured tag pills (fetched from API, grouped by category), `{{char}}`/`{{user}}` hint in example dialogues placeholder, hint props on greeting/example dialogues Textareas, and estimated token budget display (~N tokens, amber >2000, red >3000). Admin-only fields: preferred_model, max_tokens slider, system_prompt_suffix. Response length dropdown visible to all users.
- **`components/characters/ReportModal.tsx`** — Modal with 5 radio button reasons + details textarea. Handles duplicate report (409).

### UI
- **`components/ui/CookieConsent.tsx`** — Cookie consent banner (bottom, localStorage `cookie-consent`, link to Privacy Policy).
- **`components/ui/Skeleton.tsx`** — Pulse animation skeleton helper for loading states.
