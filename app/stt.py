from app.config import SERVICES, WHISPER_MODEL
from app.llm import get_groq_client


WHISPER_HINT = (
    "Booking a dental appointment. Services: "
    + ", ".join(service.replace("_", " ") for service in SERVICES)
    + "."
)


def transcribe(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    result = get_groq_client().audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=WHISPER_MODEL,
        language="en",
        prompt=WHISPER_HINT,
    )
    return result.text.strip()