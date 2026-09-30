import functools
from datetime import datetime
from unittest import result

import gspread

from config import GOOGLE_CREDENTIALS_PATH, SPREADSHEET_ID


@functools.lru_cache
def _get_worksheet():
    if not SPREADSHEET_ID:
        raise ValueError("SPREADSHEET_ID is not set in .env")

    gc = gspread.service_account(filename=GOOGLE_CREDENTIALS_PATH)
    return gc.open_by_key(SPREADSHEET_ID).sheet1


def row_to_slot(row):
    date_str = row['date'] + " " + row['time']
    date_n_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    duration = int(row['duration_minutes'])
    result = (date_n_time, duration)
    return result