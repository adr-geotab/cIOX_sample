import can
import time
import datetime
import os

print('\n\rCAN MIME Test')
print('Bringing up CAN0...')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
poll_count = 0

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
        print('GO->cIOX:', datetime.datetime.fromtimestamp(inbound_msg.timestamp), f'0x{inbound_msg.arbitration_id:08X}', hex(inbound_msg.dlc), ''.join(format(x, '02x') for x in inbound_msg.data), end='')
        
        if (inbound_msg.arbitration_id == 0x00010000 and poll_count == 0): 
            poll_count += 1
            print("|| Poll Request")
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=[0x01, 0x01, 0x00, 0x07, 0x01, 0x00, 0x00, 0x9A], timestamp=time.time())
            print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| Poll Response (Handshake)')
            bus.send(outbound_msg)

        elif (inbound_msg.arbitration_id == 0x0014ABCD): 
            print(f'|| Acknowledgement of 0x{prev_outbound_msg.arbitration_id:08X}')

            if poll_count == 2:
                poll_count += 1
                outbound_msg = can.Message(arbitration_id=0x0025ABCD, data=[0x01, 0x00, 0x00], timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-1')
                bus.send(outbound_msg)

            elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x0025ABCD':
                outbound_msg = can.Message(arbitration_id=0x000CABCD, data=[0x00, 0x0A, 0x69, 0x6D, 0x61, 0x67, 0x65, 0x2F], timestamp=time.time())
                print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-2')
                bus.send(outbound_msg)

            # elif f'0x{prev_outbound_msg.arbitration_id:08X}' == '0x00CABCD': # and prev_outbound_msg.data[0] == 0x00:
            #     outbound_msg = can.Message(arbitration_id=0x000CABCD, data=[0x6A, 0x70, 0x65, 0x67, 0x0C, 0x00, 0x00, 0x00], timestamp=time.time())
            #     print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| MIME-3')
            #     print(prev_outbound_msg.data)
            #     print(prev_outbound_msg.data[0])
            #     raise KeyboardInterrupt
            #     bus.send(outbound_msg)

        elif (inbound_msg.arbitration_id == 0x00010000 and poll_count > 0):
            poll_count +=1
            print('|| Poll Request')
            outbound_msg = can.Message(arbitration_id=0x0002ABCD, data=[0x00], timestamp=time.time())
            print('cIOX->GO:', datetime.datetime.fromtimestamp(outbound_msg.timestamp), f'0x{outbound_msg.arbitration_id:08X}', f'|| Poll Response')
            bus.send(outbound_msg)

        elif inbound_msg.arbitration_id == 0x260000:
            print(' || GO Status Information Log')

        else:
            print('|| Unclassified Message')

        prev_outbound_msg = outbound_msg

except KeyboardInterrupt:
    # Catch keyboard interrupt
    os.system("sudo /sbin/ip link set can0 down")
    print('\n\rKeyboard interrupt')