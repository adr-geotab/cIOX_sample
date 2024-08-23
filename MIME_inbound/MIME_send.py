import os
import json
import pytz
import base64
import mygeotab
from getpass import getpass
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Authenticate with MyGeotab to ensure user has access, then return mygeotab.API object
def authenticate_myg(username, database, server='my.geotab.com'):
    api = mygeotab.API(username=username, password=getpass('MyGeotab Password: '), database=database, server=server)
    api.authenticate()
    return api

# Function to send a MIME message to MyG
def send_text_message(api, device_id, mime_type, mime_content):
    # Encode the MIME content in base64
    encoded_content = base64.b64encode(mime_content.encode('utf-8')).decode('utf-8')

    # Prepare the payload object for the API call
    payload = {
        "typeName": "TextMessage",
        "entity": {
            "device": {"id": device_id},
            "messageContent": {
                "contentType": "MimeContent",
                "channelNumber": 1,
                "mimeType": mime_type,
                "binaryDataPacketDelay": "00:00:03.0000000",
                "data": encoded_content
            },
            "isDirectionToVehicle": True,
            "messageSize": 1000
        }
    }

    try:
        # Make the API call to send the text message
        result = api.add(payload['typeName'], payload['entity'])
        print("MIME sent with ID", result)
        return True
    except Exception as e:
        print("Failed:", e)
    
    return False

def main():
    # Load environment variables from .env file
    load_dotenv()
    username = os.getenv('MYGEOTAB_USERNAME')
    database = os.getenv('MYGEOTAB_DATABASE')
    server = os.getenv('MYGEOTAB_SERVER', 'my.geotab.com')

    # Define the MIME message and receiving device
    MIME_TYPE = "text/markdown"
    MIME_CONTENT = "The quick brown fox jumps over the lazy dog, while the cat watches calmly from its spot on the sofa."
    DEVICE_ID = "b21"

    # Make API call
    api = authenticate_myg(username, database, server)
    result = send_text_message(api, DEVICE_ID, MIME_TYPE, MIME_CONTENT)

    return

if __name__ == '__main__':
    main()