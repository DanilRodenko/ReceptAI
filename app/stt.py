from app.config import WHISPER_MODEL
from app.llm import get_groq_client


def transcribe(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    result = get_groq_client().audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=WHISPER_MODEL,
        language="en",
    )
    return result.text.strip()