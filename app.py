"""Connect Analytics Platform — Entry point."""

import streamlit as st

st.set_page_config(
    page_title="Connect Analytics Platform",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

landing = st.Page("pages/landing.py", title="Home", icon="🏠", default=True)
demo = st.Page("pages/demo.py", title="Demo", icon="🎧")

pg = st.navigation([landing, demo], position="hidden")
pg.run()
