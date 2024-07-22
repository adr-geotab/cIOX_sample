# MIME Inbound Messaging Sample
This directory demonstrates how to send and receive MIME messages going from the MyGeotab server to the GO device. The JS script sends the MIME message to the GO device. Following reception of the MIME message from the GO device, the data is sent to the IOX over CAN, then decoded in Python.

To learn more about payload structuring under the MIME protocol, visit the [Geotab docs](https://developers.geotab.com/hardware/guides/mimeProtocol).

## MIME_send.js
This script is responsible for sending the MIME message from MyG to a specified GO device over the cloud. The script contains a function that makes an API add call of the [TextMessage](https://developers.geotab.com/myGeotab/apiReference/objects/TextMessage) entity, taking in 3 parameters: The MyG device ID, the MIME type, and the MIME message content. The content is then encoded in base64, and MyG then internally configures the payloads with all of the higher level MIME protocol structuring. Upon successful execution of the script, it should log the MIME's ID in the console.

## MIME_inbound_sample.py
This script runs on the IOX device and listens for incoming CAN messages from the GO device. Upon bringing up the CAN bus, the IOX handshakes (0x02) in response to the first poll request (0x01) and responds to all other poll requests. After the second poll request is acknowledged by the GO device (0x14), the IOX declares its device ID in a single frame data log (0x1D). This permits the reception of TX data (0x1C), which is necessary for MIME messaging. When sent from the MyG API, the MIME message is received by the GO device and pushed to declared devices over 0x1C. Upon receiving the message, the script processes, decodes, and re-constructs the MIME message under MIME protocol structuring.

### Deoding the MIME Message
This script decodes the MIME message by first identifying which four bytes are associated with communicating the payload length. This indexing is done using Byte 1 of the first 0x1C message, which identifies the length of the MIME type because the MIME payload length immediately follows the MIME type. The length is converted from Little Endian, which provides the bytes associated with the payload. From here, a buffer is filled for both the MIME content and array depending on the iteration's byte index. The payload is converted from hex to ASCII to render legible content. Based on the payload and type length, the expected MIME length is computed, and the message is logged once this threshold is met.

### Sample CAN Logging from Python Script

(Sample Logging Image here)