import os

from dotenv import load_dotenv

load_dotenv()  # loads .env locally; on Streamlit Cloud vars come from Secrets

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")
WHISPER_MODEL  = "whisper-large-v3-turbo"

# --- Clinic schedule ---
TIMEZONE = "Europe/Dublin"
OPEN_HOUR = 9
CLOSE_HOUR = 17
SLOT_MINUTES = 30
WORKING_DAYS = {0, 1, 2, 3, 4}  # Mon–Fri, as in date.weekday()
HOLIDAY_COUNTRY = "IE"
MAX_DAYS_AHEAD = 30

# --- Services ---
SERVICE_DURATION_MINUTES = {
    "check_up": 30,
    "cleaning": 30,
    "filling": 30,
    "extraction": 60,
    "root_canal": 60,
    "periodontal_treatment": 60,
    "implant": 60,
}

SERVICES = list(SERVICE_DURATION_MINUTES.keys())


# --- Google Sheets --- 
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")


# --- Formats ---
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
