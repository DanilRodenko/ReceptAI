import os
import gspread
from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
gc = gspread.service_account(filename="credentials.json")


def get_booked_slots():
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)
    records = worksheet.get_all_records()
    booked_slots = [(str(r['date']), str(r['time'])) for r in records]
    return booked_slots


def is_slot_available(date, time, booked_slots):
    for booked_slot in booked_slots:
        if booked_slot == (date, time):
            return False
    return True


def save_appointment(name, date, time):
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)
    worksheet.append_row([name, date, time], value_input_option='USER_ENTERED')
    return True