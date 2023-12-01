import time
import os
import datetime
import asyncio
import controlexpression
import auto_correct_model
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dotenv import load_dotenv
from retrievalFunction import retrievalFunction
from pymongo.mongo_client import MongoClient
from audioRecorder import listenAndRecord, deleteAudioFile, listenAndRecordDirect
from responseGenerator import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
    getTextfromAudio,
)
import VRC_OSCLib
import argparse
from pythonosc import udp_client
from csvLogger import CSVLogger, LogElements
import easyocr1
import threading
from TTS import silero
from TTS import polly
from TTS import openaiTTS
import pyaudio
# Define list of expressions and actions for GPT and allow it to pick one

load_dotenv()
# test avatar list
Avatar_list=["Clarla","Sakura0319","chmx2023"]
# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "Users"
COLLECTION_MEMORY_OBJECTS = "TestMemory"
# Basic objects for the Database.
client= MongoClient(DATABASE_URL)
LLMdatabase= client[DATABASE_NAME]
userCollection= LLMdatabase[COLLECTION_USERS]
memoryObjectCollection=LLMdatabase[COLLECTION_MEMORY_OBJECTS]

RETRIEVAL_COUNT = 5
FILENAME = "current_conversation.wav"
CSV_LOGGER = CSVLogger()

#client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
args = parser.parse_args()
VRCclient = udp_client.SimpleUDPClient(args.ip, args.port)

# global CURRENT_FRAME
# # Initialize PyAudio
# p = pyaudio.PyAudio()
#
# # Open a stream for output
# stream = p.open(format=pyaudio.paFloat32,
#                 channels=2,
#                 rate=24100,
#                 output=True,
#                 output_device_index=8)

class CONVERSATION_MODE(Enum):
    TEXT = 1
    AUDIO = 2

class INPUTUSERNAME_MODE(Enum):
    INPUT = 1
    AUTODETECT = 2
# Basic objects for the Database.

# TTS class
# tts = silero.Silero()
# tts = polly.Polly()
# Create a deque with a max size of 5
def add_to_queue(ocr_queue,ocr_text):
    ocr_queue.append(ocr_text)

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


def startConversation(userName, currMode, usernameMode):
    global pastObservations
    if usernameMode ==INPUTUSERNAME_MODE.INPUT.value:
        conversationalUser = input("Define the username you are acting as: ")
    elif usernameMode ==INPUTUSERNAME_MODE.AUTODETECT.value:
        while(1):
            print("Detecting User Name...\n")
            OCRtext = easyocr1.run_image_processing("VRChat", ["en"])
            correct = input(
                f"Detected UserName--{OCRtext}\nPlease select the following :\n1. Yes\n2. No\n "
            )
            if correct=="1":
                conversationalUser=OCRtext
                break
    baseObservation = fetchBaseDescription(userName)
    pastObservations = fetchPastRecords(userName)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()
    # ocr_queue = deque(maxlen=3)
    # multi-thread actives idle movement
    # thread = threading.Thread(target=controlexpression.generate_random_action, args=(VRCclient,))
    # thread.start()
    while True:
        # thread = threading.Thread(target=controlexpression.generate_random_action(VRCclient))
        # thread.start()
        # controlexpression.generate_random_action(VRCclient)
        if currMode == CONVERSATION_MODE.TEXT.value:
            start = time.perf_counter()
            currentConversation = input(
                f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
            )
            end = time.perf_counter()
            text_input_time = round(end - start, 2)
            CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, text_input_time)
            CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, 0)
            # ocr_queue.clear()  # Clear the queue for each iteration
            # while (1):
            #     OCRtext = easyocr1.run_image_processing("VRChat", ["en"])
            #
            #     print(ocr_queue)
            #     if OCRtext not in ocr_queue and OCRtext not in Avatar_list:
            #         add_to_queue(ocr_queue, OCRtext)
            #     if len(ocr_queue) == 1 and OCRtext in ocr_queue:
            #         break
            #     if len(ocr_queue) == 2:
            #         break
            #
            # currentConversation = max(ocr_queue, key=len)
            # print("Recognize content:" + currentConversation)
        else:
            # start = time.perf_counter()
            start = time.perf_counter()
            transcribeText=listenAndRecordDirect(CSV_LOGGER)
            print(transcribeText)
            # end = time.perf_counter()
            # audio_record_time = round(end - start, 2)
            # CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, audio_record_time)

            currentConversation=transcribeText
            end = time.perf_counter()
            audio_to_text_time = round(end - start, 2)
            CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, audio_to_text_time)
            CSV_LOGGER.set_enum(LogElements.MESSAGE, currentConversation)
            print(currentConversation)

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
        CSV_LOGGER.write_to_csv(True)
        print(resultConversationString)
        print(
            f"Time taken for the conversation generation by GPT : {npc_response_time}"
        )
        emotions = controlexpression.extract_emotions(resultConversationString)
        result = controlexpression.remove_emotions_from_string(resultConversationString)
        print(emotions)
        print(result)
        print()
        # audio, sample_rate = tts.tts(result)
        # tts.speech(result, "Joanna", 9)
        #texttospeech time
        starttime = time.perf_counter()
        openaiTTS.generateAudio(result, 9)
        VRC_OSCLib.actionChatbox(VRCclient, result)
        endtime = time.perf_counter()
        retrieval_time2 = round(endtime - starttime, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_TTS, retrieval_time2)
        starttime = time.perf_counter()
        VRC_OSCLib.send_expression_command(emotions)
        endtime = time.perf_counter()
        retrieval_time1 = round(endtime - starttime , 2)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_CONTROLEXP, retrieval_time1)
        # audio=silero.audio_processing(audio)
        # silero.addToStream(stream,speech)
        # VRC_OSCLib.send_expression_command(emotions)
        deleteAudioFile(FILENAME)
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
    startTime = time.time()
    observationList = generateObservations(
        userName, conversationalUser, currentConversation, resultConversationString
    )
    observationList = observationList.split("\n")
    finalObservations = []
    for observation in observationList:
        if len(observation) > 0:
            finalObservations.append(observation)

    endTime = time.time()
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
    NameMode = input("Please select one the following ways of detecting User Name:\n1. Manually Input\n2. Auto detect\n")
    if NameMode == "1":
        currMode = setConversationMode()
        startConversation(userName, currMode,1)
    elif NameMode == "2":
        currMode = setConversationMode()
        startConversation(userName, currMode,2)
    else:
        print("Invalid input, please select appropriate options")

    client.close()
