# utils.py

from typing import Optional

from pyrogram.enums import ChatType
from pyrogram.types import Message as PyroMessage
from sqlmodel import Session

from telegram_agent.src.models.models import Chat, Message, MessageContext, User

# Logging -------------------------------------------------------------------------------------------------------------
from telegram_agent.log.logger import get_logger

logger = get_logger("Bot_Utils")

# Functions -----------------------------------------------------------------------------------------------------------


def extract_context(message: PyroMessage) -> MessageContext:
    """
    Extracts context from a Pyrogram message object.

    Args:
        message (PyroMessage): The message object received from Pyrogram.

    Returns:
        MessageContext: The extracted message context.
    """
    logger.info(f"Extracting message context from:\n{message}\n\n")
    print(f"\nExtracting message context...")
    # print(f"    Service Type: {message.reply_to_message.reply_to_message.service}")
    # if message.outgoing:
    #    return
    # print(f"Extracting message context from: \n\n{message}\n")
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

    if message.reply_to_message is not None:
        logger.info(f"Reply to message exists")
        print(f"Message Thread ID: {message.message_thread_id}")
        message_thread_id = message.message_thread_id  # Extract forum topic ID
        # print(
        #    f"Message Thread Name: \n{message.reply_to_message.reply_to_message.forum_topic_created}\n"
        # )

        message_thread_name = (
            message.reply_to_message.forum_topic_created.title
            if message.reply_to_message.forum_topic_created
            else None
        )
    elif message.topic is not None:
        logger.info(f"Message.topic exists")
        message_thread_name = message.topic.title
        message_thread_id = message.topic.id
    else:
        logger.info(f"No message thread name/id")
        message_thread_name = None
        message_thread_id = None

    return MessageContext(
        msg_id=message.id,
        user_id=user.id if user else None,
        chat_id=chat_id,
        chat_type=chat_type,
        chat_title=chat_title,
        message_thread_id=message_thread_id,
        message_thread_name=message_thread_name,
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
        message_thread_name=context.message_thread_name,
        date=context.date,
        text=context.text,
    )
    session.add(message)
    session.commit()
