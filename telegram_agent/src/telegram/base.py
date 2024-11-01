# Imports -------------------------------------------------------------------------------------------------------------
import os
from datetime import datetime
import asyncio
from typing import Callable, Optional
from pyrogram import Client, filters, compose
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
from telegram_agent.src.telegram.bot import TelegramBot, Dispatcher, SimpleTelegramBot
from telegram_agent.src.models.message.message_base import (
    new_idea_custom_message_processor,
)
from telegram_agent.src.pipeline.actions import (
    SendMessageAction,
    ForwardMessageAction,
    # CreateChatAction,
)
from telegram_agent.src.pipeline.models.project_scaffold import (
    scaffold_decorator,
    idea_init_decorator,
)
from telegram_agent.src.pipeline.models.project_concept import (
    wrap_message_decorator,
    brainstorming_decorator,
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
wrap_message_decorator = wrap_message_decorator
brainstorming_decorator = brainstorming_decorator


# Functions -----------------------------------------------------------------------------------------------------------
def run_bots(bots, interval=60):
    try:
        while True:
            for bot in bots:
                bot.run()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Bot execution stopped.")


# Filters -------------------------------------------------------------------------------------------------------------


# Classes -------------------------------------------------------------------------------------------------------------


# Idea init:
@idea_init_decorator
class IdeaInitBot(TelegramBot): ...


# Scaffold Bot:
@scaffold_decorator
class ScaffoldBot(TelegramBot): ...


# Wrap Message Bot
@brainstorming_decorator
class ConceptBot(TelegramBot): ...


# Main ----------------------------------------------------------------------------------------------------------------


# Scripts =------------------------------------------------------------------------------------------------------------
def simple_bots():
    bot = SimpleTelegramBot()

    run_bots([bot])


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


async def composed_bots():
    scaffold_bot = ScaffoldBot(
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        bot_name="ScaffoldBot",
    )
    idea_bot = IdeaInitBot(
        api_id=API_ID,
        api_hash=API_HASH,
        bot_name="IdeaBot",
    )
    concepting_bot = ConceptBot(
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        bot_name="ConceptBot",
    )

    bot_list = [scaffold_bot, idea_bot, concepting_bot]
    await compose(bot_list)


async def dispatch_bot():
    idea_bot = IdeaInitBot(api_id=API_ID, api_hash=API_HASH)
    scaffold_bot = ScaffoldBot(api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    dispatcher = Dispatcher(api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    dispatcher.register_bot(idea_bot)
    dispatcher.register_bot(scaffold_bot)

    await dispatcher.start()


def main():
    # asyncio.run(dispatch_bot())
    asyncio.run(composed_bots())


def init():
    app = Client("Test_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app.run()


if __name__ == "__main__":
    init()

# Misc ----------------------------------------------------------------------------------------------------------------
