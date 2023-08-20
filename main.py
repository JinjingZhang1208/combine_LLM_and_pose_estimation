from google.cloud import speech
import sounddevice as sd
import numpy as np
import os
from numpy_ringbuffer import RingBuffer
import time
import openai
import json
import simple_client
import argparse
from collections import deque
import sys
import re
from pythonosc import osc_bundle_builder, osc_message_builder, udp_client
import openai
import json
import simple_client
import argparse
import random
import time

sys.path.append('../python-osc/')
print(sd.query_devices())
# OpenAI API key and Google Cloud credentials setup
openai.api_key = '*'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '*.json'
print("OpenAI API and Google Cloud setup completed.")
# Constants for audio setup
DURATION = 8
SAMPLE_RATE = 44100
CHANNELS = 2
DEVICE = 35
BUFFER_SIZE = 10
BUFFER = RingBuffer(capacity=BUFFER_SIZE * SAMPLE_RATE * CHANNELS)
print("Audio constants initialized.")
# Deque setup for dialogs
MAX_DIALOG_HISTORY = 3
dialogs = deque(maxlen=MAX_DIALOG_HISTORY)
answers = deque(['...'] * MAX_DIALOG_HISTORY, maxlen=MAX_DIALOG_HISTORY)

print("Deque for dialog history setup.")

def callback(indata, frames, time, status):
    if status:
        print(status)
    BUFFER.extend(indata.flatten())


def stereo_to_mono(data_array):
    return np.mean(data_array.reshape((-1, CHANNELS)), axis=1)


def update_dialogs(new_transcript):
    dialogs.append(new_transcript)
    answers.append("...")

    data = {
        "Observation": "Standing",
        "Hearing": "...",
        "Past Memory": "He is a very hard working person.",
    }

    for idx, (dialog, answer) in enumerate(zip(dialogs, answers), start=1):
        data[f"Dialog {idx}"] = dialog
        data[f"Answer{idx}"] = answer

    return data


def generate_prompt(data):
    """
    Generate a JSON string from the given data.
    :param data: The data to generate the JSON string from.
    :return: The generated JSON string.
    """
    # Create a dictionary that represents the JSON structure
    prompt = {
        "context": "You are a helpful assistant in VRChat. Your name is Clarla. Your goal is to guide me in having friendly conversations with others and become a real psychotherapist in the VR world.",
        "information": {
            "dialog": "\n".join([f"{k}: {v}" for k, v in data.items() if "Dialog" in k or "Answer" in k]),
            "observation": data["Observation"],
            "hearing": data["Hearing"],
            "past_memory": data["Past Memory"],
        },
        "criteria": [
            "Act as a mentor and guide me to the next response message based on the current information.",
            "I can perform one of four tasks: Speaking, Moving-WASD, Control look direction-left,right.",
            "The task should be appropriate for the current situation and conversation.",
            "Dont repeat the example. Create new content."
            # Add the rest of the criteria here
        ],
        "response_format": "RESPONSE FORMAT: Reasoning: (Explain your reasoning here). Task: (Specify the task here). Content: (Specify the content here).",
        "example": {
            "Reasoning": "Based on the current conversation, it seems appropriate to continue the dialogue.",
            "Task": "Speaking",
            "Content": "*"
        }
    }

    # Convert the dictionary to a JSON string
    json_prompt = json.dumps(prompt, indent=4)

    return json_prompt
def extract_data_from_response(response_content):
    # Define the regular expressions
    reasoning_regex = r'"Reasoning": "(.*?)"'
    task_regex = r'"Task": "(.*?)"'
    content_regex = r'"Content": "(.*?)"'

    # Use the regular expressions to find the Reasoning, Task, and Content
    reasoning = re.search(reasoning_regex, response_content)
    task = re.search(task_regex, response_content)
    content = re.search(content_regex, response_content)

    # Extract the matched groups
    reasoning = reasoning.group(1) if reasoning else ""
    task = task.group(1) if task else ""
    content = content.group(1) if content else ""

    return reasoning, task, content

# ... The rest of your code to initialize the microphone and listen to audio ...
# Open the stream
stream = sd.InputStream(callback=callback, channels=CHANNELS, samplerate=SAMPLE_RATE, device=DEVICE)
stream.start()
print("Audio stream started.")
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
args = parser.parse_args()

vrc_client = udp_client.SimpleUDPClient(args.ip, args.port)
value=1
strr = "*thinking*"
retry="Could you speak that again? The music sound is too loud:("
try:
    while True:
        time.sleep(DURATION)
        print("Processing audio data...")
        data_array = np.array(BUFFER)
        mono_array = stereo_to_mono(data_array)
        audio_data = (mono_array * 32767).astype(np.int16).tobytes()
        client = speech.SpeechClient()

        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-US",
        )
        request = speech.RecognizeRequest(config=config, audio=audio)
        print("Sending data to Google Speech-to-Text API...")
        response = client.recognize(request=request)
        if not response.results:
            simple_client.actionChatbox(vrc_client, retry)
            print("No transcription results returned from Google Speech-to-Text.")

        else:
            print("------------------------")
            print(response.results)
            print("------------------------")
            result=response.results[0]
            transcript = result.alternatives[0].transcript
            valid_response_received = False
            print("********"+f"Transcript: {transcript}")
            simple_client.actionChatbox(vrc_client, strr)
            # Update dialogs and send the new prompt to OpenAI API
            print("Updating dialogs...")
            data = update_dialogs(transcript)

            while not valid_response_received:
                print("Generating prompt for OpenAI...")
                json_prompt = generate_prompt(data)
                print(json_prompt)

                print("Sending prompt to OpenAI GPT-3.5...")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": json_prompt},
                    ],
                    temperature=0.8,
                    max_tokens=300
                )

                print("Received response from OpenAI GPT-3.5.")
                response_content = response['choices'][0]['message']['content']

                reasoning, task, content = extract_data_from_response(response_content)
                if reasoning and task and content:
                    valid_response_received = True
                else:
                    print("Invalid response received, retrying...")

            if task == "Speaking":
                simple_client.actionChatbox(vrc_client, content)
                answers[-1] = content




except KeyboardInterrupt:
    print("Recording stopped by user")

# Make sure to stop the stream at the end
stream.stop()
stream.close()
print("Audio stream closed.")
