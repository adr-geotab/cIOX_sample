import can
import time
import datetime
import os

# Send 
def send_outbound_msg(bus, arb_id, data, desc):
    outbound_msg = can.Message(arbitration_id=arb_id, data=data, timestamp=time.time())
    print(f"cIOX->GO9 | {datetime.datetime.fromtimestamp(outbound_msg.timestamp)} | 0x{arb_id:08X} | {hex(len(data))} | {''.join(format(x, '02X') for x in data).ljust(16, ' ')} | {desc}")
    bus.send(outbound_msg)
    return outbound_msg