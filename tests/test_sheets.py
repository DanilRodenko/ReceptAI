from datetime import datetime

from sheets import row_to_slot


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