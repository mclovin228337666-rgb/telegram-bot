import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
WEBHOOK_URL = (os.getenv("WEBHOOK_URL") or "").strip()
DEFAULT_REMIND_MINUTES = int((os.getenv("DEFAULT_REMIND_MINUTES") or "60").strip())
