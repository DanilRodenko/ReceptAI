import os
from gtts import gTTS
import tempfile


def speak(text):
    tts = gTTS(text=text)
    tmp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(tmp_file.name)
    return tmp_file.name
