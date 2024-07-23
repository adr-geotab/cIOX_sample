function sendTextMessage(deviceID, mimeType, mimeContent) {
    // Encode the MIME content in base64
    const encodedContent = btoa(mimeContent);
    
    // Prepare the data object for the API call
    const data = {
        "typeName": "TextMessage",
        "entity": {
            "device": {"id": deviceID},
            "messageContent": {
                "contentType": "MimeContent",
                "channelNumber": 1,
                "mimeType": mimeType,
                "binaryDataPacketDelay": "00:00:03.0000000",
                "data": encodedContent
            },
            "isDirectionToVehicle": true,
            "messageSize": 1000
        }
    };

    // Make the API call
    api.call("Add", data, function(result) {
        console.log("MIME sent with ID", result);
    }, function(e) {
        console.error("Failed:", e);
    });
}

// Ensure that the device ID is correct; we used b21 for this sample.
sendTextMessage("b21", "text/markdown", "The quick brown fox jumps over the lazy dog, while the cat watches calmly from its spot on the sofa.");