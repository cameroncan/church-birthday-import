# read in all the companionships for ministering

import requests
import json
import os.path
import re

from datetime import date
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar']

# TODO make get_new_data a argument when calling the program
# TODO determine better authentication approach with church website

def main():
    get_new_data = True
    member_list_url = "https://lcr.churchofjesuschrist.org/services/umlu/report/member-list?lang=eng&unitNumber=544043"
    response_text = ""

    if os.path.exists("churchofjesuschrist-credentials.txt"):
        with open("churchofjesuschrist-credentials.txt", "r") as inFile:
            request_cookie = inFile.read()
    else:
        print ("No credentials found for churchofjesuschrist")
        exit(1)

    if get_new_data:
        response = requests.get(url=member_list_url, headers={"Cookie": request_cookie})

        if response.headers.get("content-type") != "application/json":
            print ("Did not receive expected content type, likely an error authenticating with churchofjesuschrist", response.text)
            exit(1)

        response_text = response.text
        with open("./memberList.json", "w") as outfile:
            outfile.write(response_text)

    with open("./memberList.json", "r") as inFile:
        member_list_str = inFile.read()

    data_json = json.loads(member_list_str)

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    todays_date = date.today()

    for member in data_json:
        first_instance_date = str(todays_date.year) + member["birth"]["date"]["date"][4:]
        if '03-16' in member["birth"]["date"]["date"]: # Criteria for testing
            print(first_instance_date)
            event = {
                "summary": member["nameGivenPreferredLocal"] + " " + member["nameFamilyPreferredLocal"] + " Birthday",
                "description": "Wish them a happy birthday today",
                "start": {
                    "date": first_instance_date,
                    "timeZone": "America/Chicago"
                },
                "end": {
                    "date": first_instance_date,
                    "timeZone": "America/Chicago"
                },
                "recurrence": [
                    "RRULE:FREQ=YEARLY"
                ],
                "reminders": {
                    "useDefault": True,
                },
                "transparency": "transparent"
            }

            event = service.events().insert(calendarId="egiv84cn1mhlfjtr4v10pcvf0c@group.calendar.google.com", body=event).execute()
            print ("Event created: %s" % (event.get('htmlLink')))

if __name__ == '__main__':
    main()
