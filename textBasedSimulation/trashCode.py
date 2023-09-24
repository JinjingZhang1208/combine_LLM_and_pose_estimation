"""
    prompt={
        "context": f"You are the user {userName} and not an AI assistant who will be having a conversation with {conversationalUser}.Act as conversational agent who is also provided with a list of relevant observations and a current conversation text. Provide a response accordingly",
        "information": {
            "You are the user":userName,
            "The person with whom you are having a conversation with":conversationalUser,
            "Current conversation":currentConversation,
            "List of relevant observations for the current conversation": observationList
        },
        "criteria": [
            "Generate a user-friendly response which allows for a seamless interaction with the other user and answer appropriately acccording to the current conversation text",
        ],
    }
    """

"""
def testSamplePrompt():
    for chunk in openai.ChatCompletion.create(
        model=GPT35,
        messages=[{
            "role":"user",
            "content":"Generate a list of numbers from 1 to 100"
        }],
        stream=True
    ):
        try:
            content=chunk["choices"][0]["delta"]["content"]
            print(content,end='')
        except:
            break
"""
"""
 prompt = {
        "context": f"You are the user {userName} having a conversation with {conversationalUser}. You are provided with the current conversation statement and your response to the given statement",
        "information": {
            "You are the user":userName,
            "The person with whom you are having a conversation with":conversationalUser,
            "current statement of conversation":currentConversation,
            "The response generated by you as the userName":userResult
        },
        "criteria": [
            "Generate a list consisting of 3 most important observations made from the conversation",
            "Each item in the list should consist of one observation separated by a new line"
        ],
        "example": "(Observation 1 text)\n(Observation 2 text)\n"
    }
"""
"""
def calculateImportance(content,stored_memory_data):
    importancePrompt ={
        "context": f"You are a conversational agent who will is provided with a set of observation strings. Determine the most important observations based on the current conversation.",
        "information": {
            "description":"Provide an integer on a scale of 1 to 10 where 1 is purely mundane and 10 is extremely poigant. rate the likely poigancy of the following observation strings"
        }
    }




def createBasePrompt(userName,baseDescription):

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
        "example": "(Observation 1)\n(Observation 2)\n"
    }
    return json.dumps(prompt,indent=4)
"""


"""
one more failed prompt.
prompt = {
        "context": f"You are the user {userName} having a conversation with {conversationalUser}. Respond as if you are a human with knowledge and memory, and do not mention or hint that you are an AI. Engage in a friendly and seamless manner according to the current conversation context.",
        "information": {
            "You are the user": userName,
            "The person with whom you are having a conversation with": conversationalUser,
            "Current conversation": currentConversation,
            "List of relevant observations for the current conversation": observationList,
        },
        "criteria": [
            "Generate a user-friendly response that allows for seamless interaction and is appropriate to the current conversation context.Keep the responses short.",
        ],
    }
"""
"""
potential prompt
prompt = {
        "context": f"As {userName}, converse with {conversationalUser}, maintaining a friendly and knowledgeable demeanor. Respond concisely and relevantly.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
            "Observations": observationList,
        },
        "criteria": [
            "Generate friendly, appropriate, and concise responses as {userName}."
        ],
    }

"""
