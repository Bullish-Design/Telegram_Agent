from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message as PyroMessage
from pyrogram.enums import ChatType
from sqlmodel import Field, SQLModel, Session, create_engine


# Database models using sqlmodel (Pydantic v2 compatible)
class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class Chat(SQLModel, table=True):
    id: int = Field(primary_key=True)
    type: str
    title: Optional[str]
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)  # Auto-incrementing ID
    # id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    msg_id: int  # Telegram message ID
    user_id: Optional[int] = Field(foreign_key="user.id")
    chat_id: int = Field(foreign_key="chat.id")
    # chat_type: str  # New field to store chat type
    # chat_title: Optional[str]  # New field to store chat title
    date: datetime
    text: Optional[str]


# Message context model using Pydantic v2
class MessageContext(BaseModel):
    msg_id: int
    user_id: Optional[int]
    chat_id: int
    # chat_type: str  # New field to store chat type
    # chat_title: Optional[str]  # New field to store chat title
    date: datetime
    text: Optional[str]
    user: Optional[User]
    chat: Chat
