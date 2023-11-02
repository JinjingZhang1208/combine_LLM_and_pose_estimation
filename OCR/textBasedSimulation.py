import time
import os
from dotenv import load_dotenv
from retrievalFunction import retrievalFunction
import datetime
from pymongo.mongo_client import MongoClient
from responseGenerator import generateInitialObservations,generateObservations,generateConversation
import sys
# Add the path of the 'b' folder to sys.path
import easyocr1
import VRC_OSCLib
from collections import deque
import time

DATABASE_URL="mongodb+srv://abdulaziz:5k9406K7@llmcluster.slofevi.mongodb.net/?retryWrites=true&w=majority";
load_dotenv()
# Constants
DATABASE_NAME='LLMDatabase'
DATABASE_URL=os.environ.get('DATABASE_URL') 
COLLECTION_USERS='Users'
COLLECTION_MEMORY_OBJECTS='MemoryObjects'

# Basic objects for the Database.
client= MongoClient(DATABASE_URL)
LLMdatabase= client[DATABASE_NAME]
userCollection= LLMdatabase[COLLECTION_USERS]
memoryObjectCollection=LLMdatabase[COLLECTION_MEMORY_OBJECTS]
x = memoryObjectCollection.find_one()
print(x)
def custom_print(*args, **kwargs):
    # Print to console
    print(*args, **kwargs)

    # Write to log file
    with open("output.log", "a") as log_file:
        print(*args, file=log_file, **kwargs)

def fetchPastRecords(userName,memoryObjectCollection):
    fetchQuery= {
    '$or': [
        {'Username': userName},
        {'Conversation with User': userName}
    ]
    }
    return list(memoryObjectCollection.find(fetchQuery).limit(10))

def updateMemoryCollection(userName,conversationalUser,observationList):
    # Get the current time.
    currTime=datetime.datetime.now()
    formattedTime=currTime.strftime("%Y-%m-%d %H:%M:%S")
    # Update the memoryObjects collection.
    memoryObjectData={
        "Username":userName,
        "Conversation with User": conversationalUser,
        "Creation Time":formattedTime,
        "Recent Access Time":formattedTime,
        "Observations":observationList
    }
    memoryObjectCollection.insert_one(memoryObjectData)

def getBaseDescription():
    description=""
    while True:
        currLine=input("Please enter a relevant description about your character. Type done to complete the description \n")
        if currLine.lower()=="done":
            break
        description+=f"{currLine}\n"
    return description

def startConversation(userName):

    conversationalUser=input("Define the username you are having a conversation with : ")
    while True:
        # currentConversation=input(f"Talk with {userName}, You are {conversationalUser}. Have a discussion! ")
        currentConversation= easyocr1.run_image_processing("VRChat",["en"])
        if currentConversation.lower()=="done":
            break
        pastObservations=fetchPastRecords(userName,memoryObjectCollection)
        # Delete and add 1 latest record.

        retreivalResults=retrievalFunction(currentConversation,pastObservations)
        startTime=time.time()
        finalStatement=generateConversation(userName,conversationalUser,currentConversation,[ data['observationText'] for data in retreivalResults])
        endTime=time.time()
        custom_print(f"Time taken for the conversation generation by GPT : {endTime-startTime:.2f}")
        custom_print(f"{userName} : {finalStatement}")
        VRC_OSCLib._direct_osc_send(data=finalStatement)
        emo=VRC_OSCLib.find_expression(finalStatement)
        print(emo)
        VRC_OSCLib.send_expression_command(emo)

        # Time the function call and fetch the results.
        startTime=time.time()
        observationList=generateObservations(userName,conversationalUser,currentConversation,finalStatement).split('\n')
        observationList=[observation.strip() for observation in observationList]
        endTime=time.time()
        custom_print(f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} ")

        updateMemoryCollection(userName,conversationalUser,observationList)




# Get username.
userName=input("Please enter a username : ")

# Check for existing user.
existingUser=userCollection.find_one({"Username":userName})

if existingUser:
    custom_print(f"Welcome back! {userName} \nContinue where you left off")
    startConversation(userName)

    """
    iterate through each record and add three new scores normalized.
    Evaluate the importance of each set of observations based on the given info 
    And calculate the most relevant one
    """
    """
    OR 
    pick the ones with highest relevance and based on that make a judgement for the remaining ones
    """
else:

    # Collect the description details.
    description=getBaseDescription()
    
    # Insert the userData to the Users collection.
    userData= {
        "Username": userName,
        "Description":description
    }
    userCollection.insert_one(userData)


    # Time the function call and fetch the results.
    startTime=time.time()
    observationList=generateInitialObservations(userName,description).split('\n')
    endTime=time.time()
    custom_print(f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} ")

    # Generate the memory object data and push it to the memory objects collection.
    updateMemoryCollection(userName,"Base Description",observationList)
    custom_print("User created successfully!")
    startConversation(userName)


    client.close()

