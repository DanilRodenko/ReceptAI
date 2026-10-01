from datetime import datetime
from re import escape


FIELDS = ("name", "service", "date", "time", "notes")

REQUIRED_FIELDS = ("name", "service", "date", "time")

def merge_draft(draft: dict, extracted: dict) -> dict:
    merged = dict(draft)
    for field in FIELDS:
        value = extracted.get(field) 
        if value is not None:
            merged[field] = value

    return merged


def missing_fields(draft: dict) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not draft.get(field)]


def requested_start(draft: dict) -> datetime | None:
    date_str = f"{draft['date']} {draft['time']}"
    try:
        date_n_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return date_n_time
    except ValueError:
        return None