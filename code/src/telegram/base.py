# Imports -------------------------------------------------------------------------------------------------------------
import os
from datetime import datetime
from typing import Optional
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message as PyroMessage

# Local Imports -------------------------------------------------------------------------------------------------------
from code.src.telegram.config import API_ID, API_HASH, TELEGRAM_KEY
from code.src.models.models_base import User, Chat, Message, MessageContext

# Constants -----------------------------------------------------------------------------------------------------------


# Functions -----------------------------------------------------------------------------------------------------------


# Classes -------------------------------------------------------------------------------------------------------------
# TelegramBot wrapper class
class TelegramBot:
    def __init__(self, api_id: int, api_hash: str, bot_token: Optional[str] = None):
        self.engine = create_engine("sqlite:///database.db", echo=False)
        SQLModel.metadata.create_all(self.engine)

        if bot_token:
            self.client = Client(
                "bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token
            )
        else:
            self.client = Client("userbot", api_id=api_id, api_hash=api_hash)

        self.client.add_handler(MessageHandler(self.message_handler, filters.all))

    def run(self):
        self.client.run()

    def message_handler(self, client: Client, message: PyroMessage):
        self.process_message(message)

    def process_message(self, message: PyroMessage):
        context = self.extract_context(message)
        self.store_message(context)
        # Example action: Echo the received message
        self.send_message(context, f"Echo: {context.text}")

    def extract_context(self, message: PyroMessage) -> MessageContext:
        user = message.from_user
        chat = message.chat

        # Create User and Chat models from message data
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

        chat_model = Chat(
            id=chat.id,
            type=chat.type,
            title=chat.title,
            username=chat.username,
            first_name=chat.first_name,
            last_name=chat.last_name,
        )

        return MessageContext(
            message_id=message.id,
            user_id=user.id if user else None,
            chat_id=chat.id,
            date=message.date,
            text=message.text,
            user=user_model,
            chat=chat_model,
        )

    def store_message(self, context: MessageContext):
        with Session(self.engine) as session:
            # Upsert User
            if context.user:
                user = session.get(User, context.user.id)
                if not user:
                    session.add(context.user)
                else:
                    for field in context.user.__fields__:
                        setattr(user, field, getattr(context.user, field))
                session.commit()

            # Upsert Chat
            chat = session.get(Chat, context.chat.id)
            if not chat:
                session.add(context.chat)
            else:
                for field in context.chat.__fields__:
                    setattr(chat, field, getattr(context.chat, field))
            session.commit()

            # Store Message
            message = Message(
                id=context.message_id,
                user_id=context.user_id,
                chat_id=context.chat_id,
                date=context.date,
                text=context.text,
            )
            session.add(message)
            session.commit()

    def send_message(self, context: MessageContext, text: str):
        self.client.send_message(chat_id=context.chat_id, text=text)


# Main ----------------------------------------------------------------------------------------------------------------


# Scripts =------------------------------------------------------------------------------------------------------------
def run_bot():
    api_id = YOUR_API_ID  # Replace with your API ID
    bot = TelegramBot(api_id, api_hash, bot_token)
    bot.run()


def init():
    app = Client("Test_Bot", api_id=API_ID, api_hash=API_HASH)
    app.run()


if __name__ == "__main__":
    init()

# Misc ----------------------------------------------------------------------------------------------------------------
