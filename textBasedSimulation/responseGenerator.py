import asyncio
from multiprocessing.resource_sharer import stop
import time
import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

GPT4 = "gpt-4"
GPT35 = "gpt-3.5-turbo"
API_KEY = os.environ.get("API_KEY")
openai.api_key = API_KEY

SAMPLE_DESCRIPTION = """John Lin is a pharmacy shopkeeper at the Willow
Market and Pharmacy who loves to help people. He
is always looking for ways to make the process
of getting medication easier for his customers;
John Lin is living with his wife, Mei Lin, who
is a college professor, and son, Eddy Lin, who is
a student studying music theory; John Lin loves
his family very much; John Lin has known the old
couple next-door, Sam Moore and Jennifer Moore,
for a few years; John Lin thinks Sam Moore is a
kind and nice man; John Lin knows his neighbor,
Yuriko Yamamoto, well; John Lin knows of his
neighbors, Tamara Taylor and Carmen Ortiz, but
has not met them before; John Lin and Tom Moreno
are colleagues at The Willows Market and Pharmacy;
John Lin and Tom Moreno are friends and like to
discuss local politics together; John Lin knows
the Moreno family somewhat well — the husband Tom
Moreno and the wife Jane Moreno.
"""


def generateInitialObservations(userName, baseDescription):
    BACKGROUND_DESCRIPTION_CONTEXT = f"You are the user {userName}. You wil be provided with a description with background details about you."

    # Create a dictionary that represents the JSON structure
    prompt = {
        "context": BACKGROUND_DESCRIPTION_CONTEXT,
        "information": {"description": baseDescription},
        "criteria": [
            "Generate a list consisting of all the important observations made from the description",
            "Each item in the list should consist of one observation separated by a new line",
        ],
        "example": "(Observation 1 text)\n(Observation 2 text)\n",
    }
    defaultBackgroundPrompt = json.dumps(prompt, indent=4)
    return getGPTResponse(defaultBackgroundPrompt, GPT35)


def generateObservations(userName, conversationalUser, currentConversation, userResult):
    prompt = {
        "context": f"Based on the conversation between {userName} and {conversationalUser}, where the current statement of conversation is '{currentConversation}', and the response generated by {userName} is '{userResult}'",
        "instruction": "provide three observations from the conversation. Only list the observations, separated by a new line, without any additional text, headers, or formatting.",
        "example": "(Observation 1 text)\n(Observation 2 text)\n",
    }

    observationPrompt = json.dumps(prompt, indent=4)
    return getGPTResponse(observationPrompt, GPT35)


def generateConversation(
    userName, conversationalUser, currentConversation, observationList
):
    prompt = {
        "context": f"You are a friendly and knowledgeable human, {userName}, engaging in a conversation with {conversationalUser}. Respond only as {userName}, and do not mention or hint that you are an AI. Maintain a friendly and seamless interaction, keeping in mind the current conversation context.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
            "Relevant observations": observationList,
        },
        "criteria": [
            "Generate user-friendly, seamless, and appropriate responses that align with the current conversation context. Keep responses short and to the point. Respond as {userName} and do not assume or hint at any other identity.",
        ],
    }

    conversationPrompt = json.dumps(prompt, indent=4)
    return getConversationGenerator(conversationPrompt, GPT35)


def getConversationGenerator(prompt, gptModel):
    response = openai.ChatCompletion.create(
        model=gptModel,
        messages=[
            {"role": "system", "content": "You are a conversational agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        max_tokens=50,
        stream=True,
    )
    return response


def getGPTResponse(prompt, gptModel):
    response = openai.ChatCompletion.create(
        model=gptModel,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=300,
    )
    return response["choices"][0]["message"]["content"]
