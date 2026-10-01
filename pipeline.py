from datetime import datetime
from zoneinfo import ZoneInfo

from config import DATE_FORMAT, SERVICE_DURATION_MINUTES, TIME_FORMAT, TIMEZONE
from llm import chat, extract
from prompts import get_extraction_prompt, get_system_prompt
from rules import validate_booking
from sheets import add_booking, get_booked_slots

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
        return datetime.strptime(date_str, f"{DATE_FORMAT} {TIME_FORMAT}")
    except ValueError:
        return None


def new_session() -> dict:
    return {
        "state": "collecting",
        "history": [],
        "draft": {field: None for field in FIELDS},
        "booking_code": None,
    }


def now_local() -> datetime:
    """Current Dublin time without tzinfo, to match naive datetimes in rules.py."""
    return datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)


def _decide(session: dict, confirmed: bool, now: datetime) -> str:
    """Move the state machine one step and return a note for Sarah."""
    draft = session["draft"]

    missing = missing_fields(draft)
    if missing:
        session["state"] = "collecting"
        return f"SYSTEM: Still missing: {', '.join(missing)}. Ask the patient for it."

    start = requested_start(draft)
    if start is None:
        session["state"] = "collecting"
        return "SYSTEM: The date or time could not be understood. Ask the patient to repeat it."

    reason = validate_booking(start, draft["service"], get_booked_slots(), now)
    if reason:
        session["state"] = "collecting"
        return f"SYSTEM: This booking is not possible. Reason: {reason} Suggest another time."

    if session["state"] == "confirming" and confirmed:  # the ONLY place where a booking is written
        duration = SERVICE_DURATION_MINUTES[draft["service"]]
        code = add_booking(draft["name"], draft["service"], start, duration, draft["notes"] or "")
        session["state"] = "booked"
        session["booking_code"] = code
        return f"SYSTEM: Booking saved. Booking code: {code}. Tell the patient the code digit by digit."

    session["state"] = "confirming"
    summary = f"{draft['name']}, {draft['service']}, {draft['date']} at {draft['time']}"
    return f"SYSTEM: All details are valid: {summary}. Read them back and ask the patient to confirm."


def handle_turn(session: dict, user_text: str, now: datetime) -> str:
    session["history"].append({"role": "user", "content": user_text})

    if session["state"] == "booked":
        note = f"SYSTEM: The appointment is already booked with code {session['booking_code']}. Do not book again."
    else:
        extraction_messages = session["history"] + [
            {"role": "system", "content": get_extraction_prompt(now.date())}
        ]
        extracted = extract(extraction_messages)
        session["draft"] = merge_draft(session["draft"], extracted)
        note = _decide(session, extracted.get("confirmed") is True, now)

    messages = (
        [{"role": "system", "content": get_system_prompt(now.date())}]
        + session["history"]
        + [{"role": "system", "content": note}]
    )
    reply = chat(messages)
    session["history"].append({"role": "assistant", "content": reply})
    return reply