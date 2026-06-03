import asyncio
import hashlib
import hmac
import json
import math
import time
from datetime import UTC, date, datetime
from typing import Literal
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..database import async_session_maker
from ..embedding import encode_query
from ..models import DailyWord, Guess, User

router = APIRouter(tags=["game"])

# In-memory rate limit: user_id -> last_guess_time (monotonic clock)
_last_guess: dict[int, float] = {}
_RATE_LIMIT_SECONDS = 1.0


def _validate_init_data(init_data: str) -> dict:
    """Validate Telegram WebApp initData signature and freshness. Returns user dict."""
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = params.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    auth_date = int(params.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(status_code=401, detail="initData expired")

    return json.loads(params.get("user", "{}"))


def _score_to_color(score: int) -> Literal["red", "orange", "yellow", "green", "gold"]:
    if score == 10000:
        return "gold"
    if score >= 7501:
        return "green"
    if score >= 5001:
        return "yellow"
    if score >= 2001:
        return "orange"
    return "red"


def _compute_score(cosine_similarity: float) -> int:
    normalized = 1 / (1 + math.exp(-(cosine_similarity - 0.245) / 0.015))
    return round(normalized * 9999)


class GuessRequest(BaseModel):
    init_data: str
    word: str


class GuessResponse(BaseModel):
    score: int
    color: str
    already_guessed: bool


class TodayGuessesRequest(BaseModel):
    init_data: str


class GuessHistoryEntry(BaseModel):
    word: str
    score: int
    color: str


@router.post("/guess", response_model=GuessResponse)
async def make_guess(body: GuessRequest) -> GuessResponse:
    tg_user = _validate_init_data(body.init_data)
    user_id: int | None = tg_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user id in initData")
    first_name: str = tg_user.get("first_name", "")
    username: str | None = tg_user.get("username")

    # Enforce ~1 guess/second per user
    now = time.monotonic()
    last = _last_guess.get(user_id, 0.0)
    if now - last < _RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=429, detail="Too many requests")
    _last_guess[user_id] = now

    today = date.today()

    daily_word: DailyWord | None = None

    async with async_session_maker() as session:
        async with session.begin():
            # Upsert user on every valid request
            await session.execute(
                pg_insert(User)
                .values(telegram_id=user_id, first_name=first_name, username=username)
                .on_conflict_do_update(
                    index_elements=["telegram_id"],
                    set_={"first_name": first_name, "username": username},
                )
            )

            # Block further guesses if user already found the word today
            won = (
                await session.execute(
                    select(Guess).where(
                        Guess.user_id == user_id,
                        Guess.word_date == today,
                        Guess.score == 10000,
                    )
                )
            ).scalar_one_or_none()

            if won is not None:
                raise HTTPException(status_code=403, detail="Ти вже знайшов слово сьогодні!")

            # Deduplication: return cached score if word already guessed today
            existing = (
                await session.execute(
                    select(Guess).where(
                        Guess.user_id == user_id,
                        Guess.word_date == today,
                        Guess.guessed_word == body.word,
                    )
                )
            ).scalar_one_or_none()

            if existing is not None:
                return GuessResponse(
                    score=existing.score,
                    color=_score_to_color(existing.score),
                    already_guessed=True,
                )

            daily_word = (
                await session.execute(select(DailyWord).where(DailyWord.date == today))
            ).scalar_one_or_none()

    if daily_word is None:
        raise HTTPException(status_code=404, detail="No word scheduled for today")

    if body.word.strip().lower() == daily_word.word.strip().lower():
        score = 10000
    else:
        guess_vec = await asyncio.to_thread(encode_query, body.word)
        cosine_sim = sum(a * b for a, b in zip(guess_vec, daily_word.embedding))
        score = min(9999, _compute_score(cosine_sim))

    try:
        async with async_session_maker() as session:
            async with session.begin():
                session.add(
                    Guess(
                        user_id=user_id,
                        word_date=today,
                        guessed_word=body.word,
                        score=score,
                        guessed_at=datetime.now(UTC),
                    )
                )
    except IntegrityError:
        # Concurrent request already inserted the same guess; return cached result
        return GuessResponse(score=score, color=_score_to_color(score), already_guessed=True)

    return GuessResponse(score=score, color=_score_to_color(score), already_guessed=False)


@router.post("/guesses/today", response_model=list[GuessHistoryEntry])
async def get_today_guesses(body: TodayGuessesRequest) -> list[GuessHistoryEntry]:
    tg_user = _validate_init_data(body.init_data)
    user_id: int | None = tg_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user id in initData")

    today = date.today()

    async with async_session_maker() as session:
        rows = (
            await session.execute(
                select(Guess)
                .where(Guess.user_id == user_id, Guess.word_date == today)
                .order_by(Guess.score.desc())
            )
        ).scalars().all()

    return [
        GuessHistoryEntry(word=g.guessed_word, score=g.score, color=_score_to_color(g.score))
        for g in rows
    ]
