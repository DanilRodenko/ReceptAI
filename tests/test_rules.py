from datetime import date, datetime
from operator import imod
from sys import int_info

import pytest
from app.rules import (
    is_on_grid,
    is_within_hours,
    is_working_day,
    overlaps,
    validate_booking,
)

NOW = datetime(2026, 10, 5, 12, 0)  # Monday noon, fixed for all tests
BOOKED = [(datetime(2026, 10, 6, 10, 0), 60)]  # existing appointment 10:00–11:00


@pytest.mark.parametrize(
    "day, expected",
    [
        (date(2026, 10, 6), True),    # Tuesday
        (date(2026, 10, 3), False),   # Saturday
        (date(2026, 12, 25), False),  # Christmas (Friday)
        (date(2026, 10, 26), False),  # October bank holiday (Monday)
    ],
)
def test_is_working_day(day, expected):
    assert is_working_day(day) == expected


@pytest.mark.parametrize(
    "start, expected",
    [
        (datetime(2026, 10, 6, 10, 0), True),
        (datetime(2026, 10, 6, 10, 30), True),
        (datetime(2026, 10, 6, 11, 12), False),  # off the 30-min grid
    ],
)
def test_is_on_grid(start, expected):
    assert is_on_grid(start) == expected


@pytest.mark.parametrize(
    "start, duration, expected",
    [
        (datetime(2026, 10, 6, 9, 0), 30, True),     # first slot of the day
        (datetime(2026, 10, 7, 16, 30), 30, True),   # ends exactly at 17:00
        (datetime(2026, 10, 6, 16, 30), 60, False),  # ends 17:30, after closing
        (datetime(2026, 10, 7, 8, 30), 30, False),   # before opening
    ],
)
def test_is_within_hours(start, duration, expected):
    assert is_within_hours(start, duration) == expected


@pytest.mark.parametrize(
    "start, duration, expected",
    [
        (datetime(2026, 10, 6, 10, 30), 30, True),  # inside 10:00–11:00
        (datetime(2026, 10, 6, 11, 0), 30, False),  # starts right at 11:00, touching is fine
        (datetime(2026, 10, 6, 9, 30), 60, True),   # 9:30–10:30 runs into 10:00
    ],
)
def test_overlaps(start, duration, expected):
    assert overlaps(start, duration, BOOKED) == expected


@pytest.mark.parametrize(
    "start, service, expected_reason",
    [
        (datetime(2026, 10, 6, 11, 0), "whitening", "Unknown service"),
        (datetime(2026, 10, 5, 10, 0), "cleaning", "past"),           # before NOW
        (datetime(2026, 10, 10, 10, 0), "cleaning", "closed"),        # Saturday
        (datetime(2026, 10, 6, 11, 15), "cleaning", "every"),         # off the 30-min grid
        (datetime(2026, 10, 6, 16, 30), "extraction", "fit within"),  # 60 min, ends 17:30
        (datetime(2026, 10, 6, 10, 30), "cleaning", "taken"),         # overlaps BOOKED
    ],
)
def test_validate_booking_rejects(start, service, expected_reason):
    reason = validate_booking(start, service, BOOKED, NOW)
    assert reason is not None
    assert expected_reason in reason


def test_valid_booking_returns_none():
    assert validate_booking(datetime(2026, 10, 6, 11, 0), "cleaning", BOOKED, NOW) is None

