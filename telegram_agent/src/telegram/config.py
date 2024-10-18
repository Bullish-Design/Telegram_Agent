import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
IDEA_LIST_THREAD_ID = os.getenv("IDEA_LIST_THREAD_ID")
IDEAS_SUPERGROUP_CHAT_ID = os.getenv("IDEAS_SUPERGROUP_CHAT_ID")

logdir = os.getenv("LOGDIR")
