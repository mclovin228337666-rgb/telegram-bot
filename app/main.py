from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update

from app.bot import application
from app.config import WEBHOOK_URL
from app.database import init_db, replace_month_schedule
from app.schedule_seed import SCHEDULE_MONTH, SCHEDULE_ROWS, SCHEDULE_YEAR
from app.scheduler import scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await replace_month_schedule(SCHEDULE_YEAR, SCHEDULE_MONTH, SCHEDULE_ROWS)

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
