# Import libraries
import can
import time
import datetime
import os
from functions import *

# Print header
print('\n\r== Idle Communication Template ==')
print('This script reads inbound CAN messages, responds to poll requests, and sends external device ID')

# Initialization and CAN startup
poll_index, datalog_index = 0, 0
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
                outbound_msg = send_outbound_msg(bus, 0x001DABCD, [0x01, 0x01, 0x70, 0x10, 0x01, 0x00], 'Send External Device ID')
                poll_index += 1
                datalog_index += 1

            elif datalog_index == 1:
                outbound_msg = send_outbound_msg(bus, 0x001DABCD, [0x00, 0x00, 0x07, 0x00, 0x01, 0x23, 0x45, 0x67], 'Send Multi-Frame Log 1')
                datalog_index += 1

            elif datalog_index == 2:
                outbound_msg = send_outbound_msg(bus, 0x001DABCD, [0x01, 0x89, 0xAB, 0xCD], 'Send Multi-Frame Log 2')
                datalog_index += 1

            elif datalog_index == 3:
                outbound_msg = send_outbound_msg(bus, 0x001DABCD, [0x00, 0xD2, 0x0A, 0x01, 0x64], 'Sending Status Data (Time Since Engine Start)')
                datalog_index += 1

            elif datalog_index == 4:
                outbound_msg = send_outbound_msg(bus, 0x001DABCD, [0x03, 0xD2, 0x0A, 0x01, 0x64], 'Sending Priority Status Data (Time Since Engine Start)')
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