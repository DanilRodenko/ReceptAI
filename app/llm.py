import os
import json

from dotenv import load_dotenv
from groq import Groq

from app.prompts import MAIN_PROMPT, EXTRACTION_PROMPT

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)

conversation_history = [
    {"role": "system", "content": MAIN_PROMPT}
]


def ask_groq(user_text):
    conversation_history.append({"role": "user", "content": user_text})

    response = GROQ_CLIENT.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history,
        max_tokens=300
    )

    answer = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": answer})
    return answer


def extract_appointment_data(history):
    messages = history + [{"role": "system", "content": EXTRACTION_PROMPT}]

    response = GROQ_CLIENT.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)