from datetime import date as Date

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from ..database import async_session_maker
from ..models import Guess, User, UserChat

router = APIRouter(tags=["game"])


class LeaderboardEntry(BaseModel):
    user_id: int
    first_name: str
    best_score: int
    is_winner: bool


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    chat_id: int = Query(...),
    date: Date = Query(...),
) -> list[LeaderboardEntry]:
    async with async_session_maker() as session:
        users_in_chat = (
            await session.execute(
                select(User)
                .join(UserChat, User.telegram_id == UserChat.user_id)
                .where(UserChat.chat_id == chat_id)
            )
        ).scalars().all()

        if not users_in_chat:
            return []

        user_ids = [u.telegram_id for u in users_in_chat]
        user_map = {u.telegram_id: u.first_name for u in users_in_chat}

        best_scores = (
            await session.execute(
                select(Guess.user_id, func.max(Guess.score).label("best_score"))
                .where(Guess.user_id.in_(user_ids), Guess.word_date == date)
                .group_by(Guess.user_id)
            )
        ).all()

        if not best_scores:
            return []

        # First player to reach 10,000 by guessed_at timestamp
        winner_row = (
            await session.execute(
                select(Guess.user_id)
                .where(
                    Guess.user_id.in_(user_ids),
                    Guess.word_date == date,
                    Guess.score == 10000,
                )
                .order_by(Guess.guessed_at)
                .limit(1)
            )
        ).first()
        winner_id = winner_row[0] if winner_row else None

        entries = [
            LeaderboardEntry(
                user_id=row.user_id,
                first_name=user_map[row.user_id],
                best_score=row.best_score,
                is_winner=row.user_id == winner_id,
            )
            for row in best_scores
        ]

        entries.sort(key=lambda e: e.best_score, reverse=True)

        return entries
