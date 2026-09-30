import functools
from datetime import datetime

import gspread

from config import GOOGLE_CREDENTIALS_PATH, SPREADSHEET_ID


@functools.lru_cache
def _get_worksheet():
    if not SPREADSHEET_ID:
        raise ValueError("SPREADSHEET_ID is not set in .env")

    gc = gspread.service_account(filename=GOOGLE_CREDENTIALS_PATH)
    return gc.open_by_key(SPREADSHEET_ID).sheet1


def row_to_slot(row: dict) -> tuple[datetime, int]:
    date_str = row['date'] + " " + row['time']
    date_n_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    duration = int(row['duration_minutes'])

    return date_n_time, duration


def get_booked_slots() -> list[tuple[datetime, int]]:
    rows = _get_worksheet().get_all_records()
    return [row_to_slot(row) for row in rows]
