import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Path to your service account key file
SERVICE_ACCOUNT_FILE = "C:\\Users\\naman\\Downloads\\watchful-slice-443014-f0-d76a3b946911.json"

# Create credentials using the service account file
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID of the spreadsheet to access (only the ID, not the full URL)
SPREADSHEET_ID = '1uNJAXOhewG7DxIVBGY1ppGv3e74AUvSbmYz_zmCaN8E'

# Initialize the Sheets API service
service = build('sheets', 'v4', credentials=credentials)

# Example: Reading data from a sheet
def read_sheet(range_name):
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        values = result.get('values', [])
        if not values:
            print('No data found.')
        else:
            print('Data:')
            for row in values:
                print(row)
    except HttpError as err:
        logger.error(f"An error occurred: {err}")
        print(f"An error occurred: {err}")

# Example: Writing data to a sheet
def write_sheet(range_name, values):
    try:
        sheet = service.spreadsheets()
        body = {'values': values}
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        print(f"{result.get('updatedCells')} cells updated.")
    except HttpError as err:
        logger.error(f"An error occurred: {err}")
        print(f"An error occurred: {err}")

# Example Usage
if __name__ == '__main__':
    # Replace with your desired range, e.g., 'Sheet1!A1:C10'
    read_range = 'Sheet1!A1:C10'
    read_sheet(read_range)

    # Data to write (list of lists)
    write_values = [
        ['Name', 'Age', 'City'],
        ['Alice', '30', 'New York'],
        ['Bob', '25', 'Los Angeles']
    ]
    write_range = 'Sheet1!A12:C14'
    write_sheet(write_range, write_values)
