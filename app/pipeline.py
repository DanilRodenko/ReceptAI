import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import DATE_FORMAT, SERVICE_DURATION_MINUTES, TIME_FORMAT, TIMEZONE
from app.llm import chat, extract
from app.prompts import get_extraction_prompt, get_system_prompt
from app.rules import is_working_day, validate_booking
from app.sheets import add_booking, get_booked_slots

FIELDS = ("name", "service", "date", "time", "notes")
REQUIRED_FIELDS = ("name", "service", "date", "time")

# Phrases Sarah must not say on her own: only the code decides what is booked or checked.
CLAIMS_BOOKING = re.compile(r"\b(booked|confirmed|scheduled|reserved)\b", re.IGNORECASE)
STALLING = re.compile(r"get back to you|i['’]?ll check|let me check", re.IGNORECASE)
WEEKDAY = re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE)


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


def requested_day(draft: dict) -> date | None:
    try:
        return datetime.strptime(str(draft.get("date")), DATE_FORMAT).date()
    except ValueError:
        return None


def spoken_day(day: date) -> str:
    """'Saturday the 17th of October' - the weekday is computed by code, never by the model."""
    suffix = "th" if 11 <= day.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day.day % 10, "th")
    return f"{day:%A} the {day.day}{suffix} of {day:%B}"


def spoken_time(start: datetime) -> str:
    return start.strftime("%I:%M %p").lstrip("0")


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


def _decide(session: dict, confirmed: bool, now: datetime) -> tuple[str, str]:
    """Move the state machine one step.

    Returns (note, fallback): an instruction for Sarah and a safe ready-made reply
    that is used if Sarah's own reply breaks the rules.
    """
    draft = session["draft"]

    day = requested_day(draft)
    if day and not is_working_day(day):  # reject a closed day early, before asking for the time
        session["state"] = "collecting"
        return (
            f"SYSTEM: The clinic is closed on {spoken_day(day)}. Nothing is booked. "
            "Tell the patient and ask for another day.",
            f"I'm sorry, we're closed on {spoken_day(day)}. Which other day would suit you?",
        )

    missing = missing_fields(draft)
    if missing:
        session["state"] = "collecting"
        known_day = f" The requested day is {spoken_day(day)}." if day else ""
        return (
            f"SYSTEM: Still missing: {', '.join(missing)}.{known_day} Nothing is booked. "
            "Ask the patient for the missing details.",
            f"Could you tell me the {' and '.join(missing)} for your appointment?",
        )

    start = requested_start(draft)
    if start is None:
        session["state"] = "collecting"
        return (
            "SYSTEM: The date or time could not be understood. Nothing is booked. "
            "Ask the patient to repeat the date and time.",
            "Sorry, I didn't catch the date and time. Could you repeat them?",
        )

    reason = validate_booking(start, draft["service"], get_booked_slots(), now)
    if reason:
        session["state"] = "collecting"
        return (
            f"SYSTEM: {spoken_day(start.date())} at {spoken_time(start)} is not possible. "
            f"Reason: {reason} Nothing is booked. Tell the patient and ask for another time.",
            f"I'm sorry, {spoken_day(start.date())} at {spoken_time(start)} isn't possible. "
            f"{reason} Which other time would suit you?",
        )

    summary = f"{draft['service'].replace('_', ' ')} for {draft['name']} on {spoken_day(start.date())} at {spoken_time(start)}"

    if session["state"] == "confirming" and confirmed:  # the ONLY place where a booking is written
        duration = SERVICE_DURATION_MINUTES[draft["service"]]
        code = add_booking(draft["name"], draft["service"], start, duration, draft["notes"] or "")
        session["state"] = "booked"
        session["booking_code"] = code
        spoken_code = ", ".join(code)
        return (
            f"SYSTEM: Booking saved: {summary}. Booking code: {code}. "
            "Tell the patient it is booked and read the code digit by digit.",
            f"You're all booked: {summary}. Your booking code is {spoken_code}.",
        )

    session["state"] = "confirming"
    return (
        f"SYSTEM: The slot is available but NOT booked yet: {summary}. "
        "Read these details back and ask the patient to confirm.",
        f"Just to confirm: {summary}. Shall I book it?",
    )


def _breaks_rules(reply: str, session: dict, just_booked: bool) -> bool:
    """True if Sarah's reply says something only the code is allowed to decide."""
    if not reply.strip() or STALLING.search(reply):
        return True
    day = requested_day(session["draft"])
    mentioned = {name.lower() for name in WEEKDAY.findall(reply)}
    if day and mentioned and f"{day:%A}".lower() not in mentioned:
        return True  # Sarah named a weekday that is not the requested date's weekday
    if just_booked:
        digits = re.sub(r"\D", "", reply)
        return session["booking_code"] not in digits  # the patient must hear the code
    if session["state"] == "booked":
        return False  # already booked earlier: small talk is fine
    return bool(CLAIMS_BOOKING.search(reply))  # nothing is booked yet


def handle_turn(session: dict, user_text: str, now: datetime) -> str:
    session["history"].append({"role": "user", "content": user_text})
    was_booked = session["state"] == "booked"

    if was_booked:
        spoken_code = ", ".join(session["booking_code"])
        note = (
            f"SYSTEM: The appointment is already booked with code {session['booking_code']}. "
            "Do not book again. Answer the patient politely."
        )
        fallback = f"Your appointment is already booked. Your booking code is {spoken_code}."
    else:
        extraction_messages = session["history"] + [
            {"role": "system", "content": get_extraction_prompt(now.date())}
        ]
        extracted = extract(extraction_messages)
        session["draft"] = merge_draft(session["draft"], extracted)
        note, fallback = _decide(session, extracted.get("confirmed") is True, now)

    messages = (
        [{"role": "system", "content": get_system_prompt(now.date())}]
        + session["history"]
        + [{"role": "system", "content": note}]
    )
    reply = chat(messages)
    just_booked = session["state"] == "booked" and not was_booked
    if _breaks_rules(reply, session, just_booked):
        reply = fallback  # guardrail: never let the model claim something the code did not do

    session["history"].append({"role": "assistant", "content": reply})
    return reply