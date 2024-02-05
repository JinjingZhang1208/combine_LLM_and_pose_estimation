from statistics import mode
from deepgram import Deepgram
import openai
from openai import OpenAI
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

GPT4 = "gpt-4"
GPT35 = "gpt-3.5-turbo"
API_KEY = os.environ.get("API_KEY")
openai_client = OpenAI(api_key=API_KEY)
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
MIMETYPE = 'audio/wav'

SAMPLE_DESCRIPTION = """John Lin is a pharmacy shopkeeper at the Willow Market and Pharmacy who loves to help people. He
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


def generate_reflection(
        userName,
        conversationalUser,
        pastConversations):
    prompt = {
        "context": f"Reflecting on the past conversations between {userName} and {conversationalUser}.",
        "pastConversations": f"{pastConversations}",
        "instruction": "Provide three new higher-level observations or insights based on the past conversations. Summarize the overall patterns and trends in the conversation, rather than specific details of individual conversational turns. Only list the observations, separated by a new line, without any additional text, headers, or formatting.",
        "example": "(Observation 1 text)\n(Observation 2 text)\n",
    }
    reflectionPrompt = json.dumps(prompt, indent=4)
    return getGPTResponse(reflectionPrompt, GPT35)


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


def generate_event_publisher_prompt(currentConversations, relevantObservations):
    prompt = {
        "context": "You are a dedicated agent, responsible for managing and providing information about user-generated events. You will either store an event or provide information about an event based on a list of observations.",
        "information": {
            "Current Conversations": currentConversations,
            "Relevant Observations": relevantObservations,
        },
        "criteria": [
            "Ensure responses are concise and informative, limited to one sentence without any unnecessary information.",
            "When asked about a specific event and you have relevant observations, respond with 'YES' and provide the event information.",
            "If there are no relevant observations for a queried event, respond with 'NO' and state that the information is not available.",
            "If user provides an event, store the event and respond with 'Received'",
        ]
    }

    eventPublisherPrompt = json.dumps(prompt, indent=4)
    return getConversationGenerator(eventPublisherPrompt, GPT35)


def generateConversation(
    userName,
    conversationalUser,
    currentConversation,
    relevantObservations: list,
    avatar_expressions,
    avatar_actions,
):
    prompt = {
        "context": f"You are a friendly and imaginative human, {userName}, having a lively conversation with {conversationalUser}. Always respond as {userName} and steer clear from any mentions or implications of being an AI. Your responses should be imaginative, especially when faced with unknowns, creating delightful and smooth interactions. Ensure that your responses do not contain emojis and refrain from repetitive greetings.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
            "Relevant observations": relevantObservations,
            "Expressions": avatar_expressions,
            "Actions": avatar_actions,
        },
        "criteria": [
            f"Craft user-friendly, seamless, and innovative responses. When specific details are scarce, improvise with inventive and relevant answers, always aligning with the ongoing chat. Your identity as {userName} should be constant, and there should be no disclosure or suggestion of being an AI.",
            f"Explicitly avoid the use of emojis and hashtags in all responses."
            f"Choose an expression from Expressions and an action from Actions autonomously, ensuring they perfectly fit the chat context. Present the output as follows: (chosen expression, chosen action)\\n(Conversation output).",
            f"Keep responses within 100-140 characters, allowing for flexibility while ensuring brevity.",
        ],
        "adaptive learning": "Remember and reference previous parts of the conversation within the same session to create a more cohesive and engaging user experience.",
    }

    conversationPrompt = json.dumps(prompt, indent=4)
    return getConversationGenerator(conversationPrompt, GPT35)


def getConversationGenerator(prompt, gptModel):
    response = openai_client.chat.completions.create(
        model=gptModel,
        messages=[
            {"role": "system", "content": "You are a conversational agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=150,
        stream=True,
    )
    return response


def getGPTResponse(prompt, gptModel):
    response = openai_client.chat.completions.create(
        model=gptModel,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=300,
    )
    return response.choices[0].message.content


# def getTextfromAudio_whisper_1(recordedFile):
#     audio_file = open(recordedFile, "rb")
#     transcript = openai_client.audio.transcriptions.create(
#         model="whisper-1", file=audio_file
#     )
#     print(f"Recorded Audio text : {transcript.text}")
#     return transcript.text


def getTextfromAudio(recordedFile):
    res = asyncio.run(get_deepgram_response(recordedFile))
    text = res.get("results", {}).get("channels", [{}])[0].get(
        "alternatives", [{}])[0].get("transcript", "")
    print(text)
    return text


async def get_deepgram_response(FILE):
    # Initialize the Deepgram SDK
    deepgram = Deepgram(DEEPGRAM_API_KEY)

    # Check whether requested file is local or remote, and prepare source
    if FILE.startswith('http'):
        # file is remote
        # Set the source
        source = {
            'url': FILE
        }
    else:
        # file is local
        # Open the audio file
        audio = open(FILE, 'rb')

        # Set the source
        source = {
            'buffer': audio,
            'mimetype': MIMETYPE
        }

    # Send the audio to Deepgram and get the response
    response = await asyncio.create_task(
        deepgram.transcription.prerecorded(
            source,
            {
                'punctuate': True,
                'model': 'nova',
            }
        )
    )

    # Write the response to the console
    return response
