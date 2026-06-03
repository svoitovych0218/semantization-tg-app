# Issue #10 — Solo play (private bot)

## Feature description

Adds support for playing the game privately via the bot without a group chat. When a user sends `/play` directly to the bot in a private conversation, the Mini App opens in **solo mode**: the full guess UI is available and functional, but the group leaderboard tab is absent.

Guesses made in solo mode are stored against `user_id + word_date` with no `chat_id`, so the same guess history is seamlessly shared when the player later opens the game from a group chat.

## Architecture decisions

### Solo vs group detection

The mode is determined by whether the `chat` key is present in Telegram WebApp `initData`:

- **Group mode**: Telegram includes a `chat` JSON object in `initData` when the Mini App is launched from a group message button.
- **Solo mode**: No `chat` key — the app was opened from a private bot message.

This detection happens in two places:
- `Navigation.tsx` (`detectChatId`) — controls whether the Leaderboard nav tab is rendered.
- `App.tsx` (`hasChatContext`) — guards the `/leaderboard` route; redirects to `/guess` in solo mode instead of rendering a blank screen.

### Guess storage is chat-agnostic

The `Guess` model has always stored guesses as `(user_id, word_date, guessed_word)` with no `chat_id` column. This means solo and group guesses are the same records, satisfying the shared-history requirement without any schema changes.

### Backend accepts solo context transparently

- `POST /guess` only reads `user.id` from `initData`; it never references `chat_id`, so solo requests succeed unchanged.
- `POST /register-chat` gracefully skips the `UserChat` upsert when `chat` is absent from `initData`, returning 204 in both solo and group contexts.

## Stack / technologies used

- **Frontend**: React + React Router, TypeScript, `@telegram-apps/sdk` for `initData` access
- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL — no changes required
- **Bot**: aiogram 3.x — `cmd_play_private` handler (added in issue #6)

## Key files changed or created

| File | Change |
|---|---|
| `frontend/src/App.tsx` | Added `hasChatContext()` helper; `/leaderboard` route now redirects to `/guess` in solo mode instead of rendering `null` |
| `frontend/src/components/Navigation.tsx` | (prior) `detectChatId()` hides the Leaderboard tab in solo mode |
| `backend/app/routers/bot_commands.py` | (prior) `cmd_play_private` handler sends Mini App button on `/play` in private chat |
| `backend/app/routers/guess.py` | No changes — already chat-agnostic |
| `backend/app/routers/register.py` | No changes — already handles missing `chat` gracefully |
