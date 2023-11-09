
from openai import OpenAI
import os
from dotenv import load_dotenv
import threading
import sounddevice
import soundfile
from pydub import AudioSegment
event = threading.Event()


load_dotenv()
API_KEY = os.environ.get("API_KEY")
client = OpenAI()
CURRENT_FRAME = 0

response = client.audio.speech.create(
    model="tts-1",
    voice="shimmer",
    input="Hello world! This is a streaming test.",
    response_format="mp3",
)

def read_audio_file(filepath: str, output_device_index: int):
    """Read an audio file and plays it on the specified output device.

    Parameters
    ----------
    filepath : str
        The path to the audio file to be played.
    output_device_index : int
        The index of the output device to use.
    """

    def callback(data_out, frames, _, status):
        global CURRENT_FRAME
        if status:
            debug("status: ", status)
        chunk_size = min(len(data) - CURRENT_FRAME, frames)
        data_out[:chunk_size] = data[CURRENT_FRAME : CURRENT_FRAME + chunk_size]
        if chunk_size < frames:
            data_out[chunk_size:] = 0
            CURRENT_FRAME = 0
            raise sounddevice.CallbackStop()
        CURRENT_FRAME += chunk_size

    def stream_thread():
        with stream:
            event.wait()  # Wait until playback is finished
        event.clear()

    data, samplerate = soundfile.read(filepath, always_2d=True)
    # Creating a thread to play the audio file.
    try:
        stream = sounddevice.OutputStream(
            samplerate=samplerate,
            device=output_device_index,
            channels=data.shape[1],
            callback=callback,
            finished_callback=event.set,
        )
    except sounddevice.PortAudioError:
        return

    thread = threading.Thread(target=stream_thread)
    thread.start()

def generateAudio(text, device_index):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format="mp3",
    )
    response.stream_to_file("output.mp3")
    AudioSegment.from_file("output.mp3").export("example.ogg", format="ogg")
    read_audio_file("example.ogg", device_index)



# response.stream_to_file("output.mp3")
# AudioSegment.from_file("output.mp3").export("example.ogg", format="ogg")

