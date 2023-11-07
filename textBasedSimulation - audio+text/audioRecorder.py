import sounddevice as sd
import io
import os
import json
import numpy as np
import ffmpeg
import wave
import speech_recognition as sr
from vosk import Model, KaldiRecognizer
from scipy.io.wavfile import write
from playsound import playsound
from pydub import AudioSegment, silence
import pyaudio
INPUT_DEVICE_INDEX = 4
OUTPUT_DEVICE_INDEX =4
TEMP_FILE = "speech_check.wav"
MODEL_PATH = "./vosk-model/vosk-model-small-en-us-0.15"


def convertAudio(fileName):
    stream = ffmpeg.input(fileName)
    stream = ffmpeg.output(stream, TEMP_FILE, acodec="pcm_s16le", ac=1, ar="16k")
    ffmpeg.run(stream, overwrite_output=True)


def isHumanSpeech(fileName):
    wf = wave.open(fileName, "rb")
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, wf.getframerate())

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)

    result = json.loads(rec.FinalResult())
    if len(result.get("text")) > 0:
        return True
    else:
        return False


# def recordAudio(fileName, silenceThreshold=-10, maxSilenceLength=2):
#     fs = 23100  # Sample rate
#     CHUNK_SIZE = int(fs * 0.5)  # Record in chunks of 0.5 seconds
#
#     audio_chunks = []
#     silence_duration = 0
#
#     print("Recording started... Speak something...")
#
#     with sd.InputStream(samplerate=fs, channels=1) as stream:
#         while True:
#             audio_chunk, overflowed = stream.read(CHUNK_SIZE)
#
#             # Convert numpy array to AudioSegment for pydub processing
#             byte_io = io.BytesIO()
#             write(byte_io, fs, audio_chunk)
#             byte_io.seek(0)
#             segment = AudioSegment.from_wav(byte_io)
#
#             if segment.dBFS < silenceThreshold:
#                 silence_duration += CHUNK_SIZE / fs
#                 if silence_duration >= maxSilenceLength:
#                     print("Silence detected, stopping recording.")
#                     break
#             else:
#                 silence_duration = 0
#             audio_chunks.append(audio_chunk)
#
#     recording = np.concatenate(audio_chunks, axis=0)
#     write(fileName, fs, recording)
#     convertAudio(fileName)
#     if not isHumanSpeech(TEMP_FILE):
#         print("Nothing recorded, speak again!")
#         recordAudio(fileName)
# Function to record audio using PyAudio
def recordAudio(fileName, silenceThreshold=-40, maxSilenceLength=2):
    fs = 48000  # Sample rate
    CHUNK_SIZE = int(fs * 0.5)  # Record in chunks of 0.5 seconds

    audio_chunks = []
    silence_duration = 0

    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=fs,
                    input=True,
                    input_device_index=4,
                    frames_per_buffer=CHUNK_SIZE)

    print("Recording started... Speak something...")

    while True:
        audio_chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        audio_chunks.append(audio_chunk)

        # Convert byte data to AudioSegment for silence detection
        segment = AudioSegment.from_raw(io.BytesIO(audio_chunk), sample_width=2, frame_rate=fs, channels=1)

        if segment.dBFS < silenceThreshold:
            silence_duration += CHUNK_SIZE / fs
            if silence_duration >= maxSilenceLength:
                print("Silence detected, stopping recording.")
                break
        else:
            silence_duration = 0

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Write to a WAV file
    wf = wave.open(fileName, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(fs)
    wf.writeframes(b''.join(audio_chunks))
    wf.close()

    # Convert and check if human speech is present
    convertAudio(fileName)
    if not isHumanSpeech(TEMP_FILE):
        print("Nothing recorded, speak again!")
        recordAudio(fileName)

def normalizeAudio(fileName):
    currSegment = AudioSegment.from_file(fileName)
    normalizeAudio = currSegment.normalize()
    normalizeAudio.export(fileName, format="wav")


def listenAndRecord(fileName):
    recordAudio(fileName)
    normalizeAudio(fileName)
    listen = input("Do you want to listen the recorded audio? [y/n]")
    if listen.lower() == "y":
        playsound(fileName)


def deleteAudioFile(fileName):
    try:
        os.remove(fileName)
    except:
        return

# print(listenAndRecord("text1.wav"))
