# Imports -------------------------------------------------------------------------------------------------------------
import os
from datetime import datetime
import asyncio
from time import sleep
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
from telegram_agent.src.llm.llm_base import TelegramLLMBase


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
    bot = Client("Test_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app = Client("UserBot", api_id=API_ID, api_hash=API_HASH)

    topic_bot = TelegramLLMBase(
        user_tg_client=app,
        bot_tg_client=bot,
    )

    topic_bot.set_system_prompt("""
    SYSTEM:
    You are a helpful project planning assistant. Your goal is to help the user think more as they plan out various aspects of the project through conversation.
    During the conversation, be sure to prompt the user to more fully explain their ideas, and make suggestions to improve the specific aspect of the project the user is working on. Unless you are specifically asked for a summary, be *EXTREMELY* concise in your responses. *IF* you are asked for a summary, still be concise, but do your best to fully summarize the relevant final output from the conversation with regards to the topic's goal.

    For each user message, think "How will this affect the project goal? What problems will it cause? What should I think about adding/changing because of this?", then state the concerns to the user **IN BULLET POINT FORMAT** but **JUST** the most important 3-5 bullet points total. 

    """)

    @bot.on_message()
    async def thread_response(client, message):
        await topic_bot.init_topic(message)
        sleep(1)
        await topic_bot.generate_chat_response(message)

        # parsed_msg = await topic_bot.parse_message(message)
        # message_list = await topic_bot.get_all_messages()
        # joined_msg = "\n\n".join(message_list)
        # for msg in message_list:
        #    print(f"\n{msg}\n")
        # matched_message = await topic_bot.get_message_match("[Goal]")
        # print(f"\n\n\nMatched Message: \n\n{matched_message}\n\n\n")
        # await topic_bot.post_message(joined_msg)

    async def get_thread_messages(message_id, topic_id):
        message_list = []
        async for msg in app.get_discussion_replies(message_id, topic_id):
            if msg.topic:
                print(f"\n{msg.topic.title} | {msg.text}")
                message_list.append(msg.text)
            else:
                print(f"\n\n\n\n\n{msg}\n\n\n\n\n\n")
        return message_list

    asyncio.run(compose([bot, app]))
    # app.run()


if __name__ == "__main__":
    init()

# Misc ----------------------------------------------------------------------------------------------------------------
