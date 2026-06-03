import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..database import async_session_maker
from ..models import User, UserChat

router = APIRouter(tags=["game"])


def _validate_init_data(init_data: str) -> tuple[dict, dict | None]:
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

    user = json.loads(params.get("user", "{}"))
    chat_raw = params.get("chat")
    chat = json.loads(chat_raw) if chat_raw else None
    return user, chat


class RegisterChatRequest(BaseModel):
    init_data: str


@router.post("/register-chat", status_code=204)
async def register_chat(body: RegisterChatRequest) -> None:
    tg_user, tg_chat = _validate_init_data(body.init_data)

    user_id: int | None = tg_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user id in initData")

    first_name: str = tg_user.get("first_name", "")
    username: str | None = tg_user.get("username")

    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(
                pg_insert(User)
                .values(telegram_id=user_id, first_name=first_name, username=username)
                .on_conflict_do_update(
                    index_elements=["telegram_id"],
                    set_={"first_name": first_name, "username": username},
                )
            )

    if tg_chat:
        chat_id: int | None = tg_chat.get("id")
        if chat_id:
            try:
                async with async_session_maker() as session:
                    async with session.begin():
                        await session.execute(
                            pg_insert(UserChat)
                            .values(user_id=user_id, chat_id=chat_id)
                            .on_conflict_do_nothing()
                        )
            except IntegrityError:
                # Chat not registered via /start yet — silently skip
                pass
