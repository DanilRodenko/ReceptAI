import functools
import json

from groq import Groq, RateLimitError

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODEL


@functools.lru_cache
def get_groq_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in .env")
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client


def _complete(messages: list[dict], temperature: float, json_mode: bool = False) -> str:
    kwargs = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 1000,
        "reasoning_effort": "low",
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = get_groq_client().chat.completions.create(**kwargs)
    except RateLimitError:
        kwargs["model"] = GROQ_FALLBACK_MODEL
        response = get_groq_client().chat.completions.create(**kwargs)

    return response.choices[0].message.content


def chat(messages: list[dict]) -> str:
    return _complete(messages, temperature=0.4)


def extract(messages: list[dict]) -> dict:
    raw = _complete(messages, json_mode=True, temperature=0)
    return json.loads(raw)