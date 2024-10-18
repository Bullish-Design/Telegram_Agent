# actions.py
"""
from typing import Callable, List
from telegram_bot.models import MessageContext
from pyrogram import Client


class BaseAction:
    async def execute(self, client: Client, context: MessageContext):
        raise NotImplementedError


class SendMessageAction(BaseAction):
    def __init__(self, chat_id: int, text: str, **kwargs):
        self.chat_id = chat_id
        self.text = text
        self.kwargs = kwargs

    async def execute(self, client: Client, context: MessageContext):
        await client.send_message(chat_id=self.chat_id, text=self.text, **self.kwargs)


class ForwardMessageAction(BaseAction):
    def __init__(self, from_chat_id: int, to_chat_id: int, message_id: int):
        self.from_chat_id = from_chat_id
        self.to_chat_id = to_chat_id
        self.message_id = message_id

    async def execute(self, client: Client, context: MessageContext):
        await client.forward_messages(
            chat_id=self.to_chat_id,
            from_chat_id=self.from_chat_id,
            message_ids=self.message_id,
        )

"""

# actions.py
import asyncio
from typing import Any, Dict, List
from telegram_agent.src.models.models import MessageContext
from pyrogram import Client
from pyrogram.errors import FloodWait, PeerFlood


class BaseAction:
    """
    Abstract base class for actions.
    """

    async def execute(self, client: Client, context: MessageContext):
        raise NotImplementedError


class SendMessageAction(BaseAction):
    """
    Action to send a message.

    Args:
        chat_id (int): The ID of the chat to send the message to.
        text (str): The text of the message to send.
        kwargs (Dict[str, Any]): Additional keyword arguments for send_message.
    """

    def __init__(self, chat_id: int, text: str, **kwargs):
        self.chat_id = chat_id
        self.text = text
        self.kwargs = kwargs

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        await client.send_message(chat_id=self.chat_id, text=self.text, **self.kwargs)


class ForwardMessageAction(BaseAction):
    """
    Action to forward a message.

    Args:
        from_chat_id (int): The ID of the source chat.
        to_chat_id (int): The ID of the destination chat.
        message_id (int): The ID of the message to forward.
    """

    def __init__(self, from_chat_id: int, to_chat_id: int, message_id: int):
        self.from_chat_id = from_chat_id
        self.to_chat_id = to_chat_id
        self.message_id = message_id

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        await client.forward_messages(
            chat_id=self.to_chat_id,
            from_chat_id=self.from_chat_id,
            message_ids=self.message_id,
        )


class CreateChatAction(BaseAction):
    """
    Action to create a new supergroup, set privacy level, and generate an invite link.

    Args:
        title (str): The title of the new chat.
        privacy (str): The privacy level ('public' or 'private').
    """

    def __init__(self, title: str, privacy: str = "private"):
        self.title = title
        self.privacy = privacy

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        # Create a new supergroup
        result = await client.create_channel(
            title=self.title, description="Created by bot", megagroup=True
        )

        # Extract the chat ID
        chat = result.chat
        chat_id = chat.id

        # Enable topics in the supergroup
        try:
            await client.toggle_forum(chat_id=chat_id, is_forum=True)
        except Exception as e:
            print(f"Failed to enable topics: {e}")

        # Generate an invite link
        invite_link = await client.create_chat_invite_link(chat_id)

        # Create a new forum topic (thread)
        try:
            forum_topic = await client.create_forum_topic(
                chat_id=chat_id, name=self.title
            )
            # Send a welcome message in the new topic
            await client.send_message(
                chat_id=chat_id,
                text="Welcome to the new supergroup!",
                message_thread_id=forum_topic.message_thread_id,
            )
        except Exception as e:
            print(f"Failed to create forum topic: {e}")

        # Reply to the user's message with the invite link
        try:
            await client.send_message(
                chat_id=context.chat_id,
                text=f"A new supergroup '{self.title}' has been created! Join here: {invite_link.invite_link}",
                reply_to_message_id=context.msg_id,
                message_thread_id=context.message_thread_id,  # Reply in the same thread if applicable
            )
        except Exception as e:
            print(f"Failed to send invite link to the user: {e}")
