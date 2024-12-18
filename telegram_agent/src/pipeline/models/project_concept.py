from pyrogram.methods.chats import create_forum_topic
from telegram_agent.src.pipeline.models._imports import (
    ChatFilter,
    MessageFilter,
    API_ID,
    API_HASH,
    BOT_TOKEN,
    get_logger,
    Pipeline,
    PipelineStep,
    FilterGroup,
    SendMessageAction,
    ForwardMessageAction,
    # CreateChatAction,
    CreateForumTopicAction,
    CreateSupergroupAction,
    MessageProcessorDecorator,
    IDEAS_SUPERGROUP_CHAT_ID,
    IDEA_LIST_THREAD_ID,
    TELEGRAM_BOT_USERNAME,
    FunctionAction,
    wrap_input,
)

# Logger --------------------------------------------------------------------------------------------------------------
logger = get_logger("Project_Concept")

# Constants -----------------------------------------------------------------------------------------------------------


# Functions -----------------------------------------------------------------------------------------------------------


# Get all topic chats:
def get_topic_chats(chat_id: int, thread_id: int): ...


# Filters -------------------------------------------------------------------------------------------------------------
filters_list = [
    ChatFilter(
        name="is_private_chat",
        condition=lambda ctx: ctx.chat_type == "private",
    ),
    ChatFilter(
        name="is_supergroup",
        condition=lambda ctx: ctx.chat_type == "supergroup",
    ),
    ChatFilter(
        name="is_idea",
        condition=lambda ctx: ctx.message_thread_name == "Idea List",
    ),
    ChatFilter(
        name="is_concept",
        condition=lambda ctx: ctx.message_thread_name == "Concept",
    ),
    MessageFilter(
        name="contains_init_keyword",
        condition=lambda ctx: "initsupergroup" in (ctx.text or "").lower(),
    ),
    MessageFilter(
        name="contains_urgent",
        condition=lambda ctx: "urgent" in (ctx.text or "").lower(),
    ),
    ChatFilter(name="not_idea", condition=lambda ctx: ctx.chat.title != "Ideas"),
    ChatFilter(
        name="brainstorming",
        condition=lambda ctx: ctx.message_thread_name == "Brainstorming",
    ),
    # MessageFilter(
    #    name="from_specific_user", condition=lambda ctx: ctx.user_id == ADMIN_CHAT_ID
    # ),
]

filters = FilterGroup(filters_list)


# Actions -------------------------------------------------------------------------------------------------------------
send_greeting = SendMessageAction(
    chat_id=lambda ctx: ctx.chat_id,
    text="Hello! How can I assist you?",
    message_thread_id=lambda ctx: ctx.message_thread_id,
)


wrap_message = FunctionAction(
    function=lambda ctx: wrap_input(ctx.text),
)

wrap_message_pipeline = [
    PipelineStep(
        filters=[filters.is_concept],
        actions=[wrap_message],
    )
]

test_brainstorm_reply_pipeline = [
    PipelineStep(
        filters=[filters.brainstorming],
        actions=[send_greeting],
    )
]

# Classes -------------------------------------------------------------------------------------------------------------
wrap_message_decorator = MessageProcessorDecorator(pipeline_steps=wrap_message_pipeline)
brainstorming_decorator = MessageProcessorDecorator(
    pipeline_steps=test_brainstorm_reply_pipeline
)

# Misc ----------------------------------------------------------------------------------------------------------------
