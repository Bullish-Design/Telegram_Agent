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


async def extract_context(message: PyroMessage) -> MessageContext:
    """
    Extracts context from a Pyrogram message object.

    Args:
        message (PyroMessage): The message object received from Pyrogram.

    Returns:
        MessageContext: The extracted message context.
    """
    logger.info(f"Extracting message context from:\n{message}\n\n")
    # print(f"\nExtracting message context...")
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


def build_message_context_from_db(session: Session, message: Message) -> MessageContext:
    """
    Builds a MessageContext instance from a Message instance by fetching related User and Chat objects.

    Args:
        session (Session): The database session.
        message (Message): The message instance from the database.

    Returns:
        MessageContext: The constructed MessageContext instance.
    """
    # Fetch the User object if user_id exists
    user = session.get(User, message.user_id) if message.user_id else None

    # Fetch the Chat object if chat_id exists
    chat = session.get(Chat, message.chat_id) if message.chat_id else None

    # Construct the MessageContext
    context = MessageContext(
        msg_id=message.msg_id,
        user_id=message.user_id,
        chat_id=message.chat_id,
        chat_type=message.chat_type,
        chat_title=message.chat_title,
        message_thread_id=message.message_thread_id,
        message_thread_name=message.message_thread_name,
        date=message.date,
        text=message.text,
        user=user,
        chat=chat,
    )

    return context


def store_message(session: Session, context: MessageContext):
    """
    Stores or updates a message and its context into the database.
    """
    # Upsert User
    if context.user:
        user = session.get(User, context.user.id)
        if not user:
            session.add(context.user)
        else:
            for field in context.user.__fields_set__:
                setattr(user, field, getattr(context.user, field))

    # Upsert Chat
    if context.chat and context.chat_id:
        chat = session.get(Chat, context.chat.id)
        if not chat:
            session.add(context.chat)
        else:
            for field in context.chat.__fields_set__:
                setattr(chat, field, getattr(context.chat, field))

    # Upsert Message
    existing_message = (
        session.query(Message)
        .filter(Message.msg_id == context.msg_id, Message.chat_id == context.chat_id)
        .first()
    )

    if not existing_message:
        # Message doesn't exist, so add it
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
            deleted=context.deleted,
        )
        session.add(message)
    else:
        # Message exists, update fields if necessary
        needs_update = False
        fields_to_compare = [
            "user_id",
            "chat_type",
            "chat_title",
            "message_thread_id",
            "message_thread_name",
            "date",
            "text",
            "deleted",
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
