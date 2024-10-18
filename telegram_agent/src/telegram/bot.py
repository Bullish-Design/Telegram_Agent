# bot.py

import asyncio
from typing import Callable, Optional

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message as PyroMessage, ForumTopic

from telegram_agent.src.telegram.database import get_session, init_db
from telegram_agent.src.models.models import MessageContext
from telegram_agent.src.telegram.utils import extract_context, store_message

# Logging -------------------------------------------------------------------------------------------------------------
from telegram_agent.log.logger import get_logger

logger = get_logger("TelegramBot")

# Classes -------------------------------------------------------------------------------------------------------------


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

        if bot_token:
            self.client = Client(
                "bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token
            )
        else:
            self.client = Client("userbot", api_id=api_id, api_hash=api_hash)

        self.client.add_handler(MessageHandler(self.message_handler, filters.all))

    def run(self):
        """
        Starts the bot.
        """
        self.client.run()

    '''
    def message_handler(self, client: Client, message: PyroMessage):
        """
        Handles incoming messages.

        Args:
            client (Client): The Pyrogram client.
            message (PyroMessage): The received message.
        """
        logger.info(f"Received message: \n\n{message}\n")
        context = extract_context(message)
        logger.info(f"Extracted context: \n\n{context}\n")
        # Ensure asynchronous processing
        if asyncio.iscoroutinefunction(self.message_processor):
            asyncio.create_task(self.message_processor(client, context))
        else:
            self.message_processor(client, context)
    '''

    async def message_handler(self, client: Client, message: PyroMessage):
        """
        Handles incoming messages.

        Args:
            client (Client): The Pyrogram client.
            message (PyroMessage): The received message.
        """
        context = extract_context(message)
        logger.info(f"Extracted context: \n\n{context}\n")

        # Ensure asynchronous processing
        if asyncio.iscoroutinefunction(self.message_processor):
            await self.message_processor(client, context)
        else:
            # Run synchronous message processor in an executor
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.message_processor, client, context)

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
        await client.send_message(
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
        return client.create_forum_topic(
            chat_id=chat_id,
            name=name,
            icon_color=icon_color,
            icon_custom_emoji_id=icon_custom_emoji_id,
        )
