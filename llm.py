import functools

from groq import Groq

from config import GROQ_API_KEY


@functools.lru_cache
def _get_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in .env")
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client
