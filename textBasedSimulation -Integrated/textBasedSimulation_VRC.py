import time
import os
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dotenv import load_dotenv
from retrievalFunction import retrievalFunction
from pymongo.mongo_client import MongoClient
from responseGenerator import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
)
import easyocr1
import VRC_OSCLib
import controlexpression
import argparse
from pythonosc import udp_client
# Define list of expressions and actions for GPT and allow it to pick one

load_dotenv()

# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "Users"
COLLECTION_MEMORY_OBJECTS = "TestMemory"
RETRIEVAL_COUNT = 5
Avatar_list=["Clarla","Sakura0319"]
# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]

#client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
args = parser.parse_args()
client = udp_client.SimpleUDPClient(args.ip, args.port)

ocr_queue = deque(maxlen=3)
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


def startConversation(userName):
    global pastObservations
    conversationalUser = input("Define the username you are acting as: ")
    baseObservation = fetchBaseDescription(userName)
    pastObservations = fetchPastRecords(userName)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()
    while True:
        ocr_queue.clear()  # Clear the queue for each iteration
        while(1):
            OCRtext = easyocr1.run_image_processing("VRChat", ["en"])

            print(ocr_queue)
            if OCRtext not in ocr_queue and OCRtext not in Avatar_list:
                add_to_queue(ocr_queue, OCRtext)
            if len(ocr_queue)==1 and OCRtext in ocr_queue:
                break
            if len(ocr_queue)==2:
                break

        currentConversation= max(ocr_queue, key=len)
        print("Recognize content:"+currentConversation)
        if currentConversation.lower() == "done":
            break
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
        startTime = time.time()
        conversationPrompt = generateConversation(
            userName,
            conversationalUser,
            currentConversation,
            [data[1] for data in baseRetrieval + observationRetrieval],
        )
        print(f"{userName} :")
        resultConversationString = ""
        for conversation in conversationPrompt:

            try:
                currText = conversation["choices"][0]["delta"]["content"]
                resultConversationString += currText
                print(currText, end="")
            except:
                break
        print(resultConversationString)
        emotions = controlexpression.extract_emotions(resultConversationString)
        result=controlexpression.remove_emotions_from_string(resultConversationString)
        print(emotions)
        print(result)
        print()
        VRC_OSCLib.actionChatbox(client, result)
        VRC_OSCLib.send_expression_command(emotions)
        endTime = time.time()
        print(
            f"Time taken for the conversation generation by GPT : {endTime-startTime:.2f}"
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
    time.sleep(10)
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

    startConversation(userName)
    client.close()