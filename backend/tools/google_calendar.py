from langchain.agents import Tool
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime
import dateparser
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "..", "..", "..", "keys", "service_account.json")

# Scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Your calendar-agent email must have access to the target calendar
CALENDAR_ID = "nav.fortesting@gmail.com"  
def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=creds)
    return service

def create_event(event_text: str) -> str:
    """
    Creates a Google Calendar event from natural language input using a service account.
    """

    service = get_calendar_service()

    # Parse datetime from text
    parsed_dt = dateparser.parse(
        event_text,
        settings={
            "TIMEZONE": "Asia/Kolkata",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.datetime.now(),
        },
    )

    if not parsed_dt:
        start_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        end_time = start_time + datetime.timedelta(hours=1)
    else:
        start_time = parsed_dt
        end_time = start_time + datetime.timedelta(hours=1)

    # Event body
    event = {
        "summary": event_text,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
    }

    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return f"✅ Event created: {created_event.get('summary')} at {created_event.get('start').get('dateTime')}"

# Export as LangChain tool
google_calendar_tool = Tool(
    name="Google Calendar",
    func=lambda x: create_event(x), check_event=True, delete_event=True,
    description=(
        "Use this tool to create Google Calendar events. "
        "Input should be a plain text description of the event"
    ),
    return_direct=True,
)
