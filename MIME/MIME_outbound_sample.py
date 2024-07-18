import can
import time
import datetime
import os
from functions import *

# Define the message to send over MIME
mime_type = "text/plain"
message_to_send = "This is a test MIME message that will be sent from the GO9 to the MyG cloud."

# Print header
print('\n\r== MIME Outbound Custom Messaging Sample ==')
print('\nThis script sends a MIME message of custom type and content from the GO device to the MyG server.')
print(f'MIME Type: {mime_type}')
print(f'Message to Send: {message_to_send}')

# Define the total payload byte array. Append info length in little-endian 1,4 bytes and ASCII vals of strs
total_payload = bytearray()
mime_type = str(mime_type)
message_to_send = str(message_to_send)
total_payload.extend([0x00, len(mime_type)])
total_payload.extend(ord(char) for char in mime_type)
total_payload.extend(len(message_to_send).to_bytes(4, byteorder='little'))
total_payload.extend(ord(char) for char in message_to_send)

# Group the payload into 8 byte arrays, and print
grouped_payloads = [total_payload[i:i+8] for i in range(0, len(total_payload), 8)]
print('\nHere is the MIME Rx payload:\n01 00 00')
for msg in [list(_) for _ in grouped_payloads]:
    for byte in msg:
        print(f'{byte:02X}', end=' ')
    print()
print('01 00 01\n')

# Initialization and CAN startup
poll_count, mime_index, tx_ack_index = 0, 0, 0
outbound_msg, prev_outbound_msg = None, None
print('Bringing up CAN0...')
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
            if poll_count == 0:
                outbound_msg = send_outbound_msg(bus, 0x0002ABCD, [0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A], 'Poll Response (Handshake)')
            else:
                outbound_msg = send_outbound_msg(bus, 0x0002ABCD, [0x00], 'Poll Response')
            poll_count += 1

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            if poll_count == 2:
                outbound_msg = send_outbound_msg(bus, 0x001DABCD, [0x01, 0x01, 0x70, 0x10, 0x01, 0x00], 'Send External Device ID')
                poll_count += 1

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x0002ABCD' and poll_count == 4:
                outbound_msg = send_outbound_msg(bus, 0x0025ABCD, [0x01, 0x00, 0x00], 'MIME-1 (Beginning Packet Wrapper)')
                poll_count += 1
                mime_index += 1

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' in ('0x0025ABCD', '0x000CABCD') and mime_index > 0 and mime_index <= len(grouped_payloads):
                outbound_msg = send_outbound_msg(bus, 0x000CABCD, grouped_payloads[mime_index-1], f'MIME-{mime_index} (MIME Rx)')
                mime_index += 1

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and mime_index-1 == len(grouped_payloads):
                outbound_msg = send_outbound_msg(bus, 0x0025ABCD, [0x01, 0x00, 0x01], f'MIME-{mime_index} (Ending Packet Wrapper)')
                mime_index += 1

        elif inbound_msg.arbitration_id == 0x1CABCD and [inbound_msg.data[0], inbound_msg.data[1]] == [0x00, 0x00]:
            print(f"\033[93mWARNING: Modem transmission failed. This typically indicates that it is not connected. The MIME content was not transferred.\033[0m")

        elif inbound_msg.arbitration_id == 0x0BABCD:
            tx_ack_index += 1
            if tx_ack_index == 2:
                print(f"\033[92mSUCCESS! The MyGeotab database has received the MIME message and it can be pulled via API.\033[0m")

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    print('\n\rEncountered user-induced keyboard interrupt\nBringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")

except Exception as e:
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")
    print('Bringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")