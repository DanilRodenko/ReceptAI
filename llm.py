import functools
import json

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL


@functools.lru_cache
def _get_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in .env")
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client


def _complete(messages: list[dict], json_mode: bool = False) -> str:
    response = _get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=300,
    )

    answer = response.choices[0].message.content
    return answer
