from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import asyncio

TOKEN = "8547678247:AAF3fk5Sx5oefyjHbHG6S0Ioqc2c-xLxa3w"

user_schedules = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-напоминалка.\n"
        "/add — добавить задачу"
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Формат:\n"
        "Задача | YYYY-MM-DD HH:MM | за сколько минут напомнить"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text

    try:
        task, time_str, remind_before = [x.strip() for x in text.split("|")]

        task_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        remind_before = int(remind_before)

        remind_time = task_time - timedelta(minutes=remind_before)

        user_schedules.setdefault(user_id, []).append({
            "task": task,
            "time": task_time,
            "remind": remind_time,
            "sent": False
        })

        await update.message.reply_text("✅ Задача добавлена!")

    except:
        await update.message.reply_text("❌ Ошибка формата")


async def reminder_loop(app):
    while True:
        now = datetime.now()

        for user_id in list(user_schedules.keys()):
            for task in user_schedules[user_id]:
                if not task["sent"] and now >= task["remind"]:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=f"⏰ Напоминание!\n{task['task']}\nВремя: {task['time']}"
                    )
                    task["sent"] = True

        await asyncio.sleep(20)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def post_init(app):
        asyncio.create_task(reminder_loop(app))

    app.post_init = post_init

    app.run_polling()


if __name__ == "__main__":
    main()
