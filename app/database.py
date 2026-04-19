import aiosqlite
from typing import Any

DB_NAME = "bot.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                employee_id INTEGER,
                remind_minutes INTEGER NOT NULL DEFAULT 60,
                waiting_for_name INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                shift_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                role TEXT,
                department TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminder_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                shift_id INTEGER NOT NULL,
                reminder_for_datetime TEXT NOT NULL,
                UNIQUE(telegram_id, shift_id, reminder_for_datetime)
            )
        """)

        await db.commit()


def normalize_name(name: str) -> str:
    return " ".join(name.lower().replace("ё", "е").split())


async def upsert_user(telegram_id: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO users (telegram_id)
            VALUES (?)
            ON CONFLICT(telegram_id) DO NOTHING
        """, (telegram_id,))
        await db.commit()


async def set_waiting_for_name(telegram_id: int, value: bool) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET waiting_for_name = ? WHERE telegram_id = ?",
            (1 if value else 0, telegram_id),
        )
        await db.commit()


async def is_waiting_for_name(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT waiting_for_name FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return bool(row[0]) if row else False


async def get_user_profile(telegram_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT u.telegram_id, u.employee_id, u.remind_minutes, u.waiting_for_name, e.full_name
            FROM users u
            LEFT JOIN employees e ON e.id = u.employee_id
            WHERE u.telegram_id = ?
        """, (telegram_id,))
        row = await cursor.fetchone()

        if not row:
            return None

        return {
            "telegram_id": row[0],
            "employee_id": row[1],
            "remind_minutes": row[2],
            "waiting_for_name": bool(row[3]),
            "full_name": row[4],
        }


async def set_user_employee(telegram_id: int, employee_id: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users
            SET employee_id = ?, waiting_for_name = 0
            WHERE telegram_id = ?
        """, (employee_id, telegram_id))
        await db.commit()


async def set_user_reminder_minutes(telegram_id: int, minutes: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET remind_minutes = ? WHERE telegram_id = ?",
            (minutes, telegram_id),
        )
        await db.commit()


async def add_employee(full_name: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO employees (full_name) VALUES (?)",
            (full_name.strip(),),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT id FROM employees WHERE full_name = ?",
            (full_name.strip(),),
        )
        row = await cursor.fetchone()
        return int(row[0])


async def find_employee_by_name(name: str) -> tuple[int, str] | None:
    normalized = normalize_name(name)

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, full_name FROM employees")
        rows = await cursor.fetchall()

        for employee_id, full_name in rows:
            if normalize_name(full_name) == normalized:
                return int(employee_id), str(full_name)

        return None


async def replace_month_schedule(year: int, month: int, schedule_rows: list[dict[str, str]]) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        for row in schedule_rows:
            await db.execute(
                "INSERT OR IGNORE INTO employees (full_name) VALUES (?)",
                (row["full_name"].strip(),),
            )

        first_day = f"{year:04d}-{month:02d}-01"
        if month == 12:
            next_month = f"{year + 1:04d}-01-01"
        else:
            next_month = f"{year:04d}-{month + 1:02d}-01"

        employee_ids_cursor = await db.execute("SELECT id FROM employees")
        employee_ids = [r[0] for r in await employee_ids_cursor.fetchall()]

        if employee_ids:
            placeholders = ",".join("?" for _ in employee_ids)
            await db.execute(
                f"DELETE FROM shifts WHERE employee_id IN ({placeholders}) AND shift_date >= ? AND shift_date < ?",
                (*employee_ids, first_day, next_month),
            )

        for row in schedule_rows:
            cur = await db.execute(
                "SELECT id FROM employees WHERE full_name = ?",
                (row["full_name"].strip(),),
            )
            employee_row = await cur.fetchone()
            employee_id = employee_row[0]

            await db.execute("""
                INSERT INTO shifts (
                    employee_id, shift_date, start_time, end_time, role, department
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                employee_id,
                row["shift_date"],
                row["start_time"],
                row["end_time"],
                row.get("role", ""),
                row.get("department", ""),
            ))

        await db.commit()


async def get_user_shifts_for_date(telegram_id: int, shift_date: str) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT s.id, e.full_name, s.shift_date, s.start_time, s.end_time, s.role, s.department
            FROM shifts s
            JOIN employees e ON e.id = s.employee_id
            JOIN users u ON u.employee_id = e.id
            WHERE u.telegram_id = ? AND s.shift_date = ?
            ORDER BY s.start_time
        """, (telegram_id, shift_date))
        rows = await cursor.fetchall()

        return [
            {
                "id": row[0],
                "full_name": row[1],
                "shift_date": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "role": row[5],
                "department": row[6],
            }
            for row in rows
        ]


async def get_user_month_shifts(telegram_id: int) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT s.id, e.full_name, s.shift_date, s.start_time, s.end_time, s.role, s.department
            FROM shifts s
            JOIN employees e ON e.id = s.employee_id
            JOIN users u ON u.employee_id = e.id
            WHERE u.telegram_id = ?
            ORDER BY s.shift_date, s.start_time
        """, (telegram_id,))
        rows = await cursor.fetchall()

        return [
            {
                "id": row[0],
                "full_name": row[1],
                "shift_date": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "role": row[5],
                "department": row[6],
            }
            for row in rows
        ]


async def get_all_users_with_shifts() -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT u.telegram_id, u.remind_minutes, e.id, e.full_name
            FROM users u
            JOIN employees e ON e.id = u.employee_id
        """)
        rows = await cursor.fetchall()

        return [
            {
                "telegram_id": row[0],
                "remind_minutes": row[1],
                "employee_id": row[2],
                "full_name": row[3],
            }
            for row in rows
        ]


async def get_employee_upcoming_shifts(employee_id: int, from_date: str) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT id, shift_date, start_time, end_time, role, department
            FROM shifts
            WHERE employee_id = ? AND shift_date >= ?
            ORDER BY shift_date, start_time
        """, (employee_id, from_date))
        rows = await cursor.fetchall()

        return [
            {
                "id": row[0],
                "shift_date": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "role": row[4],
                "department": row[5],
            }
            for row in rows
        ]


async def reminder_already_sent(telegram_id: int, shift_id: int, reminder_for_datetime: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 1
            FROM reminder_logs
            WHERE telegram_id = ? AND shift_id = ? AND reminder_for_datetime = ?
        """, (telegram_id, shift_id, reminder_for_datetime))
        return await cursor.fetchone() is not None


async def save_reminder_log(telegram_id: int, shift_id: int, reminder_for_datetime: str) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO reminder_logs (telegram_id, shift_id, reminder_for_datetime)
            VALUES (?, ?, ?)
        """, (telegram_id, shift_id, reminder_for_datetime))
        await db.commit()
