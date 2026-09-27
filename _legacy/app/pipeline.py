from app import stt, llm, tts, sheets


def run_pipeline(audio_path: str, history: list) -> tuple[str, list]:
    text = stt.transcribe(audio_path)

    answer, history = llm.ask_groq(text, history)

    data = llm.extract_appointment_data(history)

    required_keys = ["name", "date", "time", "service", "duration_minutes"]
    all_collected = all(data.get(k) is not None for k in required_keys)

    if all_collected:
        booked = sheets.get_booked_slots()

        if sheets.is_slot_available(data["date"], data["time"], data["duration_minutes"], booked):
            sheets.save_appointment(
                data["name"],
                data["date"],
                data["time"],
                data["service"],
                data["duration_minutes"]
            )
        else:
            booked_str = ", ".join([f"{a['date']} {a['time']}" for a in booked])
            prompt = (
                f"The slot {data['date']} {data['time']} is already taken. "
                f"Currently booked slots: {booked_str}. "
                f"Please suggest another available time."
            )
            answer, history = llm.ask_groq(prompt, history)

    audio_response = tts.speak(answer)

    return audio_response, history