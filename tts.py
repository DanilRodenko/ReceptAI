import io

from gtts import gTTS


def speak(text: str) -> bytes:
    buffer = io.BytesIO()
    tts = gTTS(text=text, lang="en", tld="ie")
    tts.write_to_fp(buffer)
    return buffer.getvalue()