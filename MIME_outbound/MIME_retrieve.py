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

# Fetch the TextMessage data
def fetch_text_messages(api, hours_threshold, results_limit=10000):
    text_messages = api.get(
        "TextMessage",
        resultsLimit=results_limit
    )
    text_messages_sorted = sorted(text_messages, key=lambda x: x['sent'])

    # impose filtering
    current_time = datetime.now(pytz.UTC)
    threshold_time = current_time - timedelta(hours=hours_threshold)
    response = []
    for message in text_messages_sorted[::-1]:
        if message['sent'] > threshold_time:
            if message['messageContent']['contentType'] == 'MimeContent' and not message['isDirectionToVehicle']:
                message['messageContent']['decodedData'] = base64.b64decode(message['messageContent']['data']).decode('utf-8')
                response.append(message)
        else:
            break

    return response

# Export response to JSON
def export_response(response, hours_threshold, database):
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError("Type not serializable")
    
    response = {'callParameters': {
        'database': database,
        'hoursThreshold': hours_threshold,
        'rangeStart': datetime.now(pytz.UTC),
        'rangeEnd': datetime.now(pytz.UTC) - timedelta(hours=hours_threshold),
    }, 'response': response}
    
    json_response = json.dumps(response, indent=4, default=convert_datetime)
    with open('MIME_outbound/response.json', 'w') as f:
        f.write(json_response)
    print(f"Found {len(response['response'])} messages, exported to 'MIME_outbound/response.json'.")
    
    return

def main():
    # Load environment variables from .env file
    load_dotenv()
    username = os.getenv('MYGEOTAB_USERNAME')
    database = os.getenv('MYGEOTAB_DATABASE')
    server = os.getenv('MYGEOTAB_SERVER', 'my.geotab.com')

    # Define API call params
    hours_threshold = 32*24

    api = authenticate_myg(username, database, server)
    response = fetch_text_messages(api, hours_threshold)
    export_response(response, hours_threshold, database)

    return

if __name__ == '__main__':
    main()