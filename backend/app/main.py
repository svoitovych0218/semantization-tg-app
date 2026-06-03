from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request

from .bot import bot, dp
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    webhook_url = f"{settings.WEBHOOK_URL}/webhook/{settings.BOT_TOKEN}"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    yield
    await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(title="Semantle UA", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != settings.BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
