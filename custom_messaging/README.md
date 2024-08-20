# Custom Messaging Sample
This directory demonstrates how to send custom messages from the IOX to the GO device over CAN and MyGeotab API. The data is transmitted in multi-frame data logs (0x1E) of the third party free format data type (0x00). A custom message is defined and constructed in 0x1E format, which is then sent to the GO device and subsequently pushed to the MyGeotab cloud. As such, this data is then read and then decoded to retrieve the original custom message. The multi-frame data log transmissions can occur at any time following the handshake. This custom messaging differs from [MIME messaging](../MIME_outbound) in that the payload length is limited to 27 bytes, there are no integrated content types, and that there are no 0x25 packet wrappers. As such, 0x1E logs are preferrable for more simple messaging.

## custom_messaging.py
This script is responsible for constructing the payload from the custom message string then sending it to the GO device. It runs on the IOX device, logs all inbound messages, and has three primary functions.
1. Upon bringing up the CAN bus, the IOX handshakes (0x02) in response to the first poll request (0x01) and responds to all other poll requests. 
2. After the second poll request is acknowledged by the GO device (0x14), the IOX sends the external device ID through 0x1D type 0x01.
3. Converts the custom string to properly structured 0x1E payloads, then sequentially sends the payloads upon 0x14 ACK responses from the previous payload.

The GO device receives the 0x1E multi-frame data log and pushes it to the MyGeotab cloud, which can be interacted with through the API. Unlike MIME messaging, the GO device does not confirm the reception of messages, other than the 0x14 ACK messages.

### Sample CAN Logging of Custom Messaging
Here is a sample log of pushing a custom 0x1E multi-frame data log to the GO:

![Custom Messaging CAN Logs](../images/custom_messaging.png)

### Protocol Limitations
The maximum length of the multi-frame log data must is 27 bytes. This does not include 0x1E structure overheads, such as frame counters or the data length and type identifier bytes. Since each character is converted to a byte, the maximum length of a message is 27 characters. Messages longer than this threshold will still be sent, but the GO device will truncate all characters following the 27th before sending the data to the server. Note that the inbound ACK messages are still the same and do not indicate an overflow. An example of this is shown below. When pulled from the API, the decoded result is "This message is too long to".

![Custom Messaging Warning](../images/custom_message_warning.png)

## custom_messaging_retrieve.js
This script is responsible for retriving the custom message sent from the GO device. The script contains a function that makes an API get call for the [CustomData](https://developers.geotab.com/myGeotab/apiReference/objects/CustomData) entity. The function then filters to only include CustomData objects that were sent from the vehicle within the last 24 hours. These objects are then sorted by their `dateTime` property, ascending. Each CustomData object then gets a property added named decodedData that decodes the received message from base64 to ASCII. An array of CustomData objects with the applied modifications is logged to the console as the output.

### Sample Retrieved Custom Message
Using [custom_messaging_retrieve.js](custom_messaging_retrieve.js), we can extract and decode the message from the MyGeotab server:

![MyGeotab cloud interface, confirming reception of the message](../images/custom_message_reception.png)
