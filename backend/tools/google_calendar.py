from langchain.agents import Tool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import os
import dateparser

# Google Calendar API setup
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    creds = None
    token_path = "token.json"

    # Load existing token if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def create_event(event_text: str) -> str:
    """
    Takes a natural language description of an event,
    extracts date & time, and creates it in Google Calendar.
    """

    service = get_calendar_service()

    # Try to parse a datetime from the input text
    parsed_dt = dateparser.parse(event_text, settings={"TIMEZONE": "Asia/Kolkata", "RETURN_AS_TIMEZONE_AWARE": True})

    if not parsed_dt:
        # Fallback: just schedule 1h from now
        start_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        end_time = start_time + datetime.timedelta(hours=1)
    else:
        start_time = parsed_dt
        end_time = start_time + datetime.timedelta(hours=1)  # default 1h duration

    # Format in ISO 8601
    event = {
        "summary": event_text,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return f"✅ Event created: {created_event.get('summary')} at {created_event.get('start').get('dateTime')}"

# Export as LangChain tool
google_calendar_tool = Tool(
    name="Google Calendar",
    func=lambda x: create_event(x),
    description=(
        "Use this tool to create Google Calendar events. "
        "Input should be a plain text description of the event, e.g. "
        "'Schedule meeting with Naveen tomorrow at 10pm'."
    )
)
