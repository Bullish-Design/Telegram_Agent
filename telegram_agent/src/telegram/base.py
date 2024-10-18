# Imports -------------------------------------------------------------------------------------------------------------
import os
from datetime import datetime
import asyncio
from typing import Callable, Optional
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message as PyroMessage
from pyrogram.enums import ChatType

from sqlmodel import Field, SQLModel, Session, create_engine

# Local Imports -------------------------------------------------------------------------------------------------------
from telegram_agent.src.telegram.config import API_ID, API_HASH, BOT_TOKEN

# from telegram_agent.src.models.models_base import User, Chat, Message, MessageContext
from telegram_agent.src.models.models import User, Chat, Message, MessageContext
from telegram_agent.src.telegram.utils import extract_context
from telegram_agent.src.telegram.database import get_session, init_db
from telegram_agent.src.telegram.bot import TelegramBot

# Logging -------------------------------------------------------------------------------------------------------------
from telegram_agent.log.logger import get_logger

logger = get_logger("TelegramBot_Base")
# Constants -----------------------------------------------------------------------------------------------------------


# Functions -----------------------------------------------------------------------------------------------------------


# Classes -------------------------------------------------------------------------------------------------------------


# Main ----------------------------------------------------------------------------------------------------------------


# Scripts =------------------------------------------------------------------------------------------------------------
def run_bot():
    bot = TelegramBot(api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    bot.run()


def init():
    app = Client("Test_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app.run()


if __name__ == "__main__":
    init()

# Misc ----------------------------------------------------------------------------------------------------------------
