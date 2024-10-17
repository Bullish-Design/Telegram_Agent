from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message as PyroMessage
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
    id: int = Field(primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id")
    chat_id: Optional[int] = Field(foreign_key="chat.id")
    date: datetime
    text: Optional[str]


# Message context model using Pydantic v2
class MessageContext(BaseModel):
    message_id: int
    user_id: Optional[int]
    chat_id: int
    date: datetime
    text: Optional[str]
    user: Optional[User]
    chat: Chat
