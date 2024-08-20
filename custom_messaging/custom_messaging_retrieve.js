// Parse and convert date strings to Date objects
function parseSentDate(sentDate) {
    return new Date(sentDate);
}

// Decode base64 data
function decodeBase64(data) {
    return atob(data);
}

// Get custom messages sent within the past 24 hours from the vehicles
function getRecentCustomMessages() {
    api.call("Get", {
        "typeName": "CustomData",
        "resultsLimit": 10000
    }, function(result) {
        const currentTime = new Date();
        const thresholdTime = new Date(currentTime.getTime() - 24 * 60 * 60 * 1000);

        // Filter for 24 hours, sent from vehicle
        const orderedTextMessages = result;
        const recentMessages = orderedTextMessages.filter(message => {
            const sentDate = parseSentDate(message.dateTime);
            return sentDate > thresholdTime && !message.isDirectionToVehicle;
        });

        // Sort and decode
        recentMessages.sort((a, b) => parseSentDate(a.sent) - parseSentDate(b.sent));
        recentMessages.forEach(message => {
            message.decodedData = decodeBase64(message.data);
        });
        
        // Print the sorted array of recent messages with decoded data
        console.log(recentMessages);
    }, function(e) {
        console.error("Failed:", e);
    });
}

// Call the function
getRecentCustomMessages();