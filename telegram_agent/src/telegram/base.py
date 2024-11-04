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
import pprint

from sqlmodel import Field, SQLModel, Session, create_engine

# Local Imports -------------------------------------------------------------------------------------------------------
from telegram_agent.src.telegram.config import API_ID, API_HASH, BOT_TOKEN

# from telegram_agent.src.models.models_base import User, Chat, Message, MessageContext
from telegram_agent.src.models.models import User, Chat, Message, MessageContext
from telegram_agent.src.telegram.utils import (
    extract_context,
    store_message,
    build_message_context_from_db,
)
from telegram_agent.src.telegram.database import get_session, init_db
from telegram_agent.src.telegram.bot import TelegramBot, Dispatcher, SimpleTelegramBot
from telegram_agent.src.models.message.message_base import (
    new_idea_custom_message_processor,
)
from telegram_agent.src.pipeline.actions import (
    SendMessageAction,
    ForwardMessageAction,
    # CreateChatAction,
    create_supergroup,
    init_supergroup_topics,
)
from telegram_agent.src.pipeline.models.project_scaffold import (
    scaffold_decorator,
    idea_init_decorator,
)
from telegram_agent.src.pipeline.models.project_concept import (
    wrap_message_decorator,
    brainstorming_decorator,
)
from telegram_agent.src.llm.llm_base import TelegramLLMBase, LLMbot, LLMconfig
from telegram_agent.src.telegram.chat.chat_base import ChatContext, TopicContext


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


def get_chat_context(session, parsed_msg):
    if parsed_msg.message_thread_name:
        # print(
        #    f"\n>>> Found message in thread {parsed_msg.message_thread_name}: id={parsed_msg.message_thread_id}\n\n"
        # )
        chat_context = TopicContext(
            message_thread_id=parsed_msg.message_thread_id,
            chat_id=parsed_msg.chat_id,
            session=session,
        )
    else:
        chat_context = ChatContext(
            chat_id=parsed_msg.chat_id,
            session=session,
        )
    return chat_context


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

    test_dict = {
        "Goal": "[Goal]",
        "Brainstorming": "[Prompt] Please help the user with brainstorming for the project goal.",
        "References": "[Prompt] The following posts could be useful reference information for this project. Please analyze the contents of the post and describe if/how it would be useful.",
        "Overview": "[Prompt] The following overview posts serve as a summary and 'How to' guide the user will follow to accomplish the project goal.",
        "Research": "[Prompt] The following posts describe topics of research related to the project."
    }
    code_project_dict = {
        "Features": "[Prompt] Please help the user define the features needed for a software product which will accomplish the desired project goal.",
        "Structure": "[Prompt] Please help the user determine the best directory structure for the software project. Think of the software features, and then provide the directory tree of folders and subfolders, as well as the files inside of each folder and subfolder."
        "Requirements": "[Prompt] Please help the user create a set of requirements for the code project that when successfully completed, will meet the project goal.",
        "MVP": "[Prompt] Please help the user determine a Minimum Viable Product that, when successfully implemented, will successfully demonstrate all the necessary requirements for the project goal."
    }
    idea_list_topic_int = 4
    init_db()
    session = get_session()

    @bot.on_message(group=2)
    async def thread_response(client, message):
        parsed_msg, chat_context = await get_msg_and_context(session, message)

        print(
            f"\n---------------------------------------- Thread Response -------------------------------------------------"
        )
        print(f"\n\n>>> Message:\n")  # "{parsed_msg}\n\n")
        pprint.pp(parsed_msg)
        print(f"\n>>> Chat:\n")
        pprint.pp(parsed_msg.chat)
        print(f"\n>>> User:\n")
        pprint.pp(parsed_msg.user)
        print(f"\n\n")

        history_list = chat_context.get_history()
        # for msg in history_list:
        #    print(f"\n{msg.message_thread_name} | {msg.user_id}  | {msg.text}\n")
        llm_init = LLMconfig()
        llm_init_msg = llm_init.init_llm(topic_context=chat_context)
        print(f"\n\n\nLLM Obj:\n\n{llm_init_msg}\n\n\n")

    @bot.on_message(filters.chat(-1002407722343) & filters.topic(idea_list_topic_int))
    async def init_supergroup(client, message):
        print(f"**Creating Supergroup**")
        parsed_msg, chat_context = await get_msg_and_context(session, message)
        new_group = await create_supergroup(
            topic_bot.user_tg_client, parsed_msg.text, "Project"
        )
        logger.info(f"Created new Supergroup: {new_group}")
        message.stop_propagation()

    @bot.on_message(filters.reply)
    async def update_response(client, message):
        pass

    @bot.on_message(filters.regex("InitSupergroup"))
    async def populate_supergroup(client, message):
        print(f"**Populating Supergroup**")
        parsed_msg, chat_context = await get_msg_and_context(session, message)
        await init_supergroup_topics(
            topic_bot.bot_tg_client, parsed_msg.chat_id, test_dict
        )
        print(f"   Supergroup Populated.")
        message.stop_propagation()

    @bot.on_message(filters.command("refreshdb"))  # , group=1)
    async def refreshdb(client, message):
        print(
            f"\n ---------------------------------------------- RefreshDB ---------------------------------------------------"
        )
        parsed_msg, chat_context = await get_msg_and_context(session, message)

        await chat_context.refresh_messages_to_db(
            client=topic_bot.user_tg_client, chat_id=parsed_msg.chat_id, session=session
        )
        print(f"    **Done with Refresh**")
        message.stop_propagation()

    @bot.on_message(filters.command("summary"))  # , group=1)
    async def summary(client, message):
        print(
            f"\n---------------------------------------- Summary Response -------------------------------------------------"
        )
        parsed_msg, chat_context = await get_msg_and_context(session, message)
        history_list = chat_context.get_history()
        history_text = ""
        for msg in history_list:
            msg_context = build_message_context_from_db(session, msg)
            history_text += f"{msg_context.user.username or msg_context.user.first_name}: {msg_context.text}\n"
        print(f"\n\n{history_text}\n\n")
        await message.reply_text(history_text)
        message.stop_propagation()

    @bot.on_message(filters.command("ask"))
    async def ask(client, message):
        print(
            f"\n---------------------------------------- Ask -------------------------------------------------------"
        )
        await refresh_database(session, message)
        parsed_msg, chat_context = await get_msg_and_context(session, message)

        llm_init = LLMconfig()
        llm_init_msg = llm_init.init_llm(topic_context=chat_context)
        response = llm_init.ask(message)
        print(f"\n  >>> Returned Response: \n\n{response}\n\n")
        await topic_bot.bot_tg_client.send_message(
            chat_id=parsed_msg.chat_id,
            message_thread_id=parsed_msg.message_thread_id,
            text=response,
        )

        # await message.reply_text(response)
        message.stop_propagation()

    async def get_msg_and_context(session, message):
        parsed_msg = await extract_context(message)
        store_message(session, parsed_msg)

        chat_context = get_chat_context(session=session, parsed_msg=parsed_msg)
        return parsed_msg, chat_context

    async def get_thread_messages(message_id, topic_id):
        message_list = []
        async for msg in app.get_discussion_replies(message_id, topic_id):
            if msg.topic:
                print(f"\n{msg.topic.title} | {msg.text}")
                message_list.append(msg.text)
            else:
                print(f"\n\n\n\n\n{msg}\n\n\n\n\n\n")
        return message_list

    async def refresh_database(session, message):
        parsed_msg, chat_context = await get_msg_and_context(session, message)

        await chat_context.refresh_messages_to_db(
            client=topic_bot.user_tg_client,
            chat_id=parsed_msg.chat_id,
            session=session,
            all=True,
        )

    asyncio.run(compose([bot, app]))
    # app.run()


if __name__ == "__main__":
    init()

# Misc ----------------------------------------------------------------------------------------------------------------
