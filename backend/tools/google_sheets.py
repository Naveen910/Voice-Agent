from langchain.tools import tool
from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Replace with your actual spreadsheetId
SPREADSHEET_ID = "1Y-YcuDIvVRgud5-IHap_0_ZFqTTqfnEZtZfoOXofE94"
RANGE_NAME = "Menu!A2:B6"

@tool("[google_sheets_menu_tool]", return_direct=True)
def google_sheets_menu_tool(input_str: str) -> str:
    """
    Fetches the restaurant menu from Google Sheets.
    Just pass any string (ignored if not needed).
    """
    return fetch_menu_from_google_sheets()
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get("values", [])

        if not values:
            return "Sorry, the menu is currently empty."
        
        menu = "\n".join([f"{row[0]} - {row[1]}" for row in values if len(row) >= 2])
        return f"Here’s our menu:\n{menu}"
    except Exception as e:
        return f"Error fetching menu: {str(e)}"
