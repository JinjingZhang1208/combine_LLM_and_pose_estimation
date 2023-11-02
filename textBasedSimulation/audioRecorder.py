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

INPUT_DEVICE_INDEX = 2
OUTPUT_DEVICE_INDEX = 0
TEMP_FILE = "speech_check.wav"
MODEL_PATH = "./vosk-model/vosk-model-small-en-us-0.15"


def convertAudio(fileName):
    stream = ffmpeg.input(fileName)
    stream = ffmpeg.output(stream, TEMP_FILE, acodec="pcm_s16le", ac=1, ar="16k")
    ffmpeg.run(stream, overwrite_output=True)


def isHumanSpeech(fileName):
    wf = wave.open(fileName, "rb")



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


def recordAudio(fileName, silenceThreshold=-40, maxSilenceLength=3):
    fs = 16000  # Sample rate
    CHUNK_SIZE = int(fs * 0.5)  # Record in chunks of 0.5 seconds

    audio_chunks = []
    silence_duration = 0

    print("Recording started... Speak something...")

    with sd.InputStream(samplerate=fs, channels=1) as stream:
        while True:
            audio_chunk, overflowed = stream.read(CHUNK_SIZE)

            # Convert numpy array to AudioSegment for pydub processing
            byte_io = io.BytesIO()
            write(byte_io, fs, audio_chunk)
            byte_io.seek(0)
            segment = AudioSegment.from_wav(byte_io)

            if segment.dBFS < silenceThreshold:
                silence_duration += CHUNK_SIZE / fs
                if silence_duration >= maxSilenceLength:
                    print("Silence detected, stopping recording.")
                    break
            else:
                silence_duration = 0
            audio_chunks.append(audio_chunk)

    recording = np.concatenate(audio_chunks, axis=0)
    write(fileName, fs, recording)
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
