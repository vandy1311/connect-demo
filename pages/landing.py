"""Landing page — embedded HTML with working navigation."""

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.markdown("""<style>
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stSidebarCollapsedControl"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
</style>""", unsafe_allow_html=True)

html_path = Path(__file__).parent.parent / "landing.html"
html = html_path.read_text()

# Replace all demo links with top-level navigation
html = html.replace('href="/demo"', 'href="/demo" target="_top"')
html = html.replace('href="http://localhost:8501"', 'href="/demo" target="_top"')

# Remove video section (mp4 not available on cloud)
html = html.replace(
    '<video id="demo-video" width="100%" controls style="display:none; background:#000;">',
    '<video id="demo-video" width="100%" controls style="display:none; background:#000;" hidden>'
)

components.html(html, height=3200, scrolling=True)
