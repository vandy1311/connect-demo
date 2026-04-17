"""Connect Analytics Platform — Entry point with landing page + demo."""

import streamlit as st

landing = st.Page("pages/landing.py", title="Home", icon="🏠", default=True)
demo = st.Page("pages/demo.py", title="Demo", icon="🎧")

pg = st.navigation([landing, demo], position="hidden")
pg.run()
