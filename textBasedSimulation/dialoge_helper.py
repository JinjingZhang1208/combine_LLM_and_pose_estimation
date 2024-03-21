from enums import CONVERSATION_MODE, AGENT_MODE
import re
from responseGenerator import generate_saturation_prompt
from retrievalFunction import retrievalFunction

BASE_RETRIEVAL_COUNT = 3  # change parameter
OBS_RETRIEVAL_COUNT = 5  # change parameter
RA_RETRIVAL_COUNT = 5
EVENT_RETRIVAL_COUNT = 5


def get_npc_name(agent_mode):
    if agent_mode == AGENT_MODE.NORMAL.value:
        return input("Please enter the username of character: ")
    elif agent_mode == AGENT_MODE.EVENT.value:
        return "Event Agent"
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        return "Research Agent"
    elif agent_mode == AGENT_MODE.DEBATE.value:
        return "Debate Agent"
    
    

def is_question(message):
    question_keywords = ["what", "how", "where", "when", "why", "who", "?"]
    # Convert the message to lowercase for case-insensitive comparison
    message_lower = message.lower()
    for keyword in question_keywords:
        if keyword in message_lower:
            return True
    return False


def filter_conversation(conversation):
    # Remove text within parentheses
    filtered_result = re.sub(r'\([^()]*\)', '', conversation)
    # Remove newline characters
    filtered_result = filtered_result.replace('\n', '')
    return filtered_result


def setConversationMode():
    while True:
        currMode = input(
            "Please select the following :\n1. Text Mode\n2. Audio Mode\n")
        if currMode == "1":
            return CONVERSATION_MODE.TEXT.value
        elif currMode == "2":
            return CONVERSATION_MODE.AUDIO.value
        else:
            print("Invalid input, please select appropriate options")


def set_agent_mode():
    while True:
        user_input = input(
            "Select conversation mode:\n1. Normal Conversation\n2. Event Agent\n3. Research Agent\n4. Debate Agent\nEnter the corresponding number: ")
        if user_input == "1":
            return AGENT_MODE.NORMAL.value
        elif user_input == "2":
            return AGENT_MODE.EVENT.value
        elif user_input == "3":
            return AGENT_MODE.RESEARCH.value
        elif user_input == "4":
            return AGENT_MODE.DEBATE.value
        else:
            print("Invalid input, please enter a valid number.")



def getBaseDescription(agent_mode):
    if agent_mode == AGENT_MODE.EVENT.value:
        return (
            "You are a dedicated agent, responsible for managing and providing information about user-generated events. "
            "You will either store an event or provide information about an event based on a list of observations."
        )
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        return (
            "You are an Embodied Research Assistant, responsible for engaging users with predefined goals such as challenges, and interviewing users about their experiences, e.g., their experience with VRChat."
        )
    elif agent_mode == AGENT_MODE.DEBATE.value:
        return (
            "You are an AI Agent responsible for engaging in debates with users. You will be responsible for providing information and engaging in debates with users based on a list of observations."
        )
    elif agent_mode == AGENT_MODE.NORMAL.value:
        description = ""
        while True:
            currLine = input(
                "Please enter a relevant description about your character. Type done to complete the description \n"
            )
            if currLine.lower() == "done":
                break
            description += f"{currLine}\n"
        return description
    

def getBaseDescription(agent_mode):
    if agent_mode == AGENT_MODE.EVENT.value:
        return (
            "You are a dedicated agent, responsible for managing and providing information about user-generated events. "
            "You will either store an event or provide information about an event based on a list of observations."
        )
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        return (
            "You are an Embodied Research Assistant, responsible for engaging users with predefined goals such as challenges, and interviewing users about their experiences, e.g., their experience with VRChat."
        )
    elif agent_mode == AGENT_MODE.DEBATE.value:
        return (
            "You are an AI Agent responsible for engaging in debates with users. You will be responsible for providing information and engaging in debates with users based on a list of observations."
        )
    elif agent_mode == AGENT_MODE.NORMAL.value:
        description = ""
        while True:
            currLine = input(
                "Please enter a relevant description about your character. Type done to complete the description \n"
            )
            if currLine.lower() == "done":
                break
            description += f"{currLine}\n"
        return description
    

def select_important_observations(agent_mode, base_retrieval, observation_retrieval):
    if agent_mode == AGENT_MODE.NORMAL.value:
        return [data[1] for data in base_retrieval + observation_retrieval]
    else:
        return [data[1] for data in observation_retrieval]
    

def calculate_important_scores(agent_mode, base_retrieval, observation_retrieval):
    if agent_mode == AGENT_MODE.NORMAL.value:
        scores = [round(data[0], 2) for data in base_retrieval + observation_retrieval]
    else:
        scores = [round(data[0], 2) for data in observation_retrieval]
    return scores


def perform_observation_retrieval(
    agent_mode,
    currentConversation,
    baseObservation,
    pastObservations
):
    if agent_mode == AGENT_MODE.NORMAL.value:
        baseRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=baseObservation,
            retrievalCount=BASE_RETRIEVAL_COUNT,
            isBaseDescription=True,
        )
    else:
        baseRetrieval = []

    if agent_mode == AGENT_MODE.NORMAL.value:
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=OBS_RETRIEVAL_COUNT,
            isBaseDescription=False,
        )
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=RA_RETRIVAL_COUNT,
            isBaseDescription=False,
        )
    elif agent_mode == AGENT_MODE.EVENT.value:
        # if publish event, only sort by relevance
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=EVENT_RETRIVAL_COUNT,
            isBaseDescription=False,
            is_reflection=False,
            is_publish_event=True,
        )
    elif agent_mode == AGENT_MODE.DEBATE.value:
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=OBS_RETRIEVAL_COUNT,
            isBaseDescription=False,
        )
    return baseRetrieval, observationRetrieval


def perform_saturation_logic(
    userName, conversationalUser, all_conversations
):
    print("NPC in determinting saturation...\n")

    response = generate_saturation_prompt(
        userName,
        conversationalUser,
        pastConversations=all_conversations,
    )
    print(f"Saturation response: {response}")
    if "True" in response:
        return True
    elif "False" in response:
        return False 
    
