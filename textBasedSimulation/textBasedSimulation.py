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

load_dotenv()

# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "Users"
COLLECTION_MEMORY_OBJECTS = "MemoryObjects"

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
        memoryObjectCollection.find(fetchQuery).sort("_id", -1).limit(15), maxlen=15
    )


def updateBaseDescription(userName: str, observationList: list):
    # Get the current time.
    currTime = datetime.datetime.now()
    formattedTime = currTime.strftime("%Y-%m-%d %H:%M:%S")
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": "Base Description",
        "Creation Time": formattedTime,
        "Recent Access Time": formattedTime,
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
    currTime = datetime.datetime.now()
    formattedTime = currTime.strftime("%Y-%m-%d %H:%M:%S")
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": conversationalUser,
        "Creation Time": formattedTime,
        "Recent Access Time": formattedTime,
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
        currentConversation = input(
            f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
        )
        if currentConversation.lower() == "done":
            break
        retreivalResults = retrievalFunction(
            currentConversation, baseObservation + pastObservations
        )
        startTime = time.time()
        conversationPrompt = generateConversation(
            userName,
            conversationalUser,
            currentConversation,
            [data[1] for data in retreivalResults],
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
        print()
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
