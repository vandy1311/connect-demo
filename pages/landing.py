"""Landing page — polished with tabs."""

import streamlit as st

st.markdown("""<style>
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stSidebarCollapsedControl"] { display: none !important; }
.block-container { max-width: 960px; }
div[data-testid="stMetric"] {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; padding: 14px 16px;
}
[data-testid="stMetricValue"] { color: #3b82f6 !important; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: center; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 0.9rem; }
</style>""", unsafe_allow_html=True)

# ── Tabs at top ──
tab_overview, tab_agents, tab_arch, tab_roi, tab_team = st.tabs(
    ["📊 Overview", "🤖 Agents", "🏗️ Architecture", "💰 ROI", "👥 Team"]
)

# ═══════════════════════════════════════════════════════════════
# 📊 OVERVIEW
# ═══════════════════════════════════════════════════════════════
with tab_overview:
    # Hero
    st.markdown("""<div style="text-align:center; padding:2rem 0 1.5rem;">
    <div style="display:inline-block; background:rgba(59,130,246,0.12); color:#3b82f6; font-size:0.75rem;
    font-weight:600; padding:5px 14px; border-radius:100px; margin-bottom:16px; border:1px solid rgba(59,130,246,0.2);">
    🚀 Bedrock AgentCore · Serverless · $34/month</div>
    <h1 style="font-size:2.6rem; font-weight:800; line-height:1.15; letter-spacing:-0.03em; margin:0;">
    Contact center analytics,<br>answered in seconds</h1>
    <p style="color:#94a3b8; font-size:1.05rem; line-height:1.7; margin:14px auto 0; max-width:560px;">
    Three AI agents query your Amazon Connect data lake and return actionable insights in natural language.</p>
    </div>""", unsafe_allow_html=True)

    # CTA
    _, c1, c2, _ = st.columns([1.2, 1, 1, 1.2])
    with c1:
        if st.button("🎯 Launch Demo", use_container_width=True, type="primary"):
            st.switch_page("pages/demo.py")
    with c2:
        st.link_button("▶️ Watch Video", "https://youtu.be/r60EKVYHnDo", use_container_width=True)

    st.write("")

    # Video
    st.markdown("""<div style="border-radius:12px; overflow:hidden; border:1px solid #334155; margin-bottom:1.5rem;">
    <iframe width="100%" height="420" src="https://www.youtube.com/embed/r60EKVYHnDo"
    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen></iframe></div>""", unsafe_allow_html=True)

    # Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("⚡ Time to Insight", "2s")
    m2.metric("💵 Monthly Cost", "$34")
    m3.metric("📞 Call Coverage", "100%")
    m4.metric("🚀 Deploy Time", "8 min")
    m5.metric("🔔 Alert Latency", "<60s")

    st.write("")

    # How it works
    st.markdown("### How it works")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-radius:12px; padding:1.2rem; text-align:center; height:100%;">
        <div style="font-size:2rem; margin-bottom:8px;">☁️</div>
        <div style="font-weight:700; font-size:0.9rem; margin-bottom:4px;">1. Connect Streams</div>
        <div style="color:#94a3b8; font-size:0.8rem;">CTR, agent events, and Contact Lens data flow to S3</div>
        </div>""", unsafe_allow_html=True)
    with h2:
        st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-radius:12px; padding:1.2rem; text-align:center; height:100%;">
        <div style="font-size:2rem; margin-bottom:8px;">🤖</div>
        <div style="font-weight:700; font-size:0.9rem; margin-bottom:4px;">2. Agents Analyze</div>
        <div style="color:#94a3b8; font-size:0.8rem;">Three specialized agents query data via Athena</div>
        </div>""", unsafe_allow_html=True)
    with h3:
        st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-radius:12px; padding:1.2rem; text-align:center; height:100%;">
        <div style="font-size:2rem; margin-bottom:8px;">💬</div>
        <div style="font-weight:700; font-size:0.9rem; margin-bottom:4px;">3. Ask Anything</div>
        <div style="color:#94a3b8; font-size:0.8rem;">Natural language questions, instant answers</div>
        </div>""", unsafe_allow_html=True)
    with h4:
        st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-radius:12px; padding:1.2rem; text-align:center; height:100%;">
        <div style="font-size:2rem; margin-bottom:8px;">🚨</div>
        <div style="font-weight:700; font-size:0.9rem; margin-bottom:4px;">4. Auto-Alert</div>
        <div style="color:#94a3b8; font-size:0.8rem;">SLA breaches trigger Slack alerts in &lt;60s</div>
        </div>""", unsafe_allow_html=True)

    st.write("")

    # Architecture flowchart
    st.markdown("### Architecture")
    import streamlit.components.v1 as components
    flow_html = """<!DOCTYPE html>
<html><head><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f172a;font-family:Inter,system-ui,sans-serif}
.flow{position:relative;width:760px;margin:0 auto;padding:20px 0}
.node{position:absolute;border-radius:10px;padding:10px 16px;text-align:center;z-index:2}
.node .label{font-size:12px;font-weight:700;color:#f1f5f9}
.node .sub{font-size:9px;color:#94a3b8;margin-top:2px}
.n-src{background:#172554;border:2px solid #3b82f6;width:280px;left:240px;top:0}
.n-src .label{color:#93c5fd}
.n-s3{background:#1e293b;border:1px solid #334155;width:130px;left:100px;top:80px}
.n-glue{background:#1e293b;border:1px solid #334155;width:130px;left:240px;top:80px}
.n-ath{background:#1e293b;border:1px solid #334155;width:130px;left:380px;top:80px}
.n-kb{background:#1e293b;border:1px solid #334155;width:130px;left:520px;top:80px}
.n-gw{background:#172554;border:2px solid #3b82f6;width:280px;left:240px;top:160px}
.n-gw .label{color:#93c5fd}
.n-sup{background:#052e16;border:2px solid #22c55e;width:150px;left:80px;top:240px}
.n-sup .label{color:#86efac}
.n-qual{background:#431407;border:2px solid #f97316;width:150px;left:305px;top:240px}
.n-qual .label{color:#fdba74}
.n-wfm{background:#172554;border:2px solid #3b82f6;width:150px;left:530px;top:240px}
.n-wfm .label{color:#93c5fd}
.n-lambda{background:#2e1065;border:2px solid #a78bfa;width:280px;left:240px;top:330px}
.n-lambda .label{color:#c4b5fd}
.n-eb{background:#431407;border:1px solid #f97316;width:130px;left:100px;top:410px}
.n-eb .label{color:#fdba74}
.n-sns{background:#431407;border:1px solid #f97316;width:130px;left:315px;top:410px}
.n-sns .label{color:#fdba74}
.n-slack{background:#431407;border:1px solid #f97316;width:130px;left:530px;top:410px}
.n-slack .label{color:#fdba74}
svg{position:absolute;top:0;left:0;width:100%;height:100%;z-index:1}
line{stroke:#475569;stroke-width:1.5;marker-end:url(#arrow)}
</style></head><body>
<div class="flow" style="height:470px">
<svg viewBox="0 0 760 470">
  <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/></marker></defs>
  <!-- Connect to data layer -->
  <line x1="310" y1="38" x2="165" y2="80"/>
  <line x1="350" y1="38" x2="305" y2="80"/>
  <line x1="420" y1="38" x2="445" y2="80"/>
  <line x1="460" y1="38" x2="585" y2="80"/>
  <!-- Data to gateway -->
  <line x1="165" y1="115" x2="340" y2="160"/>
  <line x1="305" y1="115" x2="360" y2="160"/>
  <line x1="445" y1="115" x2="400" y2="160"/>
  <line x1="585" y1="115" x2="420" y2="160"/>
  <!-- Gateway to agents -->
  <line x1="310" y1="198" x2="155" y2="240"/>
  <line x1="380" y1="198" x2="380" y2="240"/>
  <line x1="450" y1="198" x2="605" y2="240"/>
  <!-- Agents to lambda -->
  <line x1="155" y1="278" x2="340" y2="330"/>
  <line x1="380" y1="278" x2="380" y2="330"/>
  <line x1="605" y1="278" x2="420" y2="330"/>
  <!-- Lambda to alerts -->
  <line x1="310" y1="368" x2="165" y2="410"/>
  <line x1="380" y1="368" x2="380" y2="410"/>
  <line x1="450" y1="368" x2="595" y2="410"/>
  <!-- SNS to Slack -->
  <line x1="445" y1="430" x2="530" y2="430"/>
  <!-- EB to SNS -->
  <line x1="230" y1="430" x2="315" y2="430"/>
</svg>
<div class="node n-src"><div class="label">☁️ Amazon Connect</div><div class="sub">CTR · Agent Events · Contact Lens</div></div>
<div class="node n-s3"><div class="label">📦 S3</div><div class="sub">Data Lake</div></div>
<div class="node n-glue"><div class="label">📚 Glue</div><div class="sub">3 tables</div></div>
<div class="node n-ath"><div class="label">🔍 Athena</div><div class="sub">SQL queries</div></div>
<div class="node n-kb"><div class="label">🧠 KB</div><div class="sub">Bedrock RAG</div></div>
<div class="node n-gw"><div class="label">🌐 AgentCore Gateway</div><div class="sub">Shared · Routes tool invocations</div></div>
<div class="node n-sup"><div class="label">🟢 Supervisor</div><div class="sub">Claude 4 · 4 tools</div></div>
<div class="node n-qual"><div class="label">🟠 Quality</div><div class="sub">Claude 4 · 3 tools</div></div>
<div class="node n-wfm"><div class="label">🔵 WFM</div><div class="sub">Nova Lite · 2 tools</div></div>
<div class="node n-lambda"><div class="label">⚡ Tool Handler Lambda</div><div class="sub">Docker · 9 tools · Dispatches by tool_name</div></div>
<div class="node n-eb"><div class="label">📡 EventBridge</div><div class="sub">5 rules</div></div>
<div class="node n-sns"><div class="label">📬 SNS</div><div class="sub">5 topics</div></div>
<div class="node n-slack"><div class="label">💬 Slack</div><div class="sub">3 channels</div></div>
</div>
</body></html>"""
    components.html(flow_html, height=500, scrolling=False)

    st.write("")

    # Before / After
    st.markdown("### Before vs After")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-top:3px solid #f87171; border-radius:12px; padding:1.5rem;">
        <h4 style="color:#f87171; margin-top:0;">❌ Without the platform</h4>

| | |
|---|---|
| Time to insight | 20 minutes |
| Analytics cost | $150,000/year |
| SLA breach detection | 15+ min late |
| Call coverage | 2% manual QA |
| Burnout detection | After resignation |
| Setup time | 3 months |
</div>""", unsafe_allow_html=True)
    with b2:
        st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-top:3px solid #34d399; border-radius:12px; padding:1.5rem;">
        <h4 style="color:#34d399; margin-top:0;">✅ With the platform</h4>

| | |
|---|---|
| Time to insight | **2 seconds** |
| Analytics cost | **$34/month** |
| SLA breach detection | **Under 60 seconds** |
| Call coverage | **100% AI-analyzed** |
| Burnout detection | **8 days early** |
| Setup time | **8 minutes** |
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 🤖 AGENTS
# ═══════════════════════════════════════════════════════════════
with tab_agents:
    st.markdown("### Purpose-built agents for every role")
    st.caption("Each agent serves a specific persona with its own model, tools, and data sources")
    st.write("")

    # Supervisor
    st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-left:4px solid #34d399; border-radius:12px; padding:1.5rem; margin-bottom:1rem;">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
        <div style="width:44px; height:44px; border-radius:10px; background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.25);
        display:flex; align-items:center; justify-content:center; font-size:1.1rem; font-weight:700; color:#34d399;">S</div>
        <div><div style="font-weight:700; font-size:1.05rem;">Supervisor Agent</div>
        <div style="font-size:0.75rem; color:#64748b;">Claude Sonnet 4 · 4 tools</div></div>
    </div>
    <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:12px;">Real-time operational visibility for floor managers.</p>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_queue_health</code>
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_abandonment_analysis</code>
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_agent_utilization</code>
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">trigger_sla_alert</code>
    </div></div>""", unsafe_allow_html=True)

    # Quality
    st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-left:4px solid #fb923c; border-radius:12px; padding:1.5rem; margin-bottom:1rem;">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
        <div style="width:44px; height:44px; border-radius:10px; background:rgba(251,146,60,0.1); border:1px solid rgba(251,146,60,0.25);
        display:flex; align-items:center; justify-content:center; font-size:1.1rem; font-weight:700; color:#fb923c;">Q</div>
        <div><div style="font-weight:700; font-size:1.05rem;">Quality Agent</div>
        <div style="font-size:0.75rem; color:#64748b;">Claude Sonnet 4 · 3 tools</div></div>
    </div>
    <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:12px;">Every call analyzed. Every coaching opportunity surfaced.</p>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_sentiment_trends</code>
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_coaching_recommendations</code>
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_compliance_violations</code>
    </div></div>""", unsafe_allow_html=True)

    # WFM
    st.markdown("""<div style="background:#1e293b; border:1px solid #334155; border-left:4px solid #60a5fa; border-radius:12px; padding:1.5rem; margin-bottom:1rem;">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
        <div style="width:44px; height:44px; border-radius:10px; background:rgba(96,165,250,0.1); border:1px solid rgba(96,165,250,0.25);
        display:flex; align-items:center; justify-content:center; font-size:1.1rem; font-weight:700; color:#60a5fa;">W</div>
        <div><div style="font-weight:700; font-size:1.05rem;">WFM Agent</div>
        <div style="font-size:0.75rem; color:#64748b;">Nova Lite 2 · 2 tools</div></div>
    </div>
    <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:12px;">Predict staffing needs. Detect burnout before it happens.</p>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_staffing_forecast</code>
        <code style="background:#0f172a; padding:3px 10px; border-radius:6px; font-size:0.75rem; color:#94a3b8;">get_burnout_signals</code>
    </div></div>""", unsafe_allow_html=True)

    st.write("")
    st.info("All agents share a single **AgentCore Gateway** (Lambda type). Tool invocations route to a shared Docker Lambda that dispatches by `tool_name`. Agents stay in their domain — out-of-scope questions redirect to the right agent.")

# ═══════════════════════════════════════════════════════════════
# 🏗️ ARCHITECTURE
# ═══════════════════════════════════════════════════════════════
with tab_arch:
    st.markdown("### System Architecture")
    st.caption("From data ingestion to Slack alerts — the complete pipeline")
    st.write("")

    import streamlit.components.v1 as components
    arch_svg = """<!DOCTYPE html>
<html><head><style>
body { margin:0; background:#0f172a; font-family:Inter,system-ui,sans-serif; }
.arch { max-width:820px; margin:0 auto; padding:24px 16px; }
.layer { margin-bottom:4px; }
.layer-label {
  font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
  color:#64748b; padding:6px 12px; margin-bottom:6px;
}
.row { display:flex; gap:8px; justify-content:center; flex-wrap:wrap; margin-bottom:4px; }
.box {
  background:#1e293b; border:1px solid #334155; border-radius:10px;
  padding:14px 20px; text-align:center; min-width:140px; flex:1; max-width:260px;
}
.box .icon { font-size:20px; margin-bottom:4px; }
.box .title { font-size:13px; font-weight:700; color:#f1f5f9; }
.box .sub { font-size:10px; color:#64748b; margin-top:2px; }
.box.src { border-color:#3b82f6; background:#172554; }
.box.src .title { color:#93c5fd; }
.box.gw { border-color:#3b82f6; border-width:2px; background:#172554; }
.box.gw .title { color:#93c5fd; }
.box.agt-s { border-color:#22c55e; border-width:2px; background:#052e16; }
.box.agt-s .title { color:#86efac; }
.box.agt-q { border-color:#f97316; border-width:2px; background:#431407; }
.box.agt-q .title { color:#fdba74; }
.box.agt-w { border-color:#3b82f6; border-width:2px; background:#172554; }
.box.agt-w .title { color:#93c5fd; }
.box.fn { border-color:#a78bfa; border-width:2px; background:#2e1065; }
.box.fn .title { color:#c4b5fd; }
.box.evt { border-color:#f97316; background:#431407; }
.box.evt .title { color:#fdba74; }
.arrow { text-align:center; color:#475569; font-size:18px; padding:2px 0; letter-spacing:4px; }
.wide { max-width:100%; }
</style></head><body>
<div class="arch">

<div class="layer">
  <div class="layer-label">☁️ DATA SOURCE</div>
  <div class="row">
    <div class="box src wide" style="max-width:100%">
      <div class="icon">☁️</div>
      <div class="title">Amazon Connect</div>
      <div class="sub">CTR Records · Agent Events · Contact Lens Analysis</div>
    </div>
  </div>
</div>
<div class="arrow">▼</div>

<div class="layer">
  <div class="layer-label">💾 DATA PLATFORM</div>
  <div class="row">
    <div class="box"><div class="icon">📦</div><div class="title">S3 Data Lake</div><div class="sub">ctr/ · agent-events/ · contact-lens/</div></div>
    <div class="box"><div class="icon">📚</div><div class="title">Glue Catalog</div><div class="sub">3 tables · schema-on-read</div></div>
    <div class="box"><div class="icon">🔍</div><div class="title">Athena</div><div class="sub">SQL workgroup</div></div>
    <div class="box"><div class="icon">🧠</div><div class="title">Knowledge Base</div><div class="sub">Bedrock RAG · SOPs</div></div>
  </div>
</div>
<div class="arrow">▼</div>

<div class="layer">
  <div class="layer-label">🌐 CONTROL PLANE</div>
  <div class="row">
    <div class="box gw wide" style="max-width:100%">
      <div class="icon">🌐</div>
      <div class="title">AgentCore Gateway</div>
      <div class="sub">Shared · Lambda type · Routes tool invocations</div>
    </div>
  </div>
</div>
<div class="arrow">▼</div>

<div class="layer">
  <div class="layer-label">🤖 AI AGENTS</div>
  <div class="row">
    <div class="box agt-s"><div class="icon">🟢</div><div class="title">Supervisor</div><div class="sub">Claude Sonnet 4 · 4 tools</div></div>
    <div class="box agt-q"><div class="icon">🟠</div><div class="title">Quality</div><div class="sub">Claude Sonnet 4 · 3 tools</div></div>
    <div class="box agt-w"><div class="icon">🔵</div><div class="title">WFM</div><div class="sub">Nova Lite 2 · 2 tools</div></div>
  </div>
</div>
<div class="arrow">▼</div>

<div class="layer">
  <div class="layer-label">⚡ EXECUTION</div>
  <div class="row">
    <div class="box fn wide" style="max-width:100%">
      <div class="icon">⚡</div>
      <div class="title">Tool Handler Lambda</div>
      <div class="sub">Docker · 9 tools · Dispatches by tool_name</div>
    </div>
  </div>
</div>
<div class="arrow">▼</div>

<div class="layer">
  <div class="layer-label">🚨 ALERT PIPELINE</div>
  <div class="row">
    <div class="box evt"><div class="icon">📡</div><div class="title">EventBridge</div><div class="sub">5 alert rules</div></div>
    <div class="box evt"><div class="icon">📬</div><div class="title">SNS Topics</div><div class="sub">Per-type routing</div></div>
    <div class="box evt"><div class="icon">💬</div><div class="title">Slack</div><div class="sub">Block Kit · 3 channels</div></div>
  </div>
</div>

</div>
</body></html>"""
    components.html(arch_svg, height=920, scrolling=False)

    st.write("")
    st.markdown("### CDK Stacks")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.success("🔐 Auth")
    s2.success("💾 Data")
    s3.success("🤖 Agent")
    s4.success("🚨 Alert")
    s5.success("📚 KB")

    with st.expander("📋 Data Flow Details"):
        st.markdown("""
1. **Amazon Connect** streams CTR records, agent events, Contact Lens → **S3**
2. **Glue Catalog** provides schema-on-read for 3 tables
3. **Athena** runs SQL queries via dedicated workgroup
4. **Knowledge Base** indexes SOPs and compliance docs for RAG
5. **AgentCore Gateway** routes tool calls → shared **Lambda**
6. Lambda dispatches by `tool_name` to the right handler
7. Alerts: **EventBridge** → **SNS** (5 topics) → **Slack Lambda** → **Slack**
        """)

    with st.expander("🔐 Security & IAM"):
        st.markdown("""
- Least-privilege IAM per component
- Athena scoped to `connect-analytics` workgroup
- S3 read-only for tools (write only for Athena results)
- Bedrock access scoped to specific model ARNs
- API-key auth (hackathon) → Cognito (production)
        """)

    # Tech pills
    st.write("")
    st.markdown("""<div style="text-align:center; padding:1rem 0;">
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">Bedrock AgentCore</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">AWS CDK</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">Lambda</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">Athena</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">S3</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">Glue</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">EventBridge</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">SNS</span>
    <span style="display:inline-block; background:#1e293b; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94a3b8; margin:3px;">Bedrock KB</span>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 💰 ROI
# ═══════════════════════════════════════════════════════════════
with tab_roi:
    st.markdown("### Return on Investment")
    st.caption("Estimated annual savings for a 100-agent contact center")
    st.write("")

    st.markdown("""<div style="text-align:center; padding:2rem; background:#1e293b; border:1px solid rgba(52,211,153,0.25); border-radius:14px; margin-bottom:1.5rem;">
    <div style="font-size:3rem; font-weight:800; color:#34d399; letter-spacing:-0.03em;">$527,000+</div>
    <div style="font-size:0.9rem; color:#64748b; margin-top:4px;">estimated annual savings</div>
    </div>""", unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("📉 Reduced Abandonment", "$262K")
    r2.metric("👥 Lower Attrition", "$56K")
    r3.metric("🔄 Pipeline Replacement", "$128K")
    r4.metric("💳 Annual Platform Cost", "$408")

    st.write("")
    st.markdown("### Cost Breakdown")
    st.markdown("""
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Bedrock AgentCore | ~$15 | 3 agents, gateway |
| Lambda (tool handler) | ~$5 | ~10K invocations/month |
| Athena queries | ~$8 | ~500 queries/month |
| S3 storage | ~$3 | CTR + Contact Lens data |
| EventBridge + SNS | ~$1 | Alert pipeline |
| Knowledge Base | ~$2 | RAG embeddings |
| **Total** | **~$34** | **Per month** |
    """)

# ═══════════════════════════════════════════════════════════════
# 👥 TEAM
# ═══════════════════════════════════════════════════════════════
with tab_team:
    st.markdown("### Built by Team FIFA")
    st.caption("CSM Agentic Hackathon 2026")
    st.write("")

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""<div style="text-align:center; background:#1e293b; border:1px solid #334155; border-radius:14px; padding:2rem 1.5rem;">
        <div style="width:72px; height:72px; border-radius:50%; background:rgba(59,130,246,0.12); color:#3b82f6;
        display:inline-flex; align-items:center; justify-content:center; font-size:1.6rem; font-weight:700;
        border:2px solid #334155; margin-bottom:12px;">BB</div>
        <div style="font-weight:700; font-size:1rem;">Brigette Bucke</div>
        <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">Quality & Demo Lead</div>
        </div>""", unsafe_allow_html=True)
    with t2:
        st.markdown("""<div style="text-align:center; background:#1e293b; border:1px solid #334155; border-radius:14px; padding:2rem 1.5rem;">
        <div style="width:72px; height:72px; border-radius:50%; background:rgba(59,130,246,0.12); color:#3b82f6;
        display:inline-flex; align-items:center; justify-content:center; font-size:1.6rem; font-weight:700;
        border:2px solid #334155; margin-bottom:12px;">YC</div>
        <div style="font-weight:700; font-size:1rem;">Yunjie Chen</div>
        <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">Architecture & Infrastructure</div>
        </div>""", unsafe_allow_html=True)
    with t3:
        st.markdown("""<div style="text-align:center; background:#1e293b; border:1px solid #334155; border-radius:14px; padding:2rem 1.5rem;">
        <div style="width:72px; height:72px; border-radius:50%; background:rgba(59,130,246,0.12); color:#3b82f6;
        display:inline-flex; align-items:center; justify-content:center; font-size:1.6rem; font-weight:700;
        border:2px solid #334155; margin-bottom:12px;">VT</div>
        <div style="font-weight:700; font-size:1rem;">Vandana Tewani</div>
        <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">Alerts & Integration</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown("""<div style="text-align:center; background:#1e293b; border:1px solid #334155; border-radius:12px; padding:1.5rem; margin-top:1rem;">
    <div style="font-size:0.85rem; color:#94a3b8;">Built with <span style="color:#3b82f6; font-weight:600;">AI-DLC methodology</span></div>
    <div style="font-size:0.8rem; color:#64748b; margin-top:4px;">Powered by Amazon Bedrock AgentCore · AWS CDK · Python</div>
    </div>""", unsafe_allow_html=True)

# ── Footer ──
st.write("")
st.divider()
_, fc, _ = st.columns([1, 1, 1])
with fc:
    if st.button("🎯 Try the Demo →", use_container_width=True, type="primary", key="footer_cta"):
        st.switch_page("pages/demo.py")
st.caption("Connect Analytics Platform · AWS Hackathon 2026")
