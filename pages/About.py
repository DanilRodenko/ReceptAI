from pathlib import Path

import streamlit as st

st.set_page_config(page_title="About · ReceptAI", page_icon="🦷", layout="wide")

# The About page shows the README itself, so the two can never drift apart.
README_PATH = Path(__file__).resolve().parent.parent / "README.md"

st.markdown(README_PATH.read_text(encoding="utf-8"))