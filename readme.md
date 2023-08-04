### Demo Code
1. ConversationAgent.py ---Prompt to Chatgpt and retrieve data as input to VRC
    [1.need to open OSC in VRChat client]
    --- python ConversationAgent.py
2. /kapao/VRC-related-source/realtimePosesDetectVRC.py --- Realtime keypint and poses detect
    [1. will automatically detect VRC resolution and position on the screen and capture it, suggest to put VRC on a separate screen if want to have better performance]
   --- cd ./kapao/VRC-related-source  
   ---python realtimePosesDetectVR.py
   --- ctrl+c strop running

### Separate function code
1. simple_client.py --- use OSC to control avatars in VRC action
    [1.need to open OSC in VRChat client]
    [2.have 5 different options
        # # 1 control chatbox typing
        # # 2 control movement
        # # 3 control Look
        # # 4 interaction with item -- only supported in VR]
    --- python simple_client.py
2. /kapao/VRC-related-source/realtimeCaptureScreen.py --- Realtime capture screenshot for VRC and saved in "./scndata"
    [1. will automatically detect VRC resolution and position on the screen and capture it, suggest to put VRC on a separate screen if want to have better performance]
   --- cd ./kapao/VRC-related-source  
   ---python realtimeCaptureScreen.py
   --- ctrl+c strop running
3. /kapao/VRC-related-source/realtimeTranscribe.py --- Realtime capture voice for VRC and saved in "./sounddata"
    [1. need to manual set output device name and google transcript API key in the code]
    google API--- os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '*.json'
    target output device number --- DEVICE = *
   --- cd ./kapao/VRC-related-source  
   ---python realtimeTranscribe.py
   --- ctrl+c strop running
4. /kapao/VRC-related-source/keypointDetect.py --- separate keypoint Detection function code and save it in database, will read captured image from ./scndata
   --- cd ./kapao/VRC-related-source  
   ---python keypointDetect.py
   --- ctrl+c strop running
5. /kapao/VRC-related-source/matchingAction.py --- separate keypoint Detection and matching stored action data from database
   --- cd ./kapao/VRC-related-source  
   ---python matchingAction.py
   --- ctrl+c strop running