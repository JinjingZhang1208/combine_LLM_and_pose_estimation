from distutils import text_file
import time
import os
import datetime
import asyncio
from enum import Enum
from TTS import audio_tools
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dotenv import load_dotenv
from retrievalFunction import retrievalFunction
from pymongo.mongo_client import MongoClient
from audioRecorder import listenAndRecord, deleteAudioFile
from csvLogger import CSVLogger, LogElements

# from TTS import silero
from TTS import polly
from responseGenerator import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
    getTextfromAudio,
)

# tts = silero.Silero()
# Define list of expressions and actions for GPT and allow it to pick one

load_dotenv()

# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "Users"
COLLECTION_MEMORY_OBJECTS = "TestMemory"
RETRIEVAL_COUNT = 5
FILENAME = "current_conversation.wav"
CSV_LOGGER = CSVLogger()


class CONVERSATION_MODE(Enum):
    TEXT = 1
    AUDIO = 2


# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]

tts = polly.Polly()


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
        memoryObjectCollection.find(fetchQuery).sort("_id", -1).limit(50), maxlen=50
    )


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


def updateMemoryCollection(
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
    if len(pastObservations) > 15:
        pastObservations.pop()
    pastObservations.appendleft(memoryObjectData)


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


def startConversation(userName, currMode):
    global pastObservations
    conversationalUser = input("Define the username you are acting as: ")
    baseObservation = fetchBaseDescription(userName)
    pastObservations = fetchPastRecords(userName)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()
    while True:
        if currMode == CONVERSATION_MODE.TEXT.value:
            start = time.perf_counter()
            currentConversation = input(
                f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
            )
            end = time.perf_counter()
            text_input_time = round(end - start, 2)
            CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, text_input_time)
            CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, 0)
        else:
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
        baseRetrieval = retrievalFunction(
            currentConversation,
            baseObservation,
            RETRIEVAL_COUNT,
            isBaseDescription=True,
        )
        observationRetrieval = retrievalFunction(
            currentConversation,
            pastObservations,
            RETRIEVAL_COUNT,
            isBaseDescription=False,
        )
        end = time.perf_counter()
        retrieval_time = round(end - start, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_RETRIEVAL, retrieval_time)

        important_observations = [
            data[1] for data in baseRetrieval + observationRetrieval
        ]

        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_OBSERVATIONS, "\n".join(important_observations)
        )
        important_scores = [
            round(data[0], 2) for data in baseRetrieval + observationRetrieval
        ]

        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_SCORES, "\n".join(map(str, important_scores))
        )
        start = time.perf_counter()
        conversationPrompt = generateConversation(
            userName,
            conversationalUser,
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


def generateObservationAndUpdateMemory(
    userName, conversationalUser, currentConversation, resultConversationString
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

    updateMemoryCollection(userName, conversationalUser, finalObservations)


def setConversationMode():
    while True:
        currMode = input("Please select the following :\n1. Text Mode\n2. Audio Mode\n")
        if currMode == "1":
            return CONVERSATION_MODE.TEXT.value
        elif currMode == "2":
            return CONVERSATION_MODE.AUDIO.value
        else:
            print("Invalid input, please select appropriate options")


if __name__ == "__main__":
    pastObservations = deque()
    # Get username.
    userName = input("Please enter the username of character: ")

    # Check for existing user.
    existingUser = userCollection.find_one({"Username": userName})

    if existingUser:
        print(f"Welcome back! {userName} \nContinue where you left off")
    else:
        # Collect the description details.
        description = getBaseDescription()

        # Insert the userData to the Users collection.
        userData = {"Username": userName, "Description": description}
        userCollection.insert_one(userData)

        # Time the function call and fetch the results.
        startTime = time.time()
        observationList = generateInitialObservations(userName, description).split("\n")
        endTime = time.time()
        print(
            f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} "
        )

        # Generate the memory object data and push it to the memory objects collection.
        updateBaseDescription(userName, observationList)
        print("User created successfully!")
    currMode = setConversationMode()
    startConversation(userName, currMode)
    client.close()
