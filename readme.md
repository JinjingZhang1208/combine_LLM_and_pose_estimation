## live demo
### player view

https://drive.google.com/file/d/1w79LhTHq1B2Kg4YSWWDJD_j-XwttfSTc/view?usp=sharing

### AI avarta view

https://drive.google.com/file/d/1Bm22XHPanlFXczCqvdcCCvoculUSB43q/view?usp=sharing



## System Flow Chart

![Blank diagram (1)](https://github.com/hongyuwan/NEU-LLM-Avartars/assets/85655086/f37b8549-08d8-4c11-a631-132a3c34651f)


## Env setting
python 3.9

pip install -r requirements.txt


## Instruction about running Interaction Chatting Bot for VRC (main.py)

Integrate real-time chatting capabilities into VRChat with the power of OpenAI and Google Translate.

### Features
- Real-time text chat using OpenAI's powerful language model.
- Seamless translation of messages using Google Translate.
- Integration with VRChat's OSC functions for a holistic experience.

### Prerequisites

- An API key for OpenAI.
- Google Translate API credentials.
- VRChat with OSC functions enabled.

### Setup and Running Instructions

#### 1. Identify Sound Output Device

- Start by running `main.py`:
This will print a list of available sound devices using the command:

    ```python
    print(sd.query_devices())
Identify the ID of your desired sound output device from the printed list.

Update the DEVICE variable in main.py with the identified ID:


    DEVICE = <YOUR_DEVICE_ID>
    
2. API Setup
In main.py, configure your OpenAI API key and Google Translate API credentials:

    ```python
    openai.api_key = '<YOUR_OPENAI_API_KEY>'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '<PATH_TO_YOUR_GOOGLE_TRANSLATE_CREDENTIALS>'
3. Enable OSC in VRChat
Launch the VRChat game client.
Press R to access the game menu.
Navigate to the OSC settings and enable it.
4. Running the Chatbot
With the configurations in place, run main.py again to initiate the chatbot:
    ```bash
    python main.py

## Demo Code

The following are the main scripts involved in this project:

1. **ConversationAgent.py**: This script prompts to Chatgpt and retrieves data as input to VRC. You need to open OSC in VRChat client.
    ```bash
    python ConversationAgent.py
    ```


https://github.com/hongyuwan/NEU-LLM-Avartars/assets/85655086/c44763d6-0c04-42fb-8f88-e825d3f1283d


2. **/kapao/VRC-related-source/realtimePosesDetectVRC.py**: This script performs realtime keypoints and poses detection. It will automatically detect VRC resolution and position on the screen and capture it. For better performance, it is suggested to put VRC on a separate screen.
    ```bash
    cd ./kapao/VRC-related-source  
    python realtimePosesDetectVRC.py
    ```
    Press `ctrl+c` to stop running.


https://github.com/hongyuwan/NEU-LLM-Avartars/assets/85655086/bdcc8396-e262-4af0-b76c-4bd3bdf77c8f



## Separate Function Code

The following are individual functions involved in this project:

1. **simple_client.py**: This script uses OSC to control avatars in VRC action. You need to open OSC in VRChat client. It provides 5 different options:
    * Control chatbox typing
    * Control movement
    * Control look
    * Interaction with item (only supported in VR)
    ```bash
    python simple_client.py


https://github.com/hongyuwan/NEU-LLM-Avartars/assets/85655086/848ab0dc-8647-465a-aeb9-f7e5e028b866



2. **/kapao/VRC-related-source/realtimeCaptureScreen.py**: This script performs realtime screen capture for VRC and saves it in "./scndata". It will automatically detect VRC resolution and position on the screen and capture it. For better performance, it is suggested to put VRC on a separate screen.
    ```bash
    cd ./kapao/VRC-related-source  
    python realtimeCaptureScreen.py
    ```
    Press `ctrl+c` to stop running.

3. **/kapao/VRC-related-source/realtimeTranscribe.py**: This script performs realtime voice capture for VRC and saves it in "./sounddata". You need to manually set output device name and Google transcript API key in the code.
    ```python
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '*.json'
    DEVICE = *
    ```
    ```bash
    cd ./kapao/VRC-related-source  
    python realtimeTranscribe.py
    ```
    Press `ctrl+c` to stop running.
   

https://github.com/hongyuwan/NEU-LLM-Avartars/assets/85655086/6f048208-6dcd-4614-8446-001c3b24f288



5. **/kapao/VRC-related-source/keypointDetect.py**: This script is a separate keypoint detection function code and it saves its output in a database. It reads captured images from "./scndata".

   --- cd ./kapao/VRC-related-source  
   ---python keypointDetect.py
   --- ctrl+c strop running
6. **/kapao/VRC-related-source/matchingAction.py** --- separate keypoint Detection and matching stored action data from database
   --- cd ./kapao/VRC-related-source  
   ---python matchingAction.py
   --- ctrl+c strop running
   


https://github.com/hongyuwan/NEU-LLM-Avartars/assets/85655086/747416b7-9666-42e8-9523-0afe4be574b4

