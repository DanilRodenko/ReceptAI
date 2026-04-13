import os
import json
import gspread
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
    credentials_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    gc = gspread.service_account_from_dict(credentials_dict)
except Exception:
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    gc = gspread.service_account(filename="credentials.json")


def get_booked_slots():
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)
    records = worksheet.get_all_records()
    booked_slots = [
        {
            "date": str(r['date']),
            "time": str(r['time']),
            "duration_minutes": int(r['duration_minute'] or 30)
        }
        for r in records
    ]
    return booked_slots


def is_slot_available(new_date, new_time, new_duration, booked_slots):
    def to_minutes(t_str):
        h, m = map(int, t_str.split(':'))
        return h * 60 + m

    new_start = to_minutes(new_time)
    new_end = new_start + int(new_duration)

    for appt in booked_slots:
        if appt['date'] == new_date:
            exist_start = to_minutes(appt['time'])
            exist_end = exist_start + int(appt['duration_minutes'])
            if new_start < exist_end and new_end > exist_start:
                return False

    return True


def get_all_appointments():
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)
    return worksheet.get_all_records()


def save_appointment(name, date, time, service, duration_minute):
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)
    worksheet.append_row([name, date, time, service, duration_minute], value_input_option='USER_ENTERED')
    return True