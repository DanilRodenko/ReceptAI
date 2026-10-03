from datetime import datetime

from app import sheets
from app.sheets import generate_booking_code, row_to_slot


def test_row_to_slot_parses_date_time_and_duration():
    row = {"name": "Test", "service": "cleaning", "date": "2026-10-06",
           "time": "10:00", "duration_minutes": 30, "notes": ""}

    assert row_to_slot(row) == (datetime(2026, 10, 6, 10, 0), 30)


def test_row_to_slot_converts_duration_string_to_int():
    row = {"name": "Test", "service": "cleaning", "date": "2026-10-06",
           "time": "10:00", "duration_minutes": "60", "notes": ""}

    _, duration = row_to_slot(row)

    assert duration == 60
    assert isinstance(duration, int)


# --- booking codes ---

def test_booking_code_is_six_digit_string():
    code = generate_booking_code(set())

    assert isinstance(code, str)
    assert len(code) == 6
    assert code.isdigit()


def test_booking_code_keeps_leading_zeros(monkeypatch):
    monkeypatch.setattr(sheets.secrets, "randbelow", lambda n: 42)

    assert generate_booking_code(set()) == "000042"


def test_booking_code_skips_codes_already_taken(monkeypatch):
    # The fake generator returns 111111 first (already taken), then 222222.
    values = iter([111111, 222222])
    monkeypatch.setattr(sheets.secrets, "randbelow", lambda n: next(values))

    assert generate_booking_code({"111111"}) == "222222"


# --- add_booking with a fake worksheet (no network) ---

class FakeWorksheet:
    """Mimics a gspread worksheet: keeps rows in memory and records appended rows."""

    def __init__(self, records):
        self.records = records
        self.appended = []

    def get_all_records(self):
        return self.records

    def append_row(self, values, value_input_option=None):
        self.appended.append((values, value_input_option))


def test_add_booking_writes_row_in_column_order_and_returns_code(monkeypatch):
    sheet = FakeWorksheet(records=[{"booking_code": "111111"}])
    monkeypatch.setattr(sheets, "_get_worksheet", lambda: sheet)

    code = sheets.add_booking("Alex Murphy", "cleaning", datetime(2026, 10, 7, 14, 30), 30, "toothache")

    values, input_option = sheet.appended[0]
    assert values == [code, "Alex Murphy", "cleaning", "2026-10-07", "14:30", 30, "toothache"]
    assert input_option == "RAW"
    assert code != "111111"
    assert len(code) == 6 and code.isdigit()