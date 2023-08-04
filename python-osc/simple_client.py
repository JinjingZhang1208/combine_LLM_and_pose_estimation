"""Small example OSC client

This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import sys
sys.path.append('../python-osc/pythonosc')
import argparse
import random
import time
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder

from pythonosc import osc_message_builder
from pythonosc import udp_client


"""
/input/UseAxisRight : Use held item - not sure if this works
"""
def actionUse_axis_right(client, value):
    client.send_message("/input/Equip", value)
"""
/input/GrabAxisRight : Grab item - not sure if this works
"""
def actionGrab_axis_right(client, value):
    client.send_message("/input/GrabAxisRight", value)
"""
/input/MoveHoldFB : Move a held object forwards (1) and backwards (-1)
"""
def actionMove_hold_fb(client, value):
    client.send_message("/input/MoveHoldFB", value)
"""
/input/SpinHoldCwCcw : Spin a held object Clockwise or Counter-Clockwise
"""
def actionSpin_hold_cw_ccw(client, value):
    client.send_message("/input/SpinHoldCwCcw", value)
"""
/input/SpinHoldUD : Spin a held object Up or Down
"""
def actionSpin_hold_ud(client, value):
    client.send_message( "/input/SpinHoldUD", value)
"""
/input/SpinHoldLR : Spin a held object Left or Right
"""
def actionSpin_hold_lr(client, value):
    client.send_message( "/input/SpinHoldLR", value)

# Buttons

def actionMove(client,forward,backward,left, right, timee ,isRunning):
    if (forward==True):
        client.send_message("/input/MoveForward", 1)
    if (backward == True):
        client.send_message("/input/MoveBackward", 1)
    if (left == True):
        client.send_message("/input/MoveLeft", 1)
    if (right == True):
        client.send_message("/input/MoveRight", 1)
    if (isRunning==True):
        client.send_message("/input/Run", 1)
    time.sleep(timee)
    client.send_message("/input/MoveForward", False)
    client.send_message("/input/MoveBackward", False)
    client.send_message("/input/MoveLeft", False)
    client.send_message("/input/MoveRight", False)
    client.send_message("/input/Run", False)
    return 0

def actionForceStopmoveing(client):
    client.send_message("/input/MoveForward", False)
    client.send_message("/input/MoveBackward", False)
    client.send_message("/input/MoveLeft", False)
    client.send_message("/input/MoveRight", False)
    client.send_message("/input/Run", False)
    return 0
"""
/input/LookLeft : Turn to the left while this is 1. Smooth in Desktop, VR will do a snap-turn if Comfort Turning is on.
"""
def actionLook_left(client,value):
    client.send_message("/input/LookLeft", 1)
    time.sleep(0.05 * value)
    client.send_message("/input/LookLeft", False)
    return 0

"""
/input/LookRight : Turn to the right while this is 1. Smooth in Desktop, VR will do a snap-turn if Comfort Turning is on.
"""

def actionLook_right(client,value):
    client.send_message("/input/LookRight", 1)
    time.sleep(0.05 * value)
    client.send_message("/input/LookRight", False)
    return 0

"""
/input/Jump : Jump if the world supports it.
"""

def actionJump(client):
    client.send_message("/input/Jump", False)
    client.send_message("/input/Jump", 1)
    client.send_message("/input/Jump", False)


"""
Chatbox
/chatbox/input s b n Input text into the chatbox. If b is True, send the text in s immediately, bypassing the keyboard. If b is False, open the keyboard and populate it with the provided text. n is an additional bool parameter that when set to False will not trigger the notification SFX (defaults to True if not specified).
/chatbox/typing b Toggle the typing indicator on or off.
"""
def actionChatbox(client, str):
    # bundle
    bundle_builder = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
    # Create a new message.
    message_builder = osc_message_builder.OscMessageBuilder(address="/chatbox/input")
    message_builder.add_arg(str)
    message_builder.add_arg(True)
    message_builder.add_arg(True)
    msg = message_builder.build()

    # Add the message to the bundle.
    bundle_builder.add_content(msg)

    # Build and get the bundle.
    bundle = bundle_builder.build()
    client.send_message("/chatbox/typing", True)
    time.sleep(2)
    client.send_message("/chatbox/typing", False)
    client.send(bundle)
def voice(client, value):
    client.send_message("/input/Voice", value)
"""
VR only function(future work)
/input/ComfortLeft : Snap-Turn to the left - VR Only.

/input/ComfortRight : Snap-Turn to the right - VR Only.

/input/DropRight : Drop the item held in your right hand - VR Only.

/input/UseRight : Use the item highlighted by your right hand - VR Only.

/input/GrabRight : Grab the item highlighted by your right hand - VR Only.

/input/DropLeft : Drop the item held in your left hand - VR Only.

/input/UseLeft : Use the item highlighted by your left hand - VR Only.

/input/GrabLeft : Grab the item highlighted by your left hand - VR Only.
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)
    value=1
    for x in range(10):
        time.sleep(2)

        # # 1 control chatbox typing

        # strr="Hi!!!"
        # actionChatbox(client, strr)
        # print("typing"+strr)

        # 2 control movement
        actionMove(client,1, 0, 1, 0, 2, False)
        # actionForceStopmoveing(client)
        # actionJump(client)

        # 3 control Look
        # actionLook_left(client,1)
        # actionLook_right(client, 1)

        # # 4 interaction with item
        # # only supported in VR

        # actionUse_axis_right(client,1)
        # actionSpin_hold_ud(client,1)
        # actionSpin_hold_ud(client, False)
        # actionSpin_hold_lr(client,1)
        # actionSpin_hold_lr(client, False)

        # actionSpin_hold_cw_ccw(client,1)
        # actionSpin_hold_cw_ccw(client, False)

        # # 5 turn on voice input
        # voice(client, 1)
        # voice(client,False)
