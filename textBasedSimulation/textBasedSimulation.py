from distutils import text_file
import time
import asyncio
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from retrievalFunction import retrievalFunction
from audioRecorder import listenAndRecord, deleteAudioFile
from csvLogger import CSVLogger, LogElements
from collections import deque
from avatar_data import avatar_action_map, avatar_expression_map, avatar_voice
import datetime
import os
from dotenv import load_dotenv
from collections import deque
from pymongo.mongo_client import MongoClient

load_dotenv()


# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "NPC Avatars"
COLLECTION_MEMORY_OBJECTS = "test199"

MAX_DEQUE_LENGTH = 50

# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]


from responseGenerator import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
    getTextfromAudio,
    generate_reflection,
    generate_event_publisher_prompt,
)



BASE_RETRIEVAL_COUNT = 3  # change parameter
OBS_RETRIEVAL_COUNT = 5 # change parameter
REFLECTION_RETRIEVAL_COUNT = 9
REFLECTION_PERIOD = 3

FILENAME = "current_conversation.wav"

CSV_LOGGER = CSVLogger()


class AVATAR_DATA(Enum):
    AVATAR_EXPRESSION_MAP = "Avatar Expressions Map"
    AVATAR_ACTION_MAP = "Avatar Actions Map"
    AVATAR_VOICE = "Avatar Voice"


class CONVERSATION_MODE(Enum):
    TEXT = 1
    AUDIO = 2


def getBaseDescription():
    description = ""
    while True:
        currLine = input(
            "Please enter a relevant description about your character. Type done to complete the description \n"
        )
        if currLine.lower() == "done":
            break
        description += f"{currLine}\n"
    return description


def startConversation(userName, 
                      currMode,
                      is_publish_event):
    global pastObservations
    if not is_publish_event:
        conversationalUser = input("Define the username you are acting as: ")
    else:
        conversationalUser = "Default User"
    baseObservation = fetchBaseDescription(userName)
    if baseObservation:
        # filter empty observations
        observation_dict = baseObservation[0]
        filtered_observations = [obs for obs in observation_dict['Observations'] if obs.strip()]
        observation_dict['Observations'] = filtered_observations

    pastObservations = fetchPastRecords(userName)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()

    conversation_count = 0
    while True:
        if currMode == CONVERSATION_MODE.TEXT.value:
            start = time.perf_counter()
            if not is_publish_event:
                currentConversation = input(
                    f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
                )
            else:
                currentConversation = input(
                    f"If you want to publish an event, start with Event: <Event Name> and then provide the details. Else, start with a query. "
                )
            end = time.perf_counter()
            text_input_time = round(end - start, 2)
            CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, text_input_time)
            CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, 0)
        elif currMode == CONVERSATION_MODE.AUDIO.value:
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
        CSV_LOGGER.set_enum(LogElements.MESSAGE, currentConversation)

        if currentConversation.lower() == "done":
            break
        start = time.perf_counter()

        if not is_publish_event:
            baseRetrieval = retrievalFunction(
                currentConversation=currentConversation,
                memoryStream=baseObservation,
                retrievalCount=BASE_RETRIEVAL_COUNT,
                isBaseDescription=True,
            )

        if not is_publish_event:
            observationRetrieval = retrievalFunction(
                currentConversation=currentConversation,
                memoryStream=pastObservations,
                retrievalCount=OBS_RETRIEVAL_COUNT,
                isBaseDescription=False,
            )
        else:
            # if publish event, only sort by relevance
            observationRetrieval = retrievalFunction(
                currentConversation=currentConversation,
                memoryStream=pastObservations,
                retrievalCount=OBS_RETRIEVAL_COUNT,
                isBaseDescription=False,
                is_publish_event=True,
            )
        end = time.perf_counter()
        retrieval_time = round(end - start, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_RETRIEVAL, retrieval_time)

        if not is_publish_event:
            important_observations = [
                data[1] for data in baseRetrieval + observationRetrieval
            ]
        else:
            important_observations = [
                data[1] for data in observationRetrieval
            ]
        # print(f"Important Observations: {important_observations}")

        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_OBSERVATIONS, "\n".join(important_observations)
        )
        if not is_publish_event:
            important_scores = [
                round(data[0], 2) for data in baseRetrieval + observationRetrieval
            ]
        else:
            important_scores = [
                round(data[0], 2) for data in observationRetrieval
            ]

        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_SCORES, "\n".join(map(str, important_scores))
        )
        start = time.perf_counter()
        if not is_publish_event:
            conversationPrompt = generateConversation(
                userName,
                conversationalUser,
                currentConversation,
                important_observations,
                avatar_expressions,
                avatar_actions,
            )
        else:
            conversationPrompt = generate_event_publisher_prompt(
                currentConversation,
                important_observations,
            )
        end = time.perf_counter()
        npc_response_time = round(end - start, 2)
        print(f"{userName} :")
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
        # speech = tts.speech(resultConversationString, "Joanna", 7)
        # polly.read_audio_file()
        # print(speech)
        CSV_LOGGER.write_to_csv(True)
        print()
        print(
            f"Time taken for the conversation generation by GPT : {npc_response_time}"
        )
        eventLoop.run_in_executor(
            threadExecutor,
            generateObservationAndUpdateMemory,
            userName,
            conversationalUser,
            currentConversation,
            resultConversationString,
        )
        

        conversation_count += 1
        if conversation_count!=1 and conversation_count % REFLECTION_PERIOD == 0 and not is_publish_event:
            with ThreadPoolExecutor() as executor:
                executor.submit( 
                    perform_reflection_logic,
                    userName,
                    conversationalUser,
                    currentConversation,
                    pastObservations,
                )

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
    print(f"NPC reflection: {finalObservations}")
    update_reflection_db_and_past_obs(
        userName,
        conversationalUser,
        finalObservations
    )

def generateObservationAndUpdateMemory(
    userName, 
    conversationalUser, 
    currentConversation, 
    resultConversationString
):
    # Time the function call and fetch the results.
    startTime = time.perf_counter()
    observationList = generateObservations(
        userName, conversationalUser, currentConversation, resultConversationString
    )
    observationList = observationList.split("\n")
    finalObservations = []
    for observation in observationList:
        if len(observation) > 0:
            finalObservations.append(observation)

    endTime = time.perf_counter()
    """
    print(
        f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} "
    )
    """
    update_Memory_Collection_and_past_obs(userName, conversationalUser, finalObservations)

# Fetch the base description once.
def fetchBaseDescription(userName: str):
    return deque(
        memoryObjectCollection.find(
            {"Username": userName, "Conversation with User": "Base Description"}
        ),
    )

# fetch the past records once.
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
    currentObject=memoryObjectCollection.insert_one(memoryObjectData)
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


def setConversationMode():
    while True:
        currMode = input("Please select the following :\n1. Text Mode\n2. Audio Mode\n")
        if currMode == "1":
            return CONVERSATION_MODE.TEXT.value
        elif currMode == "2":
            return CONVERSATION_MODE.AUDIO.value
        else:
            print("Invalid input, please select appropriate options")

def publish_event_mode():
    while True:
        declare_event = input("Do you want publish or Find an event (y/n): ")
        if declare_event.lower() == "y":
            return True
        elif declare_event.lower() == "n":
            return False
        else:
            print("Invalid input, please select appropriate options")



if __name__ == "__main__":
    currMode = setConversationMode()
    is_publish_event = publish_event_mode()
    if is_publish_event:
        OBS_RETRIEVAL_COUNT=7
    pastObservations = deque()

    if not is_publish_event:
        npc_name = input("Please enter the username of character: ")
    else:
        npc_name = "Event Publisher"

    # Check for existing user.
    is_existing_npc_in_user_collection = userCollection.find_one({"Username": npc_name})

    if is_existing_npc_in_user_collection:
        print(f"Welcome back! {npc_name} \nContinue where you left off")
        avatar_expression_map = is_existing_npc_in_user_collection[AVATAR_DATA.AVATAR_EXPRESSION_MAP.value]
        avatar_action_map = is_existing_npc_in_user_collection[AVATAR_DATA.AVATAR_ACTION_MAP.value]
        avatar_voice = is_existing_npc_in_user_collection[AVATAR_DATA.AVATAR_VOICE.value]
        avatar_expressions = list(avatar_expression_map.keys())
        avatar_actions = list(avatar_action_map.keys())

    else:
        description = getBaseDescription()

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
        observationList = generateInitialObservations(npc_name, description).split("\n")
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


    startConversation(npc_name, currMode,is_publish_event)
    client.close()
