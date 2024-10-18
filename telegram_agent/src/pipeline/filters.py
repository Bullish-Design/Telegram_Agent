# filters.py
from typing import Callable
from telegram_agent.src.models.models import MessageContext

"""
class BaseFilter:
    def __call__(self, context: MessageContext) -> bool:
        raise NotImplementedError


class MessageFilter(BaseFilter):
    def __init__(self, condition: Callable[[MessageContext], bool]):
        self.condition = condition

    def __call__(self, context: MessageContext) -> bool:
        return self.condition(context)


class ChatFilter(BaseFilter):
    def __init__(self, condition: Callable[[MessageContext], bool]):
        self.condition = condition

    def __call__(self, context: MessageContext) -> bool:
        return self.condition(context)


# Define a target for chats with specific attributes
def chat_attribute_filter(attribute: str, value):
    return ChatFilter(lambda ctx: getattr(ctx.chat, attribute, None) == value)


## Example usage:
# is_channel = chat_attribute_filter("type", "channel")
# is_specific_group = chat_attribute_filter("id", SPECIFIC_CHAT_ID)


# filters.py

from typing import Callable
from .models import MessageContext
"""


class BaseFilter:
    """
    Abstract base class for filters.
    """

    def __call__(self, context: MessageContext) -> bool:
        raise NotImplementedError


class MessageFilter(BaseFilter):
    """
    Filter based on message attributes.

    Args:
        condition (Callable[[MessageContext], bool]): The condition to evaluate.
    """

    def __init__(self, condition: Callable[[MessageContext], bool]):
        self.condition = condition

    def __call__(self, context: MessageContext) -> bool:
        """
        Evaluates the filter condition.

        Args:
            context (MessageContext): The message context.

        Returns:
            bool: True if the condition is met, False otherwise.
        """
        return self.condition(context)


class ChatFilter(BaseFilter):
    """
    Filter based on chat attributes.

    Args:
        condition (Callable[[MessageContext], bool]): The condition to evaluate.
    """

    def __init__(self, condition: Callable[[MessageContext], bool]):
        self.condition = condition

    def __call__(self, context: MessageContext) -> bool:
        """
        Evaluates the filter condition.

        Args:
            context (MessageContext): The message context.

        Returns:
            bool: True if the condition is met, False otherwise.
        """
        return self.condition(context)
