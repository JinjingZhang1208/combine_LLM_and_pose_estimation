import cv2
import numpy as np
from mss import mss
import pygetwindow as gw
import os
import datetime

# Get the window
window = gw.getWindowsWithTitle('VRChat')[0]

# Define the region of the screen where VRChat is displayed
monitor = {"top": window.top, "left": window.left, "width": window.width, "height": window.height}

# Create an MSS instance
sct = mss()

# Define the directory where you want to save the screenshots
directory = "./scndata"

if not os.path.exists(directory):
    os.makedirs(directory)

while True:
    # Capture the defined part of the screen
    screenshot = sct.grab(monitor)

    # Convert the screenshot to a numpy array
    img = np.array(screenshot)

    # Display the image
    cv2.imshow('Screen', np.array(img))

    # Create a unique filename using the current timestamp
    filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    # Save the image to the defined directory
    cv2.imwrite(os.path.join(directory, filename + '.png'), img)

    # If we press ESC then break out of the loop
    if cv2.waitKey(25) & 0xFF == 27:
        cv2.destroyAllWindows()
        break