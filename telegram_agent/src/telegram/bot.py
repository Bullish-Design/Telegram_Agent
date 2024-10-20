# bot.py

import asyncio
from typing import Callable, Optional

from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message as PyroMessage, ForumTopic
from pyrogram.enums import MessageServiceType
from pyrogram.types import ChatPrivileges
from telegram_agent.src.telegram.database import get_session, init_db
from telegram_agent.src.models.models import MessageContext
from telegram_agent.src.telegram.utils import extract_context, store_message

# Logging -------------------------------------------------------------------------------------------------------------
from telegram_agent.log.logger import get_logger

logger = get_logger("TelegramBot")

# Classes -------------------------------------------------------------------------------------------------------------

# Dispatcher:
# dispatcher.py

from pyrogram import Client
from pyrogram.handlers import MessageHandler
from pyrogram import filters
from typing import List, Callable, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class Dispatcher:
    """
    Central dispatcher that receives messages and notifies registered bots.

    Args:
        api_id (int): Telegram API ID.
        api_hash (str): Telegram API Hash.
        bot_token (str): Bot token for authentication.
    """

    def __init__(self, api_id: int, api_hash: str, bot_token: str):
        # self.client = Client(
        #    "dispatcher_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token
        # )
        self.dispatcher_client = Client(
            "user_dispatcher_bot", api_id=api_id, api_hash=api_hash
        )
        self.bots: List["TelegramBot"] = []  # List of registered bots

    def register_bot(self, bot: "TelegramBot"):
        """
        Registers a bot with the dispatcher.

        Args:
            bot (BaseBot): The bot instance to register.
        """
        self.bots.append(bot)
        logger.info(f"Registered bot: {bot.__class__.__name__}")

    async def start(self):
        """
        Starts the dispatcher and the client.
        """
        await self.dispatcher_client.start()
        self.dispatcher_client.add_handler(
            MessageHandler(self.message_handler, filters.all)
        )
        logger.info("Dispatcher started.")
        await idle()  # Keeps the program running

    async def message_handler(self, client: Client, message):  # client: Client
        """
        Handles incoming messages and notifies registered bots.

        Args:
            client (Client): The Pyrogram client.
            message: The received message.
        """

        logger.debug(f"Dispatcher received message: {message}")
        # Notify all registered bots
        for bot in self.bots:
            asyncio.create_task(bot.process_message(message))


class SimpleTelegramBot:
    def __init__(self, api_id, api_hash, bot_token, name):
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.name = name
        self.last_update_id = 0

    def run(self):
        with Client(
            self.name,
            api_id=self.api_id,
            api_hash=self.api_hash,
            bot_token=self.bot_token,
        ) as app:
            # Get updates since last login
            updates = app.get_updates(offset=self.last_update_id + 1)

            for update in updates:
                message = update.message
                if message:
                    # Process the message
                    self.process_message(app, message)

                # Update the last processed update ID
                self.last_update_id = update.update_id

    def process_message(self, app, message):
        # Example: Echo the message back to the user
        app.send_message(message.chat.id, f"You said: {message.text}")


class TelegramBot:
    """
    Represents the Telegram bot.

    Args:
        api_id (int): The API ID from Telegram.
        api_hash (str): The API hash from Telegram.
        bot_token (Optional[str]): The bot token if using a bot account.
        message_processor (Optional[Callable[[Client, MessageContext], None]]): The message processor function.
    """

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        bot_token: Optional[str] = None,
        message_processor: Optional[Callable[[Client, MessageContext], None]] = None,
    ):
        init_db()
        self.session_factory = get_session
        self.message_processor = message_processor or self.default_message_processor
        # self.logger = get_logger(self.__class__.__name__)
        if bot_token:
            self.client = Client(
                "bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token
            )
            self.client.add_handler(MessageHandler(self.message_handler, filters.all))
            # self.init_bot()
        else:
            self.client = Client("userbot", api_id=api_id, api_hash=api_hash)
            self.client.add_handler(MessageHandler(self.message_handler, filters.all))

        self.logger = get_logger(self.client.name)

        self.logger.info(
            f"{self.client.name} | Initialized Telegram bot with message processor: {message_processor}"
        )

    def run(self):
        """
        Starts the bot.
        """
        self.client.run()

    def init_bot(self):
        async def set_priv():
            await self.client.set_bot_default_privileges(
                ChatPrivileges(
                    can_delete_messages=True,
                    can_restrict_members=True,
                    # can_send_other_messages=True,
                    # can_add_web_page_previews=True,
                    can_manage_topics=True,
                )
            )

        asyncio.run(set_priv())

    # async def process_message(self, message):
    #    client = self.client
    #    await self.message_handler(client, message)

    async def message_handler(self, client: Client, message: PyroMessage):
        """
        Handles incoming messages.

        Args:
            client (Client): The Pyrogram client.
            message (PyroMessage): The received message.
        """
        # Check if the message is a service message we want to skip
        SERVICE_MESSAGE_TYPES_TO_SKIP = [
            MessageServiceType.NEW_CHAT_MEMBERS,
            "left_chat_member",
            "new_chat_title",
            "new_chat_photo",
            "delete_chat_photo",
            "group_chat_created",
            "supergroup_chat_created",
            "channel_chat_created",
            MessageServiceType.FORUM_TOPIC_CREATED,
            # Add other types as needed
        ]
        self.logger.info(
            f"{self.client.name} | Message service type: {message.service}. Outgoing? {message.outgoing}"
        )
        print(
            f"{self.client.name} | Message service type: {message.service}. Outgoing? {message.outgoing}"
        )
        """
        if message.service in SERVICE_MESSAGE_TYPES_TO_SKIP:
            self.logger.info(
                f"{self.client.name} | Received a service message of type {message.service}. Skipping processing."
            )

            # return  # Exit the message processor

        if message.outgoing == "true":
            self.logger.info(
                f"{self.client.name} | Message is outgoing. Skipping processing."
            )
            # return
        """
        context = extract_context(message)
        self.logger.info(f"{self.client.name} | Extracted context: \n\n{context}\n")
        print(f"\n{self.client.name} | Received message: {context.text}\n")
        # Ensure asynchronous processing
        if asyncio.iscoroutinefunction(self.message_processor):
            self.logger.info(f"{self.client.name} | IsCoroutine!")
            await self.message_processor(self.client, context)
        else:
            self.logger.info(f"{self.client.name} | Is not Coroutine.")
            # Run synchronous message processor in an executor
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, self.message_processor, self.client, context
            )

    async def default_message_processor(self, client: Client, context: MessageContext):
        """
        Default message processor if none is provided.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        # Store the message
        with self.session_factory() as session:
            # from .utils import store_message
            store_message(session, context)

        # Send a message in the appropriate context
        await self.client.send_message(
            chat_id=context.chat_id,
            text=f"Echo: {context.text}",
            message_thread_id=context.message_thread_id,  # Reply in the same forum topic if applicable
        )

    def create_forum_topic(
        self,
        client: Client,
        chat_id: int,
        name: str,
        icon_color: Optional[int] = None,
        icon_custom_emoji_id: Optional[str] = None,
    ) -> ForumTopic:
        """
        Creates a forum topic in a supergroup chat.

        Args:
            client (Client): The Pyrogram client.
            chat_id (int): The ID of the supergroup chat.
            name (str): The name of the forum topic.
            icon_color (Optional[int]): The icon color for the topic.
            icon_custom_emoji_id (Optional[str]): The custom emoji ID for the topic icon.

        Returns:
            ForumTopic: The created forum topic.
        """
        return self.client.create_forum_topic(
            chat_id=chat_id,
            name=name,
            icon_color=icon_color,
            icon_custom_emoji_id=icon_custom_emoji_id,
        )

    # Add start and stop methods to integrate with compose
    async def start(self):
        """
        Starts the bot by starting the underlying Pyrogram client.
        """
        await self.client.start()
        # if self.client.name != "userbot":
        #    result = await self.client.set_bot_default_privileges(
        #        ChatPrivileges(
        #            can_delete_messages=True,
        #            can_restrict_members=True,
        #            # can_send_other_messages=True,
        #            # can_add_web_page_previews=True,
        #            can_manage_topics=True,
        #            can_post_messages=True,
        #            can_edit_messages=True,
        #            can_pin_messages=True,
        #            can_edit_stories=True,
        #        )
        #    )
        #    # self.logger(f"Reset Chat Priveliges => {result}")

    async def stop(self):
        """
        Stops the bot by stopping the underlying Pyrogram client.
        """
        await self.client.stop()

    # To make start and stop methods available as instance methods
    # TelegramBot.start = start
    # TelegramBot.stop = stop
