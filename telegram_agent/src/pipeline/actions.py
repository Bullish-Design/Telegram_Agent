# actions.py
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


# actions.py

from typing import Any, Dict
from .models import MessageContext
from pyrogram import Client


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
