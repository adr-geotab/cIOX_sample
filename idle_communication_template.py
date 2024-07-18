import can
import time
import datetime
import os

# Print header
print('\n\r== Idle Communication Template ==')
print('\nThis script reads inbound CAN messages, responds to poll requests, and sends external device ID')

# Initialization and CAN startup
print('Bringing up CAN0...')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
poll_count = 0
outbound_msg = None
try:
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
except OSError:
    print("\033[91mCannot find PiCAN board. Please ensure that the PiCAN is configured properly.\033[0m")
    exit()

# Log table header
print('Commencing communication session logging...\n')
print('Direction |          DateTime          |    ArbID   | DLC |       Data       | Description')
print('--------- | -------------------------- | ---------- | --- | ---------------- | --------------')

def log_msg(direction, datetime, arb_id, dlc, data, desc='', end='\n'):
    print(f"{direction} | {datetime} | 0x{arb_id:08X} | {hex(dlc)} | {''.join(format(x, '02X') for x in data).ljust(16, ' ')} | {desc}", end=end)

try:
    while True:  
        inbound_msg = bus.recv()  # Wait until a message is received.
        log_msg('GO9->cIOX', datetime.datetime.fromtimestamp(inbound_msg.timestamp), inbound_msg.arbitration_id, inbound_msg.dlc, inbound_msg.data, end='')
        
        if (inbound_msg.arbitration_id == 0x00010000 and poll_count == 0): 
            poll_count += 1
            print("Poll Request")
            data = [0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A]
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=data, timestamp=time.time())
            log_msg('cIOX->GO9', datetime.datetime.fromtimestamp(outbound_msg.timestamp), outbound_msg.arbitration_id, len(data), data, 'Poll Response (Handshake)')
            bus.send(outbound_msg)

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            print(f'Acknowledgement of 0x{prev_outbound_msg.arbitration_id:08X}')

            if poll_count == 2:
                poll_count += 1
                data = [0x01, 0x01, 0x70, 0x10, 0x01, 0x00]
                outbound_msg = can.Message(arbitration_id=0x001DABCD, data=data, timestamp=time.time())
                log_msg('cIOX->GO9', datetime.datetime.fromtimestamp(outbound_msg.timestamp), outbound_msg.arbitration_id, len(data), data, 'Send External Device ID')
                bus.send(outbound_msg)

        elif (inbound_msg.arbitration_id == 0x00010000 and poll_count > 0):
            poll_count +=1
            print('Poll Request')
            data = [0x00]
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=data, timestamp=time.time())
            log_msg('cIOX->GO9', datetime.datetime.fromtimestamp(outbound_msg.timestamp), outbound_msg.arbitration_id, len(data), data, 'Poll Response')
            bus.send(outbound_msg)

        elif inbound_msg.arbitration_id == 0x260000:
            print('GO Status Information Log', end='')
            if inbound_msg.data[0] == 0x00 and inbound_msg.data[1] == 0x00:
                if inbound_msg.data[2] == 0x00:
                    print(' (Ignition off)')
                elif inbound_msg.data[2] == 0x01:
                    print(' (Ignition on)')
            elif inbound_msg.data[0] == 0x01 and inbound_msg.data[1] == 0x00:
                if inbound_msg.data[2] == 0x00:
                    print(' (Modem is not ready)')
                elif inbound_msg.data[2] == 0x01:
                    print(' (Modem is available)')
            else:
                print()

        elif inbound_msg.arbitration_id == 0x040000:
            print('Wakeup')

        elif inbound_msg.arbitration_id == 0x1CABCD and inbound_msg.data[0] == 0x00:
            print('GO Accept Message to Buffer', end=' ')
            if inbound_msg.data[1] == 0x00:
                print('(Failed)')
                print(f"\033[93mWARNING: Modem transmission failed. This typically indicates that it is not connected. The MIME content was not transferred.\033[0m")
            elif inbound_msg.data[1] == 0x01:
                print('(Success)')

        elif inbound_msg.arbitration_id == 0x1CABCD and inbound_msg.data[0] == 0x05:
            if inbound_msg.data[1] == 0x00:
                print('External Device Channel Disabled')
            elif inbound_msg.data[1] == 0x01:
                print('External Device Channel Enabled')

        elif inbound_msg.arbitration_id == 0x0BABCD:
            print('TX Data')
    
        elif inbound_msg.arbitration_id == 0x260000:
            print('GO Status Information Log')

        else:
            print('Unclassified Message')

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    print('\n\rEncountered user-induced keyboard interrupt\nBringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")

except Exception as e:
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")
    print('Bringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")