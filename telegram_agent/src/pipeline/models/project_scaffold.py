# Imports -------------------------------------------------------------------------------------------------------------
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
)

# Logger --------------------------------------------------------------------------------------------------------------
logger = get_logger("Project_Scaffold")

# Constants -----------------------------------------------------------------------------------------------------------

# Scaffold Topics:
forum_topics = [
    "References",
    "Issues",
    "MVP",
    "Features",
    "Requirements",
    "Structure",
    "Overview",
    "Goal",
    "Concept",
    "Brainstorming",
]

# Functions -----------------------------------------------------------------------------------------------------------


# A function to generate a new forum topic action:
def generate_new_topic_action(title: str):
    return CreateForumTopicAction(title=title)


# A function to generate a collection of new forum topic actions:
def generate_topics_scaffold(titles: list[str]):
    return [generate_new_topic_action(title) for title in titles]


# A function to create a new supergroup:
def create_supergroup(title: str):
    return CreateSupergroupAction(title=title)


# Filters -------------------------------------------------------------------------------------------------------------
filters_list = [
    ChatFilter(
        name="is_private_chat", condition=lambda ctx: ctx.chat_type == "private"
    ),
    ChatFilter(
        name="is_supergroup", condition=lambda ctx: ctx.chat_type == "supergroup"
    ),
    ChatFilter(
        name="is_idea", condition=lambda ctx: ctx.message_thread_name == "Idea List"
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
    # MessageFilter(
    #    name="from_specific_user", condition=lambda ctx: ctx.user_id == ADMIN_CHAT_ID
    # ),
]

filters = FilterGroup(filters_list)

# Actions -------------------------------------------------------------------------------------------------------------
# Define actions
send_greeting = SendMessageAction(
    chat_id=None,
    text="Hello! How can I assist you?",
    message_thread_id=None,
)
# notify_admin = SendMessageAction(
#    chat_id=ADMIN_CHAT_ID,
#    text=None,
# )
# forward_to_specific_chat = ForwardMessageAction(
#    from_chat_id=None,
#    to_chat_id=SPECIFIC_CHAT_ID,
#    message_id=None,
# )
# create_chat_action = CreateChatAction(
#    title=None,  # Will be set dynamically
#    privacy="private",
# )
create_new_topic = CreateForumTopicAction(title="Brainstorming")
create_idea_supergroup = CreateSupergroupAction(bot_username=TELEGRAM_BOT_USERNAME)
scaffold_actions_list = generate_topics_scaffold(forum_topics)

# Pipeline Steps ------------------------------------------------------------------------------------------------------
# Define pipeline steps
pipeline_steps = [
    PipelineStep(
        filters=[filters.is_private_chat, filters.contains_init_keyword],
        actions=[send_greeting],
    ),
]

project_scaffold_pipeline = [
    PipelineStep(
        filters=[filters.contains_init_keyword],
        actions=scaffold_actions_list,
    )
]

idea_init_pipeline = [
    PipelineStep(
        filters=[filters.is_idea],
        actions=[create_idea_supergroup],
    )
]


# Classes -------------------------------------------------------------------------------------------------------------

# @MessageProcessorDecorator(pipeline_steps=project_scaffold_pipeline)
# class TelegramProjectScaffoldBot(TelegramBot):
#    pass
scaffold_decorator = MessageProcessorDecorator(pipeline_steps=project_scaffold_pipeline)

idea_init_decorator = MessageProcessorDecorator(pipeline_steps=idea_init_pipeline)

# Misc ----------------------------------------------------------------------------------------------------------------
