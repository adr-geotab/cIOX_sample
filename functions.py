import can
import time
import datetime

# Construct and send CAN message
def send_outbound_msg(bus, arb_id, data, desc):
    outbound_msg = can.Message(arbitration_id=arb_id, data=data, timestamp=time.time())
    print(f"cIOX->GO9 | {datetime.datetime.fromtimestamp(outbound_msg.timestamp)} | 0x{arb_id:08X} | {hex(len(data))} | {''.join(format(x, '02X') for x in data).ljust(16, ' ')} | {desc}")
    bus.send(outbound_msg)

    return outbound_msg

# Print the type of inbound message based on data and arbitration id
def classify_inbound_msg(inbound_msg, prev_outbound_msg):
    if (inbound_msg.arbitration_id == 0x00010000): 
        print("Poll Request")
    
    elif (inbound_msg.arbitration_id == 0x0014ABCD): 
        print(f'Acknowledgement of 0x{prev_outbound_msg.arbitration_id:08X}')

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
    
    return