

import sounddevice as sd
import wavio
import simpleaudio as sa
# Query and print all available devices
print(sd.query_devices())
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if (dev['name'] == 'Stereo Mix (Realtek(R) Audio)' and dev['hostApi'] == 0):
        dev_index = dev['index'];
        print('dev_index', dev_index)
# Parameters
# filename = 'output.wav'
# duration = 5  # seconds
# samplerate = 44100  # Hertz
#
# # Choose your device here. You would set this to the index of CABLE-D Output.
# device_index = 51 # This index might be different on your system.
#
# # Record audio
# print("Recording...")
# myrecording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, device=device_index)
# sd.wait()  # Wait until recording is finished
#
# # Save as WAV file
# wavio.write(filename, myrecording, samplerate, sampwidth=2)
# print("Recording saved as", filename)

# Playback
# print("Playing back...")
# wave_obj = sa.WaveObject.from_wave_file(filename)
# play_obj = wave_obj.play()
# play_obj.wait_done()  # Wait until sound has finished playing
# print("Playback finished.")
