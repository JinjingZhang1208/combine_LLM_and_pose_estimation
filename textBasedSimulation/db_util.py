import datetime
from pymongo.mongo_client import MongoClient
import os
from dotenv import load_dotenv
from collections import deque

load_dotenv()


# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "NPC Avatars"
COLLECTION_MEMORY_OBJECTS = "reflectionTest1"

MAX_DEQUE_LENGTH = 50

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
    if len(pastObservations) > MAX_DEQUE_LENGTH:
        pastObservations.pop()
    pastObservations.appendleft(memoryObjectData)