import aiosqlite
from datetime import datetime

DB_NAME = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            event_time TEXT,
            remind_minutes INTEGER
        )
        """)
        await db.commit()


async def add_event(user_id: int, text: str, event_time: str, remind_minutes: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO schedules (user_id, text, event_time, remind_minutes) VALUES (?, ?, ?, ?)",
            (user_id, text, event_time, remind_minutes)
        )
        await db.commit()


async def get_events():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM schedules")
        return await cursor.fetchall()


async def delete_event(event_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM schedules WHERE id = ?", (event_id,))
        await db.commit()
