from enums import CONVERSATION_MODE, AGENT_MODE
import re


def is_question(message):
    question_keywords = ["what", "how", "where", "when", "why", "who", "?"]
    # Convert the message to lowercase for case-insensitive comparison
    message_lower = message.lower()
    for keyword in question_keywords:
        if keyword in message_lower:
            return True
    return False


def filter_conversation(conversation):
    # Remove text within parentheses
    filtered_result = re.sub(r'\([^()]*\)', '', conversation)
    # Remove newline characters
    filtered_result = filtered_result.replace('\n', '')
    return filtered_result


def setConversationMode():
    while True:
        currMode = input(
            "Please select the following :\n1. Text Mode\n2. Audio Mode\n")
        if currMode == "1":
            return CONVERSATION_MODE.TEXT.value
        elif currMode == "2":
            return CONVERSATION_MODE.AUDIO.value
        else:
            print("Invalid input, please select appropriate options")


def set_agent_mode():
    while True:
        user_input = input(
            "Select conversation mode:\n1. Normal Conversation\n2. Event Agent\n3. Research Agent\n4. Debate Agent\nEnter the corresponding number: ")
        if user_input == "1":
            return AGENT_MODE.NORMAL.value
        elif user_input == "2":
            return AGENT_MODE.EVENT.value
        elif user_input == "3":
            return AGENT_MODE.RESEARCH.value
        elif user_input == "4":
            return AGENT_MODE.DEBATE.value
        else:
            print("Invalid input, please enter a valid number.")