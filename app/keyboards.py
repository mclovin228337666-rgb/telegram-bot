from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["Сегодня", "Завтра"],
            ["Моё расписание", "Напоминание"],
            ["Сменить ФИО"],
        ],
        resize_keyboard=True,
    )


def reminder_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("15 минут", callback_data="remind_15"),
            InlineKeyboardButton("30 минут", callback_data="remind_30"),
        ],
        [
            InlineKeyboardButton("60 минут", callback_data="remind_60"),
            InlineKeyboardButton("120 минут", callback_data="remind_120"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)
