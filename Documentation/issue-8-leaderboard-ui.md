# Issue #8 — Mini App: Leaderboard UI

## Feature description

Adds a live leaderboard view inside the Telegram Mini App showing today's rankings for the player's group chat. The view:

- Displays each player's rank, name, best score, and a color-coded dot matching the score tier (red → orange → yellow → green → gold)
- Marks the first player to reach 10,000 with a 🏆 winner indicator
- Highlights the current player's own row with a colored outline so they can immediately spot themselves
- Refreshes automatically every 10 seconds so rankings stay current as other players guess
- Shows a friendly empty state ("Ще ніхто не вгадував сьогодні") when no guesses have been submitted
- Is **hidden entirely** in solo mode (when the Mini App is opened outside a group chat, i.e. no `chat` field in `initData`): both the navigation tab and the view return `null`

## Architecture decisions

### initData parsing done locally in each component

Rather than lifting `initData` parsing into a shared context or prop, each component (`Navigation`, `LeaderboardView`) reads `window.Telegram?.WebApp?.initData` independently at mount time. This follows the same pattern as `GuessView.tsx` and avoids adding coupling between unrelated components for a value that is immutable for the lifetime of the Mini App session.

### Score-to-color mapping duplicated on the frontend

The backend's `_score_to_color` thresholds (2001 / 5001 / 7501 / 10000) are replicated in `LeaderboardView.tsx` as `scoreToColor()`. The leaderboard API deliberately omits the color field to keep the response minimal; computing it client-side from the integer score is trivial and avoids a schema change.

### Polling instead of WebSocket

A 10-second `setInterval` poll is sufficient for a daily word game where leaderboard movements are infrequent. WebSockets would add deployment complexity (persistent connections, keepalives) for no meaningful UX gain.

### Navigation tab gated at mount time

`detectChatId()` runs once inside a `useState` initializer in `Navigation`. Since Telegram's `initData` is synchronously available when the Mini App script executes, there is no race condition. Using `useState` (rather than a bare constant) ensures React owns the value and avoids stale-closure issues if the component ever remounts.

## Stack / technologies used

| Layer | Technology |
|---|---|
| Frontend framework | React 18 + TypeScript (Vite) |
| Routing | React Router v6 (`NavLink`, `Routes`) |
| Telegram integration | `window.Telegram.WebApp.initData` (URL-encoded string) |
| Styling | Plain CSS modules (`LeaderboardView.css`) using existing CSS custom properties |
| Data fetching | Native `fetch` + `setInterval` polling |
| Backend API | FastAPI `GET /leaderboard?chat_id=&date=` (issue #5) |

## Key files changed or created

| File | Change |
|---|---|
| `frontend/src/views/LeaderboardView.tsx` | Full implementation replacing the stub — polling fetch, ranked list, empty state, winner marker, self-highlight |
| `frontend/src/views/LeaderboardView.css` | Full replacement — leaderboard list styles, color-coded score classes, self-highlight outline |
| `frontend/src/components/Navigation.tsx` | Conditionally renders the Рейтинг tab only when `chat_id` is present in `initData` |
| `frontend/tsconfig.app.json` | Added `"types": ["vite/client"]` to resolve pre-existing `import.meta.env` TypeScript error |
