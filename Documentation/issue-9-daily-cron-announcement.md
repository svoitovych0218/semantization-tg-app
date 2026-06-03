# Daily Cron + 00:00 Announcement (Issue #9)

## Feature description

An APScheduler job that fires every day at midnight Kyiv time (Europe/Kyiv). On each tick it:

1. Resolves today's Kyiv date.
2. Looks up that date in `daily_word`; if nothing is scheduled it exits silently without crashing.
3. Computes the sequential day counter `N` as `(today − first_word_date).days + 1`.
4. Fetches every chat where `is_active = true`.
5. Posts `"День {N} починається! 🐙"` to each chat together with a WebApp inline keyboard button so players can open the Mini App directly from the group.

## Architecture decisions

- **New file `backend/app/scheduler.py`** — isolates scheduling concerns from the web layer; `main.py` imports only `create_scheduler()`.
- **`AsyncIOScheduler` from APScheduler 3.x** — integrates with the existing asyncio event loop used by FastAPI/Uvicorn; no extra threads required.
- **`CronTrigger(hour=0, minute=0, timezone="Europe/Kyiv")`** — fires exactly at local midnight; `zoneinfo.ZoneInfo` is used inside the job to derive the correct date regardless of server OS timezone.
- **`coalesce=True` + `misfire_grace_time=3600`** — if the process restarts right at midnight, at most one announcement fires; if the server was down longer than an hour, the missed tick is skipped entirely, preventing stale announcements.
- **Scheduler lifecycle in FastAPI `lifespan`** — `scheduler.start()` runs after the webhook is registered; `scheduler.shutdown(wait=False)` runs before the bot session closes, keeping startup/shutdown order symmetric.
- **Per-chat exception handling** — a failure to reach one chat (e.g., bot was kicked) is logged and skipped; the loop continues for remaining chats.

## Stack / technologies used

| Layer | Technology |
|---|---|
| Scheduling | APScheduler 3.x (`AsyncIOScheduler`, `CronTrigger`) |
| Timezone | Python `zoneinfo` (stdlib, no extra dependency) |
| Bot messaging | Aiogram 3.x `bot.send_message` with `WebAppInfo` button |
| Database access | SQLAlchemy 2 async + asyncpg |
| Lifecycle management | FastAPI `asynccontextmanager` lifespan |

## Key files changed or created

| File | Change |
|---|---|
| `backend/app/scheduler.py` | **Created** — `announce_daily_game` job function and `create_scheduler()` factory |
| `backend/app/main.py` | Import `create_scheduler`; start scheduler in lifespan startup, shut down in teardown |
| `backend/requirements.txt` | `apscheduler>=3.10.0` added |
