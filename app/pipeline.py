from app import stt, llm, tts


def run_pipeline(audio_path: str) -> str:
    text = stt.transcribe(audio_path)
    answer = llm.ask_groq(text)
    audio_response = tts.speak(answer)
    return audio_response