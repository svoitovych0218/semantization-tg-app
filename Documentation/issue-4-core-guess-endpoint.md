# Issue #4 — Core Guess Endpoint

## Feature description

Implements the central game mechanic for Semantle UA: a `POST /guess` endpoint that accepts a player's word guess from a Telegram Mini App, validates their identity, scores the guess against today's secret word using semantic similarity, and persists the result.

Key behaviors:
- Telegram `initData` HMAC signature validation with 24-hour expiry enforcement
- Cosine similarity scoring against today's daily word using the `multilingual-e5-small` model
- Score mapped to a color tier (red → orange → yellow → green → gold)
- Deduplication: same word on the same day returns the cached score without a new row
- User row upserted on every valid request
- Per-user rate limit of ~1 guess/second enforced in-process

## Architecture decisions

### initData validation
Telegram WebApp initData is a URL-encoded string signed with `HMAC-SHA256`. The secret key is derived as `HMAC-SHA256(key="WebAppData", data=bot_token)`. Validation checks both the HMAC and that `auth_date` is within 24 hours of the current time. This runs synchronously at the start of every request before any DB work.

### Scoring formula
`score = clamp(round(((cosine_similarity - 0.7) / 0.3) * 10000), 0, 10000)`

The range [0.7, 1.0] in cosine-similarity space maps linearly to [0, 10000]. Guesses below 0.7 similarity clamp to 0 (red); a perfect match (the secret word itself) scores 10000 (gold).

Player guesses are embedded with the `query:` prefix, and secret words with the `passage:` prefix, as required by the `intfloat/multilingual-e5-small` asymmetric retrieval model. Both vectors are L2-normalised at encode time, so cosine similarity equals their dot product.

### Transaction structure
The endpoint opens one async session for: user upsert, deduplication check, and daily-word fetch. The CPU-bound embedding runs outside this session (via `asyncio.to_thread`) to avoid holding a DB connection open during inference. A second short transaction then inserts the guess row. `IntegrityError` from the unique constraint (`user_id, word_date, guessed_word`) is caught to handle the rare concurrent-duplicate race safely.

### Rate limiting
An in-process `dict[int, float]` keyed by `user_id` stores the last accepted guess timestamp (monotonic clock). Requests arriving within 1 second of the previous one return 429. This is appropriate for a single-process deployment; a Redis-based approach would be needed for multi-instance scaling.

### Color mapping
| Score range | Color  |
|-------------|--------|
| 10000       | gold   |
| 7501–9999   | green  |
| 5001–7500   | yellow |
| 2001–5000   | orange |
| 0–2000      | red    |

## Stack / technologies used

- **FastAPI** — HTTP router and request/response models (Pydantic)
- **SQLAlchemy 2.x async** — async ORM with `pg_insert` (PostgreSQL upsert)
- **asyncpg** — async PostgreSQL driver
- **Alembic** — database migration (migration `002_core_tables`)
- **sentence-transformers** (`intfloat/multilingual-e5-small`) — semantic embedding
- **Python stdlib** — `hmac`, `hashlib` for Telegram signature validation; `time.monotonic` for rate limiting

## Key files changed or created

| File | Change |
|------|--------|
| `backend/app/routers/guess.py` | New file — `POST /guess` endpoint, initData validation, scoring, rate limiting |
| `backend/alembic/versions/002_core_tables.py` | New migration — creates `user`, `chat`, `daily_word`, `user_chat`, `guess` tables with FK constraints |
| `backend/app/models.py` | Added `Chat` model; added FK on `UserChat.chat_id → chat.telegram_id` |
| `backend/app/embedding.py` | Added `encode_query(word)` using the `query:` prefix |
| `backend/app/main.py` | Registered `guess_router` |
