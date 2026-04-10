import os
import pathlib
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL")
whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

def transcribe(audio_path: str) ->str:
    segments, _ = whisper_model.transcribe(
        audio_path,
        language='en'
    )

    text = " ".join([segment.text for segment in segments])
    return text