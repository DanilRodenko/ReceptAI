# ReceptAI

AI-powered voice appointment booking assistant for dental clinics.

## Overview
ReceptAI is a voice bot that allows patients to book dental appointments 
by speaking naturally. The bot transcribes speech, understands intent, 
checks availability, and saves bookings to Google Sheets — all in real time.

## Features
- 🎙️ Voice input via microphone
- 🤖 Conversational AI receptionist ("Sarah")
- 📅 Smart scheduling with overlap detection
- 🗓️ Google Sheets integration
- 🔊 Text-to-speech responses
- 💬 Telegram bot support (coming soon)

## Tech Stack
- **STT:** faster-whisper
- **LLM:** Groq (LLaMA 3.3 70B)
- **TTS:** gTTS
- **Storage:** Google Sheets API
- **UI:** Streamlit
- **Deployment:** Streamlit Cloud

## How It Works
1. Patient speaks into the microphone
2. Whisper transcribes audio to text
3. Groq LLM extracts name, date, time, and service
4. System checks for scheduling conflicts
5. Appointment saved to Google Sheets
6. Bot responds with voice confirmation

## Setup
```bash
git clone https://github.com/DanilRodenko/ReceptAI.git
cd ReceptAI
pip install -r requirements.txt
```

Add your credentials to `.env`:
```
GROQ_API_KEY=your_key
SPREADSHEET_ID=your_sheet_id
WHISPER_MODEL=small
```

Add `credentials.json` from Google Cloud Service Account.
```bash
streamlit run streamlit_app.py
```

## Demo
🔗 [Live Demo](https://receptai.streamlit.app/)