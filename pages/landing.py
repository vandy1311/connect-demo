"""Landing page — native Streamlit (no iframe)."""

import streamlit as st

st.markdown("""<style>
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stSidebarCollapsedControl"] { display: none !important; }
.block-container { max-width: 900px; }
</style>""", unsafe_allow_html=True)

# Nav
st.markdown("""<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #334155; margin-bottom:2rem;">
<div style="font-weight:700; font-size:0.95rem;"><span style="color:#3b82f6;">Connect</span> Analytics Platform</div>
<div style="font-size:0.85rem; color:#94a3b8;">Agents · Compare · ROI · Team</div>
</div>""", unsafe_allow_html=True)

# Hero
st.markdown("""<div style="text-align:center; padding:3rem 0 2rem;">
<div style="display:inline-block; background:rgba(59,130,246,0.12); color:#3b82f6; font-size:0.75rem;
font-weight:600; padding:4px 12px; border-radius:100px; margin-bottom:16px; border:1px solid rgba(59,130,246,0.2);">
Bedrock AgentCore · Serverless</div>
<h1 style="font-size:2.5rem; font-weight:800; line-height:1.15; letter-spacing:-0.03em;">
Contact center analytics,<br>answered in seconds</h1>
<p style="color:#94a3b8; font-size:1rem; line-height:1.7; margin:12px auto 0; max-width:540px;">
Three AI agents query your Connect data lake and return insights in natural language. Deploy with one command. Runs for $34/month.</p>
</div>""", unsafe_allow_html=True)

# CTA buttons
_, c1, c2, _ = st.columns([1.5, 1, 1, 1.5])
with c1:
    if st.button("🚀 Launch Demo", use_container_width=True, type="primary"):
        st.switch_page("pages/demo.py")
with c2:
    st.link_button("▶ Watch Video", "https://youtu.be/r60EKVYHnDo", use_container_width=True)

# Video embed
st.markdown("""<div style="max-width:800px; margin:2rem auto; border-radius:12px; overflow:hidden; border:1px solid #334155;">
<iframe width="100%" height="420" src="https://www.youtube.com/embed/r60EKVYHnDo"
frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
allowfullscreen></iframe></div>""", unsafe_allow_html=True)

# Metrics bar
st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Time to Insight", "2s")
m2.metric("Monthly Cost", "$34")
m3.metric("Call Coverage", "100%")
m4.metric("Deploy Time", "8 min")
m5.metric("Alert Latency", "<60s")

# Agents
st.divider()
st.markdown("### Purpose-built agents for every role")
st.caption("Each agent serves a specific persona with its own model, tools, and data sources")

a1, a2, a3 = st.columns(3)
with a1:
    st.markdown("#### 🟢 Supervisor Agent")
    st.caption("Claude Sonnet 4")
    st.markdown("Real-time operational visibility for floor managers.")
    st.markdown("""
- Queue health and SLA monitoring
- Abandonment root cause analysis
- Agent utilization tracking
- Automated Slack alerts on breach
""")
with a2:
    st.markdown("#### 🟠 Quality Agent")
    st.caption("Claude Sonnet 4")
    st.markdown("Every call analyzed. Every coaching opportunity surfaced.")
    st.markdown("""
- Sentiment trend analysis with charts
- Automated coaching recommendations
- Compliance violation detection
- Transcript analysis with excerpts
""")
with a3:
    st.markdown("#### 🔵 WFM Agent")
    st.caption("Nova Lite 2")
    st.markdown("Predict staffing needs. Detect burnout before it happens.")
    st.markdown("""
- Volume forecasts with confidence bands
- Burnout detection 8 days early
- Flex pool allocation guidance
- Schedule optimization
""")

# Before / After
st.divider()
st.markdown("### Before and after")
b1, b2 = st.columns(2)
with b1:
    st.markdown("#### ❌ Without the platform")
    st.markdown("""
| Metric | Value |
|--------|-------|
| Time to insight | 20 minutes |
| Analytics cost | $150,000/year |
| SLA breach detection | 15+ min late |
| Call coverage | 2% manual QA |
| Burnout detection | After resignation |
| Setup time | 3 months |
""")
with b2:
    st.markdown("#### ✅ With the platform")
    st.markdown("""
| Metric | Value |
|--------|-------|
| Time to insight | 2 seconds |
| Analytics cost | $34/month |
| SLA breach detection | Under 60 seconds |
| Call coverage | 100% AI-analyzed |
| Burnout detection | 8 days early |
| Setup time | 8 minutes |
""")

# ROI
st.divider()
st.markdown("### Return on investment")
st.caption("Estimated annual savings for a 100-agent contact center")
st.markdown('<div style="text-align:center; padding:1.5rem; background:#1e293b; border:1px solid rgba(52,211,153,0.25); border-radius:12px; margin:1rem 0;">'
            '<div style="font-size:2.8rem; font-weight:800; color:#34d399;">$527,000+</div>'
            '<div style="font-size:0.85rem; color:#64748b;">estimated annual savings</div></div>', unsafe_allow_html=True)

r1, r2, r3, r4 = st.columns(4)
r1.metric("Reduced Abandonment", "$262K")
r2.metric("Lower Attrition", "$56K")
r3.metric("Pipeline Replacement", "$128K")
r4.metric("Annual Platform Cost", "$408")

# Team
st.divider()
st.markdown("### Built by Team FIFA")
st.caption("CSM Agentic Hackathon 2026")
t1, t2, t3 = st.columns(3)
with t1:
    st.markdown('<div style="text-align:center;"><div style="width:64px;height:64px;border-radius:50%;background:rgba(59,130,246,0.12);color:#3b82f6;display:inline-flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:700;border:2px solid #334155;">BB</div><div style="font-weight:700;margin-top:8px;">Brigette Bucke</div><div style="font-size:0.78rem;color:#64748b;">Quality & Demo Lead</div></div>', unsafe_allow_html=True)
with t2:
    st.markdown('<div style="text-align:center;"><div style="width:64px;height:64px;border-radius:50%;background:rgba(59,130,246,0.12);color:#3b82f6;display:inline-flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:700;border:2px solid #334155;">YC</div><div style="font-weight:700;margin-top:8px;">Yunjie Chen</div><div style="font-size:0.78rem;color:#64748b;">Architecture & Infrastructure</div></div>', unsafe_allow_html=True)
with t3:
    st.markdown('<div style="text-align:center;"><div style="width:64px;height:64px;border-radius:50%;background:rgba(59,130,246,0.12);color:#3b82f6;display:inline-flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:700;border:2px solid #334155;">VT</div><div style="font-weight:700;margin-top:8px;">Vandana Tewani</div><div style="font-size:0.78rem;color:#64748b;">Alerts & Integration</div></div>', unsafe_allow_html=True)

# Final CTA
st.divider()
st.markdown('<div style="text-align:center; padding:2rem 0;"><h2>See it in action</h2><p style="color:#94a3b8;">Three agents. One command. Every answer in 2 seconds.</p></div>', unsafe_allow_html=True)
_, cta, _ = st.columns([1, 1, 1])
with cta:
    if st.button("🚀 Open the Demo", use_container_width=True, type="primary", key="bottom_cta"):
        st.switch_page("pages/demo.py")

st.divider()
st.caption("Built with AI-DLC methodology · Powered by Amazon Bedrock AgentCore · AWS CDK")
