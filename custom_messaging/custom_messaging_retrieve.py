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

# Fetch the CustomData objects
def fetch_custom_data(api, hours_threshold, results_limit=10000):
    custom_data = api.get(
        "CustomData",
        resultsLimit=results_limit
    )
    custom_data_sorted = sorted(custom_data, key=lambda x: x['dateTime'])

    # impose filtering
    current_time = datetime.now(pytz.UTC)
    threshold_time = current_time - timedelta(hours=hours_threshold)
    response = []
    for message in custom_data_sorted[::-1]:
        if message['dateTime'] > threshold_time:
            try:
                message['decodedData'] = base64.b64decode(message['data']).decode('utf-8')
            except UnicodeDecodeError:
                message['decodedData'] = None # invalid ASCII
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
    with open('custom_messaging/response.json', 'w') as f:
        f.write(json_response)
    print(f"Found {len(response['response'])} messages, exported to 'custom_messaging/response.json'.")
    
    return

def main():
    # Load environment variables from .env file
    load_dotenv()
    username = os.getenv('MYGEOTAB_USERNAME')
    database = os.getenv('MYGEOTAB_DATABASE')
    server = os.getenv('MYGEOTAB_SERVER', 'my.geotab.com')

    # Define API call params
    hours_threshold = 3*24

    api = authenticate_myg(username, database, server)
    response = fetch_custom_data(api, hours_threshold)
    export_response(response, hours_threshold, database)

    return

if __name__ == '__main__':
    main()