from distutils import text_file
import time
import os
import datetime
import asyncio
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dotenv import load_dotenv
from retrievalFunction import retrievalFunction
from pymongo.mongo_client import MongoClient
from audioRecorder import listenAndRecord, deleteAudioFile
from csvLogger import CSVLogger, LogElements
from avatar_data import avatar_action_map, avatar_expression_map, avatar_voice
from pandas import *
from responseGenerator import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
    getTextfromAudio,
)
import pandas as pd
load_dotenv()

# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "Users"
# test cases 2,3 last
# 2 need 2 excel, 2q-irr, then 2q
# 3 need ask + modify mongodb + ask
COLLECTION_MEMORY_OBJECTS = "mytest" # change memory name
INPUT_FILENAME="evaluations/TestQuestion/3q.xlsx" # change route
BASE_RETRIEVAL_COUNT = 7  # change parameter
OBS_RETRIEVAL_COUNT = 7 # change parameter
FILENAME = "current_conversation.wav"


CSV_LOGGER = CSVLogger()


class AVATAR_DATA(Enum):
    AVATAR_EXPRESSION_MAP = "Avatar Expressions Map"
    AVATAR_ACTION_MAP = "Avatar Actions Map"
    AVATAR_VOICE = "Avatar Voice"


class CONVERSATION_MODE(Enum):
    TEXT = 1
    AUDIO = 2


# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]


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
    print("Please enter a relevant description about your character. Type done to complete the description \n")
    if "4q" in INPUT_FILENAME:
        description = '''
        1 Ava is a kind girl who is 27 years old, she doesn't love to help people
        2 Ava was born in a small town called Winterland. Winterland is a beautiful city with nice people.
        3 Ava loves a coffee shop called MorningStar in Winterland, she goes to MorningStar cafe once a week.
        4 Ava is living with her sister Avam. Avam is a master of education student at Winterland University.
        5 Ava is a writer who writes novels. She loves to sit in MorningStar and write new stories in her novels.
        6 Ava’s favourite novel is called Amazing Doctor. Ava’s favorite sport is basketball.
        7 Ava knows her neighbor Bob. They often meet at Newbrun St. They like to play basketball together on Sunday mornings.
        8 Ava’s birthday is April 8th.
        9 Ava loves coffee. Her favourite coffee is Latte. But she dislikes americano coffee.
        10 Ava has a cat called Lucy. Lucy is a 3-year-old Golden cat.
        '''
    else:
        description = '''
        1 Ava is a kind girl who is 25 years old, she loves to help people
        2 Ava was born in a small town called Brentwood. Brentwood is a beautiful town with delicious food.
        3 Ava loves a coffee shop called Soon cafe in Brentwood, she goes to Soon cafe twice a week.
        4 Ava is living with her sister Avam. Avam is a master of computer science student at Brentwood University.
        5 Ava is a writer who writes novels. She loves to sit in Soon cafe in Brentwood and write new stories in her novels.
        6 Ava’s favourite novel is called Gone with the wind. Ava’s favourite sport is jogging.
        7 Ava knows her neighbor Bob. They often meet at the Brentwood Library. They like to play tennis together on Sunday mornings.
        8 Ava’s birthday is June 8th.
        9 Ava loves coffee. Her favourite coffee is cappuccino, but she dislikes americano coffee.
        10 Ava has a cat called Lucy. Lucy is a 3-year-old male Bengal cat.
        '''
    # while True:
    #     currLine = input(
    #         "Please enter a relevant description about your character. Type done to complete the description \n"
    #     )
    #     if currLine.lower() == "done":
    #         break
    #     description += f"{currLine}\n"
    print(description)
    return description


def startConversation(userName, currMode, questionList):
    global pastObservations
    print("Define the username you are acting as: ")
    # conversationalUser = input("Define the username you are acting as: ")
    conversationalUser="Tony"
    baseObservation = fetchBaseDescription(userName)
    pastObservations = fetchPastRecords(userName)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()
    count=0

    while True:
        if currMode == CONVERSATION_MODE.TEXT.value:
            start = time.perf_counter()
            currentConversation = questionList[count]

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
            BASE_RETRIEVAL_COUNT,
            isBaseDescription=True,
        )
        observationRetrieval = retrievalFunction(
            currentConversation,
            pastObservations,
            OBS_RETRIEVAL_COUNT,
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
            avatar_expressions,
            avatar_actions,
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

        if count<len(questionList)-1:
            count+=1
        else:
            break
    
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
        # currMode = input("Please select the following :\n1. Text Mode\n2. Audio Mode\n")
        currMode="1"
        if currMode == "1":
            return CONVERSATION_MODE.TEXT.value
        elif currMode == "2":
            return CONVERSATION_MODE.AUDIO.value
        else:
            print("Invalid input, please select appropriate options")


if __name__ == "__main__":
    pastObservations = deque()
    df = pd.read_excel(INPUT_FILENAME)
    questionList = df['Questions']

    # for value in column_data:
    #     print(value)

    # Get username.
    # userName = input("Please enter the username of character: ")
    print("Please enter a relevant description about your character. Type done to complete the description \n")
    userName = "Ava"

    # Check for existing user.
    existingUser = userCollection.find_one({"Username": userName})
    existingInCOLLECTION=memoryObjectCollection.find_one({"Username": userName})
    if existingUser:
        if existingInCOLLECTION:
            print(f"Welcome back! {userName} \nContinue where you left off")
            avatar_expression_map = existingUser[AVATAR_DATA.AVATAR_EXPRESSION_MAP.value]
            avatar_action_map = existingUser[AVATAR_DATA.AVATAR_ACTION_MAP.value]
            avatar_voice = existingUser[AVATAR_DATA.AVATAR_VOICE.value]
            avatar_expressions = list(avatar_expression_map.keys())
            avatar_actions = list(avatar_action_map.keys())

        else:
            # Collect the description details.
            description = getBaseDescription()

            # Insert the userData to the Users collection.
            userData = {
                "Username": userName,
                "Description": description,
                "Avatar Expressions Map": avatar_expression_map,
                "Avatar Actions Map": avatar_action_map,
                "Avatar Voice": avatar_voice,
            }
            startTime = time.time()
            observationList = generateInitialObservations(userName, description).split("\n")
            endTime = time.time()
            print(
                f"Time taken for the observation generation by GPT : {endTime - startTime:.2f} "
            )

            # Generate the memory object data and push it to the memory objects collection.
            updateBaseDescription(userName, observationList)
            print("User created successfully!")
            print(f"Welcome back! {userName} \nContinue where you left off")
            avatar_expressions = list(avatar_expression_map.keys())
            avatar_actions = list(avatar_action_map.keys())
    else:
        # Collect the description details.
        description = getBaseDescription()

        # Insert the userData to the Users collection.
        userData = {
            "Username": userName,
            "Description": description,
            "Avatar Expressions Map": avatar_expression_map,
            "Avatar Actions Map": avatar_action_map,
            "Avatar Voice": avatar_voice,
        }
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
        print(f"Welcome back! {userName} \nContinue where you left off")
        avatar_expressions = list(avatar_expression_map.keys())
        avatar_actions = list(avatar_action_map.keys())
    currMode = setConversationMode()
    startConversation(userName, currMode, questionList)
    client.close()
