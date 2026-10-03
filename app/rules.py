from datetime import date, datetime, timedelta

import holidays

from app.config import (
    CLOSE_HOUR,
    HOLIDAY_COUNTRY,
    OPEN_HOUR,
    SERVICE_DURATION_MINUTES,
    SLOT_MINUTES,
    WORKING_DAYS,
    MAX_DAYS_AHEAD
)

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


def validate_booking(
    start: datetime,
    service: str,
    booked: list[tuple[datetime, int]],
    now: datetime,
) -> str | None:
    """Return a rejection reason, or None if the booking is valid."""
    if service not in SERVICE_DURATION_MINUTES:
        return f"Unknown service: {service}."
    duration = SERVICE_DURATION_MINUTES[service]

    if not is_in_future(start, now):
        return "This time is in the past."
    if not is_working_day(start.date()):
        return "The clinic is closed on this day."
    if not is_on_grid(start):
        return f"Appointments start every {SLOT_MINUTES} minutes."
    if not is_within_hours(start, duration):
        return f"The appointment must fit within {OPEN_HOUR}:00-{CLOSE_HOUR}:00."
    if overlaps(start, duration, booked):
        return "This time slot is already taken."
    if start.date() > now.date() + timedelta(days=MAX_DAYS_AHEAD):
        return f"Bookings are only possible up to {MAX_DAYS_AHEAD} days ahead."

    return None