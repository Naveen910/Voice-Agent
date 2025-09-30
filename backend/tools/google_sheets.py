from langchain.tools import Tool
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "..", "..", "..", "keys", "service_account.json")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Replace with your actual spreadsheetId
SPREADSHEET_ID = "1Y-YcuDIvVRgud5-IHap_0_ZFqTTqfnEZtZfoOXofE94"
RANGE_NAME = "Menu!A2:B6"


def fetch_menu(_: str) -> str:
    """
    Fetches the restaurant menu from Google Sheets.
    Input string is ignored, just here to satisfy Tool signature.
    Returns a structured menu string that LLM can rephrase for customers.
    """
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
            return "Menu is empty."

        # Structured output
        menu_items = [{"item": row[0], "price": row[1]} for row in values if len(row) >= 2]
        menu_lines = [f"{item['item']} - {item['price']}" for item in menu_items]

        return "MENU DATA:\n" + "\n".join(menu_lines)

    except Exception as e:
        return f"Error fetching menu: {str(e)}"


google_sheets_menu_tool = Tool(
    name="Google Sheets Menu",
    func=fetch_menu,
    description="Fetch the restaurant menu from Google Sheets. Returns a structured menu list with item and price."
)
