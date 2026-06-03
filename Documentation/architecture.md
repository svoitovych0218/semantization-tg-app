# Semantle UA — Architecture & Stack

## Overview

Semantle UA is a daily semantic word-guessing game for Ukrainian Telegram group chats. Players guess a secret Ukrainian word by semantic similarity, scored 0–10,000 using sentence embeddings. The first player to reach 10,000 wins the day.

---

## Repository Layout

```
/
├── backend/                  # Python service (API + bot + embeddings)
│   ├── app/
│   │   ├── main.py           # FastAPI app, /health, /webhook/{token}
│   │   ├── bot.py            # Aiogram Bot + Dispatcher instances
│   │   ├── config.py         # Pydantic Settings (reads from .env)
│   │   ├── database.py       # SQLAlchemy async engine + Base
│   │   └── models.py         # ORM models: User, DailyWord, UserChat, Guess
│   ├── alembic/              # Database migrations
│   │   ├── env.py            # Async migration runner
│   │   └── versions/
│   │       └── 001_initial.py
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + Vite Mini App (implemented separately)
├── Documentation/
│   ├── semantle-ua-brainstorm.md
│   └── architecture.md       # this file
├── docker-compose.yml
└── .env.example
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| HTTP framework | FastAPI 0.111+ |
| Bot framework | Aiogram 3.10+ |
| ASGI server | Uvicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Embeddings | `sentence-transformers` + `intfloat/multilingual-e5-small` |
| Frontend | React + Vite (TypeScript) — Cloudflare Pages |
| Orchestration | Docker Compose |
| Config | Pydantic Settings (env file) |

---

## Service Architecture

```
┌─────────────────────────────────────────────┐
│  VPS (min 2GB RAM, e.g. Hetzner CX22)       │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  app container  :8000                │   │
│  │                                      │   │
│  │  FastAPI                             │   │
│  │   GET  /health                       │   │
│  │   POST /webhook/{token}  ──► Aiogram │   │
│  │   POST /admin/words      (game data) │   │
│  │                                      │   │
│  │  sentence-transformers (in-process)  │   │
│  │  multilingual-e5-small (~470MB RAM)  │   │
│  └──────────────┬───────────────────────┘   │
│                 │ asyncpg                   │
│  ┌──────────────▼───────────────────────┐   │
│  │  postgres container  :5432           │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
         ▲ HTTPS webhook
         │
  Telegram servers
```

The embedding model runs **inside the app container** — no separate service. Weights are baked into the Docker image at build time (`SENTENCE_TRANSFORMERS_HOME` cache populated during `docker build`), so there is no download at container startup and the service works fully offline.

---

## Database Schema

```sql
-- Registered players
user (
  telegram_id  BIGINT PRIMARY KEY,
  first_name   VARCHAR(64) NOT NULL,
  username     VARCHAR(64)
)

-- One row per day; embedding is REAL[] from multilingual-e5-small
daily_word (
  id         SERIAL PRIMARY KEY,
  word       VARCHAR(100) NOT NULL,
  date       DATE NOT NULL UNIQUE,
  embedding  REAL[] NOT NULL
)

-- Tracks which users have opened the Mini App in which group
user_chat (
  user_id    BIGINT REFERENCES user(telegram_id),
  chat_id    BIGINT,
  joined_at  TIMESTAMPTZ,
  PRIMARY KEY (user_id, chat_id)
)

-- One row per unique (player, date, word) triple — no chat_id
-- Sessions are shared: same guess history solo vs group
guess (
  id            SERIAL PRIMARY KEY,
  user_id       BIGINT REFERENCES user(telegram_id),
  word_date     DATE NOT NULL,
  guessed_word  VARCHAR(100) NOT NULL,
  score         INTEGER NOT NULL,
  guessed_at    TIMESTAMPTZ,
  UNIQUE (user_id, word_date, guessed_word)
)
```

---

## Scoring

```
score = round(((cosine_similarity - 0.7) / 0.3) * 10_000)
score = clamp(score, 0, 10_000)
```

`multilingual-e5-small` produces cosine similarities in the range 0.7–1.0 for semantically related Ukrainian words. The formula maps that range to 0–10,000.

Required prefixes:
- Secret word stored/embedded as: `"passage: {word}"`
- Player guess embedded as: `"query: {word}"`

---

## Telegram Bot Integration

Aiogram 3.x runs in **webhook mode** everywhere (ngrok for local dev). The webhook URL is registered at startup via `bot.set_webhook()` and torn down cleanly on shutdown using FastAPI's `lifespan` context manager.

Telegram POSTs updates to `POST /webhook/{BOT_TOKEN}`. The token in the path is validated against the env var before feeding the update to the Aiogram Dispatcher.

---

## Security

| Concern | Mechanism |
|---------|-----------|
| Webhook authenticity | Token in URL path validated on every request |
| initData validation | HMAC-SHA256 + 24h expiry (game logic layer) |
| Admin endpoints | `x-key` header checked against `ADMIN_KEY` env var |
| Rate limiting | Per-user in-memory ~1 req/sec (game logic layer) |

---

## Environment Variables

See `.env.example` for the full list. Required at runtime:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | asyncpg connection string (`postgresql+asyncpg://...`) |
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `WEBHOOK_URL` | Public HTTPS base URL (no trailing slash) |
| `ADMIN_KEY` | Secret for the admin API `x-key` header |

---

## Running Locally

```bash
cp .env.example .env
# Fill in BOT_TOKEN, set WEBHOOK_URL to your ngrok URL

docker-compose up --build

# Run migrations
docker-compose exec app alembic upgrade head
```

Health check: `curl http://localhost:8000/health` → `{"status":"ok"}`

---

## Key Design Decisions

- **Single Python container**: embedding model runs in-process with the API, avoiding inter-service HTTP overhead and simplifying deployment.
- **No chat_id on guess**: guess sessions are shared across solo and group play — leaderboard scope is handled by `user_chat` join at query time.
- **Webhook over polling**: lower latency, no long-poll thread, cleaner shutdown.
- **Model baked into image**: deterministic startup time, works in air-gapped environments, no HuggingFace rate limits in production.

---

## Deferred to v2

- LLM-generated flavor text after each round
- Hints system
- Personal stats / streaks
- CI/CD pipeline
- Multi-language support (model already supports 100 languages)
