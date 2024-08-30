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
print('\n\r== MIME Inbound Messaging Sample ==')
print('This script receives, re-constructs, and decodes MIME messages from the MyG server.')

# Initialization and CAN startup
poll_index, inbound_tx_index = 0, 0
outbound_msg, prev_outbound_msg, messages_expected = None, None, None
mime_type_buffer, mime_content_buffer, read_data = [], [], False
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
                outbound_msg = send_can_frame(bus, 0x0002ABCD, [0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A], 'Poll Response (Handshake)')
            else:
                outbound_msg = send_can_frame(bus, 0x0002ABCD, [0x00], 'Poll Response')
            poll_index += 1

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            if poll_index == 2:
                outbound_msg = send_can_frame(bus, 0x001DABCD, [0x01, 0x01, 0x70, 0x10, 0x01, 0x00], 'Send External Device ID')
                # print(f"\033[92mThe IOX's Device ID has been declared. It can now receive TX data. You can now send the MIME message.\033[0m")
                poll_index += 1

        elif (inbound_msg.arbitration_id == 0x000BABCD): 
            inbound_tx_index += 1
            if inbound_tx_index == 1:
                payload_length_little_endian = []
                payload_length_bytes = [
                    {'msg_id': (inbound_msg.data[1]+2)//8+1, 'byte_id': (inbound_msg.data[1]+2)%8},
                    {'msg_id': (inbound_msg.data[1]+3)//8+1, 'byte_id': (inbound_msg.data[1]+3)%8},
                    {'msg_id': (inbound_msg.data[1]+4)//8+1, 'byte_id': (inbound_msg.data[1]+4)%8},
                    {'msg_id': (inbound_msg.data[1]+5)//8+1, 'byte_id': (inbound_msg.data[1]+5)%8},
                ]

            for byte_index in payload_length_bytes:
                if inbound_tx_index == byte_index['msg_id']:
                    payload_length_little_endian.append(inbound_msg.data[byte_index['byte_id']])

            if len(payload_length_little_endian) == 4:
                if read_data is True:
                    mime_content_buffer.extend([byte for byte in inbound_msg.data])
                else:
                    payload_length = int.from_bytes(bytearray(payload_length_little_endian), byteorder='little')
                    bytes_expected = (payload_length_bytes[3]['msg_id']-1)*8 + payload_length_bytes[3]['byte_id'] + payload_length + 1
                    messages_expected = (bytes_expected-1)//8 + 1
                    for byte_index, byte in enumerate(inbound_msg.data):
                        if payload_length_bytes[3]['msg_id'] == inbound_tx_index:
                            if byte_index >= payload_length_bytes[3]['byte_id']+1:
                                mime_content_buffer.append(byte)
                            else:
                                mime_type_buffer.append(byte)
                        else:
                            mime_content_buffer.append(byte)
                    read_data = True

                if inbound_tx_index == messages_expected:
                    mime_type_buffer = mime_type_buffer[2:-4]
                    print(f"\n\033[92mSUCCESS! The MIME message has been received.\033[0m\nMIME Type: {bytes(mime_type_buffer).decode('latin-1')}\nMIME Payload: {bytes(mime_content_buffer).decode('latin-1')}\n")
                    inbound_tx_index = 0
                    read_data = False
                    mime_content_buffer = []
                    mime_type_buffer = []
            else:
                mime_type_buffer.extend([byte for byte in inbound_msg.data])

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    print('\n\rEncountered user-induced keyboard interrupt\nBringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")

except Exception as e:
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")
    print('Bringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")