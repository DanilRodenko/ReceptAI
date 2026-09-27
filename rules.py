from datetime import date, datetime

import holidays

from config import TIMEZONE, OPEN_HOUR, CLOSE_HOUR, WORKING_DAYS, HOLIDAY_COUNTRY

ie_holidays = holidays.country_holidays(HOLIDAY_COUNTRY)


def is_working_day(day: date) -> bool:
    return day.weekday() in WORKING_DAYS and day not in ie_holidays