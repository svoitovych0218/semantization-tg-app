import datetime
import logging
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func, select

from .bot import bot
from .config import settings
from .database import async_session_maker
from .models import Chat, DailyWord

logger = logging.getLogger(__name__)

_KYIV_TZ = ZoneInfo("Europe/Kyiv")


async def announce_daily_game() -> None:
    today = datetime.datetime.now(_KYIV_TZ).date()

    async with async_session_maker() as session:
        today_word = await session.scalar(
            select(DailyWord).where(DailyWord.date == today)
        )
        if today_word is None:
            logger.info("No word scheduled for %s — skipping daily announcement", today)
            return

        first_date: datetime.date | None = await session.scalar(
            select(func.min(DailyWord.date))
        )
        day_number = (today - first_date).days + 1

        chats = list(await session.scalars(
            select(Chat).where(Chat.is_active.is_(True))
        ))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Грати 🎮",
            web_app=WebAppInfo(url=settings.MINI_APP_URL),
        )
    ]])
    text = f"День {day_number} починається! 🐙"

    for chat in chats:
        try:
            await bot.send_message(
                chat_id=chat.telegram_id,
                text=text,
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception("Failed to announce to chat %s", chat.telegram_id)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=str(_KYIV_TZ))
    scheduler.add_job(
        announce_daily_game,
        CronTrigger(hour=0, minute=0, timezone=str(_KYIV_TZ)),
        id="daily_announcement",
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler
