from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.config import BOT_TOKEN
from app.database import add_event

application = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Добавь событие так:\n"
        "/add Текст | YYYY-MM-DD HH:MM | минуты_до"
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = " ".join(context.args).split("|")

        text = data[0].strip()
        event_time = data[1].strip()
        remind = int(data[2].strip())

        await add_event(
            update.effective_user.id,
            text,
            event_time,
            remind
        )

        await update.message.reply_text("Событие добавлено!")

    except Exception:
        await update.message.reply_text("Ошибка формата!")


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add))


async def send_message(user_id: int, text: str):
    await application.bot.send_message(chat_id=user_id, text=text)
