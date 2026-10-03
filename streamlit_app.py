import streamlit as st

from app.pipeline import handle_turn, new_session, now_local
from app.sheets import get_all_rows
from app.stt import transcribe
from app.tts import speak

GREETING = "Hi, this is Sarah from Elite Dental Center. How can I help you today?"
STATE_LABELS = {
    "collecting": "Collecting details",
    "confirming": "Waiting for confirmation",
    "booked": "Booked",
}

st.set_page_config(page_title="ReceptAI", page_icon="🦷", layout="wide")


def start_session() -> None:
    session = new_session()
    session["history"].append({"role": "assistant", "content": GREETING})
    st.session_state.session = session
    st.session_state.last_audio = None


@st.cache_data(ttl=30)
def load_schedule() -> list[dict]:
    """Booked slots for display. Booking codes are hidden: they identify a patient's booking."""
    rows = get_all_rows()
    visible = [{k: v for k, v in row.items() if k != "booking_code"} for row in rows]
    return sorted(visible, key=lambda row: (str(row["date"]), str(row["time"])))


if "session" not in st.session_state:
    start_session()
session = st.session_state.session

st.title("🦷 ReceptAI")
st.caption("Voice receptionist for a dental clinic. Speak or type to book an appointment.")

left, right = st.columns([3, 2])

with left:
    audio = st.audio_input("Speak to Sarah")
    typed = st.chat_input("...or type your message")

    user_text = None
    reply_audio = None
    try:
        # Streamlit reruns the script on every interaction and returns the same recording again,
        # so we only process a recording we have not seen before.
        if audio is not None and audio.getvalue() != st.session_state.last_audio:
            st.session_state.last_audio = audio.getvalue()
            with st.spinner("Listening..."):
                user_text = transcribe(audio.getvalue())
            if not user_text:
                st.warning("I couldn't hear anything. Please try again.")
        if typed:
            user_text = typed

        if user_text:
            with st.spinner("Sarah is thinking..."):
                reply = handle_turn(session, user_text, now_local())
                reply_audio = speak(reply)
            if session["state"] == "booked":
                load_schedule.clear()  # show the new booking right away
    except Exception:
        st.error("Sorry, something went wrong. Please try again in a moment.")

    for message in session["history"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if reply_audio:
        st.audio(reply_audio, format="audio/mp3", autoplay=True)

    if st.button("Start over"):
        start_session()
        st.rerun()

with right:
    st.subheader("Booked slots")
    try:
        schedule = load_schedule()
        if schedule:
            st.dataframe(schedule, width="stretch", hide_index=True)
        else:
            st.info("No bookings yet.")
    except Exception:
        st.warning("The schedule is unavailable right now.")

    with st.expander("Under the hood", expanded=True):
        st.write(f"**State:** {STATE_LABELS[session['state']]}")
        st.write("**What Sarah knows so far:**")
        st.json(session["draft"])
        if session["booking_code"]:
            st.success(f"Booking code: {session['booking_code']}")