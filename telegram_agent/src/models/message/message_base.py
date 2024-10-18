# custom_message_processor.py
from telegram_bot.database import get_session
from telegram_bot.utils import store_message
from telegram_bot.models import MessageContext
from pyrogram import Client

from pipeline import Pipeline, PipelineStep
from filters import MessageFilter, ChatFilter
from actions import SendMessageAction


async def custom_message_processor(client: Client, context: MessageContext):
    # Store the message
    with get_session() as session:
        store_message(session, context)

    # Define filters
    is_private_chat = ChatFilter(lambda ctx: ctx.chat_type == "private")
    is_supergroup = ChatFilter(lambda ctx: ctx.chat_type == "supergroup")
    contains_keyword = MessageFilter(lambda ctx: "hello" in (ctx.text or "").lower())

    # Define actions
    send_greeting = SendMessageAction(
        chat_id=context.chat_id,
        text="Hello! How can I assist you?",
        message_thread_id=context.message_thread_id,
    )
    notify_admin = SendMessageAction(
        chat_id=ADMIN_CHAT_ID, text=f"Message from {context.user_id}: {context.text}"
    )

    # Define pipeline steps
    pipeline_steps = [
        PipelineStep(
            filters=[is_private_chat, contains_keyword], actions=[send_greeting]
        ),
        PipelineStep(filters=[is_supergroup], actions=[notify_admin]),
    ]

    # Create and process the pipeline
    pipeline = Pipeline(steps=pipeline_steps)
    await pipeline.process(client, context)

    # custom_message_processor.py


from telegram_bot.database import get_session
from telegram_bot.utils import store_message
from telegram_bot.models import MessageContext
from pyrogram import Client

from telegram_bot.pipeline import Pipeline, PipelineStep
from telegram_bot.filters import MessageFilter, ChatFilter
from telegram_bot.actions import SendMessageAction, ForwardMessageAction

# Define constants (replace with actual values)
ADMIN_CHAT_ID = 123456789  # Replace with your admin chat ID
SPECIFIC_CHAT_ID = 987654321  # Replace with the target chat ID


async def custom_message_processor(client: Client, context: MessageContext):
    """
    Custom message processor that filters messages and performs actions.

    Args:
        client (Client): The Pyrogram client.
        context (MessageContext): The message context.
    """
    # Store the message
    with get_session() as session:
        store_message(session, context)

    # Define filters
    is_private_chat = ChatFilter(lambda ctx: ctx.chat_type == "private")
    is_supergroup = ChatFilter(lambda ctx: ctx.chat_type == "supergroup")
    contains_keyword = MessageFilter(lambda ctx: "hello" in (ctx.text or "").lower())
    contains_urgent = MessageFilter(lambda ctx: "urgent" in (ctx.text or "").lower())
    from_specific_user = MessageFilter(lambda ctx: ctx.user_id == ADMIN_CHAT_ID)

    # Define actions
    send_greeting = SendMessageAction(
        chat_id=context.chat_id,
        text="Hello! How can I assist you?",
        message_thread_id=context.message_thread_id,
    )
    notify_admin = SendMessageAction(
        chat_id=ADMIN_CHAT_ID, text=f"Message from {context.user_id}: {context.text}"
    )
    forward_to_specific_chat = ForwardMessageAction(
        from_chat_id=context.chat_id,
        to_chat_id=SPECIFIC_CHAT_ID,
        message_id=context.msg_id,
    )

    # Define pipeline steps
    pipeline_steps = [
        # Step 1: Send greeting in private chats containing 'hello'
        PipelineStep(
            filters=[is_private_chat, contains_keyword], actions=[send_greeting]
        ),
        # Step 2: Notify admin for messages in supergroups
        PipelineStep(filters=[is_supergroup], actions=[notify_admin]),
        # Step 3: Forward urgent messages to a specific chat
        PipelineStep(filters=[contains_urgent], actions=[forward_to_specific_chat]),
    ]

    # Create and process the pipeline
    pipeline = Pipeline(steps=pipeline_steps)
    await pipeline.process(client, context)
