# Telegram Scheduler Bot

Бот для сотрудников компании с индивидуальным расписанием и напоминаниями.

## 🚀 Возможности

* Добавление событий
* Напоминания за N минут
* Индивидуальное расписание для каждого пользователя

## 🛠 Установка

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Запуск

```bash
uvicorn app.main:app --reload
```

## 🌐 Deploy (Render)

* Build:

```
pip install -r requirements.txt
```

* Start:

```
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

## ⚙️ ENV переменные

```
BOT_TOKEN=your_token
WEBHOOK_URL=https://your-app.onrender.com
```

## 🤖 Использование

```
/start
/add Встреча | 2026-04-20 15:00 | 30
```

## 📌 Стек

* Python 3.11.9
* FastAPI
* python-telegram-bot
* APScheduler
* SQLite

