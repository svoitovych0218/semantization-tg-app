# Bot Commands & Webhook (Issue #6)

## Feature description

Wires up the Aiogram bot with the two commands players use to interact with the game:

- **`/start` in a group** — registers (or re-registers) the group chat in the `chat` table and replies with a confirmation message. The upsert is idempotent: calling `/start` again in an already-registered chat simply refreshes the title and ensures `is_active` is `true`.
- **`/play` in a group** — sends a reply containing a WebApp inline keyboard button. Because the message originates in the group, Telegram automatically includes `chat_id` in `initData` when the Mini App opens, enabling group-scoped leaderboards.
- **`/play` in private chat** — sends the same WebApp button in solo mode; `chat_id` will not be present in `initData`.

Webhook registration with Telegram was already handled by the `lifespan` handler in `main.py` (set on startup, deleted on shutdown).

## Architecture decisions

- **New file `backend/app/routers/bot_commands.py`** — follows the same module layout as FastAPI routers (one file per concern). Uses an Aiogram `Router` instance that is included into the dispatcher (`dp`) in `bot.py`.
- **Chat type filtering via Aiogram magic filters** — `F.chat.type.in_({"group", "supergroup"})` and `F.chat.type == ChatType.PRIVATE` keep the three handlers fully independent and avoid runtime if/else branching.
- **PostgreSQL upsert for `/start`** — reuses the same `pg_insert(...).on_conflict_do_update(...)` pattern already established in the guess router, keeping the conflict resolution logic in SQL rather than Python.
- **`MINI_APP_URL` added to settings** — `config.py` now exposes this variable; the play keyboard helper reads it at call time so it picks up the value after startup without re-importing.

## Stack / technologies used

| Layer | Technology |
|---|---|
| Bot framework | Aiogram 3.x |
| Web framework | FastAPI (webhook endpoint already in `main.py`) |
| Database access | SQLAlchemy 2 async + asyncpg |
| Config | pydantic-settings (`Settings` in `config.py`) |
| Telegram button type | `WebAppInfo` inline keyboard button |

## Key files changed or created

| File | Change |
|---|---|
| `backend/app/routers/bot_commands.py` | **Created** — Aiogram router with three command handlers |
| `backend/app/bot.py` | Import and `dp.include_router(commands_router)` added |
| `backend/app/config.py` | `MINI_APP_URL: str` field added to `Settings` |
| `.env.example` | `MINI_APP_URL` documented with a placeholder value |
