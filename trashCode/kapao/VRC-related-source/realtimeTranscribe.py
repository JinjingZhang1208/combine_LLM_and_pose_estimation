from google.cloud import speech
import sounddevice as sd
import numpy as np
from datetime import datetime
import os
from numpy_ringbuffer import RingBuffer
import time

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'stellar-utility-267412-7ce130fe08a8.json'

print(sd.query_devices())

print("transcript start")
# Constants
DURATION = 10  # seconds
SAMPLE_RATE = 44100
CHANNELS = 2  # Mono recording
DEVICE = 35  # Set this to the device ID for 'Stereo Mix (Realtek HD Audio Stereo input)'
BUFFER_SIZE = 10  # Buffer size in seconds
BUFFER = RingBuffer(capacity=BUFFER_SIZE * SAMPLE_RATE * CHANNELS)  # need to multiply by CHANNELS for stereo recording

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status)
    BUFFER.extend(indata.flatten())

def stereo_to_mono(data_array):
    """Converts stereo audio data to mono."""
    return np.mean(data_array.reshape((-1, CHANNELS)), axis=1)

# Open the stream
stream = sd.InputStream(callback=callback, channels=CHANNELS, samplerate=SAMPLE_RATE, device=DEVICE)
stream.start()

try:
    while True:
        time.sleep(DURATION)

        # Convert buffer to numpy array
        data_array = np.array(BUFFER)

        # Convert stereo to mono
        mono_array = stereo_to_mono(data_array)

        # Convert numpy array to byte
        audio_data = (mono_array * 32767).astype(np.int16).tobytes()

        # Initialize a client
        client = speech.SpeechClient()

        # Create RecognitionAudio instance
        audio = speech.RecognitionAudio(content=audio_data)

        # Create recognition configuration
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-US",
        )

        # Create RecognitionConfig instance
        request = speech.RecognizeRequest(
            config=config,
            audio=audio,
        )

        # Recognize speech
        response = client.recognize(request=request)

        for result in response.results:
            print("Transcript: {}".format(result.alternatives[0].transcript))

except KeyboardInterrupt:
    print("Recording stopped by user")

stream.stop()
stream.close()
