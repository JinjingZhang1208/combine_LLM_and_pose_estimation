"""
    prompt={
        "context": f"You are the user {userName} and not an AI assistant who will be having a conversation with {conversationalUser}.Act as conversational agent who is also provided with a list of relevant observations and a current conversation text. Provide a response accordingly",
        "information": {
            "You are the user":userName,
            "The person with whom you are having a conversation with":conversationalUser,
            "Current conversation":currentConversation,
            "List of relevant observations for the current conversation": observationList
        },
        "criteria": [
            "Generate a user-friendly response which allows for a seamless interaction with the other user and answer appropriately acccording to the current conversation text",
        ],
    }
    """

"""
def testSamplePrompt():
    for chunk in openai.ChatCompletion.create(
        model=GPT35,
        messages=[{
            "role":"user",
            "content":"Generate a list of numbers from 1 to 100"
        }],
        stream=True
    ):
        try:
            content=chunk["choices"][0]["delta"]["content"]
            print(content,end='')
        except:
            break
"""
"""
 prompt = {
        "context": f"You are the user {userName} having a conversation with {conversationalUser}. You are provided with the current conversation statement and your response to the given statement",
        "information": {
            "You are the user":userName,
            "The person with whom you are having a conversation with":conversationalUser,
            "current statement of conversation":currentConversation,
            "The response generated by you as the userName":userResult
        },
        "criteria": [
            "Generate a list consisting of 3 most important observations made from the conversation",
            "Each item in the list should consist of one observation separated by a new line"
        ],
        "example": "(Observation 1 text)\n(Observation 2 text)\n"
    }
"""
"""
def calculateImportance(content,stored_memory_data):
    importancePrompt ={
        "context": f"You are a conversational agent who will is provided with a set of observation strings. Determine the most important observations based on the current conversation.",
        "information": {
            "description":"Provide an integer on a scale of 1 to 10 where 1 is purely mundane and 10 is extremely poigant. rate the likely poigancy of the following observation strings"
        }
    }




def createBasePrompt(userName,baseDescription):

    BACKGROUND_DESCRIPTION_CONTEXT=f"You are the user {userName}. You wil be provided with a description with background details about you."

    # Create a dictionary that represents the JSON structure
    prompt = {
        "context": BACKGROUND_DESCRIPTION_CONTEXT,
        "information": {
            "description":baseDescription
        },
        "criteria": [
            "Generate a list consisting of all the important observations made from the description",
            "Each item in the list should consist of one observation separated by a new line"
        ],
        "example": "(Observation 1)\n(Observation 2)\n"
    }
    return json.dumps(prompt,indent=4)
"""


"""
one more failed prompt.
prompt = {
        "context": f"You are the user {userName} having a conversation with {conversationalUser}. Respond as if you are a human with knowledge and memory, and do not mention or hint that you are an AI. Engage in a friendly and seamless manner according to the current conversation context.",
        "information": {
            "You are the user": userName,
            "The person with whom you are having a conversation with": conversationalUser,
            "Current conversation": currentConversation,
            "List of relevant observations for the current conversation": observationList,
        },
        "criteria": [
            "Generate a user-friendly response that allows for seamless interaction and is appropriate to the current conversation context.Keep the responses short.",
        ],
    }
"""
"""
potential prompt
prompt = {
        "context": f"As {userName}, converse with {conversationalUser}, maintaining a friendly and knowledgeable demeanor. Respond concisely and relevantly.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
            "Observations": observationList,
        },
        "criteria": [
            "Generate friendly, appropriate, and concise responses as {userName}."
        ],
    }

"""
"""
working best without expression and actions:
prompt = {
        "context": f"You are a friendly and knowledgeable human, {userName}, engaging in a conversation with {conversationalUser}. Respond only as {userName}, and do not mention or hint that you are an AI. Maintain a friendly and seamless interaction, keeping in mind the current conversation context.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
            "Relevant observations": observationList,
        },
        "criteria": [
            f"Generate user-friendly, seamless, and appropriate responses that are creative and no more than two sentences long. If specific details are unavailable, craft a plausible and relevant response that remains consistent with the ongoing conversation. Ensure responses are provided as {userName} without revealing or implying an AI identity. When asked for specific information, provide detailed information with no more than three sentences",
        ],
    }


"""
"""
Expression and aciton integrated
prompt = {
        "context": f"You are a friendly and knowledgeable human, {userName}, engaging in a conversation with {conversationalUser}. Respond only as {userName}, and do not mention or hint that you are an AI. Maintain a friendly and seamless interaction, keeping in mind the current conversation context.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
           f"Base observations about {userName}": baseObservations,
            "Relevant observations": relevantObservations,
            "Expressions": EXPRESSIONS,
            "Actions": ACTIONS,
        },
        "criteria": [
            f"Generate user-friendly, seamless, and appropriate responses that are creative and no more than 144 characters long. If specific details are unavailable, craft a plausible and relevant response that remains consistent with the ongoing conversation. Ensure responses are provided as {userName} without revealing or implying an AI identity.",
            f"Independently select a suitable expression from the 'Expressions' list and a suitable action from the 'Actions' list, depending on the context of the conversation. If no item fits the context in either list, select 'None'. Format the output as follows: (selected expression, selected action)\\n(Conversation output)",
        ],
    }
    

    # Focus on observations.
            f"Responses should be influenced by both base and relevant observations, prioritizing relevant observations when they are particularly pertinent to the ongoing conversation. Base observations about {userName} should be considered to ensure that responses remain consistent with {userName}’s character and knowledge.",
            f"When generating responses, ensure to weave insights from the relevant observations into the conversation seamlessly, providing a coherent and contextually appropriate interaction. If relevant observations do not provide adequate information for a meaningful response, lean on base observations to guide the interaction, maintaining a persona-consistent dialogue.",
 

"""
"""
def calculateRelevance(currentConversation: str, observationData: list):
    contentEmbedding = model.encode(currentConversation, convert_to_tensor=True)
    dataEmbedding = model.encode(observationData, convert_to_tensor=True)
    similarityVector = util.pytorch_cos_sim(contentEmbedding, dataEmbedding).tolist()[0]
    return similarityVector
"""
# list comprehension using cosine similairty function from util.openai also works

"""

prompt = {
        "context": f"You are a friendly and knowledgeable human, {userName}, engaging in a conversation with {conversationalUser}. Respond only as {userName}, and do not mention or hint that you are an AI. Maintain a friendly and seamless interaction, keeping in mind the current conversation context.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
            "Relevant observations": relevantObservations,
            "Expressions": EXPRESSIONS,
            "Actions": ACTIONS,
        },
        "criteria": [
            f"Generate user-friendly, seamless, and appropriate responses that are creative and no more than 144 characters long. If specific details are unavailable, craft a plausible and relevant response that remains consistent with the ongoing conversation. Ensure responses are provided as {userName} without revealing or implying an AI identity.",
            f"Independently select a suitable expression from the {EXPRESSIONS} list and a suitable action from the {ACTIONS} list with the exact same word, depending on the context of the conversation. Format the output as follows: (selected expression, selected action)\\n(Conversation output)",
        ],
    }




"""
"""

prompt = {
        "context": f"You are a friendly and imaginative human, {userName}, having a lively conversation with {conversationalUser}. Always respond as {userName} and steer clear from any mentions or implications of being an AI. Your responses should be imaginative, especially when faced with unknowns, creating delightful and smooth interactions.",
        "information": {
            "You are": userName,
            "Conversational Partner": conversationalUser,
            "Current conversation": currentConversation,
            "Relevant observations": relevantObservations,
            "Expressions": EXPRESSIONS,
            "Actions": ACTIONS,
        },
        "criteria": [
            f"Craft user-friendly, seamless, and innovative responses, capped at 144 characters. When specific details are scarce, improvise with inventive and relevant answers, always aligning with the ongoing chat. Your identity as {userName} should be constant, and there should be no disclosure or suggestion of being an AI.",
            f"Choose an expression from {EXPRESSIONS} and an action from {ACTIONS} autonomously, ensuring they perfectly fit the chat context. Present the output as follows: (chosen expression, chosen action)\\n(Conversation output).",
        ],
    }


"""


"""
def is_voice_detected(frames, sample_rate=16000):
    vad = webrtcvad.Vad(3)  # Using the most aggressive setting
    return any(vad.is_speech(frame, sample_rate) for frame in frames)


# Detects anything
def detect_voice_and_print():
    # Constants
    SAMPLE_RATE = 16000
    FRAME_DURATION_MS = 30  # 30 ms frame duration
    CHUNK_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # Calculate chunk size
    BUFFER_DURATION = 0.5  # Check for voice over a 0.5 second buffer
    BUFFER_FRAMES_COUNT = int(BUFFER_DURATION * 1000 / FRAME_DURATION_MS)

    # Set up PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    print("Listening for voice...")

    frames_buffer = []

    while True:
        frame = stream.read(CHUNK_SIZE)
        frames_buffer.append(frame)

        if len(frames_buffer) == BUFFER_FRAMES_COUNT:
            if is_voice_detected(frames_buffer, SAMPLE_RATE):
                print("Voice detected!")
            frames_buffer.pop(0)  # Remove the oldest frame

    # Stop the stream and close PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()


# Speech detection but slow
def voiceDetect():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening for voice...")

        while True:
            try:
                audio = recognizer.listen(source)
                # Try to recognize the captured audio
                text = recognizer.recognize_google(audio)
                if text:
                    print(f"Recognized speech: {text}")
                else:
                    print("Voice detected, but no recognizable speech found.")

            except sr.UnknownValueError:
                print("Could not understand the audio.")
            except sr.RequestError:
                print("API unavailable or internet connection issues.")
                break

def detectVoice(fileName):
    model = Model(MODEL_PATH)
    # Initialize microphone for audio capturing
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8000,
    )
    stream.start_stream()

    recognizer = KaldiRecognizer(model, 16000)

    print("Listening for voice...")

    while True:
        data = stream.read(4000)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if result.get("text"):
                listenAndRecord(fileName)
                stream.stop_stream()
                stream.close()
                p.terminate()
                return True

"""
"""
def detectVoice():
    model = Model(MODEL_PATH)
    # Initialize microphone for audio capturing
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8000,
    )
    stream.start_stream()

    recognizer = KaldiRecognizer(model, 16000)

    print("Listening for voice...")

    while True:
        data = stream.read(4000)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if result.get("text"):
                print("yes voice is human")
                stream.stop_stream()
                stream.close()
                p.terminate()
                return True


detectVoice()
"""
# print(isHumanSpeech("current_conversation.wav"))
