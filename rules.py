from datetime import date, datetime, timedelta

import holidays

from config import TIMEZONE, OPEN_HOUR, CLOSE_HOUR, WORKING_DAYS, HOLIDAY_COUNTRY, SLOT_MINUTES

ie_holidays = holidays.country_holidays(HOLIDAY_COUNTRY)


def is_working_day(day: date) -> bool:
    return day.weekday() in WORKING_DAYS and day not in ie_holidays

def is_on_grid(start: datetime) -> bool:
    return start.minute % SLOT_MINUTES == 0


def is_within_hours(start: datetime, duration: int) -> bool:
    end = start + timedelta(minutes=duration)
    opening = start.replace(hour=OPEN_HOUR, minute=0)
    closing = start.replace(hour=CLOSE_HOUR, minute=0)
    return start >= opening and end <= closing


def is_in_future(start: datetime, now: datetime) -> bool:
    return start > now


def overlaps(start: datetime, duration: int, booked: list[tuple[datetime, int]]) -> bool:
    new_end = start + timedelta(minutes=duration)
    for booked_start, booked_duration in booked:
        booked_end = booked_start + timedelta(minutes=booked_duration)
        if start < booked_end and new_end > booked_start:
            return True
    return False