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