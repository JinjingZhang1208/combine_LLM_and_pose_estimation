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

from responseGenerator import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
    getTextfromAudio,
    generate_reflection,
)

from db_util import (
    fetchBaseDescription,
    fetchPastRecords,
    updateMemoryCollection,
    updateBaseDescription,
    update_reflection_db_and_past_obs,
    client,
    userCollection,
)


BASE_RETRIEVAL_COUNT = 3  # change parameter
OBS_RETRIEVAL_COUNT = 5 # change parameter
REFLECTION_RETRIEVAL_COUNT = 9
REFLECTION_PERIOD = 3

FILENAME = "current_conversation.wav"

CSV_LOGGER = CSVLogger()

event_publisher_base_description =  """
The Event Publisher is a dedicated agent whose mission is to accept and store events published by users. It serves as a central hub for all user-generated events, providing access to these events for any inquiring individuals.

When asked about a specific event, the Event Publisher will search its memory and share the relevant information. If the requested event is not in its memory, the Event Publisher will honestly admit that it does not know.

Above all, the Event Publisher is committed to providing accurate and reliable information. It strictly avoids hallucination, ensuring that all shared events are real and verifiable.
"""


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


def startConversation(userName, currMode,is_publish_event):
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
            currentConversation = input(
                f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
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

        baseRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=baseObservation,
            retrievalCount=BASE_RETRIEVAL_COUNT,
            isBaseDescription=True,
        )
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=OBS_RETRIEVAL_COUNT,
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
        eventLoop.run_in_executor(
            threadExecutor,
            generateObservationAndUpdateMemory,
            userName,
            conversationalUser,
            currentConversation,
            resultConversationString,
        )
        

        conversation_count += 1
        if conversation_count!=1 and conversation_count % REFLECTION_PERIOD == 0:
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

def publish_event_mode():
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
    print(f"is_publish_event: {is_publish_event}")
    pastObservations = deque()

    if not is_publish_event:
        npc_name = input("Please enter the username of character: ")
    else:
        npc_name = "Event Publisher"

    # Check for existing user.
    is_existing_npc = userCollection.find_one({"Username": npc_name})

    if is_existing_npc:
        print(f"Welcome back! {npc_name} \nContinue where you left off")
        avatar_expression_map = is_existing_npc[AVATAR_DATA.AVATAR_EXPRESSION_MAP.value]
        avatar_action_map = is_existing_npc[AVATAR_DATA.AVATAR_ACTION_MAP.value]
        avatar_voice = is_existing_npc[AVATAR_DATA.AVATAR_VOICE.value]
        avatar_expressions = list(avatar_expression_map.keys())
        avatar_actions = list(avatar_action_map.keys())

    else:
        if not is_publish_event:
            # Collect the description details.
            description = getBaseDescription()
        else: 
            description = event_publisher_base_description

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
