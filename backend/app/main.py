import asyncio
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request

from .bot import bot, dp
from .config import settings
from .embedding import warm_up
from .routers.admin import router as admin_router
from .routers.guess import router as guess_router
from .routers.leaderboard import router as leaderboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load the embedding model before accepting traffic
    await asyncio.to_thread(warm_up)

    webhook_url = f"{settings.WEBHOOK_URL}/webhook/{settings.BOT_TOKEN}"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)

    yield

    await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(title="Semantle UA", lifespan=lifespan)
app.include_router(admin_router)
app.include_router(guess_router)
app.include_router(leaderboard_router)


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
