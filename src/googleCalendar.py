from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from signal import signal, SIGINT
from sys import exit
import threading

from discordb import MyDiscord
import asyncio
from time import sleep

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Credentials of the Google Calendar API
CREDENTIALS = 'secret.json'
DISCORD_TOKEN = open('disctoken.txt').read()

global disc
disc = None

def discProc():
    global disc
    disc = MyDiscord()
    disc.run(DISCORD_TOKEN)

def bootDiscord():
    th = threading.Thread(target=discProc)
    th.start()

# cumples [
#     cumples {
#         'summary' : string
#         'date' : datetime
#         'honored' : string
#         'message' : string
#     }
# ]
# List of dictionaries with the above structure
birthdays = []

global displayName
displayName = None


def getService():
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
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
                    CREDENTIALS, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('calendar', 'v3', credentials=creds)
        return service


# Gets the Honored of the user if exists
def getHonoredEmail(event):
    guests = event.get('attendees', [])
    if (len(guests) == 1):
        return guests[0].get('email', [])
    if len(guests) == 2:
        honored = guests[1].get('email', [])
        host = event.get('creator', []).get('email', [])
        if honored != host:
            return honored

    return None


# Gets the id of Discord Platform in the description of the event
def getHonored(event):
    message = event.get('description', [])
    if len(message) != 0:
        honored = message.split('\n')[0]
        if honored[0] == '@':
            return honored[1:]


# Get the description of the user and use it like a custom message if exists
def getMessage(event):
    message = event.get('description', [])
    if len(message) != 0:
        lines = message.split('\n')[1:]
        str = ''
        for line in lines:
            str += line + '\n'
        return str


    return None


# Get the date (day, month, year) of the event
def getDate(event):
    date_str = event.get('start', []).get('date', [])
    if type(date_str) is str:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")

    date_str = event.get('start', []).get('dateTime', [])
    if type(date_str) is str:
        return datetime.datetime.strptime(date_str[0:10], "%Y-%m-%d")

    return None


# Get the title of the event
def getSummary(event):
    return event['summary']


# Print an Event
def printEvent(event):
    print(event['summary'], ':')
    date = getDate(event)
    print(date)

    honored = getHonored(event)
    if honored != None:
        print( '\t Homenajeado: ', honored)

        message = getMessage(event)
        if message != None:
            print('\t Mensaje personalizado: ', message)

        print('\n')

    else:
        print('\t No se puede enviar el mensaje porque no hay invitado \n')

# Gets the display name of the creator of an event
def getDisplayName(event):
    global displayName
    displayName = event['creator'].get('displayName', event['creator']['email'])

# Add birthay to birthdays list
def addBirthday(event):
    if not displayName:
        getDisplayName(event)

    honored = getHonored(event)
    summary = getSummary(event)
    if honored is not None:
        date = getDate(event)

        # Creates a dictionary with useful info
        birthday = {
            'summary' : summary,
            'honored' : honored,
            'date' : date
        }

        # If exists a custom message add it
        message = getMessage(event)
        if message is not None:
            birthday['message'] = message

        # Adds to birthdays list the birthday
        birthdays.append(birthday)


# Filter the events of the user to get the birthday events
def filterBirthdays(service):
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    tomorrow = (datetime.datetime.today()).date()
    tomorrow = datetime.datetime.combine(tomorrow, datetime.datetime.max.time())
    tomorrow = tomorrow.isoformat() + 'Z'
    next_t = None
    events = []

    while next_t != '-1':
        events_result = service.events().list(calendarId='primary', timeMin=now, timeMax=tomorrow,
                                        maxResults=2000, singleEvents=True,
                                        orderBy='startTime', pageToken=next_t).execute()
        events += events_result.get('items', [])
        next_t = events_result.get('nextPageToken', '-1')

    for event in events:
        addBirthday(event)


# Print the birthdays list
def printBirthdays():
    for birthday in birthdays:
        print('Titulo: ', birthday['summary'], '\t Homenajeado: ', birthday['honored'], '\t Fecha: ', birthday['date'])
        if 'message' in birthday:
            print('Mensaje personalizado: ', birthday['message'], '\n')


# Get birthdays list
def getBirthdays():
    filterBirthdays(getService())
    return birthdays


# Sends a Discord message
def sendMessage(honored, message):
    global disc, displayName
    disc.enviarMSG(displayName, honored, message)

def main():
    filterBirthdays(getService())
    printBirthdays()

    # # Call the Calendar API
    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    # events_result = service.events().list(calendarId='primary', timeMin=now,
    #                                     maxResults=10, singleEvents=True,
    #                                     orderBy='startTime').execute()
    # events = events_result.get('items', [])
    #
    # if not events:
    #     print('No upcoming events found.')
    # for event in events:
    #     start = event['start'].get('dateTime', event['start'].get('date'))
    #     print(start, event['summary'])

if __name__ == '__main__':
    main()
# [END calendar_quickstart]
