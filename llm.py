import functools
import json

from groq import Groq, RateLimitError

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODEL


@functools.lru_cache
def _get_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in .env")
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client


def _complete(messages: list[dict], json_mode: bool = False) -> str:
    kwargs = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 300,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = _get_client().chat.completions.create(**kwargs)
    except RateLimitError:
        kwargs["model"] = GROQ_FALLBACK_MODEL
        response = _get_client().chat.completions.create(**kwargs)

    return response.choices[0].message.content
