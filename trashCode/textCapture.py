import pyautogui
from pytesseract import image_to_string

def capture_and_recognize(x, y, width, height):
    """
    Capture a region of the screen and recognize the text within it.

    Parameters:
    - x, y: the top-left corner of the region
    - width, height: the dimensions of the region
    """

    # Capture the specified region of the screen
    screenshot = pyautogui.screenshot(region=(x, y, width, height))

    # Use OCR to recognize text in the screenshot
    recognized_text = image_to_string(screenshot)

    return recognized_text

# Example: Capture and recognize text from a region at (100, 100) with width 500 and height 200
x, y, width, height = 100, 100, 500, 200
text = capture_and_recognize(x, y, width, height)
print(text)

# Note: You'll need to adjust (x, y, width, height) according to where VRChat's chatbox is located on your screen.
