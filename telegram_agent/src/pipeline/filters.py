# filters.py
from typing import Callable, List
from telegram_agent.src.models.models import MessageContext

from telegram_agent.log.logger import get_logger

logger = get_logger("Filters")

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

    Args:
        name (str): The name of the filter.
    """

    def __init__(self, name: str):
        self.name = name

    def __call__(self, context: MessageContext) -> bool:
        raise NotImplementedError


class MessageFilter(BaseFilter):
    """
    Filter based on message attributes.

    Args:
        name (str): The name of the filter.
        condition (Callable[[MessageContext], bool]): The condition to evaluate.
    """

    def __init__(self, name: str, condition: Callable[[MessageContext], bool]):
        self.name = name
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
        name (str): The name of the filter.
        condition (Callable[[MessageContext], bool]): The condition to evaluate.
    """

    def __init__(self, name: str, condition: Callable[[MessageContext], bool]):
        self.name = name
        self.condition = condition
        logger.info(f"Initialized ChatFilter: {self.name}")
        logger.info(f"            Condition: {self.condition}")

    def __call__(self, context: MessageContext) -> bool:
        """
        Evaluates the filter condition.

        Args:
            context (MessageContext): The message context.

        Returns:
            bool: True if the condition is met, False otherwise.
        """
        logger.info(f"ChatFilter: {self.name}")
        logger.info(f"ChatFilter: {self.condition}")
        return self.condition(context)


class FilterGroup:
    """
    A container class for filters, allowing access via dot notation.

    Args:
        filters (List[BaseFilter]): A list of filter instances.
    """

    def __init__(self, filters: List[BaseFilter]):
        self.filters = filters
        for f in filters:
            if hasattr(f, "name") and f.name:
                if hasattr(self, f.name):
                    raise ValueError(
                        f"A filter with the name '{f.name}' already exists."
                    )
                setattr(self, f.name, f)
            else:
                raise ValueError("Each filter must have a 'name' attribute.")
