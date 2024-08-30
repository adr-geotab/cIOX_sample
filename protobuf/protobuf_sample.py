# Import libraries
import can
import time
import datetime
import os
import sys
import binascii
import math
import iox_messaging_pb2

# Import functions.py from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import *

def decode_protobuf_message(go_response):
    print(iox_messaging_pb2.IoxFromGo().ParseFromString(go_response))

# Print header
print('\n\r== Protobuf Sample ==')
print('This script subscribes to protobuf messaging and reads the inbound publishes')

# Construct protobuf message
iox_message = iox_messaging_pb2.IoxToGo()
pubsub_message = iox_messaging_pb2.PubSubToGo()
subscribe_message = iox_messaging_pb2.Subscribe()
subscribe_message.topic = 6 # TOPIC_ENGINE_SPEED
pubsub_message.sub.CopyFrom(subscribe_message)
iox_message.pub_sub.CopyFrom(pubsub_message)
serialized_string = iox_message.SerializeToString()
binary_data = serialized_string
hex_data = binascii.hexlify(binary_data).decode('utf-8')
formatted_hex_data = ' '.join([f'0x{hex_data[i:i+2]}' for i in range(0, len(hex_data), 2)])
payload_values = formatted_hex_data.split()
hex_values = [int(hex_str, 16) for hex_str in payload_values]
data_length = len(hex_values)
total_frames = int(math.ceil(data_length + 8) / 7)
frame_counter = 0
log_type = 13
data_length_field = data_length.to_bytes(2, byteorder='little')
first_frame_data = [frame_counter, log_type] + list(data_length_field) + hex_values[:4]
protobuf_payload = [first_frame_data]
for frame_counter in range(1, total_frames):
    start_index = frame_counter * 4
    end_index = start_index + 7
    subsequent_frame_data = [frame_counter] + hex_values[start_index:end_index]
    protobuf_payload.append(subsequent_frame_data)

# Initialization and CAN startup
msg_index = 0
outbound_msg, prev_outbound_msg = None, None
print('\nBringing up CAN0...')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
try:
    bus = can.interface.Bus(interface='socketcan', channel='can0')
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
            if msg_index == 0:
                outbound_msg = send_can_frame(bus, 0x0002ABCD, [0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A], 'Poll Response (Handshake)')
            else:
                outbound_msg = send_can_frame(bus, 0x0002ABCD, [0x00], 'Poll Response')
            msg_index += 1

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            if msg_index == 2:
                outbound_msg = send_can_frame(bus, 0x001DABCD, [0x01, 0x01, 0x70, 0x10, 0x01, 0x00], 'Send External Device ID')
                msg_index += 1
            elif msg_index >= 4 and msg_index < (4+len(protobuf_payload)):
                outbound_msg = send_can_frame(bus, 0x001EABCD, protobuf_payload[msg_index-4], f'Protobuf Subscription Request (Frame {msg_index-3})')
                msg_index += 1

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    print('\n\rEncountered user-induced keyboard interrupt\nBringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")

except Exception as e:
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")
    print('Bringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")