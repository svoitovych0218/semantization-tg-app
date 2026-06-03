import asyncio
from datetime import date as Date
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..database import async_session_maker
from ..embedding import encode_passage
from ..models import DailyWord

router = APIRouter(prefix="/admin", tags=["admin"])


class WordInput(BaseModel):
    word: str
    date: Date


class WordResult(BaseModel):
    word: str
    date: Date
    status: Literal["ok", "error"]
    error: str | None = None


@router.post("/words", response_model=list[WordResult])
async def bulk_insert_words(
    body: list[WordInput],
    x_key: str | None = Header(None, alias="x-key"),
) -> list[WordResult]:
    if x_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    results: list[WordResult] = []

    for item in body:
        try:
            # encode_passage is CPU-bound; run in thread pool to avoid blocking the event loop
            embedding = await asyncio.to_thread(encode_passage, item.word)

            async with async_session_maker() as session:
                async with session.begin():
                    session.add(DailyWord(word=item.word, date=item.date, embedding=embedding))

            results.append(WordResult(word=item.word, date=item.date, status="ok"))

        except IntegrityError:
            results.append(
                WordResult(
                    word=item.word,
                    date=item.date,
                    status="error",
                    error=f"date {item.date} already has a word assigned",
                )
            )
        except Exception as exc:
            results.append(
                WordResult(
                    word=item.word,
                    date=item.date,
                    status="error",
                    error=str(exc),
                )
            )

    return results
