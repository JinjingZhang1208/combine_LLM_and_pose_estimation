## Demo Code

The following are the main scripts involved in this project:

1. **ConversationAgent.py**: This script prompts to Chatgpt and retrieves data as input to VRC. You need to open OSC in VRChat client.
    ```bash
    python ConversationAgent.py
    ```

2. **/kapao/VRC-related-source/realtimePosesDetectVRC.py**: This script performs realtime keypoints and poses detection. It will automatically detect VRC resolution and position on the screen and capture it. For better performance, it is suggested to put VRC on a separate screen.
    ```bash
    cd ./kapao/VRC-related-source  
    python realtimePosesDetectVRC.py
    ```
    Press `ctrl+c` to stop running.


## Separate Function Code

The following are individual functions involved in this project:

1. **simple_client.py**: This script uses OSC to control avatars in VRC action. You need to open OSC in VRChat client. It provides 5 different options:
    * Control chatbox typing
    * Control movement
    * Control look
    * Interaction with item (only supported in VR)
    ```bash
    python simple_client.py
    ```

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

4. **/kapao/VRC-related-source/keypointDetect.py**: This script is a separate keypoint detection function code and it saves its output in a database. It reads captured images from "./scndata".

   --- cd ./kapao/VRC-related-source  
   ---python keypointDetect.py
   --- ctrl+c strop running
5. /kapao/VRC-related-source/matchingAction.py --- separate keypoint Detection and matching stored action data from database
   --- cd ./kapao/VRC-related-source  
   ---python matchingAction.py
   --- ctrl+c strop running
