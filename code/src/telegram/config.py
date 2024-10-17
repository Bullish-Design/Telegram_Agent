import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_KEY = os.getenv("TELEGRAM_KEY")
API_ID = TELEGRAM_KEY.split(":")[0]
API_HASH = TELEGRAM_KEY.split(":")[-1]
