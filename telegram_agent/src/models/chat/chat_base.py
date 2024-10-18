# custom_message_processor.py
from telegram_agent.src.pipeline.filters import ChatFilter, MessageFilter
from telegram_agent.src.pipeline.actions import SendMessageAction, ForwardMessageAction
from telegram_agent.src.pipeline.pipeline_base import Pipeline, PipelineStep

from telegram_agent.src.models.models import MessageContext
from telegram_agent.src.telegram.database import get_session
from telegram_agent.src.telegram.utils import store_message

"""
async def custom_message_processor(client: Client, context: MessageContext):
    # Store the message
    with get_session() as session:
        store_message(session, context)

    # Define filters
    is_supergroup = ChatFilter(lambda ctx: ctx.chat_type == "supergroup")
    contains_urgent = MessageFilter(lambda ctx: "urgent" in (ctx.text or "").lower())

    # Define actions
    forward_to_specific_chat = ForwardMessageAction(
        from_chat_id=context.chat_id,
        to_chat_id=123456789,  # Target chat ID
        message_id=context.msg_id,
    )

    # Define pipeline steps
    pipeline_steps = [
        PipelineStep(
            filters=[is_supergroup, contains_urgent], actions=[forward_to_specific_chat]
        ),
    ]

    # Create and process the pipeline
    pipeline = Pipeline(steps=pipeline_steps)
    await pipeline.process(client, context)
"""


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


# Define a target for chats with specific attributes
def chat_attribute_filter(attribute: str, value):
    return ChatFilter(lambda ctx: getattr(ctx.chat, attribute, None) == value)


# Example usage:
# is_channel = chat_attribute_filter("type", "channel")
# is_specific_group = chat_attribute_filter("id", SPECIFIC_CHAT_ID)


## Filter messages from a specific user
# from_user = MessageFilter(lambda ctx: ctx.user_id == SPECIFIC_USER_ID)

## Filter messages sent within a specific time range
# within_time_range = MessageFilter(lambda ctx: START_TIME <= ctx.date <= END_TIME)


# Combine filters using logical operations
def and_filter(*filters):
    return MessageFilter(lambda ctx: all(f(ctx) for f in filters))


def or_filter(*filters):
    return MessageFilter(lambda ctx: any(f(ctx) for f in filters))


## Eample:
# combined_filter = and_filter(is_supergroup, contains_urgent, from_user)
