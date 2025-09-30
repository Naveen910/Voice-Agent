from langchain.tools import Tool
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dateparser.search import search_dates
import datetime
import dateparser
import os
import re
import calendar

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "..", "..", "..", "keys", "service_account.json")

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = "nav.fortesting@gmail.com"

# ----------------------------
# Google Calendar service
# ----------------------------
def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)

# ----------------------------
# Extractors
# ----------------------------
def extract_party_size(event_text: str):
    match = re.search(r"\bfor\s+(\d+)", event_text, re.IGNORECASE)
    return int(match.group(1)) if match else None

def extract_datetime(event_text: str):
    cleaned_text = re.sub(r"\bfor\s+\d+\b", "", event_text, flags=re.IGNORECASE).strip()
    weekdays = {day.lower(): i for i, day in enumerate(calendar.day_name)}
    tokens = cleaned_text.lower().split()

    weekday_found = None
    for token in tokens:
        if token in weekdays:
            weekday_found = weekdays[token]
            break

    if weekday_found is not None:
        today = datetime.datetime.now(datetime.timezone.utc).astimezone()
        days_ahead = (weekday_found - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        target_date = today + datetime.timedelta(days=days_ahead)
        time_match = re.search(r"\b\d{1,2}(:\d{2})?\s?(am|pm)\b", cleaned_text, re.IGNORECASE)
        time_str = time_match.group(0) if time_match else "7 pm"
        datetime_str = f"{target_date.strftime('%Y-%m-%d')} {time_str}"
        return dateparser.parse(
            datetime_str,
            settings={"TIMEZONE": "Asia/Kolkata", "RETURN_AS_TIMEZONE_AWARE": True},
        )

    results = search_dates(
        cleaned_text,
        settings={
            "TIMEZONE": "Asia/Kolkata",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        },
    )
    return results[0][1] if results else None

def extract_name(event_text: str):
    match = re.search(r"(?:my name is|this is)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", event_text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_phone(event_text: str):
    match = re.search(r"(\+?\d{1,4}[\s-]?\d{6,12})", event_text)
    return match.group(1) if match else None

# ----------------------------
# Event creation (returns dict)
# ----------------------------
def create_event(event_text: str) -> dict:
    service = get_calendar_service()

    party_size = extract_party_size(event_text)
    parsed_dt = extract_datetime(event_text)
    customer_name = extract_name(event_text)
    phone = extract_phone(event_text)

    if not parsed_dt:
        return {"status": "error", "message": "Could not parse date/time from request."}

    start_time = parsed_dt
    end_time = start_time + datetime.timedelta(hours=1)

    title = f"Table for {party_size}" if party_size else "Restaurant Reservation"
    description_lines = []
    if party_size:
        description_lines.append(f"Guests: {party_size}")
    if customer_name:
        description_lines.append(f"Name: {customer_name}")
    if phone:
        description_lines.append(f"Phone: {phone}")
    description_lines.append(f"Original request: {event_text}")
    description = "\n".join(description_lines)

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
    }

    try:
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
        return {
            "status": "confirmed",
            "date": created_event['start']['dateTime'],
            "guests": party_size if party_size else "unspecified",
            "name": customer_name if customer_name else "unspecified",
            "phone": phone if phone else "unspecified",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ----------------------------
# LangChain Tool
# ----------------------------
google_calendar_tool = Tool(
    name="Reservation Calendar",
    func=create_event,
    description="Check availability and book table reservations for customers. Returns structured reservation details (status, date, guests, name, phone).",
)
