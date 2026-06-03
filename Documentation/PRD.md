# Semantle UA — Product Requirements Document

## Problem Statement

Ukrainian Telegram users have no native-language semantic word game available directly inside their group chats. Existing options (Wordle-style clones, the original English Semantle) are either language-agnostic, require leaving Telegram, or lack the social layer that makes daily word games sticky. Players want to compete with their friend group, not a global leaderboard of strangers — and they want the game to live where the conversation already happens.

---

## Solution

A daily semantic word-guessing game delivered as a Telegram Mini App. Once per day, a secret Ukrainian word is chosen. Players inside a registered group chat guess words; each guess is scored 0–10,000 based on semantic similarity to the secret word (via cosine similarity of multilingual embeddings). The player who first scores 10,000 wins the day, but the game stays open for everyone else to keep playing. The leaderboard is per-chat and resets each day, making every group its own daily competition.

The game also works in private chat with the bot as a solo experience, sharing the same guess history as any group sessions for that day.

---

## User Stories

1. As a group chat member, I want to start a new game in my chat by sending `/start` to the bot, so that my group can participate in the daily challenge.
2. As a player, I want to open the Mini App directly from the 00:00 announcement message in my group, so that I can start playing immediately when the new day begins.
3. As a player, I want to open the Mini App using the `/play` command at any time, so that I can join the game even if I missed the announcement.
4. As a player, I want to play the game privately in the bot without a group, so that I can enjoy the game solo even if I have no active group.
5. As a player, I want my guesses from a solo session to count toward my group leaderboard, so that I don't have to guess the same words twice in different contexts.
6. As a player, I want to type a Ukrainian word and instantly receive a score from 0 to 10,000, so that I know how semantically close my guess was to the secret word.
7. As a player, I want the score to be color-coded (red / orange / yellow / green / gold), so that I can gauge my closeness at a glance without reading the number.
8. As a player, I want to see all my guesses for today sorted by score (highest first), so that I can triangulate the secret word based on what has worked.
9. As a player, I want to be told my previous score when I submit a word I already guessed today, so that I don't accidentally use up time re-entering duplicates.
10. As a player, I want to guess as many times as I want per day with no limit, so that I can keep exploring semantic space freely.
11. As a player, I want to see the group leaderboard showing each player's best score today, so that I know how I rank against my chat-mates.
12. As a player, I want the leaderboard to update in real time as others guess, so that the competition feels live.
13. As a player, I want to see a trophy marker next to the first person who scored 10,000 today, so that I know who found the word first.
14. As a player, I want to keep playing after someone else hits 10,000, so that I can still find the word and improve my own rank.
15. As a player, I want the secret word to never be revealed, so that the mystery is preserved and I can't spoil it for others who haven't played yet.
16. As a player in a different timezone, I want the game to reset at midnight Kyiv time, so that the game cycle is consistent and predictable for all Ukrainian users.
17. As a group chat member, I want the bot to post a minimal announcement at 00:00 with a day counter and a play button, so that I'm reminded to play each new day.
18. As a first-time player, I want my Telegram identity to be used automatically with no login or registration, so that I can start playing immediately without any friction.
19. As a player using a mobile device, I want the Mini App to feel native with color feedback and smooth interactions, so that guessing feels responsive.
20. As a game admin, I want to submit a batch of words with their assigned dates via a protected HTTP endpoint, so that I can pre-populate the word schedule without accessing the server directly.
21. As a game admin, I want the secret word's embedding to be computed at insertion time, so that there is no risk of the cron job failing at midnight.
22. As a developer, I want `initData` from Telegram to be validated with HMAC signature and a 24-hour expiry check on every request, so that scores cannot be forged by spoofing user identity.
23. As a developer, I want per-user in-memory rate limiting (~1 guess/second), so that automated scripts cannot brute-force the word or overwhelm the embedding computation.
24. As a developer, I want the bot to run in webhook mode in both local and production environments, so that the deployment model is consistent and event-driven.

---

## Implementation Decisions

### Architecture

- **Single Python service** running FastAPI (HTTP API), Aiogram 3.x (Telegram bot), and the `sentence-transformers` embedding model in one process on one container. No internal HTTP between services.
- **PostgreSQL** as the sole persistent store, running in a separate Docker container orchestrated via `docker-compose`.
- **Frontend** is a React + Vite (TypeScript) app deployed to Cloudflare Pages (separate domain from the backend API).
- **Backend** deployed on a VPS with a minimum of 2GB RAM. nginx handles SSL termination and proxies to FastAPI. Let's Encrypt for the TLS certificate.
- **Webhook mode everywhere.** In local development, ngrok exposes the local server; Aiogram's webhook handler is mounted on a FastAPI route.

### Embedding Model

- Model: `intfloat/multilingual-e5-small` (~470MB, ~500MB RAM at runtime, CPU inference ~20ms).
- Prefixes: secret word stored as `"passage: {word}"`, player guess scored as `"query: {word}"`.
- Scoring formula: `score = round(((cosine_similarity - 0.7) / 0.3) * 10000)`, clamped to `[0, 10000]`.
- Model weights baked into the Docker image at build time — no download on container start.

### Database Schema

```
chat        — telegram_id BIGINT PK, title TEXT, registered_at TIMESTAMP, is_active BOOL
user        — telegram_id BIGINT PK, first_name TEXT, username TEXT
user_chat   — user_id BIGINT FK, chat_id BIGINT FK, joined_at TIMESTAMP
daily_word  — id SERIAL PK, word TEXT, date DATE UNIQUE, embedding REAL[]
guess       — id SERIAL PK, user_id BIGINT FK, word_date DATE FK, guessed_word TEXT,
              score INT, guessed_at TIMESTAMP
```

Key decisions:
- `guess` has no `chat_id` — sessions are shared across contexts (solo and group) per `user_id + word_date`.
- `user_chat` tracks which users have "joined" a given chat's leaderboard (populated when a user first opens the Mini App from a group message).
- `embedding` stored as `REAL[]`; cosine similarity computed in Python (no pgvector needed).
- Migrations managed with **Alembic**.

### API Contracts

- `POST /guess` — body: `{ initData: string, guessed_word: string }`. Returns `{ score, color, already_guessed }`. Hard-rejects invalid or expired `initData` with 401.
- `GET /leaderboard` — query: `?chat_id=…&date=…`. Returns ranked list of `{ user_id, first_name, best_score, is_winner }`.
- `POST /admin/words` — header: `x-key` (from env). Body: `[{ word: string, date: string }]`. Computes and stores embeddings for each word. Returns per-word success/failure.
- `POST /webhook/{token}` — Aiogram webhook handler mounted on FastAPI.

### Bot Behavior

- `/start` in a group: registers the chat in the `chat` table, responds with a confirmation.
- `/play` in a group: posts a message with a WebApp button so `chat_id` is included in `initData`.
- `/play` in private chat: opens the Mini App without a `chat_id` (solo mode).
- 00:00 cron (Kyiv time): posts "День {N} починається! 🐙 [Грати]" to every active chat.

### Session & Leaderboard Logic

- A user's guess history for a day is all `guess` rows for `user_id + word_date`, regardless of context.
- The group leaderboard shows all users in `user_chat` for that `chat_id`, joined to their `MAX(score)` for today.
- A user "joins" a group leaderboard the first time they open the Mini App via a group message (upsert into `user_chat`).
- First player to reach 10,000 receives a winner marker; game continues for others.

### Security

- `initData` HMAC validation + `auth_date` within 24 hours on every API request.
- Admin endpoint protected by `x-key` header (static secret from environment).
- Per-user in-memory rate limiting: reject with 429 if same `user_id` submits more than ~1 guess/second.

---

## Testing Decisions

Good tests verify external behavior — what the API returns given specific inputs — not internal implementation details like which SQL query was run or which Python method was called.

### What makes a good test here

- Tests call the FastAPI HTTP endpoints (or Aiogram handlers via test client), not internal service functions directly.
- Use a real PostgreSQL test database (not mocks) to catch schema-level bugs early.
- `initData` validation tests should cover: valid signature + fresh timestamp (accept), valid signature + expired timestamp (reject), invalid signature (reject), missing header (reject).
- Scoring tests should cover: boundary values (similarity = 0.7 → score 0, similarity = 1.0 → score 10,000), duplicate guess (returns stored score, no new row), rate limit exceeded (429).
- Leaderboard tests should cover: empty leaderboard, single player, multiple players with multiple guesses (only best score shown), winner marker on first 10,000 scorer.

### Modules to test

- **Guess endpoint** — scoring, deduplication, rate limiting, initData rejection.
- **Leaderboard endpoint** — ranking correctness, winner marker, chat scoping.
- **Admin word endpoint** — auth rejection, bulk insert, embedding storage, duplicate date handling.
- **initData validation** — signature check, expiry window.
- **Cron job / daily word selection** — correct word returned for a given date.

---

## Out of Scope

- **LLM flavor text** — post-round commentary generated by an LLM ("Ти думав про море..."). Deferred to v2.
- **Hints** — LLM-generated or static hints for stuck players. Deferred to v2.
- **Personal stats** — win count, streaks, average score over time. Deferred to v2.
- **All-time chat hall of fame** — cumulative leaderboard across days. Deferred to v2.
- **Word reveal** — the secret word is never shown to players, even after the day ends.
- **Offensive word blocking** — guesses are private to the player; no public harm from offensive inputs.
- **Multi-language support** — Ukrainian only for v1; model supports 100 languages but word list is Ukrainian.
- **CI/CD pipeline** — deployment is manual SSH for now.
- **Moderation tools** — no admin UI or report mechanism in v1.

---

## Further Notes

- **Score color mapping:** 0–2,000 red, 2,001–5,000 orange, 5,001–7,500 yellow, 7,501–9,999 green, 10,000 gold.
- **Day counter:** the 00:00 announcement includes a sequential day number (e.g., "День 42") derived from the date offset from the first word in the schedule.
- **VPS RAM requirement:** the embedding model requires ~500MB RAM at runtime. Combined with FastAPI, Aiogram, OS, and PostgreSQL, a minimum of 2GB RAM is required to avoid OOM kills.
- **Cloudflare Pages + separate API domain:** CORS must explicitly allow the Cloudflare Pages origin on all FastAPI routes that the Mini App calls.
- **ngrok for local webhook:** the local `WEBHOOK_URL` env var points to the ngrok tunnel; swapped for the real domain in production via environment config.
- **Word list management:** words are added via the `POST /admin/words` bulk endpoint. Embeddings are computed at insert time, so the midnight cron job has zero risk of embedding service failure affecting game start.
