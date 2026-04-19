from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update

from app.bot import application
from app.scheduler import start_scheduler, scheduler
from app.database import init_db
from app.config import WEBHOOK_URL


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    await application.initialize()
    await application.start()

    start_scheduler()

    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

    yield

    await application.bot.delete_webhook()
    scheduler.shutdown(wait=False)
    await application.stop()
    await application.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
