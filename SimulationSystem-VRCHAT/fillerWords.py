import soundfile
from pydub import AudioSegment
from openai import OpenAI
import os
from dotenv import load_dotenv
import threading
import sounddevice
event = threading.Event()
# General Fillers Dictionary
fillers = {
    "filler1": "emm...as you know...I would say",
    "filler2": "um...let me think...Interesting",
    "filler3": "I mean...Actually...",
    "filler4": "Well, sort of... its like...",
    "filler5": "Actually, that's quite a complex topic. Hmm...",
    "filler6": "So, let's dive into this. Uh, where to begin...",
    "filler7": "Interesting... Let me ponder that for a second...",
    "filler8": "Ah, I need to consider this carefully...",
    "filler9": "Hmm, let me think about that for a moment...",
    # "filler10": "Now, if I may... it's a bit complicated because...",
    # "filler11": "You see, it's not that straightforward. Let me explain...",
    # "filler12": "In a way, it's quite unique. So basically...",
    # "filler13": "Hmm, there are several aspects to consider here...",
    # "filler14": "It's not as simple as it seems. In fact...",
    # "filler15": "There's a bit more to it than you might think. For instance...",
    # "filler16": "It's a multi-faceted issue, really. To elaborate...",
    # "filler17": "One might say it's a complex situation. To put it simply...",
    # "filler18": "It's a bit of a conundrum, you see. Essentially...",
    # "filler19": "It's not black and white, as you can imagine. More like...",
    # "filler20": "There's more than meets the eye here. Specifically...",
    # "filler21": "It's a layered topic, indeed. Let's unwrap it...",
    # "filler22": "It's quite a puzzle, to be honest. To break it down...",
    # "filler23": "There's a lot to unpack here. Let's start with...",
    # "filler24": "It's a bit nuanced, you know. In particular...",
    # "filler25": "It's an intricate subject, to be sure. Broadly speaking...",
    # "filler26": "One could argue it's quite detailed. In a nutshell...",
    # "filler27": "There are various dimensions to it. For example...",
    # "filler28": "It's a rich topic, to say the least. In general terms...",
    # "filler29": "It's a deep well to explore. First off...",
    # "filler30": "There's a whole spectrum to consider. Mainly...",
    # "filler31": "It's a multifaceted puzzle. Let me piece it together...",
    # "filler32": "It's not cut and dried, of course. Primarily...",
    # "filler33": "It's a topic with many layers. At the core...",
    # "filler34": "It's a broad area to cover. Let's start with the basics...",
    # "filler35": "It's a bit complex, I must say. From one angle...",
    # "filler36": "There's a lot to say here. First and foremost...",
    # "filler37": "It's quite a dense topic. To distill it...",
    # "filler38": "There's a variety of factors involved. For starters...",
    # "filler39": "It's not straightforward, obviously. On the surface...",
    # "filler40": "It's a subject with depth. In essence...",
    # "filler41": "There are several nuances. To begin with...",
    # "filler42": "It's quite a detailed matter. At its heart...",
    # "filler43": "There's a range of perspectives. Looking at it from one side...",
    # "filler44": "It's a multifaceted issue. In the broader sense...",
    # "filler45": "There are multiple layers to it. To delve deeper...",
    # "filler46": "It's not just black and white. Essentially...",
    # "filler47": "There's a bit of complexity here. To simplify...",
    # "filler48": "It's a topic that needs unpacking. Let's dissect it...",
    # "filler49": "It's not a one-dimensional issue. On a fundamental level...",
    # "filler50": "There are various facets to consider. From this perspective...",
    # "filler51": "It's quite a vast topic. To condense it...",
    # "filler52": "There's more than one way to look at it. Primarily...",
    # "filler53": "It's an area with many aspects. To focus on one part...",
    # "filler54": "There's quite a bit to consider. At a basic level...",
    # "filler55": "It's not just a simple matter. In terms of specifics...",
    # "filler56": "There are different angles to this. To highlight one...",
    # "filler57": "It's an issue with depth. From a particular viewpoint...",
    # "filler58": "There's a lot beneath the surface. To start with the basics...",
    # "filler59": "It's a subject that's not easily defined. In broad strokes..."

}
# Question-Related Fillers Dictionary
fillersQ = {
    "fillerQ1": "Well, that's an interesting question, you see...",
    "fillerQ2": "You know, that's a really good question. Let's see...",
    "fillerQ3": "That's a thought-provoking question. To delve into it...",
    "fillerQ4": "Indeed, that's a significant query. To address it...",
    "fillerQ5": "That's a very insightful question. To tackle it head-on...",
    "fillerQ6": "You've asked a pivotal question. To get to the heart of it...",
    "fillerQ7": "That's a challenging question. To dissect it...",
    "fillerQ8": "You raise an important point. To delve into the details...",
    "fillerQ9": "That's a profound question, indeed. To explore it...",
    "fillerQ10": "You've touched on a key issue. To examine it closely...",
    "fillerQ11": "That's an intriguing question. To look at it from all angles...",
    "fillerQ12": "You've posed a complex question. To unwrap it...",
    "fillerQ13": "That's a critical question to consider. To break it down...",
    "fillerQ14": "You've asked a pivotal query. To get to the core of it...",
    "fillerQ15": "That's a substantial question. To analyze it...",
    "fillerQ16": "You pose a thought-provoking question. To dive deeper...",
    "fillerQ17": "That's a multifaceted question. To explore its depths...",
    "fillerQ18": "You've raised a vital point. To scrutinize it...",
    "fillerQ19": "That's a deep question, indeed. To look at it comprehensively...",
    "fillerQ20": "You've highlighted a crucial issue. To dissect its layers...",
    "fillerQ21": "That's a significant question to ponder. To examine its facets...",
    "fillerQ22": "You ask a compelling question. To navigate through it...",
    "fillerQ23": "That's a detailed question. To sift through the specifics...",
    "fillerQ24": "You've posed an intriguing query. To explore its nuances...",
    "fillerQ25": "That's a vital question to address. To analyze its components...",
    "fillerQ26": "You raise a fundamental issue. To look at it in depth..."
}
# Short Fillers Dictionary
fillersS = {
    "fillerS1": "umm...well...umm...",
    "fillerS2": "uhh...Okay...uhh..",
    "fillerS3": "erm...erm...alright..",
    "fillerS4": "So...hmm...hmm...",
    "fillerS5": "Hmm...Yes, well...",
    "fillerS6": "Ah...Indeed...Ah...",
    "fillerS7": "Right...Okay...So...",
    "fillerS8": "Well...Yes...Hmm...",
    "fillerS9": "Okay...Right...Well...",
    "fillerS10": "So...Ah...Indeed...",
    "fillerS11": "Yes...Hmm...Right...",
    "fillerS12": "Ah...So...Okay...",
    "fillerS13": "Well...Ah...Yes...",
    "fillerS14": "Okay...So...Hmm...",
    "fillerS15": "Hmm...Right...Ah...",
    "fillerS16": "Yes...So...Okay...",
    "fillerS17": "Right...Well...Ah...",
    "fillerS18": "Ah...Hmm...Yes...",
    "fillerS19": "So...Okay...Right...",
    "fillerS20": "Hmm...Ah...So...",
    "fillerS21": "Okay...Yes...Well...",
    "fillerS22": "Yes...Ah...So...",
    "fillerS23": "Right...Hmm...Okay...",
    "fillerS24": "Ah...Well...Yes...",
    "fillerS25": "So...Hmm...Right...",
    "fillerS26": "Hmm...Okay...Yes...",
    "fillerS27": "Yes...Right...Ah...",
    "fillerS28": "Well...So...Hmm...",
    "fillerS29": "Okay...Ah...Right...",
    "fillerS30": "Hmm...Yes...So...",
    "fillerS31": "Ah...Okay...Right...",
    "fillerS32": "Right...Yes...Ah...",
    "fillerS33": "Well...Hmm...Okay...",
    "fillerS34": "Okay...So...Yes...",
    "fillerS35": "So...Right...Ah...",
    "fillerS36": "Yes...Hmm...Okay...",
    "fillerS37": "Ah...So...Well...",
    "fillerS38": "Right...Okay...Yes...",
    "fillerS39": "Well...Ah...So...",
    "fillerS40": "Okay...Hmm...Right...",
    "fillerS41": "So...Yes...Ah...",
    "fillerS42": "Yes...Okay...Well...",
    "fillerS43": "Ah...Right...So...",
    "fillerS44": "Right...Well...Hmm...",
    "fillerS45": "Well...Okay...Ah...",
    "fillerS46": "Okay...So...Hmm...",
    "fillerS47": "So...Ah...Right...",
    "fillerS48": "Yes...Well...Okay...",
    "fillerS49": "Ah...Hmm...So...",
    "fillerS50": "Right...Ah...Yes..."
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

# # # Iterate over each item in the dictionary
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
# for key, value in fillersS.items():
#     # Here 'key' is the filler identifier (like 'filler1', 'filler2', etc.)
#     # and 'value' is the corresponding filler text.
#     generateAudio(value, key)
#     print(f"{key}: {value}")