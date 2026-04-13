import os
import streamlit as st
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

try:
    WHISPER_MODEL = st.secrets["WHISPER_MODEL"]
except Exception:
    WHISPER_MODEL = os.getenv("WHISPER_MODEL")


@st.cache_resource
def load_model():
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


whisper_model = load_model()


def transcribe(audio_path: str) -> str:
    segments, _ = whisper_model.transcribe(
        audio_path,
        language='en'
    )
    text = " ".join([segment.text for segment in segments])
    return text