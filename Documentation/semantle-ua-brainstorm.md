# 🐙 Семантле UA — Brainstorm Summary

> A daily semantic word-guessing game for Telegram group chats, built for Ukrainian speakers.

---

## Concept

Once a day at 00:00 Kyiv time, a secret word is chosen. Players in a group chat must guess it by semantic similarity — the closer their guess is in meaning to the secret word, the higher their score. The challenge is to reach 10,000.

Inspired by Semantle, but social-first: the leaderboard is per chat, so every group competes together.

---

## Core Game Loop

```
00:00 → secret word chosen → embedding pre-computed and stored
  ↓
Player opens Mini App inside group chat
  ↓
Player types a guess (Ukrainian word)
  ↓
Server scores the guess (0–10,000) via cosine similarity
  ↓
Score shown with color feedback
  ↓
Leaderboard updates — best guess per player, ranked in this chat
  ↓
Someone hits 10,000 → wins the day 🏆
```

---

## Scoring

Scores range from **0 to 10,000**, mapped from cosine similarity of word embeddings.

| Score | Color | Meaning |
|-------|-------|---------|
| 0–2,000 | 🔴 Red | Cold |
| 2,001–5,000 | 🟠 Orange | Warm |
| 5,001–7,500 | 🟡 Yellow | Hot |
| 7,501–9,999 | 🟢 Green | Very close |
| 10,000 | 🏆 Gold | Found it! |

> **Note:** `multilingual-e5-small` outputs cosine similarity in the range 0.7–1.0 (not 0–1). Score must be normalized:
> `score = round(((similarity - 0.7) / 0.3) * 10000)`, clamped to [0, 10000].

---

## Platform

**Telegram Mini App** (WebApp) — not a plain bot. Reasons:
- Real UI with color-coded scores, animations, smooth leaderboard
- Telegram passes `initData` with `user_id` + `chat_id` automatically — no login needed
- Works inside group chats natively

---

## Tech Stack

### Frontend
- React + Vite
- Telegram Mini App SDK (theme vars, user identity, haptic feedback)

### Backend
- Node.js + Express / Fastify
- Bot layer: `grammy` or `telegraf`
- Cron job (node-cron) for daily word at 00:00 Kyiv time

### Embedding Service (separate Docker container)
- Python + FastAPI
- `sentence-transformers` with `intfloat/multilingual-e5-small`
- Called by Node.js over internal HTTP

### Database
- PostgreSQL

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  VPS (e.g. Hetzner CX22, ~€4/month)         │
│                                             │
│  ┌──────────────┐    ┌───────────────────┐  │
│  │  Node.js     │───▶│  Python FastAPI   │  │
│  │  (API, bot,  │    │  + e5-small model │  │
│  │  game logic) │◀───│  :8001            │  │
│  │  :3000       │    └───────────────────┘  │
│  └──────┬───────┘                           │
│         │                                   │
│  ┌──────▼───────┐                           │
│  │  PostgreSQL  │                           │
│  │  :5432       │                           │
│  └──────────────┘                           │
└─────────────────────────────────────────────┘
```

All services managed with `docker-compose`.

---

## Database Schema

```
daily_word   — id, word, date, embedding_vector (float[])
guess        — id, user_id, chat_id, word_date, guessed_word, score, guessed_at
user         — telegram_id, first_name, username
```

---

## Embedding Model: `multilingual-e5-small`

- **Size:** ~470MB, ~500MB RAM at runtime
- **Languages:** 100, including Ukrainian (well-supported, not low-resource)
- **Inference:** CPU is fine for single-word lookups (~20ms per guess)
- **No fine-tuning needed** for Ukrainian out of the box
- **No OOV problem:** transformer tokenizes at subword level — every word gets an embedding
- **Required prefixes:**
  - Secret word stored as: `"passage: {word}"`
  - User guess scored as: `"query: {word}"`

### Hosting options

| Stage | Option | Cost |
|-------|--------|------|
| Prototyping | HuggingFace Serverless Inference API | Free |
| Launch | Self-hosted on Hetzner VPS (bundled with app) | Included in €4/mo |
| Scale | HuggingFace Inference Endpoints (scale-to-zero) | ~$20–60/month |

---

## Where LLM (e.g. Claude) Is Used

LLMs are **not** used for scoring — embeddings handle that deterministically. LLMs are used for:

- **Daily word generation** — called once per day, curated and thematic
- **Post-round flavor text** — "Ти думав про море, але відповідь була глибше 🐙"
- *(Optional)* Hints if a player is stuck

---

## Input Validation (Node.js layer)

```
Empty string       → reject: "введи слово"
Numbers only       → reject: "введи слово"
Too long (>50 chars) → reject
Gibberish letters  → allow (model returns low score naturally)
```

---

## Docker Notes

- Docker Hub pull limits (100/hr free tier) are irrelevant — images are only pulled on deploy
- Model weights baked into Docker image at **build time** — no download on container startup, works offline
- `docker-compose` orchestrates all three services: app, embedding, postgres

---

## Language

**Ukrainian only** for v1. Expansion to other languages is straightforward — just swap the daily word list; the model already supports 100 languages.

---

## Open Questions / Next Steps

- [ ] Build browser UI prototype (mock scoring) to validate game feel
- [ ] Decide on daily word source: manual curation vs LLM-generated vs curated wordlist
- [ ] Define leaderboard reset logic (daily? keep history?)
- [ ] Handle ties (multiple players hit 10,000)
- [ ] Telegram bot announcement message at 00:00 to each registered chat
- [ ] Moderation: block offensive words from being guessable or chosen as secret
