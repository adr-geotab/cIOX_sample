import can
import time
import datetime
import os

print('\n\rCAN Rx test')
print('Bring up CAN0....')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
count = 0
prev_msg = None
x001dabcd_count = 0

try:
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
except OSError:
    print('Cannot find PiCAN board.')
    exit()

print('Communication session begins\n')

try:
    while True:
        message = bus.recv()  # Wait until a message is received.

        print(datetime.datetime.fromtimestamp(message.timestamp),
              hex(message.arbitration_id), hex(message.dlc), ''.join(format(x, '02x') for x in message.data), end='')
        
        if (message.arbitration_id == 0x00010000 and count == 0): 
            count += 1
            print("|| Handshaking")
            msg = can.Message(arbitration_id=0x0002ABCD, data=[0x01,0x01,0x00, 0x07, 0x01, 0x00, 0x00, 0x9A])
            print(f'Sending Poll Response 0x0{msg.arbitration_id:X}')
            bus.send(msg)
        elif (message.arbitration_id == 0x0014ABCD): 
            print(f"|| Acknowledged", end=' ')
            try:
                print(f'0x{prev_msg.arbitration_id:X}')
            except:
                print()

            if f'0x00{prev_msg.arbitration_id:X}' == f'0x001DABCD' and prev_msg.data[1] == 0x01: # 1st single frame data log was ackowledged
                msg = can.Message(arbitration_id=0x001EABCD, data=[0x00,0x00,0x07, 0x00, 0x01, 0x23, 0x45, 0x67])
                print('Sending Free Format Third Party Data (1st Frame) 0x1EABCD')
                bus.send(msg)
            elif f'0x00{prev_msg.arbitration_id:X}' == f'0x001EABCD' and prev_msg.data[0] == 0x00: # multi frame log (1) was ackowledged
                msg = can.Message(arbitration_id=0x001EABCD, data=[0x01,0x89,0xAB, 0xCD])
                print('Sending Free Format Third Party Data (2nd Frame) 0x1EABCD')
                bus.send(msg)
            elif f'0x00{prev_msg.arbitration_id:X}' == f'0x001EABCD' and prev_msg.data[0] == 0x01: # multi frame log (2) was ackowledged
                msg = can.Message(arbitration_id=0x001DABCD, data=[0x00,0xD2,0x0A,0x01,0x64])
                print('Sending Status Data 0x1DABCD')
                bus.send(msg)
            elif f'0x00{prev_msg.arbitration_id:X}' == f'0x001DABCD' and prev_msg.data[1] == 0xD2 and x001dabcd_count == 0: # 2nd single frame data log was ackowledged
                x001dabcd_count += 1
                msg = can.Message(arbitration_id=0x001DABCD, data=[0x00,0xD2,0x0A,0x01,0x64])
                print('Sending Priority Status Data 0x1DABCD')
                bus.send(msg)

        elif (message.arbitration_id == 0x00010000 and count >0):
            count +=1
            print('|| Poll Request')
            msg = can.Message(arbitration_id=0x0002ABCD, data=[0x00])
            print(f'Sending Poll Response 0x0{msg.arbitration_id:X}')
            bus.send(msg)
            continue
        elif message.arbitration_id == 0x260000:
            print(' || GO Status Information Log')
        else:
            print('|| Unclassified Message')
        
        if count == 2:
            count += 1
            print("Sending External Device ID 0x1DABCD")
            msg = can.Message(arbitration_id=0x001DABCD, data=[0x01,0x01,0x70, 0x10, 0x01, 0x00])
            bus.send(msg)

        prev_msg = msg
        
except KeyboardInterrupt:
    # Catch keyboard interrupt
    os.system("sudo /sbin/ip link set can0 down")
    print('\n\rKeyboard interrupt')