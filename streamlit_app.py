import tempfile
import streamlit as st
import pandas as pd
from app.pipeline import run_pipeline
from app.sheets import get_booked_slots


st.set_page_config(
    page_title="ReceptAI",
    layout="wide"
)

st.title("ReceptAI")

left, right = st.columns(2)


with left:
    audio_value = st.audio_input("Speak")
    if audio_value:
        st.audio(audio_value)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_value.read())
            tmp_path = tmp.name

        bot_audio = run_pipeline(tmp_path)

        if bot_audio:
            st.subheader("Assistance Answer")
            st.audio(bot_audio, format='audio/mp3', autoplay=True)


with right:
    data = get_booked_slots()
    if data:
        df = pd.DataFrame(data, columns=["Date", "Time"])
        st.subheader("Booked slots")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.subheader("No booked slots")
        st.info("The schedule is currently empty.")
