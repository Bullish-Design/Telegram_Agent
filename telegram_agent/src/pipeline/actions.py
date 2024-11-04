# actions.py
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from telegram_agent.src.models.models import MessageContext
from pyrogram import Client
from pyrogram.errors import FloodWait, PeerFlood
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.raw import functions, types
from time import sleep
from pyrogram import raw
from pyrogram import errors


# Local imports -------------------------------------------------------------------------------------------------------
from telegram_agent.src.telegram.config import TELEGRAM_BOT_ID, TELEGRAM_BOT_USERNAME

# Logging -------------------------------------------------------------------------------------------------------------
from telegram_agent.log.logger import get_logger

logger = get_logger("ActionsLog")

# Constants -----------------------------------------------------------------------------------------------------------


# Functions ------------------------------------------------------------------------------------------------------------
async def toggle_forum(client: Client, chat_id: int, enabled: bool = False):
    try:
        r = await client.invoke(
            raw.functions.channels.ToggleForum(
                channel=await client.resolve_peer(chat_id), enabled=enabled
            )
        )

        return bool(r)
    except errors.RPCError:
        return False


def wrap_input(input_str: str, wrap_char: str = "`") -> str:
    """
    Wrap a string with a specified character.
    Args:
        input_str (str): The input string.
        wrap_char (str): The character to wrap the string with.
    Returns:
        str: The wrapped string.
    """
    return f"{wrap_char}{input_str}{wrap_char}"


# Create supergroup topic
async def create_supergroup_topic(client: Client, group_id: int, topic_title: str):
    logger.info(f"Creating forum topic: {topic_title}")
    forum_topic = await client.create_forum_topic(chat_id=group_id, title=topic_title)
    logger.info(f"Created forum topic: {forum_topic}")
    return forum_topic


# Post Message
async def post_message(
    client: Client, msg_text: str, chat_id: int, topic_id: Optional[int] = None
):
    if topic_id:
        await client.send_message(
            chat_id=chat_id,
            message_thread_id=topic_id,
            text=msg_text,
        )
    else:
        await client.send_message(
            chat_id=chat_id,
            text=msg_text,
        )


# class TopicInit(BaseModel):
#    name: str


test_dict = {
    "Goal": "[Goal]",
    "Brainstorming": "[Prompt] Please help the user with brainstorming for the project goal.",
    "References": "[Prompt] The following posts could be useful for this project. Please analyze the contents of the post and describe if/how it would be useful.",
    "Overview": "[Prompt] The following overview posts serve as a summary and 'How to' guide the user will follow to accomplish the project goal.",
}


# Initialize a supergroup with topics and topic prompts/outcomes
async def init_supergroup_topics(client: Client, group_id: int, group_init_dict: Dict):
    for k, v in reversed(list(group_init_dict.items())):
        topic = await create_supergroup_topic(client, group_id, k)
        await post_message(client, v, group_id, topic.id)


# Create a Supergroup with a "Config" topic, post a message with the supergroup type
async def create_supergroup(client: Client, title: str, group_type: str):
    try:
        # Create a new supergroup
        result = await client.create_supergroup(
            title=title,
            description="Created by bot",
        )
        sleep(0.5)
        logger.info(f"Created supergroup: {type(result)} -  {result}")
        chat_id = result.id

        # Enable topics in the supergroup
        try:
            await toggle_forum(client, chat_id, True)
            # await client.toggle_forum_topics(chat_id=chat_id, enabled=True)
            logger.info(f"Enabled topics in supergroup: {chat_id}")
        except Exception as e:
            logger.error(f"Failed to enable topics: {e}")
        # result.is_forum = True
        logger.info(f"Supergroup deets. Is forum set to true?:\n{result}")
        sleep(0.5)

        # Set chat permissions
        try:
            permissions_result = await client.set_chat_permissions(
                chat_id,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_manage_topics=True,
                ),
            )
            logger.info(f"Set chat permissions: {permissions_result}")
        except Exception as e:
            logger.error(f"Failed to update permissions: {e}")
        # Generate an invite link
        invite_link = await client.create_chat_invite_link(chat_id)

        # Add the bot to the chat
        bot_username = TELEGRAM_BOT_USERNAME
        if bot_username:
            logger.info(f"Adding bot to the chat: {bot_username}")
            try:
                mem_result = await client.add_chat_members(
                    chat_id, user_ids=bot_username
                )
                logger.info(f"Result of adding bot to chat: {mem_result}")
                await asyncio.sleep(2)
                promo_res = await client.promote_chat_member(
                    chat_id,
                    user_id=bot_username,
                    privileges=ChatPrivileges(
                        can_delete_messages=True,
                        can_restrict_members=True,
                        can_manage_topics=True,
                        can_post_messages=True,
                        can_edit_messages=True,
                        can_pin_messages=True,
                        can_edit_stories=True,
                    ),
                )
                logger.info(f"Result of promoting bot: {promo_res}")
            except Exception as e:
                logger.error(f"Failed to add bot to the chat: {e}")
        else:
            logger.warning(
                "Bot username not provided, skipping adding bot to the chat."
            )

        sleep(0.5)
        # Create a new forum topic (thread)
        try:
            # forum_topic = await client.create_forum_topic(chat_id, "Config")
            # logger.info(f"Easy forum topic result? \n{forum_topic}")
            forum_topic = await create_supergroup_topic(
                client=client, group_id=chat_id, topic_title="Config"
            )
            config_text = f"#InitSupergroup | {group_type}"
            # Send a welcome message in the new topic
            await client.send_message(
                chat_id=chat_id,
                text=config_text,
                message_thread_id=forum_topic.id,
            )
        except Exception as e:
            logger.error(f"Failed to create forum topic: {e}")

        sleep(0.5)
        ## Reply to the user's message with the invite link
        # try:
        #    await message.reply_text(
        #        f"A new supergroup '{title}' has been created! Join here: {invite_link.invite_link}",
        #        quote=True,
        #    )
        # except Exception as e:
        #    logger.error(f"Failed to send invite link to the user: {e}")

    except Exception as e:
        logger.error(f"Error creating supergroup: {e}")
        # await message.reply_text("An error occurred while creating the supergroup.")


# Classes -------------------------------------------------------------------------------------------------------------


class BaseAction:
    """
    Abstract base class for actions.
    """

    async def execute(self, client: Client, context: MessageContext):
        raise NotImplementedError


class FunctionAction(BaseAction):
    """
    Action that executes a provided function with message text and chat ID,
    then replies to the message with the function's output.

    Args:
        func (Callable[[Optional[str], int], Any]):
            A coroutine function that takes message text and chat ID as arguments and returns a response string.
    """

    def __init__(self, function: Callable[[Optional[str], int], Any]):
        if not callable(function):
            raise ValueError("func must be a callable")
        self.function = function

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the provided function with the message text and chat ID,
        then sends the result as a reply to the original message.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        message_text = context.text
        chat_id = context.chat_id
        msg_id = context.msg_id

        logger.info(
            f"Executing function with chat_id={chat_id} and message_text='{message_text}'"
        )

        try:
            # Check if the function is a coroutine
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(message_text, chat_id)
            else:
                result = self.func(message_text, chat_id)

            if not isinstance(result, str):
                logger.warning(
                    "Function did not return a string. Converting to string."
                )
                result = str(result)

            logger.info(f"Function executed successfully. Sending reply.")
            await client.send_message(
                chat_id=chat_id,
                text=result,
                reply_to_message_id=msg_id,
                disable_web_page_preview=True,  # Optional: Customize as needed
            )
        except Exception as e:
            logger.error(f"Error executing FunctionAction: {e}")
            await client.send_message(
                chat_id=chat_id,
                text="An error occurred while processing your request.",
                reply_to_message_id=msg_id,
            )


class SendMessageAction(BaseAction):
    """
    Action to send a message.

    Args:
        chat_id (int): The ID of the chat to send the message to.
        text (str): The text of the message to send.
        kwargs (Dict[str, Any]): Additional keyword arguments for send_message.
    """

    def __init__(
        self, chat_id: int, text: str, message_thread_id: Optional[int], **kwargs
    ):
        self.chat_id = chat_id
        self.text = text
        self.message_thread_id = message_thread_id
        self.kwargs = kwargs

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        logger.info(
            f"Sending message to chatID: {self.chat_id} | {self.text} | {self.message_thread_id}"
        )
        if self.message_thread_id:
            await client.send_message(
                chat_id=self.chat_id,
                text=self.text,
                message_thread_id=self.message_thread_id,
                **self.kwargs,
            )
        else:
            await client.send_message(
                chat_id=self.chat_id,
                text=self.text,
                **self.kwargs,
            )


class ForwardMessageAction(BaseAction):
    """
    Action to forward a message.

    Args:
        from_chat_id (int): The ID of the source chat.
        to_chat_id (int): The ID of the destination chat.
        message_id (int): The ID of the message to forward.
    """

    def __init__(self, from_chat_id: int, to_chat_id: int, message_id: int):
        self.from_chat_id = from_chat_id
        self.to_chat_id = to_chat_id
        self.message_id = message_id

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        await client.forward_messages(
            chat_id=self.to_chat_id,
            from_chat_id=self.from_chat_id,
            message_ids=self.message_id,
        )


"""
class CreateChatAction(BaseAction):
    '''
    Action to create a new supergroup, set privacy level, and generate an invite link.

    Args:
        title (str): The title of the new chat.
        privacy (str): The privacy level ('public' or 'private').
    '''

    def __init__(self, title: str, privacy: str = "private"):
        self.title = title
        self.privacy = privacy

    async def execute(self, client: Client, context: MessageContext):
        '''
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        '''
        # Create a new supergroup
        result = await client.create_supergroup(
            title=self.title,
            description="Created by bot",
            # megagroup=True,
        )
        logger.info(f"Created channel: {result}")
        # Extract the chat ID
        # chat = result.chat
        chat_id = result.id
        # chat_obj = client.resolve_peer(chat_id)
        # logger.info(f"Chat Object: {chat_obj}")
        # Enable topics in the supergroup
        try:
            # toggled_result = functions.channels.ToggleForum(
            #    channel=chat_obj, enabled=True
            # )
            await client.toggle_forum_topics(chat_id=chat_id, enabled=True)
        except Exception as e:
            print(f"Failed to enable topics: {e}")
        # logger.info(f"Enabled topics in channel: {toggled_result}")

        # Generate an invite link
        invite_link = await client.create_chat_invite_link(chat_id)
        # Add the bot
        logger.info(f"Adding bot to the chat: {TELEGRAM_BOT_USERNAME}")
        try:
            await client.add_chat_members(chat_id, user_ids=TELEGRAM_BOT_USERNAME)
        except Exception as e:
            print(f"Failed to add bot to the chat: {e}")

        # Create a new forum topic (thread)
        try:
            forum_topic = await client.create_forum_topic(
                chat_id=chat_id, title="Config"
            )
            logger.info(f"Created forum topic: {forum_topic}")
            # Send a welcome message in the new topic
            await client.send_message(
                chat_id=chat_id,
                text=f"#Project_Template:{context.chat_title}",
                message_thread_id=forum_topic.id,
            )
        except Exception as e:
            print(f"Failed to create forum topic: {e}")

        # Reply to the user's message with the invite link
        try:
            await client.send_message(
                chat_id=context.chat_id,
                text=f"A new supergroup '{self.title}' has been created! Join here: {invite_link.invite_link}",
                reply_to_message_id=context.msg_id,
                message_thread_id=context.message_thread_id,  # Reply in the same thread if applicable
            )
        except Exception as e:
            print(f"Failed to send invite link to the user: {e}")
"""


class CreateSupergroupAction(BaseAction):
    """
    Action to create a new supergroup, set privacy level, and generate an invite link.

    Args:
        title (str): The title of the new chat.
        privacy (str): The privacy level ('public' or 'private').
        bot_username (str): The username of the bot to add to the new supergroup.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        privacy: Optional[str] = "private",
        bot_username: Optional[str] = None,
    ):
        self.title = title
        self.privacy = privacy
        self.bot_username = bot_username

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        logger.info(f"Creating new Supergroup from context: {context}")
        if self.title is None:
            self.title = context.text or "New Supergroup"
        print(f"\nCreating new Supergroup: {self.title}\n")
        # Create a new supergroup
        result = await client.create_supergroup(
            title=self.title,
            description="Created by bot",
        )
        sleep(0.5)
        logger.info(f"Created supergroup: {result}")
        chat_id = result.id

        # Enable topics in the supergroup
        try:
            await client.toggle_forum_topics(chat_id=chat_id, enabled=True)
            logger.info(f"Enabled topics in supergroup: {chat_id}")
        except Exception as e:
            logger.error(f"Failed to enable topics: {e}")

        sleep(0.5)

        permissions_result = await client.set_chat_permissions(
            chat_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_manage_topics=True,
            ),
        )
        logger.info(f"New Permissions: {permissions_result}")
        # Generate an invite link
        invite_link = await client.create_chat_invite_link(chat_id)

        # Add the bot to the chat
        if self.bot_username:
            logger.info(f"Adding bot to the chat: {self.bot_username}")
            try:
                mem_result = await client.add_chat_members(
                    chat_id, user_ids=self.bot_username
                )
                logger.info(f"Result of adding a bot to chat => {mem_result}")
                await asyncio.sleep(2)
                promo_res = await client.promote_chat_member(
                    chat_id,
                    user_id=self.bot_username,
                    privileges=ChatPrivileges(
                        can_delete_messages=True,
                        can_restrict_members=True,
                        # can_send_other_messages=True,
                        # can_add_web_page_previews=True,
                        can_manage_topics=True,
                        can_post_messages=True,
                        can_edit_messages=True,
                        can_pin_messages=True,
                        can_edit_stories=True,
                    ),
                )
                logger.info(f"Result of bot promo => {promo_res}")
            except Exception as e:
                logger.error(f"Failed to add bot to the chat: {e}")
        else:
            logger.warning(
                "Bot username not provided, skipping adding bot to the chat."
            )
        sleep(0.5)
        # Create a new forum topic (thread)
        try:
            forum_topic = await client.create_forum_topic(
                chat_id=chat_id, title="Config"
            )
            logger.info(f"Created forum topic: {forum_topic}")
            # Send a welcome message in the new topic
            await client.send_message(
                chat_id=chat_id,
                text=f"#InitSupergroup",
                message_thread_id=forum_topic.id,
            )
        except Exception as e:
            logger.error(f"Failed to create forum topic: {e}")
        sleep(0.5)
        # Reply to the user's message with the invite link
        try:
            await client.send_message(
                chat_id=context.chat_id,
                text=f"A new supergroup '{self.title}' has been created! Join here: {invite_link.invite_link}",
                reply_to_message_id=context.msg_id,
                message_thread_id=context.message_thread_id,
            )
        except Exception as e:
            logger.error(f"Failed to send invite link to the user: {e}")


class CreateForumTopicAction(BaseAction):
    """
    Action to create a new supergroup, set privacy level, and generate an invite link.

    Args:
        title (str): The title of the new Forum Topic.
        privacy (str): The privacy level ('public' or 'private').
        bot_username (str): The username of the bot to add to the new supergroup.
    """

    def __init__(self, title: str, group_id: Optional[str] = None):
        self.title = title
        self.group_id = group_id
        # self.bot_username = bot_username

    async def execute(self, client: Client, context: MessageContext):
        """
        Executes the action.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        logger.info(f"Creating new Forum Topic in context: {context}")
        if self.group_id:
            chat_id = self.group_id
        else:
            chat_id = context.chat_id
        print(
            f"\nCreating new Forum Topic: {self.title}"
        )  # " with chatID: {chat_id}\n")
        # member = await client.get_chat_member(chat_id, "me")
        # logger.info(member)
        # chat_rights =
        # Create a new forum topic (thread)
        sleep(1)
        try:
            forum_topic = await client.create_forum_topic(
                chat_id=chat_id, title=self.title
            )
            logger.info(f"Created forum topic: {forum_topic}")
            # Send a welcome message in the new topic
            # await client.send_message(
            #    chat_id=chat_id,
            #    text=f"#InitSupergroup",
            #    message_thread_id=forum_topic.id,
            # )
        except Exception as e:
            logger.error(f"Failed to create forum topic: {e}")


class ReturnTopicChats(BaseAction):
    pass
