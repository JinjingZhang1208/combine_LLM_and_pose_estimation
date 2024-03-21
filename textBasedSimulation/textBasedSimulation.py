from responseGenerator import (
    generateInitialObservations,
    generateConversation,
    getTextfromAudio,
    generate_reflection,
    generate_saturation_prompt
)
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from retrievalFunction import retrievalFunction
from audioRecorder import listenAndRecord
from csvLogger import CSVLogger, LogElements
from collections import deque
from avatar_data import avatar_action_map, avatar_expression_map, avatar_voice
import datetime
import os
from dotenv import load_dotenv
from collections import deque
from pymongo.mongo_client import MongoClient
from dialoge_helper import filter_conversation, is_question, setConversationMode, set_agent_mode
from enums import CONVERSATION_MODE, AGENT_MODE, AVATAR_DATA


load_dotenv()


# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "NPC Avatars"
COLLECTION_MEMORY_OBJECTS = "ev013"

MAX_DEQUE_LENGTH = 50

# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]
MAX_WAIT_TIME = 120  # 2 minutes

BASE_RETRIEVAL_COUNT = 3  # change parameter
OBS_RETRIEVAL_COUNT = 5  # change parameter
RA_OBS_COUNT = 5
EVENT_OBS_COUNT = 5
REFLECTION_RETRIEVAL_COUNT = 5
REFLECTION_PERIOD = 5
CHECK_SATURATION_PEROID = 1
RESEARCH_GOALS = "experience in Vr chat, what activities they like doing in Vr chat and overall why do they value regarding VR chat?"
DEBATE_GOALS = "AI Agents should be included in VRChat in the future"
FILENAME = "current_conversation.wav"

all_conversations = []

CSV_LOGGER = CSVLogger()


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


def text_conversation_input(agent_mode, userName, conversationalUser, conversation_count):
    start = time.perf_counter()
    if agent_mode == AGENT_MODE.RESEARCH.value:
        currentConversation = input(
            f"Talks with {userName}, You are {conversationalUser}. Talk about {RESEARCH_GOALS}! "
        )
    elif agent_mode == AGENT_MODE.DEBATE.value:
        currentConversation = input(
            f"Talk with {userName}, You are {conversationalUser}. Engage in a debate on {DEBATE_GOALS}! "
        )
    else:
        currentConversation = input(
            f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
        )

    end = time.perf_counter()
    text_input_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, text_input_time)
    CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, 0)

    return currentConversation


def audio_conversation_input(CSV_LOGGER, FILENAME):
    start = time.perf_counter()
    listenAndRecord(FILENAME, CSV_LOGGER)
    end = time.perf_counter()
    audio_record_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, audio_record_time)

    start = time.perf_counter()
    currentConversation = getTextfromAudio(FILENAME)
    end = time.perf_counter()
    audio_to_text_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, audio_to_text_time)

    return currentConversation


def startConversation(npc_name, currMode, agent_mode):
    global pastObservations
    global all_conversations

    if agent_mode == AGENT_MODE.NORMAL.value or agent_mode == AGENT_MODE.RESEARCH.value or agent_mode == AGENT_MODE.DEBATE.value:
        conversationalUser = input("Define the username you are acting as: ")
    elif agent_mode == AGENT_MODE.EVENT.value:
        conversationalUser = "User"
    baseObservation = fetchBaseDescription(npc_name)
    pastObservations = fetchPastRecords(conversationalUser)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()

    conversation_count = 0
    while True:
        push_conversation = True # only push conversation if it is not a question
        current_conversation = ""

        if currMode == CONVERSATION_MODE.TEXT.value:
            currentConversation = text_conversation_input( agent_mode, npc_name, conversationalUser, conversation_count)
        elif currMode == CONVERSATION_MODE.AUDIO.value:
            currentConversation = audio_conversation_input( CSV_LOGGER, FILENAME)
        CSV_LOGGER.set_enum(LogElements.MESSAGE, currentConversation)

        if currentConversation.lower() == "done":
            break

        if agent_mode != AGENT_MODE.EVENT.value:
            current_conversation += f"User: {currentConversation}. "
        else:
            if not is_question(currentConversation):
                current_conversation += f"User: {currentConversation}. "
            elif is_question(currentConversation):
                push_conversation = False

        start = time.perf_counter()
        baseRetrieval, observationRetrieval = perform_observation_retrieval( agent_mode, currentConversation, baseObservation, pastObservations )
        end = time.perf_counter()

        retrieval_time = round(end - start, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_RETRIEVAL, retrieval_time)
        if agent_mode == AGENT_MODE.NORMAL.value:
            important_observations = [ data[1] for data in baseRetrieval + observationRetrieval ]
        else:
            important_observations = [ data[1] for data in observationRetrieval ]
        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_OBSERVATIONS, "\n".join(
                important_observations)
        )
        # print(f"base retrieval: {baseRetrieval}")
        # print(f"observation retrieval: {observationRetrieval}")
        print(f"Important Observations: {important_observations}")

        if agent_mode == AGENT_MODE.NORMAL.value:
            important_scores = [ round(data[0], 2) for data in baseRetrieval + observationRetrieval ]
        else:
            important_scores = [ round(data[0], 2) for data in observationRetrieval ]
        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_SCORES, "\n".join(map(str, important_scores))
        )

        start = time.perf_counter()
        conversationPrompt = generate_conversation_prompt(
            npc_name, conversationalUser, currentConversation, important_observations, avatar_expressions, avatar_actions, agent_mode)
        end = time.perf_counter()
        npc_response_time = round(end - start, 2)

        print(f"{npc_name} :")
        resultConversationString = ""
        for conversation in conversationPrompt:
            try:
                currText = conversation.choices[0].delta.content
                resultConversationString += currText
                print(currText, end="")
            except:
                break
        CSV_LOGGER.set_enum(LogElements.NPC_RESPONSE, resultConversationString)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_RESPONSE, npc_response_time)

        filtered_result = filter_conversation(resultConversationString)
        if agent_mode != AGENT_MODE.EVENT.value:
            current_conversation += f"{npc_name}: {filtered_result}.\n"

        print()

        CSV_LOGGER.write_to_csv(True) # write all values to csv

        print(
            f"Time taken for the conversation generation by GPT : {npc_response_time}"
        )
        if push_conversation:
            eventLoop.run_in_executor( threadExecutor, generateObservationAndUpdateMemory, npc_name, conversationalUser, currentConversation, resultConversationString, current_conversation)

        all_conversations.append(current_conversation)

        conversation_count += 1
        if conversation_count != 1 and conversation_count % REFLECTION_PERIOD == 0 and agent_mode == AGENT_MODE.NORMAL.value:
            eventLoop.run_in_executor(threadExecutor, perform_reflection_logic, npc_name, conversationalUser, currentConversation, pastObservations)
        
        if conversation_count != 1 and conversation_count % CHECK_SATURATION_PEROID == 0 and perform_saturation_logic(npc_name, conversationalUser, all_conversations):
            print("Conversation ended due to saturation.")
            break


def fetchBaseDescription(userName: str):
    baseObservation = deque(
        memoryObjectCollection.find(
            {"Username": userName, "Conversation with User": "Base Description"}
        ),
    )

    if baseObservation:
        observation_dict = baseObservation[0]
        filtered_observations = [
            obs for obs in observation_dict['Observations'] if obs.strip()
        ]
        observation_dict['Observations'] = filtered_observations

    return baseObservation


def fetchPastRecords(userName: str):
    fetchQuery = {
        "$or": [{"Username": userName}, {"Conversation with User": userName}],
        "Conversation with User": {"$ne": "Base Description"},
    }
    return deque(
        memoryObjectCollection.find(fetchQuery).sort("_id", -1).limit(MAX_DEQUE_LENGTH), maxlen=MAX_DEQUE_LENGTH
    )


def update_reflection_db_and_past_obs(
        userName: str,
        conversationalUser: str,
        observationList: list
):
    global pastObservations
    # Get the current time.
    currTime = datetime.datetime.utcnow()
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": conversationalUser,
        "Creation Time": currTime,
        "Observations": observationList,
    }
    currentObject = memoryObjectCollection.insert_one(memoryObjectData)
    # Delete the oldest record and add the latest one.
    memoryObjectData["_id"] = currentObject.inserted_id
    # Delete the oldest record and add the latest one.
    if len(pastObservations) > MAX_DEQUE_LENGTH:
        pastObservations.pop()
    pastObservations.appendleft(memoryObjectData)


def updateBaseDescription(userName: str, observationList: list):
    # Get the current time.
    currTime = datetime.datetime.utcnow()
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": "Base Description",
        "Creation Time": currTime,
        "Observations": observationList,
    }
    # Update the latest collection with the id parameter and insert to the database.
    memoryObjectCollection.insert_one(memoryObjectData)
    # Delete the oldest record and add the latest one.


def update_Memory_Collection_and_past_obs(
    userName: str, conversationalUser: str, observationList: list
):
    global pastObservations
    # Get the current time.
    currTime = datetime.datetime.utcnow()
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": conversationalUser,
        "Creation Time": currTime,
        "Observations": observationList,
    }
    # Update the latest collection with the id parameter and insert to the database.
    currentObject = memoryObjectCollection.insert_one(memoryObjectData)
    memoryObjectData["_id"] = currentObject.inserted_id
    # Delete the oldest record and add the latest one.
    if len(pastObservations) > MAX_DEQUE_LENGTH:
        pastObservations.pop()
    pastObservations.appendleft(memoryObjectData)


def perform_reflection_logic(
    userName, conversationalUser, currentConversation, pastObservations,
):
    print("NPC in reflection...\n")
    reflection_retrieval = retrievalFunction(
        currentConversation=currentConversation,
        memoryStream=pastObservations,
        retrievalCount=REFLECTION_RETRIEVAL_COUNT,
        isBaseDescription=False,
        is_reflection=True,
    )
    reflection_observations = [data[1] for data in reflection_retrieval]

    reflection_list = generate_reflection(
        userName,
        conversationalUser,
        pastConversations=reflection_observations,
    ).split("\n")
    finalObservations = []
    for observation in reflection_list:
        if len(observation) > 0:
            finalObservations.append(observation)
    # print(f"NPC reflection: {finalObservations}")
    update_reflection_db_and_past_obs(
        userName,
        conversationalUser,
        finalObservations
    )


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



def generateObservationAndUpdateMemory(
    userName,
    conversationalUser,
    currentConversation,
    resultConversationString,
    npc_dialogues
):
    # # Time the function call and fetch the results.
    # startTime = time.perf_counter()
    # observationList = generateObservations(
    #     userName, conversationalUser, currentConversation, resultConversationString
    # )
    # observationList = observationList.split("\n")
    finalObservations = []
    finalObservations.append(npc_dialogues)
    # for observation in observationList:
    #     if len(observation) > 0:
    #         finalObservations.append(observation)

    # endTime = time.perf_counter()
    """
    print(
        f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} "
    )
    """
    update_Memory_Collection_and_past_obs(
        userName, conversationalUser, finalObservations)


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
            retrievalCount=RA_OBS_COUNT,
            isBaseDescription=False,
        )
    elif agent_mode == AGENT_MODE.EVENT.value:
        # if publish event, only sort by relevance
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=EVENT_OBS_COUNT,
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


def generate_conversation_prompt(npc_name, conversationalUser, currentConversation, important_observations, avatar_expressions, avatar_actions, agent_mode=None, research_goals=None, debate_goals=None):
    if agent_mode == AGENT_MODE.RESEARCH.value:
        return generateConversation(npc_name, conversationalUser, currentConversation, important_observations, avatar_expressions, avatar_actions, agent_mode=agent_mode, research_goals=RESEARCH_GOALS)
    elif agent_mode == AGENT_MODE.DEBATE.value:
        return generateConversation(npc_name, conversationalUser, currentConversation, important_observations, avatar_expressions, avatar_actions, agent_mode=agent_mode, debate_goals=DEBATE_GOALS)
    else:
        return generateConversation(npc_name, conversationalUser, currentConversation, important_observations, avatar_expressions, avatar_actions, agent_mode=agent_mode)


if __name__ == "__main__":
    currMode = setConversationMode()
    agent_mode = set_agent_mode()

    pastObservations = deque()

    if agent_mode == AGENT_MODE.NORMAL.value:
        npc_name = input("Please enter the username of character: ")
    elif agent_mode == AGENT_MODE.EVENT.value:
        npc_name = "Event Agent"
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        npc_name = "Research Agent"
    elif agent_mode == AGENT_MODE.DEBATE.value:
        npc_name = "Debate Agent"

    # Check for existing user.
    is_existing_npc_in_user_collection = userCollection.find_one(
        {"Username": npc_name})

    if is_existing_npc_in_user_collection:
        # print(f"Welcome back! {npc_name} \nContinue where you left off")
        avatar_expression_map = is_existing_npc_in_user_collection[
            AVATAR_DATA.AVATAR_EXPRESSION_MAP.value]
        avatar_action_map = is_existing_npc_in_user_collection[AVATAR_DATA.AVATAR_ACTION_MAP.value]
        avatar_voice = is_existing_npc_in_user_collection[AVATAR_DATA.AVATAR_VOICE.value]
        avatar_expressions = list(avatar_expression_map.keys())
        avatar_actions = list(avatar_action_map.keys())
    else:
        description = getBaseDescription(agent_mode)
        # Insert the userData to the Users collection.
        userData = {
            "Username": npc_name,
            "Description": description,
            "Avatar Expressions Map": avatar_expression_map,
            "Avatar Actions Map": avatar_action_map,
            "Avatar Voice": avatar_voice,
        }
        userCollection.insert_one(userData)
        # Time the function call and fetch the results.
        startTime = time.time()
        observationList = generateInitialObservations(
            npc_name, description).split("\n")
        endTime = time.time()
        print(
            f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} "
        )

        # Generate the memory object data and push it to the memory objects collection.
        updateBaseDescription(npc_name, observationList)
        print("User created successfully!")
        print(f"Welcome back! {npc_name} \nContinue where you left off")
        avatar_expressions = list(avatar_expression_map.keys())
        avatar_actions = list(avatar_action_map.keys())

    startConversation(npc_name, currMode, agent_mode)
    client.close()
