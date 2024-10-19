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
from telegram_agent.src.telegram.utils import extract_context, store_message
from telegram_agent.src.telegram.database import get_session, init_db
from telegram_agent.src.telegram.bot import TelegramBot
from telegram_agent.src.models.message.message_base import (
    new_idea_custom_message_processor,
)
from telegram_agent.src.pipeline.actions import (
    SendMessageAction,
    ForwardMessageAction,
    CreateChatAction,
)
from telegram_agent.src.pipeline.models.project_scaffold import (
    scaffold_decorator,
    idea_init_decorator,
)

# Logging -------------------------------------------------------------------------------------------------------------
from telegram_agent.log.logger import get_logger

logger = get_logger("TelegramBot_Base")
# Constants -----------------------------------------------------------------------------------------------------------
bot = TelegramBot(
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    # message_processor=new_idea_custom_message_processor,
)

userbot = TelegramBot(
    api_id=API_ID,
    api_hash=API_HASH,
    # message_processor=new_idea_custom_message_processor,
)

scaffold_decorator = scaffold_decorator
idea_init_decorator = idea_init_decorator

# Functions -----------------------------------------------------------------------------------------------------------


# Filters -------------------------------------------------------------------------------------------------------------


# Classes -------------------------------------------------------------------------------------------------------------


# Idea init:
@idea_init_decorator
class IdeaInitBot(TelegramBot):
    pass


# Scaffold Bot:
@scaffold_decorator
class ScaffoldBot(TelegramBot):
    pass


# Main ----------------------------------------------------------------------------------------------------------------


# Scripts =------------------------------------------------------------------------------------------------------------
def run_bot():
    # bot = TelegramBot(
    #    api_id=API_ID,
    #    api_hash=API_HASH,
    #    bot_token=BOT_TOKEN,
    #    message_processor=new_idea_custom_message_processor,
    # )

    scaffold_bot = ScaffoldBot(api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    scaffold_bot.run()


def run_userbot():
    # userbot = TelegramBot(
    #    api_id=API_ID,
    #    api_hash=API_HASH,
    #    message_processor=new_idea_custom_message_processor,
    # )

    idea_bot = IdeaInitBot(api_id=API_ID, api_hash=API_HASH)

    idea_bot.run()


def init():
    app = Client("Test_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app.run()


if __name__ == "__main__":
    init()

# Misc ----------------------------------------------------------------------------------------------------------------
