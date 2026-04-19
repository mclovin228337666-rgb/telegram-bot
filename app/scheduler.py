from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from app.database import get_events
from app.bot import send_message

scheduler = AsyncIOScheduler()


async def check_events():
    events = await get_events()

    now = datetime.now()

    for event in events:
        event_id, user_id, text, event_time, remind_minutes = event

        event_dt = datetime.fromisoformat(event_time)
        remind_time = event_dt - timedelta(minutes=remind_minutes)

        if remind_time <= now < remind_time + timedelta(minutes=1):
            await send_message(
                user_id,
                f"⏰ Напоминание: {text}\nВремя: {event_dt.strftime('%H:%M')}"
            )


def start_scheduler():
    scheduler.add_job(check_events, "interval", minutes=1)
    scheduler.start()
