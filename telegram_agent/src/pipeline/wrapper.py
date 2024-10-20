# Imports -------------------------------------------------------------------------------------------------------------

from telegram_agent.src.models.models import User, Chat, Message, MessageContext
from telegram_agent.src.telegram.database import get_session, init_db
from telegram_agent.src.telegram.utils import extract_context, store_message
from telegram_agent.src.pipeline.pipeline_base import Pipeline, PipelineStep
from telegram_agent.src.pipeline.actions import (
    SendMessageAction,
    ForwardMessageAction,
    CreateSupergroupAction,
    CreateForumTopicAction,
    # CreateChatAction,
)

# Logging -------------------------------------------------------------------------------------------------------------
from telegram_agent.log.logger import get_logger

logger = get_logger("MessageProcessorWrapper")

# Classes -------------------------------------------------------------------------------------------------------------


class MessageProcessorDecorator:
    """
    Decorator class that wraps the TelegramBot class to inject a custom message processor.

    Args:
        pipeline_steps (List[PipelineStep]): A list of pipeline steps to process messages.
    """

    def __init__(self, pipeline_steps, bot_username=None):
        self.pipeline_steps = pipeline_steps
        self.bot_username = bot_username

    def __call__(self, bot_class):
        """
        Called when the decorator is applied to the TelegramBot class.

        Args:
            bot_class (class): The TelegramBot class to decorate.

        Returns:
            class: The wrapped TelegramBot class with the custom message processor.
        """

        # Define the message_processor function
        async def message_processor(client, context: MessageContext):
            """
            Custom message processor that stores messages and processes them through the pipeline.

            Args:
                client (Client): The Pyrogram client.
                context (MessageContext): The message context.
            """
            # Store the message
            logger.info(f"Processing message with context: \n\n{context}\n")
            logger.debug("Storing the message.")
            with get_session() as session:
                store_message(session, context)

            # Check if the message text is blank
            if not context.text or not context.text.strip():
                logger.info("Received a blank message. Skipping processing.")
                return

            # Update dynamic fields in actions
            logger.debug("Updating dynamic fields in actions.")
            for step in self.pipeline_steps:
                for action in step.actions:
                    if isinstance(action, SendMessageAction):
                        logger.info(f"Processing SendMessageAction: {action}")
                        # Set dynamic chat_id and message_thread_id
                        action.chat_id = context.chat_id
                        action.message_thread_id = context.message_thread_id
                        if action.text is None:
                            action.text = (
                                f"Message from {context.user_id}: {context.text}"
                            )
                    elif isinstance(action, ForwardMessageAction):
                        logger.info(f"Processing ForwardMessageAction: {action}")
                        action.from_chat_id = context.chat_id
                        action.message_id = context.msg_id

                    elif isinstance(action, CreateSupergroupAction):
                        logger.info(
                            f"Processing CreateSupergroupAction: {action} from context:\n\n{context}\n"
                        )
                        # Set dynamic title if needed
                        # if action.title is None:
                        #    action.title = context.text or "New Supergroup"
                        ## Ensure bot username is set
                        # if self.bot_username is None:
                        #    raise ValueError(
                        #        "Bot username must be provided for CreateSupergroupAction."
                        #    )
                        # action.bot_username = self.bot_username
                    elif isinstance(action, CreateForumTopicAction):
                        logger.info(f"Processing CreateForumTopicAction: {action}")
                        # Set dynamic title if needed
                        # if action.title is None:
                        #    action.title = context.text or "New Forum Topic"

            # Create and process the pipeline
            logger.debug("Processing the pipeline.")
            pipeline = Pipeline(steps=self.pipeline_steps)
            logger.info(f"Processing pipeline with pipeline: {pipeline}")
            await pipeline.process(client, context)

        # Define a new class that wraps bot_class
        class WrappedTelegramBot(bot_class):
            def __init__(bot_self, *args, **kwargs):
                """
                Initializes the wrapped TelegramBot and injects the custom message processor.

                Args:
                    *args: Positional arguments.
                    **kwargs: Keyword arguments.
                """
                # Add message_processor to kwargs if not already provided
                if (
                    "message_processor" not in kwargs
                    or kwargs["message_processor"] is None
                ):
                    kwargs["message_processor"] = message_processor
                logger.debug(
                    f"Initializing wrapped TelegramBot with kwargs: {kwargs}\n\n{kwargs['message_processor']}\n"
                )
                # Call the original __init__
                super(WrappedTelegramBot, bot_self).__init__(*args, **kwargs)

        return WrappedTelegramBot
