# Issue #7 — Mini App: Guess UI

## Feature description

The core player-facing screen of the Semantle UA Telegram Mini App. Players type a Ukrainian word and tap Submit; the app calls the backend, gets a semantic similarity score (0–10 000), and immediately shows the result as a color-coded row in a scrollable history list. The history persists across sessions — on first load the app fetches all of today's guesses from the server.

Color mapping matches the spec:

| Range         | Color  |
|---------------|--------|
| 0 – 2 000     | red    |
| 2 001 – 5 000 | orange |
| 5 001 – 7 500 | yellow |
| 7 501 – 9 999 | green  |
| 10 000        | gold 🏆|

Additionally, when the Mini App is opened from a group, the opener's `user_chat` row is upserted so they appear on the group leaderboard.

## Architecture decisions

### Two new backend endpoints

**`POST /guesses/today`** — called on app mount to restore today's history. Accepts `init_data` in the request body (signed, so safe over POST), validates the Telegram signature, and returns the user's guesses for today sorted by score descending.

**`POST /register-chat`** — called on app open. Validates initData, upserts the `user` row, then conditionally upserts `user_chat` if a `chat` object is present in `initData` (Telegram only provides this when the Mini App is opened from a group). The user_chat insert is done in a separate transaction so that a missing `chat` FK (group never ran /start) is a silently-swallowed `IntegrityError` rather than rolling back the user upsert.

### State management — no external store

All game state lives in local React state (`useState`). Guesses are fetched on mount and merged with in-session submissions. No Redux / Zustand needed at this complexity level.

### Duplicate word handling

When the server returns `already_guessed: true`, no new row is added. Instead a brief notification banner appears and the existing row in the list flashes with a CSS outline animation for 2.5 seconds, then resets.

### Haptic feedback

Called via `window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')` (the raw Telegram Mini App JS SDK). Wrapped in try/catch so the app degrades silently outside Telegram (dev mode). The `TelegramHapticFeedback` interface was added to `telegram.d.ts`.

### API base URL

The frontend uses `import.meta.env.VITE_API_BASE_URL` (Vite env var) to locate the backend. Defaults to `''` (same origin), which works in dev with a reverse proxy. In production (Cloudflare Pages + separate backend), `VITE_API_BASE_URL` must be set at build time to the backend's public URL.

## Stack / technologies

- **Frontend**: React 18, TypeScript, Vite, `react-router-dom`, Telegram Mini App JS SDK (`window.Telegram.WebApp`)
- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL, Pydantic v2
- **CSS**: custom properties from `index.css` (`--score-red`, `--score-green`, etc.), CSS animations for flash/fade-in

## Key files changed or created

| File | Change |
|------|--------|
| `backend/app/routers/register.py` | New — `POST /register-chat` endpoint |
| `backend/app/routers/guess.py` | Added `TodayGuessesRequest`, `GuessHistoryEntry` models and `POST /guesses/today` handler |
| `backend/app/main.py` | Wire up `register_router` |
| `frontend/src/telegram.d.ts` | Added `TelegramHapticFeedback` interface and `initData` / `HapticFeedback` properties to `TelegramWebApp` |
| `frontend/src/views/GuessView.tsx` | Full rewrite — form, fetch logic, history list, duplicate highlight, haptic |
| `frontend/src/views/GuessView.css` | Added `.guess-list`, `.guess-row`, color dot/score variants, highlight animation |
