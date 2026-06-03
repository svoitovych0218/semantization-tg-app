from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..config import settings
from ..database import async_session_maker
from ..models import Chat

router = Router()


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_start_group(message: Message) -> None:
    chat = message.chat
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(
                pg_insert(Chat)
                .values(
                    telegram_id=chat.id,
                    title=chat.title or "",
                    registered_at=datetime.now(UTC),
                    is_active=True,
                )
                .on_conflict_do_update(
                    index_elements=["telegram_id"],
                    set_={"title": chat.title or "", "is_active": True},
                )
            )
    await message.reply("Чат зареєстровано! Тепер гравці можуть грати в Semantle UA 🎮")


def _play_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Грати 🎮",
            web_app=WebAppInfo(url=settings.MINI_APP_URL),
        )
    ]])


@router.message(Command("play"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_play_group(message: Message) -> None:
    await message.reply(
        "Натисни кнопку нижче, щоб відкрити гру:",
        reply_markup=_play_keyboard(),
    )


@router.message(Command("play"), F.chat.type == ChatType.PRIVATE)
async def cmd_play_private(message: Message) -> None:
    await message.reply(
        "Грай самостійно!",
        reply_markup=_play_keyboard(),
    )
