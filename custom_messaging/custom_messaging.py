# Import libraries
import can
import time
import datetime
import os
import sys

# Import functions.py from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import *

# Define the message to send
message_to_send = "0x1E multi-frame datalog"

# Print header
print('\n\r== Custom Messaging Script ==')
print('This script intakes and configures a user-inputted message to be transmitted to the MyGeotab cloud via 0x1E multi-frame data logs.')
print(f'Message to Send: {message_to_send}\n\nPayload to Send:')

# Construct the payload
total_payload = [0x00]
total_payload.extend(len(message_to_send).to_bytes(2, byteorder='little'))
total_payload.extend([int(hex(ord(char)), 16) for char in message_to_send])
nested_payload = [total_payload[i:i + 7] for i in range(0, len(total_payload), 7)]
for index, i in enumerate(nested_payload):
    i.insert(0, index)
    for j in i:
        print(f'0x{j:02X}', end=' ')
    print()

# Warn for GO truncation
if len(message_to_send) > 28:
    print(f"\033[93mWARNING: 0x1E multi-frame data logs support up to 27 bytes. Your message is {len(message_to_send)} bytes. \nThe message will still send but the GO will truncate the message after byte 27. \nTo send longer messages, refer to the MIME protocol.\033[0m")

# Initialization and CAN startup
messaging_index, datalog_index = 0, 0
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
            if messaging_index == 0:
                outbound_msg = send_outbound_msg(bus, 0x0002ABCD, [0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A], 'Poll Response (Handshake)')
            else:
                outbound_msg = send_outbound_msg(bus, 0x0002ABCD, [0x00], 'Poll Response')
            messaging_index += 1

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            if messaging_index == 2:
                outbound_msg = send_outbound_msg(bus, 0x001DABCD, [0x01, 0x01, 0x70, 0x10, 0x01, 0x00], 'Send External Device ID')
                messaging_index += 1
                datalog_index += 1

            elif datalog_index <= len(nested_payload) and datalog_index != 0:
                outbound_msg = send_outbound_msg(bus, 0x001EABCD, nested_payload[datalog_index-1], f'Send Multi-Frame Log {datalog_index}')
                datalog_index += 1

            elif datalog_index == len(nested_payload) + 1:
                print(f"\033[92mSUCCESS! The 0x1E message has been transmitted to the GO and will be pushed to the MyG cloud.\033[0m")
                datalog_index += 1

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    print('\n\rEncountered user-induced keyboard interrupt\nBringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")

except Exception as e:
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")
    print('Bringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")
