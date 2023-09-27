import openai
import json
import simple_client
import argparse
import random
import time
import sys


sys.path.append('../python-osc/')
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder

from pythonosc import osc_message_builder
from pythonosc import udp_client

def generate_prompt(data):
    """
    Generate a JSON string from the given data.
    :param data: The data to generate the JSON string from.
    :return: The generated JSON string.
    """
    # Create a dictionary that represents the JSON structure
    prompt = {
        "context": "You are a helpful assistant in VRChat. Your goal is to guide me in having friendly conversations with others and become a real psychotherapist in the VR world.",
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
            # Add the rest of the criteria here
        ],
        "response_format": "RESPONSE FORMAT: Reasoning: (Explain your reasoning here). Task: (Specify the task here). Content: (Specify the content here).",
        "example": {
            "Reasoning": "Based on the current conversation, it seems appropriate to continue the dialogue.",
            "Task": "Speaking",
            "Content": "What subjects are you studying in school?"
        }
    }

    # Convert the dictionary to a JSON string
    json_prompt = json.dumps(prompt, indent=4)

    return json_prompt

    # Convert the dictionary to a JSON string
    json_prompt = json.dumps(prompt, indent=4)

    return json_prompt

# Example usage:
data = {
    "Dialog 1": "How are you?",
    "Answer1": "Good. And you?",
    "Dialog 2": "Not bad. I'm so busy those days.",
    "Answer2": "What are you doing?",
    "Dialog 3": "real life stuff you know like exams in school",
    "Answer3": "...",
    "Observation": "Standing",
    "Hearing": "...",
    "Past Memory": "He is a very hard working person.",
}

json_prompt = generate_prompt(data)
print(json_prompt)
print("---------------------------------------------------")
response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": json_prompt},
    ]
    ,
    temperature=0.8,
  max_tokens=300
)

print(response)
import re

response_content = response['choices'][0]['message']['content']

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

print(f"Reasoning: {reasoning}")
print(f"Task: {task}")
print(f"Content: {content}")


parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
args = parser.parse_args()

client = udp_client.SimpleUDPClient(args.ip, args.port)
value=1
for x in range(10):
    time.sleep(2)

        # client.send_message("/input/Jump", 1)
        # # 1 control chatbox typing

    strr="I Love you"
    if task=="Speaking":
        simple_client.actionChatbox(client, content)





