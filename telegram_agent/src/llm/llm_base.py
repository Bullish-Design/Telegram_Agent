# Imports -------------------------------------------------------------------------------------------------------------
from pydantic import BaseModel
from typing import Any, Optional, List, Dict
from openai import OpenAI
from mirascope.core import openai, prompt_template
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import Message as PyroMessage
from sqlmodel import Session

from time import sleep

# Library Imports -----------------------------------------------------------------------------------------------------
from telegram_agent.src.config import openai_api_key
from telegram_agent.src.telegram.utils import extract_context, store_message
from telegram_agent.log.logger import get_logger
from telegram_agent.src.models.models import User, Chat, Message, MessageContext

# LLM Client ----------------------------------------------------------------------------------------------------------

local_client = OpenAI(
    api_key="ollama",
    # base_url=local_model_url,
)


logger = get_logger("TelegramLLMBase")


# Constants -----------------------------------------------------------------------------------------------------------

# Base system prompt:


# Functions -----------------------------------------------------------------------------------------------------------


# Topic Chat Call:
@openai.call("gpt-4o-mini")
@prompt_template("""{combined_prompt}

Here's what's been discussed thus far: {context}

USER:
Please use the context of the conversation thus far to help meet the system prompt goals, in accordance to the user's latest message: 

{message}

**REMEMBER!! BE EXTREMELY CONCISE UNLESS ASKED FOR A SUMMARY!!! USE BULLET POINTS IN YOUR RESPONSE - YOU ARE NOT HERE TO EXPLAIN HOW TO DO THINGS. YOUR GOAL IS TO THINK OF THE CONSEQUENCES OF IMPLEMENTING WHAT THE USER STATES IN THEIR MESSAGE, AND HELP ENSURE THE USER DOESN'T MISS ANY IMPORTANT CONSEQUENCES IN THEIR PROJECT PLANNING**

**DO NOT** concern yourself or the user about normal aspects of designing a project (performance, documentation, maintenance, testing, etc.)
**ONLY** focus on high level system/structural consequences, assuming the user implements what they talk about in their message. 
**RESPOND WITH 3-5 BULLET POINTS ONLY**
""")
def chat_response(combined_prompt: str, context: str, message: str) -> str: ...


# Classes -------------------------------------------------------------------------------------------------------------


# LLM Chatbot Base:
class TelegramLLMBase(BaseModel):
    user_tg_client: Client
    bot_tg_client: Client
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    chat_id: Optional[int] = None
    topic_id: Optional[int] = None
    topic_messages: Optional[List[Any]] = []
    # TODO: Store messages as an attribute to reduce api calls. Just append each message to the list, and have a "get all" function for refreshes

    class Config:
        arbitrary_types_allowed = True

    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the LLM."""
        self.system_prompt = prompt

    def set_user_prompt(self, prompt: str):
        """Set the user prompt for the LLM."""
        self.user_prompt = prompt

    async def get_combined_topic_prompt(self):
        goal_message = await self.get_message_match("[Goal]")
        # print(f"\nGoal: \n\n{goal_message}\n\n")
        sleep(0.25)
        goal_text = goal_message.text
        topic_prompt_message = await self.get_message_match("[Prompt]", self.topic_id)
        # print(f"\nPrompt: \n\n{topic_prompt_message}\n\n")
        sleep(0.25)
        topic_prompt_text = topic_prompt_message.text
        combined_prompt = topic_prompt_text.replace("{goal}", "\n\n" + goal_text)
        print(f"\n\nCombined Prompt: \n\n{combined_prompt}\n\n")
        return combined_prompt

    async def combine_prompt(self):
        prompt_list = []
        if self.system_prompt:
            prompt_list.append(self.system_prompt)
        if self.user_prompt:
            prompt_list.append(self.user_prompt)

    async def generate_chat_response(self, message: PyroMessage):
        combined_prompt = await self.get_combined_topic_prompt()
        print(f"\n\nCombined_prompt: \n\n{combined_prompt}\n\n")
        context = await self.build_topic_summary()
        print(f"\n\nContext:\n\n{context}\n\n")
        parsed_message = await self.parse_message(message)
        print(f"\n\nMessage:\n\n{parsed_message.text}\n\n")
        response = chat_response(combined_prompt, context, parsed_message.text)
        print(f"\n\nResponse...\n\n{response}\n")
        await self.post_message(response)

    async def init_topic(self, message: PyroMessage):
        msg = await self.parse_message(message=message)
        # print(f"\n\nMessage:\n\n{msg}\n\n")
        self.chat_id = msg.chat_id
        self.topic_id = msg.message_thread_id
        topic_messages = await self.get_topic_messages()
        # print(f"\nMessages: \n{topic_messages}\n\n")
        self.topic_messages = topic_messages

    async def parse_message(self, message: PyroMessage) -> MessageContext:
        sleep(0.25)
        parsed_message = await extract_context(message)
        return parsed_message

    async def get_all_messages(self) -> List[str]:
        """
        Get all messages in a superthread.
        """
        sleep(0.5)
        all_messages = self.user_tg_client.get_chat_history(self.chat_id)
        message_list = []
        async for msg in all_messages:
            # sleep(0.25)
            if msg.text:
                message_list.append(msg)
        return message_list

    async def get_topic_messages(self) -> List[PyroMessage]:
        """
        Retrieve messages from the specified chat and topic.
        """
        message_list = []
        sleep(0.5)
        if self.chat_id and self.topic_id:
            all_messages = self.user_tg_client.get_discussion_replies(
                self.chat_id, self.topic_id
            )
            # print(f"\n\nGetting Topic Messages...\n\n{all_messages}\n\n")
            async for msg in all_messages:  # sleep(0.25)
                if msg.text:
                    message_list.append(msg)
        elif self.chat_id:
            all_messages = self.user_tg_client.get_chat_history(self.chat_id)
            async for msg in all_messages:
                # sleep(0.25)
                if msg.text:
                    message_list.append(msg)
        return message_list

    async def get_message_match(
        self, match_str: str, topic_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Search for a message that contains the match_str.
        """
        if topic_id:
            messages = self.topic_messages  # await self.get_topic_messages()
            for msg in messages:
                if match_str in msg.text:
                    return msg
        else:
            sleep(0.5)
            messages = await self.get_all_messages()
            for msg in messages:
                if match_str in msg.text:
                    return msg
        return None

    async def build_topic_summary(self):
        topic_messages = self.topic_messages  # await self.get_topic_messages()
        topic_thread = ""
        topic_msg_list = []
        for msg in reversed(topic_messages):
            parsed_msg = await self.parse_message(msg)
            user = parsed_msg.user.username or parsed_msg.user.first_name
            topic_thread = topic_thread + f"\n{user}: {parsed_msg.text}\n"
            # msg_dict = {"user": msg.user.username, "text": msg.text}
            # topic_msg_list.append(msg_dict)
        return topic_thread

    async def summarize_chat(self):
        """
        Summarize the chat conversation using the LLM.
        """
        messages = self.topic_messages  # await self.get_topic_messages()
        conversation = "\n".join(messages)
        prompt = f"{self.system_prompt}\n\nConversation:\n{conversation}\n\nPlease provide a summary of the above conversation."
        response = await self.llm_client.complete(prompt=prompt)
        await self.bot_tg_client.send_message(self.chat_id, response)

    async def post_message(self, message_str: str):
        """Post a message to the chat and/or topic."""
        await self.bot_tg_client.send_message(
            chat_id=self.chat_id, message_thread_id=self.topic_id, text=message_str
        )


# Forum Topic Chatbot
class ForumTopicLLM(TelegramLLMBase):
    pass


# LLM thread prompt

# Misc ----------------------------------------------------------------------------------------------------------------


# Etc -----------------------------------------------------------------------------------------------------------------
