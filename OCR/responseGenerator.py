import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

GPT4='gpt-4'
GPT35='gpt-3.5-turbo'
API_KEY=os.environ.get('API_KEY') 
openai.api_key="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"

SAMPLE_DESCRIPTION="""John Lin is a pharmacy shopkeeper at the Willow
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


def generateInitialObservations(userName,baseDescription):

    BACKGROUND_DESCRIPTION_CONTEXT=f"You are the user {userName}. You wil be provided with a description with background details about you."

    # Create a dictionary that represents the JSON structure
    prompt = {
        "context": BACKGROUND_DESCRIPTION_CONTEXT,
        "information": {
            "description":baseDescription
        },
        "criteria": [
            "Generate a list consisting of all the important observations made from the description",
            "Each item in the list should consist of one observation separated by a new line"
        ],
        "example": "(Observation 1 text)\n(Observation 2 text)\n"
    }
    defaultBackgroundPrompt=json.dumps(prompt,indent=4)
    return getGPTResponse(defaultBackgroundPrompt,GPT35)

def generateObservations(userName,conversationalUser,currentConversation,userResult):
    prompt = {
        "context": f"You are the user {userName} having a conversation with {conversationalUser}. You are provided with the current conversation statement {currentConversation} and your response to it as the user Result",
        "information": {
            "You are the user":userName,
            "The person with whom you are having a conversation with":conversationalUser,
            "user Result":userResult
        },
        "criteria": [
            "Generate a list consisting of 3 most important observations made from the conversation",
            "Each item in the list should consist of one observation separated by a new line"
        ],
        "example": "(Observation 1 text)\n(Observation 2 text)\n"
    }
    observationPrompt=json.dumps(prompt,indent=4)
    return getGPTResponse(observationPrompt,GPT35)

def generateConversation(userName,conversationalUser,currentConversation,observationList):
    prompt={
        "context": f"You are the user {userName} and not an AI assistant who will be having a conversation with {conversationalUser}.Act as conversational agent who is also provided with a list of relevant observations and a current conversation text. Provide a response accordingly",
        "information": {
            "You are the user":userName,
            "The person with whom you are having a conversation with":conversationalUser,
            "Current conversation":currentConversation,
            "List of relevant observations for the current conversation": observationList
        },
        "criteria": [
            "Generate a user-friendly response which allows for a seamless interaction with the other user and answer appropriately acccording to the current conversation text. Maximum 100 characters.",
        ],
    }
    conversationPrompt=json.dumps(prompt,indent=4)
    return getGPTResponse(conversationPrompt,GPT4)

def getGPTResponse(prompt,gptModel):
    response = openai.ChatCompletion.create(
    model=gptModel,
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        ,
        temperature=0.8,
    max_tokens=300
    )
    return response['choices'][0]['message']['content']
