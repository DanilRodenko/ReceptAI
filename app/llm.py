import os
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from app.prompts import get_main_prompt, get_extraction_prompt

load_dotenv()

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)


def ask_groq(user_text, history):
    if not history:
        history = [{"role": "system", "content": get_main_prompt()}]

    history.append({"role": "user", "content": user_text})

    response = GROQ_CLIENT.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history,
        max_tokens=300
    )

    answer = response.choices[0].message.content
    history.append({"role": "assistant", "content": answer})
    return answer, history


def extract_appointment_data(history):
    messages = history + [{"role": "system", "content": get_extraction_prompt()}]

    response = GROQ_CLIENT.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)