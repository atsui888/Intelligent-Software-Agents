# Class for Google Calendar
import datetime
import json
import os.path
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import timedelta
from typing import Union, List, Dict
from dataclasses import dataclass, asdict

"""
thoughts:
I would just store the Time component only without any Zone. Whenever the API has to serve it, add the correct date and convert that as local time to UTC for that date.

Database = 17:00 (use a timestamp without date, hours as byte, minutes as byte, string)

Retrieve = Date where we want the event + Database 17:00 => Convert this from local to UTC

This way you will always serve the correct time in UTC.

?? does google cal require timezone info?

"""


@dataclass
class CalendarEvent:
    idx: int  # for chatbot to refer to, coz user isn't going to name the long cal_id
    cal_id: str  # Google Calendar UUID to identify which calendar
    event_id: str  # Google UUID to id which event in the calendar
    kind: str
    etag: str
    event_type: str
    html_link: str
    status: str
    organiser: dict
    created_date_str: str  # iso format, with "T" as separator
    created_time_str: str
    creator: dict
    updated_date_str: str
    updated_time_str: str
    summary: str
    details: str
    location: str
    start_date_str: str
    start_time_str: str
    end_date_str: str
    end_time_str: str
    attendees: List[Dict]
    color_id: int
    transparency: str
    sequence: int
    reminders: dict

    """
    e.g attendees:
        "attendees": [
                {"email": "atsuishisen@yahoo.com"},
                {"email": "richard.chai@outlook.sg"},
            ]
    """

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class GoogleCalendar:
    # SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    test_cal_url = "https://calendar.google.com/calendar/embed?src=d507fda6b535440f2b3c4caecda1a6b7efb785a192b0fe4e3b8274e5bac269e1%40group.calendar.google.com&ctz=Asia%2FSingapore"

    def __init__(self,
                 calendar_id: str =
                 "d507fda6b535440f2b3c4caecda1a6b7efb785a192b0fe4e3b8274e5bac269e1@group.calendar.google.com"):
        self._creds = None
        self._get_or_load_credentials()
        self._calendar_id = calendar_id
        self._calendar_events = []

    @property
    def calendar_events(self):
        return self._calendar_events

    def _get_or_load_credentials(self):
        if os.path.exists("token.json"):
            self._creds = Credentials.from_authorized_user_file("token.json", GoogleCalendar.SCOPES)
            # If there are no (valid) credentials available, let the user log in.
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                os.remove("token.json")
                self._creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", GoogleCalendar.SCOPES
                )
                self._creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(self._creds.to_json())

    def _clear_events_memory(self):
        self._calendar_events = []

    def with_idx_get_event_id(self, idx: int) -> str:
        for event in self._calendar_events:
            if event.idx == idx:
                return event.event_id

    def with_event_id_remove_event(self, event_id: str):
        self._calendar_events = [
            event
            for event in self._calendar_events
            if event.event_id != event_id
        ]

    def add_to_calender_events_memory(self, events):
        # event keys:
        # dict_keys(['kind', 'etag', 'id', 'status', 'htmlLink', 'created', 'updated', 'summary', 'colorId',
        # 'creator', 'organizer', 'start', 'end', 'transparency', 'iCalUID', 'sequence', 'reminders', 'eventType',
        # 'description', 'attendees'])
        for idx, event in enumerate(events):
            created_date = event.get('created')
            created_date_str = created_date.split('T')[0] if 'T' in created_date else created_date
            created_time_str = created_date.split('T')[1] if 'T' in created_date else '00:00:00'

            updated_date = event.get('updated')
            updated_date_str = updated_date.split('T')[0] if 'T' in updated_date else updated_date
            updated_time_str = updated_date.split('T')[1] if 'T' in updated_date else '00:00:00'

            start = event["start"].get("dateTime", event["start"].get("date"))
            start = start.split('+')[0]
            start_date_str = start.split('T')[0] if 'T' in start else start
            start_time_str = start.split('T')[1] if 'T' in start else '00:00:00'

            end = event["end"].get("dateTime", event["end"].get("date"))
            end = end.split('+')[0]
            end_date_str = end.split('T')[0] if 'T' in end else end
            end_time_str = end.split('T')[1] if 'T' in end else '00:00:00'

            self._calendar_events.append(CalendarEvent(
                idx=idx,
                cal_id=event.get("iCalUID"),
                event_id=event.get("id"),
                kind=event.get("kind"),
                etag=event.get("etag"),
                event_type=event.get("eventType"),
                html_link=event.get("htmlLink"),
                status=event.get('status'),
                organiser=event.get('organizer'),
                created_date_str=created_date_str,
                created_time_str=created_time_str,
                creator=event.get('creator'),
                updated_date_str=updated_date_str,
                updated_time_str=updated_time_str,
                summary=event.get("summary"),
                start_date_str=start_date_str,
                start_time_str=start_time_str,
                end_date_str=end_date_str,
                end_time_str=end_time_str,
                color_id=event.get('colorId'),
                transparency=event.get('transparency'),
                sequence=event.get('sequence'),
                reminders=event.get('reminders'),
                details=event.get('description'),
                attendees=event.get('attendees'),
                location=event.get('location')
            ))

    def get_upcoming_events_by_date(self, desired_date_str: Union[None, str] = None,
                                    desired_time_zone: Union[None, str] = None):
        try:
            service = build("calendar", "v3", credentials=self._creds)

            if desired_time_zone is None:
                desired_time_zone = 'Asia/Singapore'
                # the next line, timezone is not recognised by pytz, don't use
                # desired_time_zone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.__str__()

            # sst_now = datetime.datetime.now(pytz.timezone('Asia/Singapore'))
            if desired_date_str is None:
                sst_start = datetime.datetime.now(pytz.timezone(desired_time_zone))
            else:
                # datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
                sst_start = datetime.datetime.strptime(
                    desired_date_str, "%Y-%m-%d").astimezone(pytz.timezone(desired_time_zone))

            # set end dt to midnight of "now"
            sst_eod = datetime.datetime(sst_start.year, sst_start.month, sst_start.day,
                                        23, 59, 59).astimezone(pytz.timezone('Asia/Singapore'))

            print(f"Getting all events from now until end of day")
            self._clear_events_memory()
            events_result = (
                service.events()
                .list(
                    calendarId=self._calendar_id,
                    timeMin=sst_start.isoformat(),
                    timeMax=sst_eod.isoformat(),
                    # maxResults=num_events,  # if 10, means get the upcoming 10 events
                    singleEvents=True,  # True
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return
            self.add_to_calender_events_memory(events)
            return self._calendar_events
        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_n_upcoming_events(self, num_events: int = 10):
        try:
            service = build("calendar", "v3", credentials=self._creds)

            # Call the Calendar API
            now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            print(f"Getting the upcoming {num_events} events")
            self._clear_events_memory()
            events_result = (
                service.events()
                .list(
                    # calendarId="primary",
                    calendarId=self._calendar_id,
                    timeMin=now,
                    maxResults=num_events,  # if 10, means get the upcoming 10 events
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return

            self.add_to_calender_events_memory(events)
            return self._calendar_events
        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_event_details(self, event_idx: Union[str, int]) -> str:
        """
            try to read as much as possible from get_by_n events and get_by_date
            to store in the list
            so that this method just grabs the data from the list if possible,
            otherwise get via Google api
        :param event_idx:
        :return:
        """
        event_id = self.with_idx_get_event_id(idx=int(event_idx))
        event_details = ""
        for event in self._calendar_events:
            if event.event_id == event_id:
                event_details += f"Event:\t\t{event.summary}\n"
                event_details += f"Created by:\t{event.creator.get('email')}\n"
                event_details += f"Start Date:\t{event.start_date_str}\n"
                event_details += f"Start Time:\t{event.start_time_str}\n"
                event_details += f"End Date:\t{event.end_date_str}\n"
                event_details += f"End Time:\t{event.end_time_str}"
        return event_details

        # raise NotImplementedError()

    def add_event(self, summary: str, location: str = '', details: str = '', color_id: int = 6,
                  start_date_time=None,
                  start_time_zone=None,
                  end_date_time=None,
                  end_time_zone=None,
                  recurrence: Union[None, str] = None,
                  attendees: Union[None, List[Dict]] = None
                  ):
        """

        :param summary:
        :param location:
        :param details:
        :param color_id:
        :param start_date_time: str: e.g. "2024-03-28T18:15:00+08:00" i.e. isoformat
        :param start_time_zone: str: e.g. "Asia/Singapore"
        :param end_date_time:   str: e.g. "2024-03-28T18:15:00+08:00" i.e. isoformat
        :param end_time_zone:   str: e.g. "Asia/Singapore"
        :param recurrence:
        :param attendees: List[Dict] e.g.
            "attendees": [
                            {"email": "atsuishisen@yahoo.com"},
                            {"email": "richard.chai@outlook.sg"},
                        ]
        :return:
        """
        if start_time_zone is None:
            start_time_zone = "Asia/Singapore"
            # the next line doesn't work. the time zone not recognised
            # start_time_zone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.__str__()

        if end_time_zone is None:
            end_time_zone = "Asia/Singapore"
            # the next line doesn't work. the time zone not recognised
            # end_time_zone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.__str__()

        if start_date_time is None and end_date_time is None:
            time_now = datetime.datetime.now()
            end_time = time_now + timedelta(hours=1)  # if not spec, default end_time is 1 hour after start time
            # set to isoformat e.g. "2024-03-28T18:15:00+08:00" with no microseconds, only HH:MM:SS
            start_date_time = time_now.astimezone().replace(microsecond=0).isoformat()
            end_date_time = end_time.astimezone().replace(microsecond=0).isoformat()
        elif start_date_time is not None and end_date_time is None:
            # start_date_time is already in ISO format (else cannot pass in this fn)
            # set end datetime default 1 hour after start datetime and convert to iso format
            tmp = start_date_time.split('+')[0] if '+' in start_date_time else start_date_time
            start_date_time_dt = datetime.datetime.strptime(tmp, '%Y-%m-%dT%H:%M:%S')
            end_time_dt = start_date_time_dt + timedelta(hours=1)
            end_date_time = end_time_dt.astimezone().replace(microsecond=0).isoformat()
        elif start_date_time is None and end_date_time is not None:
            tmp = end_date_time.split('+')[0] if '+' in end_date_time else end_date_time
            end_date_time_dt = datetime.datetime.strptime(tmp, '%Y-%m-%dT%H:%M:%S')
            start_time_dt = end_date_time_dt - timedelta(hours=1)
            start_date_time = start_time_dt.astimezone().replace(microsecond=0).isoformat()

        if recurrence is None:
            # "RRULE:FREQ=DAILY;COUNT=3"  # Count=3, means repeat Freq 3 times i.e. total of 3 days, once a day
            "RRULE:FREQ=DAILY;COUNT=1"
        if attendees is None:
            attendees = []

        try:
            service = build("calendar", "v3", credentials=self._creds)
            event = {
                "summary": summary,
                "location": location,
                "description": details,
                "colorId": color_id,
                "start": {
                    "dateTime": start_date_time,  # e.g. "2024-03-28T18:15:00+08:00"
                    "timeZone": start_time_zone
                },
                "end": {
                    "dateTime": end_date_time,  # e.g. "2024-03-28T18:15:00+08:00"
                    "timeZone": end_time_zone
                },
                "recurrence": [
                    recurrence
                ],
                # "attendees": [
                #     {"email": "atsuishisen@yahoo.com"},
                #     {"email": "richard.chai@outlook.sg"},
                # ]
                "attendees": attendees
            }
            events_result = service.events().insert(calendarId=self._calendar_id, body=event).execute()
            return f"Event created: \n{events_result.get('htmlLink')}"
        except HttpError as error:
            print(f"An error occurred: {error}")

    def delete_event(self, event_id: str):
        try:
            service = build("calendar", "v3", credentials=self._creds)
            service.events().delete(calendarId=self._calendar_id,
                                    eventId=event_id,
                                    sendUpdates='all').execute()  # sendUpdates='all' | 'externalOnly' | 'None'
            # . For calendar migration tasks, consider using the Events.import method instead.
            # https://developers.google.com/calendar/api/v3/reference/events/delete
            # Event deletion notification is sent to attendees and not the calendar owner

            # remove this event from the calendar list so that the state is current.
            self.with_event_id_remove_event(event_id)
        except HttpError as error:
            print(f"An error occurred: {error}")

        pass


if __name__ == "__main__":
    g_cal = GoogleCalendar()

    # Test 1
    print('*' * 50)
    # RES = g_cal.add_event(
    #     summary="my new event 111",
    #     location="Hilton Hotel",
    #     start_date_time="2024-04-29T16:00:00+08:00",  # ""2024-03-28T18:15:00+08:00"
    #     end_date_time="2024-04-29T17:00:00+08:00",
    #     start_time_zone="Asia/Singapore",
    #     end_time_zone="Asia/Singapore",
    #     details="This is a test description.",          # OK
    #     attendees=[                                     # OK
    #         {"email": "atsuishisen@yahoo.com"},
    #         {"email": "richard.chai@outlook.sg"},
    #         ]
    # )
    # print(RES)
    # print('*'*50)

    # Test 2
    # EVENTS = g_cal.get_n_upcoming_events(num_events=1)
    # print('\n', len(EVENTS), '\n')
    # for evt in EVENTS:
    #     for k, v in evt.to_dict().items():
    #         print(k, v)
    # print('\n\n')

    # Test 3
    # EVENTS = g_cal.get_upcoming_events_by_date(desired_date_str='2024-05-05')  # step 1
    # # EVENTS = g_cal.get_upcoming_events_by_date()
    # if EVENTS is None:
    #     print("No tasks found on this day.")
    # else:
    #     # for evt in EVENTS:
    #     #     for k, v in evt.to_dict().items():
    #     #         print(k, v)
    #     # print('*'*50)
    #     print('event details:\n\n')
    #     for evt in EVENTS:
    #         # print(type(evt))
    #         # print(evt)
    #         EVENT_DETAILS = g_cal.get_event_details(evt.idx)  # step 2
    #         print(type(EVENT_DETAILS))
    #         print(evt.idx)
    #         print(EVENT_DETAILS, '\n')
    #     print(g_cal.calendar_events)

    # Test 4 - delete one event_id
    # we do not instantiate a new GoogleCalendar object, coz we want to remove also from the list.
    # coz user may want to remove more than one item in the same convo
    choice = input('\nkey the idx to remove: ')
    EVENT_ID = g_cal.with_idx_get_event_id(int(choice))
    g_cal.delete_event(EVENT_ID)
    EVENTS = g_cal.calendar_events
    for evt in EVENTS:
        for k, v in evt.to_dict().items():
            print(k, v)
    pass

    # Test 5 - get details of a specific event
    # g_cal.get_n_upcoming_events(num_events=1)


    # Test 6 - modify detail/s of the specific event

