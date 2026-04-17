"""Landing page — serves the static HTML landing page."""

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Hide sidebar on landing
st.markdown("""<style>
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stSidebarCollapsedControl"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
</style>""", unsafe_allow_html=True)

# Read landing HTML
html_path = Path(__file__).parent.parent / "landing.html"
html = html_path.read_text()

# Replace demo links with javascript that posts message to parent
html = html.replace(
    'href="/demo"',
    'href="/demo" onclick="window.parent.location.href=\'/demo\'; return false;"'
)

# Render full-page HTML
components.html(html, height=2800, scrolling=True)
