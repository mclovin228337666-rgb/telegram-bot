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
    rows = []
    for hour in range(1, 25, 2):
        row = [InlineKeyboardButton(f"{hour} ч", callback_data=f"remind_{hour}")]
        if hour + 1 <= 24:
            row.append(
                InlineKeyboardButton(f"{hour + 1} ч", callback_data=f"remind_{hour + 1}")
            )
        rows.append(row)

    return InlineKeyboardMarkup(rows)
