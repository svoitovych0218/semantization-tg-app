# Issue #5 — Leaderboard Endpoint

## Feature description

Adds `GET /leaderboard?chat_id=…&date=…` — a read endpoint that returns a ranked daily leaderboard for a Telegram group chat. Each entry shows the player's best score for the requested date and marks the one player who first guessed the word exactly (`score == 10000`).

## Architecture decisions

- **Scoped to `user_chat`** — only users who have ever opened the Mini App from the given group appear on its leaderboard (enforced via JOIN on the `user_chat` join table).
- **Best-score aggregation** — uses `MAX(score) GROUP BY user_id` so multiple guesses per user are collapsed to their single best attempt.
- **Winner determination** — among all 10,000-score guesses for that day, the winner is the row with the earliest `guessed_at` timestamp. This correctly handles the edge case where two players hit 10,000; only the chronologically first one is marked `is_winner: true`.
- **Empty-list semantics** — returns `[]` (HTTP 200) when no one has guessed yet, matching the spec; no 404 is raised.
- **Separate router file** — `leaderboard.py` follows the same module pattern as `guess.py` and `admin.py` and is registered in `main.py` alongside the other routers.

## Stack / technologies used

- **FastAPI** — `APIRouter` + `Query` params for the GET endpoint
- **SQLAlchemy 2 async** — `select`, `func.max`, `.in_()`, `.order_by`, `.limit` via `async_session_maker`
- **Pydantic v2** — `LeaderboardEntry` response model
- **PostgreSQL** — all data lives in the existing `user`, `user_chat`, and `guess` tables; no schema migration needed

## Key files changed or created

| File | Change |
|------|--------|
| `backend/app/routers/leaderboard.py` | New — leaderboard router with `GET /leaderboard` |
| `backend/app/main.py` | Imports and mounts `leaderboard_router` |
