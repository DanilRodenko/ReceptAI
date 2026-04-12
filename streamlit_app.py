import tempfile
import streamlit as st
import pandas as pd
from app.pipeline import run_pipeline
from app.sheets import get_all_appointments

st.set_page_config(
    page_title="ReceptAI",
    layout="wide"
)

if "history" not in st.session_state:
    st.session_state.history = []

st.title("ReceptAI")

left, right = st.columns(2)

with left:
    audio_value = st.audio_input("Speak")

    if audio_value:
        st.audio(audio_value)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_value.read())
            tmp_path = tmp.name

        with st.spinner("Processing..."):
            bot_audio, new_history = run_pipeline(tmp_path, st.session_state.history)
            st.session_state.history = new_history

        if bot_audio:
            st.subheader("Assistant Answer")
            st.audio(bot_audio, format='audio/mp3', autoplay=True)

with right:
    data = get_all_appointments()
    if data:
        df = pd.DataFrame(data)
        st.subheader("Booked slots")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.subheader("No booked slots")
        st.info("The schedule is currently empty.")

if st.button("Clear Chat"):
    st.session_state.history = []
    st.rerun()