import sounddevice as sd
import os
import time
from scipy.io.wavfile import write
from playsound import playsound
from pydub import AudioSegment

INPUT_DEVICE_INDEX = 51
OUTPUT_DEVICE_INDEX = 51
DURATION = 8

sd.default.device = INPUT_DEVICE_INDEX, OUTPUT_DEVICE_INDEX



def timer(duration):
    while duration:
        mins, secs = divmod(duration, 60)
        timer = f"{mins} mins:{secs} seconds Left"
        print(timer, end=" \r")
        time.sleep(1)
        duration -= 1


def recordAudio(fileName):
    # frequency
    fs = 44100  # frames per second
    duration = DURATION  # seconds in integer

    print("Recording..........")

    # start recording
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=2)

    timer(duration)  # call timer function
    sd.wait()

    # write the data in filename and save it
    write(fileName, fs, myrecording)


def normalizeAudio(fileName):
    currSegment = AudioSegment.from_file(fileName)
    normalizeAudio = currSegment.normalize()
    normalizeAudio.export(fileName, format="wav")


def listenAndRecord(fileName):
    recordAudio(fileName)
    normalizeAudio(fileName)
    listen="n"
    # listen = input("Do you want to listen the recorded audio? [y/n]")
    if listen.lower() == "y":
        playsound(fileName)


def deleteAudioFile(fileName):
    try:
        os.remove(fileName)
    except:
        return
