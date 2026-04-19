from fastapi import FastAPI, Request
from telegram import Update
from app.bot import application
from app.scheduler import start_scheduler
from app.database import init_db
from app.config import BOT_TOKEN, WEBHOOK_URL

app = FastAPI()


@app.on_event("startup")
async def startup():
    await init_db()

    start_scheduler()

    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)

    await application.process_update(update)

    return {"ok": True}
