# Admin Words Endpoint

## Purpose

`POST /admin/words` is the sole mechanism for pre-populating the daily word schedule. It accepts a batch of word/date pairs, computes embeddings for each word at insert time, and stores them in the `daily_word` table. No SSH or direct database access is required to manage the game's word list.

---

## Stack

| Concern | Technology |
|---------|-----------|
| HTTP layer | FastAPI (`APIRouter`) |
| Auth | `x-key` request header matched against `ADMIN_KEY` env var |
| Embedding | `sentence-transformers` — `intfloat/multilingual-e5-small` |
| DB layer | SQLAlchemy 2.x async (`async_session_maker`) |
| Schema migration | Alembic (`002_daily_word`) |

---

## New Files

```
backend/
├── app/
│   ├── embedding.py          # SentenceTransformer singleton + encode_passage()
│   └── routers/
│       ├── __init__.py
│       └── admin.py          # POST /admin/words
└── alembic/versions/
    └── 002_daily_word.py     # Creates daily_word table
```

---

## API Contract

### `POST /admin/words`

**Authentication**: `x-key: <ADMIN_KEY>` header required. Missing or wrong key → `401 Unauthorized`.

**Request body** (`application/json`):
```json
[
  { "word": "мова",  "date": "2026-06-10" },
  { "word": "вода",  "date": "2026-06-11" }
]
```

**Response** (`200 OK`):
```json
[
  { "word": "мова", "date": "2026-06-10", "status": "ok" },
  { "word": "вода", "date": "2026-06-11", "status": "ok" }
]
```

**Duplicate date** (per-word error, rest of the batch is unaffected):
```json
[
  { "word": "мова", "date": "2026-06-10", "status": "error", "error": "date 2026-06-10 already has a word assigned" }
]
```

---

## Embedding Model

Model: `intfloat/multilingual-e5-small` (~470 MB, ~500 MB RAM at runtime, ~20 ms/word on CPU).

- Secret words are embedded with the **`passage:`** prefix: `"passage: {word}"`
- Player guesses (in the `/guess` endpoint, future issue) use the **`query:`** prefix
- Embeddings are stored as `REAL[]` in PostgreSQL (384-dimensional float32 vectors)
- Cosine similarity is computed in Python at guess time (no pgvector needed)

The model is loaded as a **lazy singleton** (`get_model()`) and pre-warmed at startup via `warm_up()` called inside FastAPI's `lifespan` using `asyncio.to_thread`. This means:
- Container startup is slightly slower (~5–10s to load weights)
- The first `/admin/words` request is fast (model already in memory)

---

## Concurrency Safety

`encode_passage()` is synchronous and CPU-bound (runs the transformer forward pass). It is always called via `asyncio.to_thread(encode_passage, word)` inside the endpoint to avoid blocking the event loop. This is important when processing large batches.

---

## Per-Item Transaction Isolation

Each word in the batch is inserted in its own `async with session.begin()` block. This means:
- A duplicate-date `IntegrityError` on item N does **not** roll back items 1..N-1
- The outer loop catches the error, records `status: "error"`, and continues
- No savepoints or nested transactions are needed

---

## Database Schema (`002_daily_word` migration)

```sql
CREATE TABLE daily_word (
  id        SERIAL PRIMARY KEY,
  word      VARCHAR(100) NOT NULL,
  date      DATE         NOT NULL,
  embedding REAL[]       NOT NULL,
  CONSTRAINT uq_daily_word_date UNIQUE (date)
);
```

Run the migration:
```bash
docker-compose exec app alembic upgrade head
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ADMIN_KEY` | Secret compared against `x-key` header. Already in `.env.example`. |

---

## Example Usage

```bash
curl -X POST https://your-api/admin/words \
  -H "x-key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '[
    {"word": "мова",  "date": "2026-06-10"},
    {"word": "вода",  "date": "2026-06-11"},
    {"word": "земля", "date": "2026-06-12"}
  ]'
```

---

## What's Not Yet Implemented

- Input validation: word length capped at model's max token limit
- Soft-delete / update: replacing a word for an existing date (currently requires direct DB edit)
- Batch embedding: computing all embeddings in parallel via `model.encode(batch)` for large uploads
