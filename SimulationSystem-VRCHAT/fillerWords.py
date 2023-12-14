import soundfile
from pydub import AudioSegment
from openai import OpenAI
import os
from dotenv import load_dotenv
import threading
import sounddevice
event = threading.Event()

fillers = {
    "filler1": "emm...as you know...I would say",
    "filler2": "um...let me think...Interesting",
    "filler3": "I mean...Actually...",
    "filler4": "Well, sort of... its like...",
    "filler5": "Actually, that's quite a complex topic. Hmm...",
    "filler6": "So, let's dive into this. Uh, where to begin...",
    "filler7": "Interesting... Let me ponder that for a second...",
    "filler8": "Ah, I need to consider this carefully...",
    "filler9": "Hmm, let me think about that for a moment..."
}
fillersQ = {
    "fillerQ1": "Well, that's an interesting question, you see...",
    "fillerQ2": "You know, that's a really good question. Let's see..."
}

def generateAudio(text, filler):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format="mp3",
    )
    response.stream_to_file("TTS/fillerWord/"+filler+".mp3")
    AudioSegment.from_file("TTS/fillerWord/"+filler+".mp3").export("TTS/fillerWord/"+filler+".ogg", format="ogg")
    if os.path.exists("TTS/fillerWord/"+filler+".mp3"):
        os.remove("TTS/fillerWord/"+filler+".mp3")
        print(".mp3 file deleted")

load_dotenv()
API_KEY = os.environ.get("API_KEY")
client = OpenAI()
CURRENT_FRAME = 0

response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input="Hello world! This is a streaming test.",
    response_format="mp3",
)

# # Iterate over each item in the dictionary
# for key, value in fillers.items():
#     # Here 'key' is the filler identifier (like 'filler1', 'filler2', etc.)
#     # and 'value' is the corresponding filler text.
#     generateAudio(value, key)
#     print(f"{key}: {value}")
# for key, value in fillersQ.items():
#     # Here 'key' is the filler identifier (like 'filler1', 'filler2', etc.)
#     # and 'value' is the corresponding filler text.
#     generateAudio(value, key)
#     print(f"{key}: {value}")