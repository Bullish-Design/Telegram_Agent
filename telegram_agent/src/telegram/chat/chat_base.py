# Imports
from typing import List, Optional
from pydantic import BaseModel, PrivateAttr
from sqlmodel import Session
from pyrogram.types import Message as PyroMessage
from pyrogram import Client
import re

# Library Imports -----------------------------------------------------------------------------------------------------
from telegram_agent.src.telegram.utils import extract_context, store_message
from telegram_agent.src.models.models import Message


class ChatContext(BaseModel):
    chat_id: int
    session: Session  # = PrivateAttr()

    class Config:
        arbitrary_types_allowed = True

    def get_history(self, all: Optional[bool] = False) -> List[Message]:
        messages = (
            self.session.query(Message)
            .filter(Message.chat_id == self.chat_id)
            .order_by(Message.date)
            .all()
            # .unique()
        )
        return messages

    async def get_all_messages(self, client) -> List[PyroMessage]:
        """
        Retrieve messages from the specified chat and topic.
        """
        message_list = []

        if self.chat_id:
            all_messages = client.get_chat_history(self.chat_id)
            async for msg in all_messages:
                # sleep(0.25)
                if msg.text:
                    message_list.append(msg)
        return message_list

    async def refresh_messages_to_db(
        self, client: Client, chat_id: int, session: Session
    ):
        """
        Fetch messages from the specified chat and synchronize them with the database.
        For each message:
        - If it doesn't exist in the database, add it.
        - If it exists, compare the fields and update if necessary.
        """
        # Fetch all existing messages from the database for the given chat
        existing_messages = (
            session.query(Message).filter(Message.chat_id == chat_id).all()
        )
        # Create a dictionary mapping msg_id to Message objects for quick lookup
        existing_messages_dict = {
            message.msg_id: message for message in existing_messages
        }
        msg_list = await self.get_all_messages(client)
        # Fetch messages from the chat using Pyrogram
        for msg in msg_list:  # client.get_chat_history(chat_id):
            if msg.text:
                # Extract message context
                context = await extract_context(msg)
                # Check if the message exists in the database
                existing_message = existing_messages_dict.get(context.msg_id)
                if not existing_message:
                    # Message doesn't exist, so add it
                    store_message(session, context)
                    # Add the new message to the existing_messages_dict
                    existing_messages_dict[context.msg_id] = (
                        session.query(Message)
                        .filter(
                            Message.msg_id == context.msg_id,
                            Message.chat_id == context.chat_id,
                        )
                        .first()
                    )
                else:
                    # Message exists, compare fields and update if necessary
                    needs_update = False
                    fields_to_compare = [
                        "user_id",
                        "chat_type",
                        "chat_title",
                        "message_thread_id",
                        "message_thread_name",
                        "date",
                        "text",
                    ]
                    for field in fields_to_compare:
                        db_value = getattr(existing_message, field)
                        new_value = getattr(context, field)
                        if db_value != new_value:
                            setattr(existing_message, field, new_value)
                            needs_update = True
                    if needs_update:
                        session.add(existing_message)
                        session.commit()

    def search(self, pattern: str, all: Optional[bool] = False) -> List[Message]:
        messages = self.get_history(all)
        regex = re.compile(pattern)
        matching_messages = [
            msg for msg in messages if msg.text and regex.search(msg.text)
        ]
        msg_id = None
        return_messages = []
        for msg in matching_messages:
            if msg.msg_id != msg_id:
                msg_id = msg.msg_id
                return_messages.append(msg)
        return return_messages

    def get_goal(self): ...

    def get_configuration_messages(
        self, label: str, all: Optional[bool] = False
    ) -> List[Message]:
        """
        Searches for configuration messages in the chat history that match the given label.

        Args:
            label (str): The label inside the square brackets to search for.

        Returns:
            List[Message]: A list of messages that match the label.
        """
        pattern = rf"^\[{label}\](.*)"
        return self.search(pattern, all)

    def init_prompt(self):
        pass


class TopicContext(ChatContext):
    message_thread_id: Optional[int]

    def get_history(self, all: Optional[bool] = False) -> List[Message]:
        if all:
            messages = (
                self.session.query(Message)
                .filter(Message.chat_id == self.chat_id)
                .order_by(Message.date)
                .all()
                # .unique()
            )
        else:
            messages = (
                self.session.query(Message)
                .filter(
                    Message.chat_id == self.chat_id,
                    Message.message_thread_id == self.message_thread_id,
                )
                .order_by(Message.date)
                .all()
                # .unique()
            )
        return messages

    async def refresh_messages_to_db(
        self, client: Client, chat_id: int, session: Session
    ):
        """
        Fetch messages from the specified chat and synchronize them with the database.
        For each message:
        - If it doesn't exist in the database, add it.
        - If it exists, compare the fields and update if necessary.
        """
        # Fetch all existing messages from the database for the given chat
        existing_messages = (
            session.query(Message)
            .filter(
                Message.chat_id == chat_id,
                Message.message_thread_id == self.message_thread_id,
            )
            .all()
        )
        # Create a dictionary mapping msg_id to Message objects for quick lookup
        existing_messages_dict = {
            message.msg_id: message for message in existing_messages
        }
        msg_list = await self.get_all_messages(client)
        # Fetch messages from the chat using Pyrogram
        for msg in msg_list:  # client.get_chat_history(chat_id):
            if msg.text:
                # Extract message context
                context = await extract_context(msg)
                # Check if the message exists in the database
                existing_message = existing_messages_dict.get(context.msg_id)
                if not existing_message:
                    # Message doesn't exist, so add it
                    store_message(session, context)
                    # Add the new message to the existing_messages_dict
                    existing_messages_dict[context.msg_id] = (
                        session.query(Message)
                        .filter(
                            Message.msg_id == context.msg_id,
                            Message.chat_id == context.chat_id,
                        )
                        .first()
                    )
                else:
                    # Message exists, compare fields and update if necessary
                    needs_update = False
                    fields_to_compare = [
                        "user_id",
                        "chat_type",
                        "chat_title",
                        "message_thread_id",
                        "message_thread_name",
                        "date",
                        "text",
                    ]
                    for field in fields_to_compare:
                        db_value = getattr(existing_message, field)
                        new_value = getattr(context, field)
                        if db_value != new_value:
                            setattr(existing_message, field, new_value)
                            needs_update = True
                    if needs_update:
                        session.add(existing_message)
                        session.commit()


# Misc


# Etc
