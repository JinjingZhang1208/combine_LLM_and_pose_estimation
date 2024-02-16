import configparser
import contextlib
import importlib
import re
import threading
from os import getenv
from pathlib import Path
import numpy as np
import boto3
import botocore
import botocore.exceptions
import sounddevice
import soundfile
import numpy as np
import io
import time
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
import pyaudio
CURRENT_FRAME = 0
event = threading.Event()
playback_lock = threading.Lock()
load_dotenv()
import os
class Polly:
    """Use Amazon Polly API to synthesize a speech.

    This class can be used as speech_provider attribute for the VRCSpeechAssistant class.

    Attributes
    ----------
    AWS_CONFIG_FILE: Path
        Default location of Amazon AWS API config file.
    AWS_CREDENTIALS_FILE: Path
        Default location of Amazon AWS API credentials file.
    VOICES_PATH: Path
        The location of the voices files that will be generated.
    """

    AWS_CONFIG_FILE = Path.home() / ".aws" / "config"
    AWS_CREDENTIALS_FILE = Path.home() / ".aws" / "credentials"
    VOICES_PATH = Path(getenv("APPDATA")) / "VRChat LLM Avartars" / "voices"

    def __init__(self):
        """Initialize instance."""
        self.aws_config = configparser.ConfigParser()
        self.aws_credentials = configparser.ConfigParser()
        self._init_config()
        self.client = boto3.client("polly")
        # The first self.client.synthesize_speech called takes a little time to respond,
        # calling self.speech once before the user call it.
        self.speech("test", "Justin", 999)

    def _init_config(self):
        self._load_base_aws_config()
        if self.AWS_CONFIG_FILE.exists():
            self.aws_config.read(self.AWS_CONFIG_FILE)
        self.save_aws_config()
        self._load_base_aws_credentials()
        if self.AWS_CREDENTIALS_FILE.exists():
            self.aws_credentials.read(self.AWS_CREDENTIALS_FILE)
        self.save_aws_credentials()

    def _load_base_aws_config(self):
        self.aws_config["default"] = {"region": "us-west-2"}

    def _load_base_aws_credentials(self):
        self.aws_credentials["default"] = {
            "aws_access_key_id": "AKIAXHCQPAHUFWENZPUJ",
            "aws_secret_access_key": "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",
        }

    def save_aws_config(self):
        """Save aws configuration changes to the aws configuration file."""
        self.AWS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.aws_config.write(self.AWS_CONFIG_FILE.open("w", encoding="utf-8"))

    def save_aws_credentials(self):
        """Save aws credentials changes to the aws credentials file."""
        self.AWS_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.aws_credentials.write(self.AWS_CREDENTIALS_FILE.open("w", encoding="utf-8"))

    def speech(self, text: str, voice_id: str, output_device_index: int, extra_tags: dict = None):


        """Convert a text into a speech and then play it to the given output_device.

        Parameters
        ----------
        text : str
            The text to be converted to speech.
        voice_id : str
            The voice id of the voice you want to use.
        output_device_index : int
            The index of the output device.
        extra_tags : dict
            A dict of extra tags. Currently only {"Whispered": bool} available.
        """

        def convert_to_ssml(input_text):
            # https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html
            if extra_tags and extra_tags.get("whispered"):
                return (
                    "<speak>"
                    + '<amazon:auto-breaths frequency="low" volume="soft" duration="x-short">'
                    + '<amazon:effect name="whispered">'
                    + input_text
                    + "</amazon:effect>"
                    + "</amazon:auto-breaths>"
                    + "</speak>"
                )
            return (
                "<speak>"
                + '<amazon:auto-breaths frequency="low" volume="soft" duration="x-short">'
                + input_text
                + "</amazon:auto-breaths>"
                + "</speak>"
            )

        # # Remove special characters from the text for the file destination.
        filename = re.sub("[#<$+%>!`&*'|{?\"=/}:@]", "", text)
        # print(self.VOICES_PATH / voice_id / f"w_{filename}.ogg")
        if extra_tags and extra_tags.get("whispered"):
            filepath = self.VOICES_PATH / voice_id / f"currentConversation.ogg"
        else:
            filepath = self.VOICES_PATH / voice_id / f"currentConversation.ogg"
        # It creates the directory if it doesn't exist.
        filepath.parent.mkdir(parents=True, exist_ok=True)
        # Create the answer from Amazon Polly if the file does not exist.
        # if not filepath.exists():
        if not filepath.exists():
            try:
                response = self.client.synthesize_speech(
                    Text=convert_to_ssml(text),
                    VoiceId=voice_id.split(" ")[0],
                    OutputFormat="ogg_vorbis",
                    TextType="ssml",
                )
            except botocore.exceptions.ClientError as err:
                error(err)
                return
            with open(filepath, "wb") as file:
                file.write(response["AudioStream"].read())
        read_audio_file(str(filepath), output_device_index)

        # try:
        #         response = self.client.synthesize_speech(
        #             Text=convert_to_ssml(text),
        #             VoiceId=voice_id.split(" ")[0],
        #             OutputFormat="ogg_vorbis",
        #             TextType="ssml",
        #         )
        # except botocore.exceptions.ClientError as err:
        #     error(err)
        # return response["AudioStream"].read()



def read_audio_file(filepath: str, output_device_index: int):
    global CURRENT_FRAME

    # Acquire the lock before starting playback
    playback_lock.acquire()

    def callback(data_out, frames, _, status):
        global CURRENT_FRAME
        if status:
            print("status: ", status)
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
        playback_lock.release()  # Release the lock after playback

    try:
        data, samplerate = soundfile.read(filepath, always_2d=True)
    except Exception as e:
        print("Error reading audio file:", e)
        playback_lock.release()
        return

    event = threading.Event()

    try:
        stream = sounddevice.OutputStream(
            samplerate=samplerate,
            device=output_device_index,
            channels=data.shape[1],
            callback=callback,
            finished_callback=event.set,
        )
    except sounddevice.PortAudioError as e:
        print("Error creating audio stream:", e)
        playback_lock.release()
        return

    thread = threading.Thread(target=stream_thread)
    thread.start()
    thread.join()  # Wait for the playback thread to finish

    # Delete the audio file after playback
    try:
        os.remove(filepath)
        print("Audio file deleted successfully.")
    except Exception as e:
        print("Error deleting audio file:", e)

# tts = Polly()
# 'en': ['v3_en', 'v3_en_indic', 'lj_v2', 'lj_8khz', 'lj_16khz']
# print(tts.list_voices())
# print(tts.list_models())
# print(tts.list_languages)

# starttime = time.time()
# text = "240 Central Park is a beautiful park located in the heart of Manhattan, New York City. It's a perfect place for walks, picnics, and enjoying nature!"

# text = "240 Central Park is a beautiful park, New York City. It's a perfect place for walks, picnics, and enjoying nature!"
#
# tts.speech(text, "Joanna", 8)
# tts.speech(text, "Joanna", 8)
# #
# endtime = time.time()
# print("time spent:")
# print( endtime - starttime)