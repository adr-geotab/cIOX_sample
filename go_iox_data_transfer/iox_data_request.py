# Import libraries
import can
import time
import datetime
import os
import sys

# Import functions.py from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import *

# Print header
print('\n\r== IOX Data Request Script ==')
print('This script requests and reads multi-frame data from the GO device of message type 0x27.')

# Initialization and CAN startup
poll_index = 0
outbound_msg, prev_outbound_msg = None, None
print('\nBringing up CAN0...')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
try:
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
except OSError:
    print("\033[91mCannot find PiCAN board. Please ensure that the PiCAN is configured properly.\033[0m")
    exit()

# Log table header
print('Commencing communication session logging...\n')
print('Direction |          DateTime          |    ArbID   | DLC |       Data       | Description')
print('--------- | -------------------------- | ---------- | --- | ---------------- | --------------')

try:
    while True:
        inbound_msg = bus.recv()  # Wait until a message is received.
        print(f"GO9->cIOX | {datetime.datetime.fromtimestamp(inbound_msg.timestamp)} | 0x{inbound_msg.arbitration_id:08X} | {hex(inbound_msg.dlc)} | {''.join(format(x, '02X') for x in inbound_msg.data).ljust(16, ' ')}", end=' | ')
        classify_inbound_msg(inbound_msg, prev_outbound_msg)
        
        if (inbound_msg.arbitration_id == 0x00010000): 
            if poll_index == 0:
                outbound_msg = send_outbound_msg(bus, 0x0002ABCD, [0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A], 'Poll Response (Handshake)')
            else:
                outbound_msg = send_outbound_msg(bus, 0x0002ABCD, [0x00], 'Poll Response')
            poll_index += 1

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            if poll_index == 2:
                outbound_msg = send_outbound_msg(bus, 0x0025ABCD, [0x02, 0x00, 0x01], 'Request GO Device Data')
                poll_index += 1

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    print('\n\rEncountered user-induced keyboard interrupt\nBringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")

except Exception as e:
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")
    print('Bringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")