# custom_message_processor.py
from filters import ChatFilter, MessageFilter
from actions import ForwardMessageAction


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
