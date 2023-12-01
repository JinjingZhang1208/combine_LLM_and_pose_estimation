import sounddevice as sd

import io
import os
import json
import numpy as np
import ffmpeg
import wave
from distutils.log import Log
import speech_recognition as sr
import time
from vosk import Model, KaldiRecognizer
from scipy.io.wavfile import write
from playsound import playsound
from pydub import AudioSegment, silence
import pyaudio
from csvLogger import CSVLogger, LogElements

INPUT_DEVICE_INDEX = 17
OUTPUT_DEVICE_INDEX =17
TEMP_FILE = "speech_check.wav"
MODEL_PATH = "./vosk-model/vosk-model-small-en-us-0.15"
AUDIO_CSV_LOGGER = ""

def convertAudio(fileName):
    stream = ffmpeg.input(fileName)
    stream = ffmpeg.output(stream, TEMP_FILE, acodec="pcm_s16le", ac=1, ar="16k")
    ffmpeg.run(stream, overwrite_output=True)


def isHumanSpeech(fileName):
    global AUDIO_CSV_LOGGER
    start = time.perf_counter()
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
        end = time.perf_counter()
        detect_time = round(end - start, 2)
        AUDIO_CSV_LOGGER.set_enum(
            LogElements.TIME_FOR_HUMAN_SPEECH_RECOGNITION, detect_time
        )
        return True
    else:
        return False


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
                    input_device_index=3,
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


def listenAndRecord(fileName, CSV_LOGGER: CSVLogger):
    global AUDIO_CSV_LOGGER
    AUDIO_CSV_LOGGER = CSV_LOGGER
    start = time.perf_counter()
    recordAudio(fileName)
    end = time.perf_counter()
    record_time = round(end - start, 2)
    AUDIO_CSV_LOGGER.set_enum(LogElements.TIME_FOR_AUDIO_RECORD, record_time)

    start = time.perf_counter()
    normalizeAudio(fileName)
    end = time.perf_counter()
    normalize_time = round(end - start, 2)
    AUDIO_CSV_LOGGER.set_enum(LogElements.TIME_FOR_VOICE_NORMALIZATION, normalize_time)
    # listen = input("Do you want to listen the recorded audio? [y/n]")
    # if listen.lower() == "y":
    #     playsound(fileName)


def deleteAudioFile(fileName):
    try:
        os.remove(fileName)
    except:
        return

# print(listenAndRecord("text1.wav"))
def recordAudioToByteStream(silenceThreshold=-40, maxSilenceLength=1):
    fs = 16000  # Sample rate
    CHUNK_SIZE = int(fs * 0.5)  # Record in chunks of 0.5 seconds

    audio_chunks = []
    silence_duration = 0
    recording_started = False
    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=fs,
                    input=True,
                    input_device_index=3,
                    frames_per_buffer=CHUNK_SIZE)

    print("Recording started... Speak something...")

    while True:
        audio_chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)

        # Convert byte data to AudioSegment for silence detection
        segment = AudioSegment.from_raw(io.BytesIO(audio_chunk), sample_width=2, frame_rate=fs, channels=1)

        # Check for non-silence to start recording
        if segment.dBFS > silenceThreshold:
            recording_started = True

        if recording_started:
            audio_chunks.append(audio_chunk)

            # Check for silence to stop recording
            if segment.dBFS < silenceThreshold:
                silence_duration += CHUNK_SIZE / fs
                if silence_duration >= maxSilenceLength:
                    print("Silence detected, stopping recording.")
                    break
            else:
                silence_duration = 0

    # Combine audio chunks and return as byte stream
    audio_data = b''.join(audio_chunks)
    byte_stream = io.BytesIO(audio_data)
    return byte_stream

def convertAndCheckAudio(byte_stream):
    # Convert audio to the desired format in memory
    audio_data = AudioSegment.from_raw(byte_stream, sample_width=2, frame_rate=16000, channels=1)
    normalized_audio_data = audio_data.normalize()
    converted_stream = io.BytesIO()

    start = time.perf_counter()
    normalized_audio_data.export(converted_stream, format="wav")
    end = time.perf_counter()
    normalize_time = round(end - start, 2)
    AUDIO_CSV_LOGGER.set_enum(LogElements.TIME_FOR_VOICE_NORMALIZATION, normalize_time)

    converted_stream.seek(0)

    # Check if the converted audio contains human speech
    return isHumanSpeechByte(converted_stream)

def isHumanSpeechByte(byte_stream):
    global AUDIO_CSV_LOGGER
    global transcribeText
    start = time.perf_counter()

    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)
    end = time.perf_counter()
    detect_time = round(end - start, 2)
    AUDIO_CSV_LOGGER.set_enum(
        LogElements.TIME_FOR_HUMAN_SPEECH_RECOGNITION, detect_time
    )

    start = time.perf_counter()
    # byte_stream.seek(0)
    while True:
        data = byte_stream.read(8000)  # Read in chunks of 4000 bytes
        if len(data) == 0:
            break  # Break the loop if no more data is available
        rec.AcceptWaveform(data)

    result = json.loads(rec.FinalResult())
    if len(result.get("text", "")) > 0:
        transcribeText = result.get("text", "")
        end = time.perf_counter()
        detect_time = round(end - start, 2)
        AUDIO_CSV_LOGGER.set_enum(
            LogElements.TIME_AUDIO_TO_TEXT, detect_time
        )
        return True
    else:
        return False

    #
    # if len(result.get("text", "")) > 0:
    #     transcribeText=result.get("text", "")
    #     end = time.perf_counter()
    #     detect_time = round(end - start, 2)
    #     AUDIO_CSV_LOGGER.set_enum(
    #         LogElements.TIME_FOR_HUMAN_SPEECH_RECOGNITION, detect_time
    #     )
    #     return True
    # else:
    #     return False

def listenAndRecordDirect(CSV_LOGGER):
    global AUDIO_CSV_LOGGER
    AUDIO_CSV_LOGGER = CSV_LOGGER
    audio_file_name = "recorded_speech.wav"  # Name of the file where audio will be saved
    while True:
        start = time.perf_counter()
        audio_byte_stream = recordAudioToByteStream()
        end = time.perf_counter()
        record_time = round(end - start, 2)
        AUDIO_CSV_LOGGER.set_enum(LogElements.TIME_FOR_AUDIO_RECORD, record_time)

        if not convertAndCheckAudio(audio_byte_stream):
            print("Nothing recorded, speak again!")
            continue
            # Saving the audio data to a file

            break

        with open(audio_file_name, "wb") as f:
            audio_byte_stream.seek(0)
            raw_audio_data = AudioSegment.from_raw(audio_byte_stream, sample_width=2, frame_rate=16000, channels=1)
            raw_audio_data.export(audio_file_name, format="wav")
        # Prompt to play the recorded audio
        # listen = input("Do you want to listen to the recorded audio? [y/n] ")
        # if listen.lower() == "y":
        #     playsound(audio_file_name)

        # raw_audio_data = AudioSegment.from_raw(audio_byte_stream, sample_width=2, frame_rate=48000, channels=1)
        # raw_audio_data.export(audio_file_name, format="wav")


        break
    return transcribeText

