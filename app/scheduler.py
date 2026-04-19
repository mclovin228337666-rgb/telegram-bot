from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot import send_message
from app.database import (
    get_all_users_with_shifts,
    get_employee_upcoming_shifts,
    reminder_already_sent,
    save_reminder_log,
)

scheduler = AsyncIOScheduler()


async def check_shifts() -> None:
    now = datetime.now().replace(second=0, microsecond=0)
    users = await get_all_users_with_shifts()
    today = now.date().isoformat()

    for user in users:
        upcoming_shifts = await get_employee_upcoming_shifts(user["employee_id"], today)

        for shift in upcoming_shifts:
            shift_dt = datetime.fromisoformat(f"{shift['shift_date']} {shift['start_time']}:00")
            remind_at = shift_dt - timedelta(minutes=user["remind_minutes"])

            if remind_at <= now < remind_at + timedelta(minutes=1):
                reminder_key = remind_at.isoformat(timespec="minutes")
                already_sent = await reminder_already_sent(
                    user["telegram_id"], shift["id"], reminder_key
                )
                if already_sent:
                    continue

                text = (
                    "⏰ Напоминание о смене\n"
                    f"Сотрудник: {user['full_name']}\n"
                    f"Дата: {shift['shift_date']}\n"
                    f"Время: {shift['start_time']}–{shift['end_time']}"
                )
                if shift.get("role"):
                    text += f"\nДолжность: {shift['role']}"

                await send_message(user["telegram_id"], text)
                await save_reminder_log(user["telegram_id"], shift["id"], reminder_key)


def start_scheduler() -> None:
    scheduler.add_job(check_shifts, "interval", minutes=1, id="check_shifts", replace_existing=True)
    scheduler.start()
