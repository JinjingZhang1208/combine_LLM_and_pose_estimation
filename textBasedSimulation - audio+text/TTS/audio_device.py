import pyaudio
# Create a PyAudio instance
p = pyaudio.PyAudio()

# Print information about all available devices
for i in range(p.get_device_count()):
    device_info = p.get_device_info_by_index(i)
    print(f"Device {i}: {device_info['name']}")
    print(f"   - Input Channels: {device_info['maxInputChannels']}")
    print(f"   - Output Channels: {device_info['maxOutputChannels']}")
    print(f"   - Default Sample Rate: {device_info['defaultSampleRate']}\n")