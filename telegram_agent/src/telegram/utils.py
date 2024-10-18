# utils.py

from typing import Optional

from pyrogram.enums import ChatType
from pyrogram.types import Message as PyroMessage
from sqlmodel import Session

from .models import Chat, Message, MessageContext, User


def extract_context(message: PyroMessage) -> MessageContext:
    """
    Extracts context from a Pyrogram message object.

    Args:
        message (PyroMessage): The message object received from Pyrogram.

    Returns:
        MessageContext: The extracted message context.
    """
    user = message.from_user
    chat = message.chat

    # Create User model from message data
    user_model = (
        User(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        if user
        else None
    )

    # Check if chat is not None
    if chat:
        # Handle Enum types safely
        chat_type_value = (
            (chat.type.value if isinstance(chat.type, ChatType) else str(chat.type))
            if chat.type
            else None
        )

        chat_model = Chat(
            id=chat.id,
            type=chat_type_value,
            title=chat.title,
            username=chat.username,
            first_name=chat.first_name,
            last_name=chat.last_name,
        )
        chat_id = chat.id
        chat_type = chat_type_value
        chat_title = chat.title
    else:
        # Handle case where chat is None
        chat_model = None
        chat_id = None
        chat_type = None
        chat_title = None

    message_thread_id = message.message_thread_id  # Extract forum topic ID

    return MessageContext(
        msg_id=message.id,
        user_id=user.id if user else None,
        chat_id=chat_id,
        chat_type=chat_type,
        chat_title=chat_title,
        message_thread_id=message_thread_id,
        date=message.date,
        text=message.text,
        user=user_model,
        chat=chat_model,
    )


def store_message(session: Session, context: MessageContext):
    """
    Stores a message and its context into the database.

    Args:
        session (Session): The database session.
        context (MessageContext): The message context to store.
    """
    # Upsert User
    if context.user:
        user = session.get(User, context.user.id)
        if not user:
            session.add(context.user)
        else:
            for field in context.user.__fields_set__:
                setattr(user, field, getattr(context.user, field))

    # Upsert Chat if available
    if context.chat and context.chat_id:
        chat = session.get(Chat, context.chat.id)
        if not chat:
            session.add(context.chat)
        else:
            for field in context.chat.__fields_set__:
                setattr(chat, field, getattr(context.chat, field))

    # Store Message
    message = Message(
        msg_id=context.msg_id,
        user_id=context.user_id,
        chat_id=context.chat_id,
        chat_type=context.chat_type,
        chat_title=context.chat_title,
        message_thread_id=context.message_thread_id,
        date=context.date,
        text=context.text,
    )
    session.add(message)
    session.commit()