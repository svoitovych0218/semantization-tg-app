import datetime

from sqlalchemy import BigInteger, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "user"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))


class DailyWord(Base):
    __tablename__ = "daily_word"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, unique=True)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float(precision=24)), nullable=False)


class UserChat(Base):
    __tablename__ = "user_chat"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.telegram_id"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC)
    )


class Guess(Base):
    __tablename__ = "guess"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.telegram_id"), nullable=False)
    word_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    guessed_word: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    guessed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC)
    )

    __table_args__ = (UniqueConstraint("user_id", "word_date", "guessed_word", name="uq_guess_per_word"),)
