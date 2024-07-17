import can
import time
import datetime
import os

print('\n\rCAN MIME Test')
print('Bringing up CAN0...')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
poll_count = 0
mime_index = 0
tx_ack_index = 0
outbound_msg = None

# MIME Message to be Sent
# type: image/jpeg
# payload: Firmware init

try:
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
except OSError:
    print('Cannot find PiCAN board.')
    exit()

print('Commencing communication session...\n')
# print('Direction: DateTime ArbitrationID, DLC, [Payload] || Description')

try:
    while True:  
        inbound_msg = bus.recv()  # Wait until a message is received.
        print('GO->cIOX:', datetime.datetime.fromtimestamp(inbound_msg.timestamp), f'0x{inbound_msg.arbitration_id:08X}', hex(inbound_msg.dlc), ''.join(format(x, '02x') for x in inbound_msg.data)+(' ' if inbound_msg.data else ''), end='')
        
        if (inbound_msg.arbitration_id == 0x00010000 and poll_count == 0): 
            poll_count += 1
            print("|| Poll Request")
            payload = [0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A]
            hex_string = ''.join(format(byte, '02X') for byte in payload)
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=payload, timestamp=time.time())
            print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || Poll Response (Handshake)')
            bus.send(outbound_msg)

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            print(f'|| Acknowledgement of 0x{prev_outbound_msg.arbitration_id:08X}')

            if poll_count == 2:
                poll_count += 1
                payload = [0x01, 0x01, 0x70, 0x10, 0x01, 0x00]
                hex_string = ''.join(format(byte, '02X') for byte in payload)
                outbound_msg = can.Message(arbitration_id=0x001DABCD, data=payload, timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || Send External Device ID')
                bus.send(outbound_msg)

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x0002ABCD' and poll_count == 4:
                poll_count += 1
                payload = [0x01, 0x00, 0x00]
                hex_string = ''.join(format(byte, '02X') for byte in payload)
                outbound_msg = can.Message(arbitration_id=0x0025ABCD, data=payload, timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || MIME-1 (Beginning Packet Wrapper)')
                bus.send(outbound_msg)
                mime_index += 1
                
            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x0025ABCD' and mime_index == 1:
                payload = [0x00, 0x0A, 0x69, 0x6D, 0x61, 0x67, 0x65, 0x2F]
                hex_string = ''.join(format(byte, '02X') for byte in payload)
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=payload, timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || MIME-2 (MIME Type)')
                bus.send(outbound_msg)
                mime_index += 1

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and mime_index == 2:
                payload = [0x6A, 0x70, 0x65, 0x67, 0x0C, 0x00, 0x00, 0x00]
                hex_string = ''.join(format(byte, '02X') for byte in payload)
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=payload, timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || MIME-3 (MIME Type)')
                bus.send(outbound_msg)
                mime_index += 1

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and mime_index == 3:
                payload = [0x46, 0x69, 0x72, 0x6D, 0x77, 0x61, 0x72, 0x65]
                hex_string = ''.join(format(byte, '02X') for byte in payload)
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=payload, timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || MIME-4 (MIME Payload)')
                bus.send(outbound_msg)
                mime_index += 1
            
            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and mime_index == 4:
                payload = [0x49, 0x6E, 0x69, 0x74]
                hex_string = ''.join(format(byte, '02X') for byte in payload)
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=payload, timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || MIME-5 (MIME Payload)')
                bus.send(outbound_msg)
                mime_index += 1

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and mime_index == 5:
                payload = [0x01, 0x00, 0x01]
                hex_string = ''.join(format(byte, '02X') for byte in payload)
                outbound_msg = can.Message(arbitration_id=0x0025ABCD, data=payload, timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || MIME-6 (Ending Packet Wrapper)')
                bus.send(outbound_msg)
                mime_index += 1

        elif (inbound_msg.arbitration_id == 0x00010000 and poll_count > 0):
            poll_count +=1
            print('|| Poll Request')
            payload = [0x00]
            hex_string = ''.join(format(byte, '02X') for byte in payload)
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=payload, timestamp=time.time())
            print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'0x{len(payload):X} {hex_string} || Poll Response')
            bus.send(outbound_msg)

        elif inbound_msg.arbitration_id == 0x260000:
            print('|| GO Status Information Log', end='')
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
            print('|| Wakeup')

        elif inbound_msg.arbitration_id == 0x1CABCD and inbound_msg.data[0] == 0x00:
            print('|| GO Accept Message to Buffer', end=' ')
            if inbound_msg.data[1] == 0x00:
                print('(Failed)')
                print(f"\033[93mWARNING: Modem transmission failed. This typically indicates that it is not connected. The MIME content was not transferred.\033[0m")
            elif inbound_msg.data[1] == 0x01:
                print('(Success)')

        elif inbound_msg.arbitration_id == 0x1CABCD and inbound_msg.data[0] == 0x05:
            if inbound_msg.data[1] == 0x00:
                print('|| External Device Channel Disabled')
            elif inbound_msg.data[1] == 0x01:
                print('|| External Device Channel Enabled')

        elif inbound_msg.arbitration_id == 0x0BABCD:
            print('|| TX Data')
            tx_ack_index += 1
            if tx_ack_index == 2:
                print(f"\033[92mSUCCESS! The MyGeotab database has received the MIME message and it can be pulled via API.\033[0m")
    
        elif inbound_msg.arbitration_id == 0x260000:
            print('|| GO Status Information Log')

        else:
            print('|| Unclassified Message')

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    print('\n\rKeyboard interrupt\nBringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")

except Exception as e:
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")
    print('Bringing down CAN0...')
    os.system("sudo /sbin/ip link set can0 down")