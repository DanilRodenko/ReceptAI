from app import stt, llm, tts, sheets


def run_pipeline(audio_path: str) -> str:
    text = stt.transcribe(audio_path)
    answer = llm.ask_groq(text)

    data = llm.extract_appointment_data(llm.conversation_history)

    all_collected = all(data.get(k) is not None for k in ["name", "date", "time"])

    if all_collected:
        booked = sheets.get_booked_slots()
        if sheets.is_slot_available(data["date"], data["time"], booked):
            sheets.save_appointment(data["name"], data["date"], data["time"], data['service'], data['duration_minutes'])
        else:
            answer = llm.ask_groq("That slot is taken, please suggest another time.")

    audio_response = tts.speak(answer)
    return audio_response