# pipeline.py
from typing import List
from telegram_bot.src.models import MessageContext
from pyrogram import Client
from filters import ChatFilter
from actions.py import SendMessageAction


class PipelineStep:
    def __init__(self, filters: List[BaseFilter], actions: List[BaseAction]):
        self.filters = filters
        self.actions = actions

    async def process(self, client: Client, context: MessageContext):
        # Evaluate all filters
        if all(f(context) for f in self.filters):
            # Execute all actions
            for action in self.actions:
                await action.execute(client, context)


class Pipeline:
    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    async def process(self, client: Client, context: MessageContext):
        for step in self.steps:
            await step.process(client, context)


# Example: Define a target for chats with a specific title
def chat_title_filter(title: str):
    return ChatFilter(lambda context: context.chat_title == title)


# Example: Define a target for chats of a specific type
def chat_type_filter(chat_type: str):
    return ChatFilter(lambda context: context.chat_type == chat_type)


# pipeline.py

from typing import List
from .models import MessageContext
from .filters import BaseFilter
from .actions import BaseAction
from pyrogram import Client


class PipelineStep:
    """
    Represents a step in the pipeline.

    Args:
        filters (List[BaseFilter]): The list of filters for this step.
        actions (List[BaseAction]): The list of actions for this step.
    """

    def __init__(self, filters: List[BaseFilter], actions: List[BaseAction]):
        self.filters = filters
        self.actions = actions

    async def process(self, client: Client, context: MessageContext):
        """
        Processes the context through this pipeline step.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        # Evaluate all filters
        if all(f(context) for f in self.filters):
            # Execute all actions
            for action in self.actions:
                await action.execute(client, context)


class Pipeline:
    """
    Represents the message processing pipeline.

    Args:
        steps (List[PipelineStep]): The list of pipeline steps.
    """

    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    async def process(self, client: Client, context: MessageContext):
        """
        Processes the context through the pipeline.

        Args:
            client (Client): The Pyrogram client.
            context (MessageContext): The message context.
        """
        for step in self.steps:
            await step.process(client, context)
