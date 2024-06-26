import can
import time
import datetime
import os

print('\n\rCAN MIME Test')
print('Bringing up CAN0...')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
poll_count = 0

# MIME Message to be Sent
# type: text/plain
# payload: Test

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
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=[0x01, 0x01, 0x00, 0x47, 0x39, 0x00, 0x00, 0x9A], timestamp=time.time())
            print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| Poll Response (Handshake)')
            bus.send(outbound_msg)

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            print(f'|| Acknowledgement of 0x{prev_outbound_msg.arbitration_id:08X}')

            if poll_count == 2:
                poll_count += 1
                outbound_msg = can.Message(arbitration_id=0x0025ABCD, data=[0x01, 0x00, 0x00], timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-1 (Beginning Packet Wrapper)')
                bus.send(outbound_msg)

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x0025ABCD' and prev_outbound_msg.data[2] == 0x00:
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=[0x00, 0x0A, 0x74, 0x65, 0x78, 0x74, 0x2F, 0x70], timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-2 (MIME Type)')
                bus.send(outbound_msg)

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and prev_outbound_msg.data[0] == 0x00:
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=[0x6C, 0x61, 0x69, 0x6E, 0x0C, 0x00, 0x00, 0x00], timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-3 (MIME Type)')
                bus.send(outbound_msg)

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and prev_outbound_msg.data[0] == 0x6C:
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=[0x54, 0x65, 0x73, 0x74], timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-4 (MIME Payload)')
                bus.send(outbound_msg)
            
            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x000CABCD' and prev_outbound_msg.data[0] == 0x54:
                outbound_msg = can.Message(arbitration_id=0x0025ABCD, data=[0x01, 0x00, 0x01], timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-5 (Ending Packet Wrapper)')
                bus.send(outbound_msg)

        elif (inbound_msg.arbitration_id == 0x00010000 and poll_count > 0):
            poll_count +=1
            print('|| Poll Request')
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=[0x00], timestamp=time.time())
            print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| Poll Response')
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

        elif inbound_msg.arbitration_id == 0x1CABCD:
            print('|| GO Accept Message to Buffer')
            if inbound_msg.data[0] == 0x00 and inbound_msg.data[1] == 0x00:
                print(f"\033[93mWARNING: Modem transmission failed. This typically indicates that it is not connected. The MIME content was not transferred.\033[0m")

        elif inbound_msg.arbitration_id == 0x260000:
            print('|| GO Status Information Log')

        else:
            print('|| Unclassified Message')

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    # Catch keyboard interrupt
    os.system("sudo /sbin/ip link set can0 down")
    print('\n\rKeyboard interrupt')

except Exception as e:
    os.system("sudo /sbin/ip link set can0 down")
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error details: {e}")