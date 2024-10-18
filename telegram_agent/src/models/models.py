# models.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    Represents a Telegram user.

    Attributes:
        id (int): The unique identifier for the user.
        username (Optional[str]): The username of the user.
        first_name (Optional[str]): The first name of the user.
        last_name (Optional[str]): The last name of the user.
    """

    id: int = Field(primary_key=True)
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class Chat(SQLModel, table=True):
    """
    Represents a Telegram chat.

    Attributes:
        id (int): The unique identifier for the chat.
        type (str): The type of the chat (e.g., 'private', 'group').
        title (Optional[str]): The title of the chat.
        username (Optional[str]): The username of the chat.
        first_name (Optional[str]): The first name (if private chat).
        last_name (Optional[str]): The last name (if private chat).
    """

    id: int = Field(primary_key=True)
    type: str
    title: Optional[str]
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class Message(SQLModel, table=True):
    """
    Represents a Telegram message.

    Attributes:
        id (Optional[int]): The primary key (auto-incremented).
        msg_id (int): The message ID from Telegram.
        user_id (Optional[int]): The ID of the user who sent the message.
        chat_id (Optional[int]): The ID of the chat where the message was sent.
        chat_type (Optional[str]): The type of the chat.
        chat_title (Optional[str]): The title of the chat.
        message_thread_id (Optional[int]): The forum topic ID if applicable.
        date (datetime): The date the message was sent.
        text (Optional[str]): The text content of the message.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    msg_id: int  # Telegram message ID
    user_id: Optional[int] = Field(foreign_key="user.id")
    chat_id: Optional[int] = Field(default=None, foreign_key="chat.id")
    chat_type: Optional[str] = Field(default=None)
    chat_title: Optional[str] = Field(default=None)
    message_thread_id: Optional[int] = Field(default=None)
    date: datetime
    text: Optional[str]


class MessageContext(BaseModel):
    """
    Contains the context of a message for processing.

    Attributes:
        msg_id (int): The message ID from Telegram.
        user_id (Optional[int]): The ID of the user who sent the message.
        chat_id (Optional[int]): The ID of the chat where the message was sent.
        chat_type (Optional[str]): The type of the chat.
        chat_title (Optional[str]): The title of the chat.
        message_thread_id (Optional[int]): The forum topic ID if applicable.
        date (datetime): The date the message was sent.
        text (Optional[str]): The text content of the message.
        user (Optional[User]): The user object.
        chat (Optional[Chat]): The chat object.
    """

    msg_id: int
    user_id: Optional[int]
    chat_id: Optional[int]
    chat_type: Optional[str]
    chat_title: Optional[str]
    message_thread_id: Optional[int]
    date: datetime
    text: Optional[str]
    user: Optional[User]
    chat: Optional[Chat]
