from datetime import datetime

import pytest

from app import pipeline
from app.pipeline import merge_draft, missing_fields, new_session, requested_start

NOW = datetime(2026, 10, 5, 12, 0)  # Monday noon


# --- pure helpers ---

def test_merge_draft_keeps_old_values_when_new_ones_are_missing():
    draft = {"name": "Alex", "service": "cleaning", "date": None, "time": None, "notes": None}
    extracted = {"name": None, "service": None, "date": "2026-10-06", "time": "10:00", "notes": None}

    merged = merge_draft(draft, extracted)

    assert merged == {"name": "Alex", "service": "cleaning", "date": "2026-10-06",
                      "time": "10:00", "notes": None}
    assert draft["date"] is None  # the original draft is not modified


def test_missing_fields_ignores_optional_notes():
    draft = {"name": "Alex", "service": "cleaning", "date": "2026-10-06", "time": None, "notes": None}

    assert missing_fields(draft) == ["time"]


def test_requested_start_returns_none_for_bad_format():
    assert requested_start({"date": "2026-10-06", "time": "10:00"}) == datetime(2026, 10, 6, 10, 0)
    assert requested_start({"date": "2026-10-06", "time": "10am"}) is None


# --- state machine with fakes (no LLM, no Google) ---

class FakeWorld:
    """Replaces every external call that pipeline makes and records what happened."""

    def __init__(self, extractions, booked_slots=None):
        self.extractions = list(extractions)  # what extract() returns on each turn, in order
        self.booked_slots = booked_slots or []
        self.notes = []  # SYSTEM notes that Sarah received
        self.saved = []  # every add_booking call
        self.sarah_says = "Sure, one moment."  # what the fake chat model replies

    def extract(self, messages):
        return self.extractions.pop(0)

    def chat(self, messages):
        self.notes.append(messages[-1]["content"])
        return self.sarah_says

    def get_booked_slots(self):
        return self.booked_slots

    def add_booking(self, name, service, start, duration, notes):
        self.saved.append((name, service, start, duration))
        return "004821"


@pytest.fixture
def world(monkeypatch):
    def _install(extractions, booked_slots=None):
        fake = FakeWorld(extractions, booked_slots)
        monkeypatch.setattr(pipeline, "extract", fake.extract)
        monkeypatch.setattr(pipeline, "chat", fake.chat)
        monkeypatch.setattr(pipeline, "get_booked_slots", fake.get_booked_slots)
        monkeypatch.setattr(pipeline, "add_booking", fake.add_booking)
        return fake

    return _install


NAME_AND_SERVICE = {"name": "Alex Murphy", "service": "cleaning", "confirmed": False}
TUESDAY_10 = {"date": "2026-10-06", "time": "10:00", "confirmed": False}
YES = {"confirmed": True}


def test_happy_path_books_exactly_once(world):
    fake = world([NAME_AND_SERVICE, TUESDAY_10, YES])
    session = new_session()

    pipeline.handle_turn(session, "Hi, I'm Alex Murphy, I need a cleaning", NOW)
    assert session["state"] == "collecting"

    pipeline.handle_turn(session, "Tuesday at 10", NOW)
    assert session["state"] == "confirming"

    pipeline.handle_turn(session, "Yes, please", NOW)
    assert session["state"] == "booked"
    assert session["booking_code"] == "004821"

    pipeline.handle_turn(session, "Thanks, bye", NOW)  # the v1 double-booking moment
    assert len(fake.saved) == 1
    assert fake.saved[0] == ("Alex Murphy", "cleaning", datetime(2026, 10, 6, 10, 0), 30)


def test_yes_before_summary_does_not_book(world):
    # The model wrongly says confirmed=True while we are still collecting.
    fake = world([{**NAME_AND_SERVICE, "confirmed": True}, {**TUESDAY_10, "confirmed": True}])
    session = new_session()

    pipeline.handle_turn(session, "Alex Murphy, cleaning, yes", NOW)
    pipeline.handle_turn(session, "Tuesday at 10, yes", NOW)

    assert session["state"] == "confirming"  # summary must be read back first
    assert fake.saved == []


def test_rule_violation_keeps_collecting_and_tells_sarah_why(world):
    saturday = {"date": "2026-10-10", "time": "10:00", "confirmed": False}
    fake = world([NAME_AND_SERVICE, saturday])
    session = new_session()

    pipeline.handle_turn(session, "Alex Murphy, cleaning", NOW)
    pipeline.handle_turn(session, "Saturday at 10", NOW)

    assert session["state"] == "collecting"
    assert "closed" in fake.notes[-1]
    assert fake.saved == []


def test_slot_taken_while_patient_was_confirming_is_not_booked(world):
    fake = world([NAME_AND_SERVICE, TUESDAY_10, YES])
    session = new_session()

    pipeline.handle_turn(session, "Alex Murphy, cleaning", NOW)
    pipeline.handle_turn(session, "Tuesday at 10", NOW)
    assert session["state"] == "confirming"

    fake.booked_slots = [(datetime(2026, 10, 6, 10, 0), 30)]  # someone else booked it meanwhile
    pipeline.handle_turn(session, "Yes", NOW)

    assert session["state"] == "collecting"
    assert "taken" in fake.notes[-1]
    assert fake.saved == []


def test_closed_day_is_rejected_before_time_is_known(world):
    saturday_no_time = {"name": "Alex Murphy", "service": "cleaning", "date": "2026-10-17", "confirmed": False}
    fake = world([saturday_no_time])
    session = new_session()

    pipeline.handle_turn(session, "Alex Murphy, cleaning, 17th of October", NOW)

    assert session["state"] == "collecting"
    assert "closed on Saturday the 17th of October" in fake.notes[-1]


def test_summary_weekday_comes_from_code_not_from_the_model(world):
    fake = world([NAME_AND_SERVICE, TUESDAY_10])
    session = new_session()

    pipeline.handle_turn(session, "Alex Murphy, cleaning", NOW)
    pipeline.handle_turn(session, "the 6th at 10", NOW)

    assert "Tuesday the 6th of October at 10:00 AM" in fake.notes[-1]


# --- guardrails: Sarah's reply is checked by code before the patient hears it ---

def test_false_booking_claim_is_replaced_by_safe_reply(world):
    # The screenshot bug: the model says "I've booked..." while nothing was saved.
    fake = world([NAME_AND_SERVICE, TUESDAY_10])
    fake.sarah_says = "All right, I've booked your cleaning. Your appointment is confirmed."
    session = new_session()

    pipeline.handle_turn(session, "Alex Murphy, cleaning", NOW)
    reply = pipeline.handle_turn(session, "Tuesday at 10", NOW)

    assert session["state"] == "confirming"
    assert fake.saved == []
    assert "Shall I book it?" in reply
    assert "I've booked" not in reply


def test_stalling_reply_is_replaced(world):
    fake = world([NAME_AND_SERVICE])
    fake.sarah_says = "Sure, I'll check the availability and get back to you."
    session = new_session()

    reply = pipeline.handle_turn(session, "Alex Murphy, cleaning", NOW)

    assert "get back to you" not in reply
    assert "date and time" in reply


def test_wrong_weekday_is_replaced(world):
    # The other screenshot bug: "Monday the 17th of October" for a Saturday.
    saturday = {"name": "Alex Murphy", "service": "cleaning", "date": "2026-10-17", "confirmed": False}
    fake = world([saturday])
    fake.sarah_says = "Got it. What time on Monday the 17th of October would you prefer?"
    session = new_session()

    reply = pipeline.handle_turn(session, "Alex Murphy, cleaning, 17th of October", NOW)

    assert "Monday" not in reply
    assert "closed on Saturday the 17th of October" in reply


def test_patient_always_hears_the_booking_code(world):
    fake = world([NAME_AND_SERVICE, TUESDAY_10, YES])
    fake.sarah_says = "Great, see you then!"  # the model forgot the code
    session = new_session()

    pipeline.handle_turn(session, "Alex Murphy, cleaning", NOW)
    pipeline.handle_turn(session, "Tuesday at 10", NOW)
    reply = pipeline.handle_turn(session, "Yes", NOW)

    assert session["state"] == "booked"
    assert "0, 0, 4, 8, 2, 1" in reply


def test_spoken_day_uses_code_computed_weekday():
    from datetime import date
    assert pipeline.spoken_day(date(2026, 10, 17)) == "Saturday the 17th of October"
    assert pipeline.spoken_day(date(2026, 10, 1)) == "Thursday the 1st of October"
    assert pipeline.spoken_day(date(2026, 10, 22)) == "Thursday the 22nd of October"
    assert pipeline.spoken_day(date(2026, 10, 13)) == "Tuesday the 13th of October"