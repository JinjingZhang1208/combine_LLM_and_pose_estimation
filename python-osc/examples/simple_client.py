"""Small example OSC client

This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import argparse
import random
import time
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder

from pythonosc import osc_message_builder
from pythonosc import udp_client

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)
    # bundle
    bundle_builder = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
    # Create a new message.
    message_builder = osc_message_builder.OscMessageBuilder(address="/chatbox/input")
    message_builder.add_arg("I Love U")
    message_builder.add_arg(True)
    message_builder.add_arg(True)
    msg = message_builder.build()

    # Add the message to the bundle.
    bundle_builder.add_content(msg)

    # Build and get the bundle.
    bundle = bundle_builder.build()
    #bundle

    # sub_bundle = bundle.build()
    # # Now add the same bundle inside itself.
    # bundle.add_content(sub_bundle)
    # # The bundle has 5 elements in total now.
    #
    # bundle = bundle.build()
    # You can now send it via a client as described in other examples.
    print(bundle)
    for x in range(10):
        time.sleep(2)
        client.send_message("/chatbox/typing", True)
        # client.send_message("/chatbox/typing", "False")
        # client.send_message("/chatbox/input","www True")
        time.sleep(2)
        client.send_message("/chatbox/typing", False)
        client.send(bundle)
        # client.send_message("/input/QuickMenuToggleleft", 0)
        # client.send_message("/input/MoveForward",1)
        client.send_message("/input/MoveForward", 0)


