from datetime import date, timedelta

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import BOT_TOKEN, DEFAULT_REMIND_MINUTES
from app.database import (
    find_employee_by_name,
    get_user_month_shifts,
    get_user_profile,
    get_user_shifts_for_date,
    is_waiting_for_name,
    set_user_employee,
    set_user_reminder_minutes,
    set_waiting_for_name,
    upsert_user,
)
from app.keyboards import main_menu_keyboard, reminder_keyboard

application = Application.builder().token(BOT_TOKEN).build()


def format_shift_list(shifts: list[dict]) -> str:
    if not shifts:
        return "Смен нет."

    lines = []
    for shift in shifts:
        line = f"• {shift['shift_date']} | {shift['start_time']}–{shift['end_time']}"
        if shift.get("role"):
            line += f" | {shift['role']}"
        lines.append(line)
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    await upsert_user(telegram_id)

    profile = await get_user_profile(telegram_id)

    if profile and profile.get("employee_id"):
        hours = profile["remind_minutes"] // 60
        await update.message.reply_text(
            f"Привет, {profile['full_name']}!\n"
            f"Текущее напоминание: за {hours} ч до смены.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await set_waiting_for_name(telegram_id, True)
    await update.message.reply_text(
        "Привет! Введи ФИО полностью, как в расписании.\n"
        "Пример: Суворова Дарья Евгеньевна"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    await upsert_user(telegram_id)

    if text == "Сегодня":
        today = date.today().isoformat()
        shifts = await get_user_shifts_for_date(telegram_id, today)
        await update.message.reply_text(
            "Твои смены на сегодня:\n" + format_shift_list(shifts),
            reply_markup=main_menu_keyboard(),
        )
        return

    if text == "Завтра":
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        shifts = await get_user_shifts_for_date(telegram_id, tomorrow)
        await update.message.reply_text(
            "Твои смены на завтра:\n" + format_shift_list(shifts),
            reply_markup=main_menu_keyboard(),
        )
        return

    if text == "Моё расписание":
        shifts = await get_user_month_shifts(telegram_id)
        await update.message.reply_text(
            "Твоё расписание на загруженный месяц:\n" + format_shift_list(shifts),
            reply_markup=main_menu_keyboard(),
        )
        return

    if text == "Напоминание":
        await update.message.reply_text(
            "Выбери, за сколько часов напоминать перед каждой сменой:",
            reply_markup=reminder_keyboard(),
        )
        return

    if text == "Сменить ФИО":
        await set_waiting_for_name(telegram_id, True)
        await update.message.reply_text("Хорошо. Введи ФИО полностью заново.")
        return

    waiting = await is_waiting_for_name(telegram_id)
    if waiting:
        employee = await find_employee_by_name(text)
        if not employee:
            await update.message.reply_text(
                "Не нашёл такое ФИО в расписании.\n"
                "Проверь написание и введи ещё раз."
            )
            return

        employee_id, full_name = employee
        await set_user_employee(telegram_id, employee_id)

        profile = await get_user_profile(telegram_id)
        if profile and not profile.get("remind_minutes"):
            await set_user_reminder_minutes(telegram_id, DEFAULT_REMIND_MINUTES)

        await update.message.reply_text(
            f"Готово. Ты привязан к расписанию сотрудника:\n{full_name}\n\n"
            f"Теперь выбери время напоминания:",
            reply_markup=reminder_keyboard(),
        )
        return

    await update.message.reply_text(
        "Я не понял сообщение. Используй кнопки ниже или команду /start.",
        reply_markup=main_menu_keyboard(),
    )


async def reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    hours = int(query.data.split("_")[1])
    minutes = hours * 60

    await upsert_user(telegram_id)
    await set_user_reminder_minutes(telegram_id, minutes)

    profile = await get_user_profile(telegram_id)
    full_name = profile["full_name"] if profile and profile.get("full_name") else "сотрудник"

    await query.message.reply_text(
        f"Готово. Для {full_name} напоминание установлено за {hours} ч до каждой смены.",
        reply_markup=main_menu_keyboard(),
    )


async def send_message(user_id: int, text: str) -> None:
    await application.bot.send_message(chat_id=user_id, text=text)


application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(reminder_callback, pattern=r"^remind_"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
