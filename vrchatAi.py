import os
from typing import Dict
import openai
from .env import VRChatEnv
from .agents import ConversationAgent

class VRChatAI:
    def __init__(
        self,
        vrchat_login: Dict[str, str] = None,
        openai_api_key: str = None,
        conversation_agent_model_name: str = "gpt-4",
        conversation_agent_temperature: float = 0.7,
        conversation_agent_max_tokens: int = 150,
    ):
        """
        The main class for VRChatAI.
        Conversation agent is the AI that generates responses to other players' messages.
        :param vrchat_login: VRChat login config
        :param openai_api_key: OpenAI API key
        :param conversation_agent_model_name: Conversation agent model name
        :param conversation_agent_temperature: Conversation agent temperature
        :param conversation_agent_max_tokens: Conversation agent max tokens
        """
        # init env
        self.env = VRChatEnv(
            vrchat_login=vrchat_login,
        )

        # set openai api key
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # init agents
        self.conversation_agent = ConversationAgent(
            model_name=conversation_agent_model_name,
            temperature=conversation_agent_temperature,
            max_tokens=conversation_agent_max_tokens,
        )

    def step(self, message):
        """
        Process a message from another player and generate a response.
        :param message: The message from another player.
        :return: The AI's response.
        """
        # Generate a response using the conversation agent
        response = self.conversation_agent.generate_response(message)

        # Send the response in VRChat
        self.env.send_message(response)

        return response
