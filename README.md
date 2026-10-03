# 🦷 ReceptAI

**A voice receptionist that books dental appointments by itself — and cannot lie about it, because the booking rules live in code, not in the prompt.**

[![CI](https://github.com/DanilRodenko/ReceptAI/actions/workflows/tests.yml/badge.svg)](https://github.com/DanilRodenko/ReceptAI/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)

**Live demo:** https://receptai.streamlit.app

![ReceptAI screenshot](https://raw.githubusercontent.com/DanilRodenko/ReceptAI/main/docs/screenshot.png)

## Problem & Data

A small clinic loses bookings when nobody picks up the phone. An LLM can hold the
conversation, but a plain chatbot is not safe for this job: it invents weekdays,
says "you're booked" when nothing was saved, and happily books a Saturday.

ReceptAI splits the work:

- **The LLM handles language** — understands the patient, extracts details, phrases the reply.
- **Deterministic code handles business rules** — opening hours, holidays, overlaps, and the only path that writes a booking.

**Data.** There is no training dataset. The single source of truth is a Google Sheet
with one row per booking:

`booking_code | name | service | date | time | duration_minutes | notes`

Clinic rules (all in `app/config.py`):

| Rule | Value |
|---|---|
| Opening hours | Mon–Fri, 09:00–17:00 (Europe/Dublin) |
| Closed | Weekends and Irish public holidays |
| Slot grid | Every 30 minutes |
| Booking horizon | Up to 30 days ahead |
| 30-minute services | check-up, cleaning, filling |
| 60-minute services | extraction, root canal, periodontal treatment, implant |

## Architecture

```
            voice / text
                 │
        ┌────────▼─────────┐
        │  streamlit_app   │  UI — the only file that imports streamlit
        └────────┬─────────┘
                 │
   stt.py ──►  pipeline.py  ──► tts.py
  (Whisper)   state machine     (gTTS)
              + guardrail
          ┌──────┼───────────┐
          ▼      ▼           ▼
       llm.py  rules.py   sheets.py
       (Groq)  pure       (Google Sheets)
               functions
                 │
              config.py
```

**One turn of the conversation:**

1. Whisper turns the audio into text.
2. `extract` (temperature 0, JSON mode) pulls `name / service / date / time / confirmed` out of the dialogue.
3. `_decide` — plain Python — checks the draft against the rules and fresh data from the sheet, and moves the state machine:

   `collecting → confirming → booked`

4. `chat` (temperature 0.4) writes the reply, guided by a system note from step 3.
5. The **guardrail** checks the reply. If it breaks a rule, the patient hears a deterministic fallback instead.
6. gTTS speaks the reply.

**Safety decisions:**

- A booking is written only if the state was already `confirming` **and** the patient said yes to a read-back summary. The slot is re-validated against the sheet right before the write.
- The model never computes weekdays. Code does (`spoken_day`), and both prompts carry a 30-day calendar.
- The guardrail rejects four kinds of reply: a false "it's booked", stalling ("I'll check and get back to you"), a wrong weekday, and a booking confirmation without the code.
- Each booking gets a 6-digit code generated with `secrets`. Speech-to-text mangles names, so the code — not the name — identifies a booking. It is hidden from the public table.
- If the main model hits a rate limit, the call is retried on a smaller fallback model.

## Results / Evaluation

**45 automated tests**, run on every push and pull request:

| File | Tests | What it covers |
|---|---|---|
| `test_rules.py` | 21 | Hours, grid, holidays, overlaps, horizon — with boundary cases |
| `test_pipeline.py` | 14 | State machine and guardrail, with a fake LLM and a fake sheet |
| `test_sheets.py` | 6 | Row parsing, booking codes, collisions |
| `test_llm.py` | 4 | Model fallback, JSON mode |

No test calls a real API: the LLM and the sheet are replaced with fakes, so the suite
runs in about a second and costs nothing.

**4 bugs found in live voice testing, each fixed and locked in with a test:**

| # | What happened | Root cause | Fix |
|---|---|---|---|
| 1 | Empty replies | Hidden reasoning tokens used up `max_tokens` | Higher limit + `reasoning_effort="low"` |
| 2 | "Saturday" understood as a Sunday date | The model computed the date itself | Calendar of real dates in the prompt |
| 3 | The bot read internal notes and ISO dates aloud | Prompt did not separate notes from speech | Prompt rules + dates formatted in code |
| 4 | "I've booked you in" — with nothing saved | Nothing checked the reply against reality | Guardrail with a deterministic fallback |

**Not measured yet:** extraction accuracy on a labelled set of phrases. That is the next step (see below).

## Tech stack

- **LLM:** Groq — `openai/gpt-oss-120b`, fallback `openai/gpt-oss-20b`
- **Speech-to-text:** Groq `whisper-large-v3-turbo`
- **Text-to-speech:** gTTS
- **Storage:** Google Sheets via `gspread` (service account)
- **UI:** Streamlit, deployed on Streamlit Community Cloud
- **Quality:** pytest, GitHub Actions
- **Other:** `holidays` (Irish public holidays), `python-dotenv`

**CI/CD:** every push runs the tests in GitHub Actions. Changes go through a pull
request; after the merge to `main`, Streamlit Cloud redeploys the app automatically.

## Run locally

Requires Python 3.11, a free [Groq API key](https://console.groq.com) and a Google
service account with access to a sheet that has the header row shown above.

```bash
git clone https://github.com/DanilRodenko/ReceptAI.git
cd ReceptAI
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env        # fill in GROQ_API_KEY and SPREADSHEET_ID
# put the service account key next to it as credentials.json

streamlit run streamlit_app.py
```

Run the tests:

```bash
python -m pytest -v
```

Talk to the bot in the terminal, without voice:

```bash
python -m scripts.chat_cli
```

Secrets are never committed: `.env` and `credentials.json` are in `.gitignore`;
in production they are stored in Streamlit secrets.

## Limitations & next steps

- **No evaluation set yet.** Next: ~30 labelled phrases to measure extraction accuracy and compare models.
- **Booking only.** Rescheduling and cancelling by booking code are not implemented.
- **Names from speech are unreliable.** The booking code works around it; spelling the name back would be better.
- **gTTS sounds robotic.** Fine for a prototype, not for a real phone line.
- **One dentist, one chair.** No parallel schedules.
- **Demo data is public.** Anyone can book in the demo; the sheet needs a scheduled reset.