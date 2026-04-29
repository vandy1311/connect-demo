"""
Connect Analytics Platform — Demo UI
Streamlit app for hackathon demo with 3 agent tabs + architecture view.
Run: streamlit run demo_ui/app.py
"""

import base64
import json
import os
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote as url_quote

import streamlit as st

# Live query engine — DuckDB over Parquet
try:
    import sys
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).parent.parent))
    from live_query import live_agent_response
    _LIVE_MODE = True
except Exception:
    _LIVE_MODE = False

# ---------------------------------------------------------------------------
# Slack integration
# ---------------------------------------------------------------------------
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Load from .env file if present
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "SLACK_WEBHOOK_URL" and v.strip():
                SLACK_WEBHOOK_URL = v.strip()

# Also check Streamlit secrets (for Streamlit Cloud deployment)
try:
    import streamlit as _st
    if not SLACK_WEBHOOK_URL or "YOUR" in SLACK_WEBHOOK_URL:
        SLACK_WEBHOOK_URL = _st.secrets.get("SLACK_WEBHOOK_URL", SLACK_WEBHOOK_URL)
    # Load AWS credentials from secrets into env vars for boto3
    for _key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"):
        _val = _st.secrets.get(_key, "")
        if _val:
            os.environ[_key] = _val
except Exception:
    pass


def post_to_slack(alert: dict) -> bool:
    """Post an alert to Slack via webhook. Returns True on success."""
    if not SLACK_WEBHOOK_URL or "YOUR" in SLACK_WEBHOOK_URL:
        return False

    emoji_map = {
        "SLA_BREACH": "🚨",
        "COMPLIANCE_VIOLATION": "🛑",
        "BURNOUT_RISK": "🔥",
    }
    emoji = emoji_map.get(alert["type"], "⚠️")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {alert['type'].replace('_', ' ').title()}", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Time:* {alert['time']}\n{alert['message']}"},
        },
    ]

    payload = json.dumps({"blocks": blocks}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
# Page config handled by app.py entry point

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global */
    .stApp { background: #0f172a; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0; padding: 10px 20px;
        font-weight: 600; font-size: 0.85rem;
    }

    /* Agent headers */
    .supervisor-header { color: #34d399; border-left: 3px solid #34d399; padding-left: 14px; font-size: 1.3rem; }
    .quality-header { color: #fb923c; border-left: 3px solid #fb923c; padding-left: 14px; font-size: 1.3rem; }
    .wfm-header { color: #60a5fa; border-left: 3px solid #60a5fa; padding-left: 14px; font-size: 1.3rem; }

    /* Chat bubbles */
    .user-msg {
        background: #1e293b; border-radius: 12px; padding: 14px 18px;
        margin: 10px 0; border-left: 3px solid #3b82f6; color: #f1f5f9;
    }
    .agent-msg {
        background: #1e293b; border-radius: 12px; padding: 14px 18px;
        margin: 10px 0; border-left: 3px solid #34d399; color: #f1f5f9;
    }

    /* Slack alerts in sidebar */
    .slack-alert {
        background: #1e293b; border: 1px solid #334155;
        border-radius: 10px; padding: 12px 14px; margin: 8px 0; font-size: 0.85rem; color: #f1f5f9;
    }
    .slack-alert .alert-type { font-weight: 700; font-size: 0.9rem; }
    .slack-alert.sla { border-left: 3px solid #f87171; }
    .slack-alert.compliance { border-left: 3px solid #fb923c; }
    .slack-alert.burnout { border-left: 3px solid #60a5fa; }

    /* Agent cards */
    .agent-card {
        border-radius: 12px; padding: 18px; margin: 8px 0;
        background: #1e293b; border: 1px solid #334155;
    }
    .agent-card.sup { border-left: 3px solid #34d399; }
    .agent-card.qual { border-left: 3px solid #fb923c; }
    .agent-card.wfm { border-left: 3px solid #60a5fa; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #0f172a; }

    /* Metrics */
    [data-testid="stMetric"] {
        background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 12px;
    }
    [data-testid="stMetricValue"] { color: #3b82f6; font-weight: 700; }

    /* Prompt buttons */
    .stButton > button {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 16px !important;
        min-height: 80px !important;
        font-size: 0.88rem !important;
        text-align: left !important;
        white-space: pre-line !important;
        line-height: 1.5 !important;
        transition: all 0.2s ease !important;
        color: #f1f5f9 !important;
    }
    .stButton > button:hover {
        background: #273548 !important;
        border-color: #64748b !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25) !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — Slack alert feed + architecture
# ---------------------------------------------------------------------------
with st.sidebar:
    if st.button("🏠 Home", use_container_width=True, type="secondary"):
        st.switch_page("pages/landing.py")

    st.markdown("---")

    # Mode toggle
    st.markdown("### ⚡ Data Mode")
    live_mode = st.toggle("Live Data", value=_LIVE_MODE, key="live_mode_toggle",
                          help="ON = Real SQL queries over 70K records via DuckDB\nOFF = Canned demo responses")
    if live_mode and _LIVE_MODE:
        st.success("🟢 LIVE — querying 70K records", icon="⚡")
    elif live_mode and not _LIVE_MODE:
        st.warning("DuckDB not available — using demo mode")
        live_mode = False
    else:
        st.info("📋 DEMO — canned responses")
    try:
        pass  # architecture diagram not available in cloud deploy
    except Exception:
        st.caption("Architecture diagram")
    st.markdown("---")

    # Voice toggle
    st.markdown("### 🔊 Voice Output")
    voice_enabled = st.toggle("Enable Nova Sonic voice", value=False, key="voice_toggle")
    if voice_enabled:
        st.success("Voice ON", icon="🔊")
        if st.button("🔊 Test Voice Now", key="test_voice_btn"):
            st.session_state["_run_voice_test"] = True
    else:
        st.caption("Text-only mode")

    st.markdown("---")

    # Slack status
    st.markdown("### 💬 Slack Integration")
    if SLACK_WEBHOOK_URL and "YOUR" not in SLACK_WEBHOOK_URL:
        st.success("Connected", icon="✅")
        st.caption("Alerts will post to Slack in real time")
    else:
        st.warning("Not configured", icon="⚠️")
        st.caption("Add webhook URL to demo_ui/.env")

    st.markdown("---")
    st.markdown("### 🔔 Slack Alert Feed")

    if "alerts" not in st.session_state:
        st.session_state.alerts = []

    for alert in reversed(st.session_state.alerts):
        css_class = "sla" if "SLA" in alert["type"] else "burnout" if "BURNOUT" in alert["type"] else "compliance"
        st.markdown(f"""
        <div class="slack-alert {css_class}">
            <span class="alert-type">{alert['emoji']} {alert['type']}</span><br>
            <span style="color:#5f6b7a">{alert['time']}</span><br>
            {alert['message']}
        </div>
        """, unsafe_allow_html=True)

    if not st.session_state.alerts:
        st.caption("Alerts will appear here during the demo...")

    st.markdown("---")
    st.markdown("### 💰 Estimated Cost")
    st.metric("Monthly (demo load)", "$22–34")
    st.caption("AgentCore + Athena + Lambda + S3 + SNS")


# ---------------------------------------------------------------------------
# Main content — Agent tabs
# ---------------------------------------------------------------------------
st.markdown("""
<div style="background:#1e293b; border:1px solid #334155; border-radius:12px; padding:32px; margin-bottom:20px; text-align:center;">
    <div style="display:inline-block; background:rgba(59,130,246,0.12); color:#3b82f6; font-size:0.75rem;
                font-weight:600; padding:4px 12px; border-radius:100px; margin-bottom:16px; border:1px solid rgba(59,130,246,0.2);">
        Bedrock AgentCore &middot; Serverless &middot; Toggle Live/Demo in sidebar
    </div>
    <h1 style="font-size:2rem; font-weight:800; letter-spacing:-0.03em; margin:0 0 8px 0; color:#f1f5f9;">
        Connect Analytics Platform
    </h1>
    <p style="color:#94a3b8; font-size:0.95rem; margin:0;">
        Three AI agents that turn contact center data into decisions
    </p>
    <div style="display:flex; justify-content:center; gap:24px; margin-top:20px;">
        <div style="text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:#34d399;">S</div>
            <div style="font-size:0.7rem; color:#64748b;">Supervisor</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:#fb923c;">Q</div>
            <div style="font-size:0.7rem; color:#64748b;">Quality</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:#60a5fa;">W</div>
            <div style="font-size:0.7rem; color:#64748b;">WFM</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab_auto, tab_sup, tab_qual, tab_wfm, tab_handoff, tab_dash, tab_roi, tab_kb, tab_before, tab_deploy, tab_arch = st.tabs([
    "🎬 Auto Demo", "Supervisor", "Quality", "WFM", "Agent Handoff",
    "Dashboard", "ROI", "Knowledge Base",
    "Before / After", "Deploy", "Architecture"
])


# ---------------------------------------------------------------------------
# Demo response simulator — returns canned responses matching demo script
# ---------------------------------------------------------------------------

# Stub kb_retrieve for deployment (no backend needed for demo)
def kb_retrieve(query, max_results=2):
    return []


def simulate_agent_response(agent: str, query: str) -> dict:
    """Return a simulated agent response matching the demo script."""
    q = query.lower()

    # ── Supervisor queries ──
    if "queue health" in q:
        return {
            "text": (
                "**Queue Health Summary (Last 60 min)**\n\n"
                "⚠️ **Billing Queue — SLA BREACH**\n"
                "- Queue size: 87 contacts\n"
                "- Longest wait: 12 min 0 sec\n"
                "- Service level: 68.5% *(threshold: 80%)*\n"
                "- Avg handle time: 5 min 45 sec\n"
                "- Abandonment: 14%\n\n"
                "✅ **Sales Queue — Healthy**\n"
                "- Queue size: 32 contacts\n"
                "- Longest wait: 3 min 0 sec\n"
                "- Service level: 82.0%\n\n"
                "**Recommendation:** Pull 2 agents from Technical queue to Billing immediately."
            ),
            "alert": {
                "type": "SLA_BREACH",
                "emoji": "🚨",
                "message": "Billing queue at 68.5% SLA (threshold 80%). 87 contacts waiting, longest wait 12 min.",
            },
            "metrics": [
                {"label": "Billing SLA", "value": "68.5%", "delta": "-11.5%"},
                {"label": "Queue Size", "value": "87", "delta": "+23"},
                {"label": "Longest Wait", "value": "12 min", "delta": "+8 min"},
                {"label": "Abandonment", "value": "14%", "delta": "+9%"},
            ],
            "actions": [
                {"label": "Pull 2 agents to Billing", "confirmation": "Agent-005 and Agent-012 reassigned from Technical to Billing. Effective immediately.",
                 "slack_alert": {"type": "SLA_BREACH", "emoji": "", "message": "2 agents reassigned to Billing to address SLA breach."}},
                {"label": "Activate flex pool", "confirmation": "2 flex pool agents deployed to Billing for 10 AM - 2 PM block."},
                {"label": "Notify manager", "confirmation": "SLA breach report sent to Contact Center Manager via email and Slack."},
            ],
        }

    if "abandonment" in q or "spike" in q:
        return {
            "text": (
                "**Abandonment Root Cause Analysis — 2:00 PM**\n\n"
                "📉 Abandonment spiked to **18%** at 2:00 PM (baseline: 5%)\n\n"
                "**Root Cause:** Two agents (Agent-001 and Agent-002) went on break "
                "simultaneously at 1:58 PM. With peak volume (3x normal) hitting at the "
                "same time, occupancy surged to **96%** for 18 minutes.\n\n"
                "**Impact:**\n"
                "- 18 contacts abandoned in the 2:00–2:18 PM window\n"
                "- Average wait before abandon: 12 min 0 sec\n"
                "- Billing queue was most affected (14 of 18 abandons)\n\n"
                "**Recommendation:** Stagger break schedules during 10 AM–2 PM peak. "
                "Never allow more than 1 agent on break per queue during peak hours."
            ),
            "metrics": [
                {"label": "Peak Abandon Rate", "value": "18%", "delta": "+13%"},
                {"label": "Peak Hour", "value": "2:00 PM", "delta": ""},
                {"label": "Contacts Lost", "value": "18", "delta": ""},
                {"label": "Occupancy Peak", "value": "96%", "delta": "+21%"},
            ],
            "actions": [
                {"label": "Enable break staggering", "confirmation": "Automated break staggering enabled for all queues during 10 AM - 2 PM. Max 1 agent per queue on break."},
                {"label": "Create incident report", "confirmation": "Post-incident report created for the 2 PM abandonment spike. Assigned to Supervisor for review within 24 hours."},
            ],
        }

    if "utilization" in q or ("who" in q and "available" in q):
        return {
            "text": (
                "**Agent Utilization (Last 8 hours)**\n\n"
                "| Agent | Occupancy | Status | Handle Time | Contacts |\n"
                "|-------|-----------|--------|-------------|----------|\n"
                "| Agent-023 | 98% | ON_CALL | 7 min 12 sec | 34 |\n"
                "| Agent-031 | 96% | ON_CALL | 6 min 48 sec | 31 |\n"
                "| Agent-017 | 93% | ACW | 8 min 15 sec | 28 |\n"
                "| Agent-005 | 72% | AVAILABLE | 5 min 30 sec | 22 |\n"
                "| Agent-012 | 45% | AVAILABLE | 4 min 50 sec | 18 |\n\n"
                "Agent-023 and Agent-031 are running critically high. Consider reassignment."
            ),
            "actions": [
                {"label": "Reassign Agent-023 to low-volume queue", "confirmation": "Agent-023 moved from Billing to Returns queue. Occupancy should drop to ~75% within 30 minutes.",
                 "slack_alert": {"type": "BURNOUT_RISK", "emoji": "", "message": "Agent-023 reassigned from Billing to Returns — occupancy intervention."}},
                {"label": "Reassign Agent-031 to low-volume queue", "confirmation": "Agent-031 moved from Support to Returns queue. Shift reduced by 1 hour today."},
                {"label": "Move Agent-012 to Billing", "confirmation": "Agent-012 (45% occupancy, AVAILABLE) moved to Billing queue to cover the gap from Agent-023 reassignment."},
            ],
        }

    if "busiest" in q or "peak" in q:
        return {
            "text": (
                "**Peak Hour Analysis (Today)**\n\n"
                "| Hour | Volume | Avg Wait | Abandonment |\n"
                "|------|--------|----------|-------------|\n"
                "| 10:00 AM | 78 calls | 28 sec | 4% |\n"
                "| 11:00 AM | 92 calls | 45 sec | 7% |\n"
                "| 12:00 PM | 88 calls | 52 sec | 9% |\n"
                "| 1:00 PM | 82 calls | 48 sec | 8% |\n"
                "| 2:00 PM | 95 calls | 2 min 10 sec | 18% |\n\n"
                "Peak volume is 10 AM to 2 PM with 3x normal volume. "
                "The 2 PM spike correlates with simultaneous agent breaks."
            ),
            "metrics": [
                {"label": "Peak Hour", "value": "2:00 PM", "delta": ""},
                {"label": "Peak Volume", "value": "95", "delta": "+3x"},
                {"label": "Worst Wait", "value": "2m 10s", "delta": ""},
                {"label": "Worst Abandon", "value": "18%", "delta": "+13%"},
            ],
            "actions": [
                {"label": "Stagger breaks during peak", "confirmation": "Break staggering policy enabled for 10 AM - 2 PM. Max 1 agent per queue on break. All supervisors notified."},
                {"label": "Add peak hour staffing", "confirmation": "2 additional agents scheduled for 10 AM - 2 PM shift Monday through Friday. Flex pool activated."},
                {"label": "Create break schedule", "confirmation": "Automated break schedule generated for 25 agents. Breaks distributed evenly across 10 AM - 2 PM with no overlaps per queue."},
            ],
        }

    if "transfer" in q:
        return {
            "text": (
                "**Transfer Rate Analysis (Last 7 Days)**\n\n"
                "| Queue | Transfer Rate | Top Destination | Avg Transfers/Day |\n"
                "|-------|--------------|-----------------|-------------------|\n"
                "| Support | 12% | Billing | 18 |\n"
                "| Sales | 8% | Support | 11 |\n"
                "| Billing | 5% | Returns | 7 |\n"
                "| Returns | 3% | Support | 4 |\n"
                "| VIP | 2% | Support | 2 |\n\n"
                "Support queue has the highest transfer rate at 12%, primarily routing to Billing. "
                "This suggests agents may need better billing training or the IVR routing needs adjustment."
            ),
            "actions": [
                {"label": "Schedule billing training", "confirmation": "Training session scheduled for Support team — next Tuesday 2 PM. Calendar invites sent to 12 agents."},
                {"label": "Review IVR routing rules", "confirmation": "IVR routing audit ticket created — assigned to Telecom team. Target: reduce Support→Billing transfers by 50%."},
                {"label": "Send report to manager", "confirmation": "Transfer rate report emailed to Contact Center Manager with recommendations.",
                 "slack_alert": {"type": "SLA_BREACH", "emoji": "", "message": "Transfer rate report shared — Support queue at 12%, IVR review recommended."}},
            ],
        }

    if "sla" in q and ("breach" in q or "right now" in q):
        return {
            "text": (
                "**Current SLA Status**\n\n"
                "| Queue | SLA | Threshold | Status |\n"
                "|-------|-----|-----------|--------|\n"
                "| Billing | 68.5% | 80% | BREACH |\n"
                "| Support | 74.0% | 70% | OK |\n"
                "| Sales | 82.0% | 80% | OK |\n"
                "| Returns | 78.0% | 75% | OK |\n"
                "| VIP | 88.0% | 90% | BREACH |\n\n"
                "Two queues are currently in breach: Billing (11.5% below threshold) and VIP (2% below). "
                "Billing is the priority — recommend immediate agent reallocation."
            ),
            "alert": {
                "type": "SLA_BREACH",
                "emoji": "",
                "message": "Billing queue at 68.5% SLA (threshold 80%). VIP at 88% (threshold 90%).",
            },
            "actions": [
                {"label": "Reallocate agents to Billing", "confirmation": "2 agents moved from Returns to Billing queue. SLA recovery expected within 10 minutes."},
                {"label": "Assign standby to VIP", "confirmation": "1 flex pool agent placed on VIP standby. Will activate if SLA drops below 85%."},
            ],
        }

    # ── Quality queries ──
    if "coaching" in q or "agents need" in q:
        return {
            "text": (
                "**Coaching Recommendations (This Week)**\n\n"
                "🔴 **Agent-017** — Negative sentiment rate: **30%** (4 negative calls)\n"
                "- Pattern: Frequent interruptions during customer explanations\n"
                "- Sample: *\"Customer was upset about billing error — agent cut off mid-sentence\"*\n"
                "- **Recommendation:** De-escalation coaching + active listening module\n\n"
                "🟡 **Agent-009** — Negative sentiment rate: **20%**\n"
                "- Pattern: Long hold times without status updates\n"
                "- **Recommendation:** Hold management training + empathy refresher\n\n"
                "All other agents are below the 15% threshold."
            ),
            "transcript_audio": [
                {"label": "Agent-017 — poor de-escalation", "file": "assets/transcripts/negative_interruption.mp3",
                 "text": "Ma'am, if you could just. Let me. I understand but. Ma'am I need you to..."},
                {"label": "Agent-009 — dismissive tone", "file": "assets/transcripts/agent_coaching_needed.mp3",
                 "text": "Yeah so basically your payment didn't go through. I don't really know why..."},
            ],
            "actions": [
                {"label": "Schedule coaching for Agent-017", "confirmation": "Coaching session booked. Calendar invite sent.",
                 "calendar": {"title": "Coaching Session — Agent-017 De-escalation", "description": "De-escalation coaching for Agent-017.\nFocus: Active listening, empathy statements, avoiding interruptions.\nPrepare: Review 4 negative call recordings from this week.", "start_hours": 48, "duration_minutes": 30},
                 "email": {"to": "teamlead@company.com", "subject": "Coaching Scheduled — Agent-017", "body": "Hi,\n\nA coaching session has been scheduled for Agent-017:\n\n- Topic: De-escalation + Active Listening\n- When: In 48 hours (see calendar invite)\n- Duration: 30 minutes\n- Reason: 30% negative sentiment rate, 4 negative calls this week\n\nPlease review the call recordings before the session.\n\nThank you"},
                 "slack_alert": {"type": "COMPLIANCE_VIOLATION", "emoji": "", "message": "Coaching scheduled for Agent-017 — de-escalation + active listening module."}},
                {"label": "Schedule coaching for Agent-009", "confirmation": "Hold management training scheduled for Agent-009 — Friday 2 PM."},
                {"label": "Generate coaching report", "confirmation": "Weekly coaching report generated and emailed to QA Manager."},
            ],
        }

    if "worst call" in q or "sentiment" in q:
        return {
            "text": (
                "**Sentiment Trends (Last 7 Days)**\n\n"
                "Monday shows a clear negative spike — 25% negative vs 15% baseline.\n\n"
                "**Worst Call — Agent-017, Monday 2:14 PM**\n"
                "- Overall sentiment: NEGATIVE (-3.8)\n"
                "- Categories: Escalation, Billing\n"
                "- Transcript excerpt: *\"I've been on hold for 20 minutes and nobody "
                "can tell me why I was charged twice...\"*\n"
                "- Agent interrupted customer 3 times in first 2 minutes\n"
                "- Call escalated to supervisor at 8:42 mark"
            ),
            "chart": "sentiment",
            "transcript_audio": [
                {"label": "Customer (negative)", "file": "assets/transcripts/negative_billing.mp3",
                 "text": "I've been on hold for 20 minutes and nobody can tell me why I was charged twice..."},
                {"label": "Agent interrupting", "file": "assets/transcripts/negative_interruption.mp3",
                 "text": "Ma'am, if you could just. Let me. I understand but..."},
            ],
            "actions": [
                {"label": "Flag for coaching review", "confirmation": "Call flagged for QA review. Added to Agent-017's coaching queue with priority."},
                {"label": "Share with team lead", "confirmation": "Call recording and analysis shared with Agent-017's team lead for coaching session."},
            ],
        }

    if "compliance" in q or "violation" in q:
        return {
            "text": (
                "**Compliance Violations (Last 7 Days)**\n\n"
                "Found **12 violations** across 3 types:\n\n"
                "| Type | Count | Severity |\n"
                "|------|-------|----------|\n"
                "| MISSING_DISCLOSURE | 7 | MEDIUM |\n"
                "| PCI_VIOLATION | 3 | HIGH |\n"
                "| SCRIPT_DEVIATION | 2 | LOW |\n\n"
                "3 PCI violations flagged for immediate review — "
                "agents read full card numbers aloud on recorded lines."
            ),
            "alert": {
                "type": "COMPLIANCE_VIOLATION",
                "emoji": "",
                "message": "3 PCI violations detected this week. Agents reading card numbers on recorded lines.",
            },
            "actions": [
                {"label": "Assign PCI retraining", "confirmation": "Mandatory PCI-DSS retraining assigned to 3 agents. Due within 48 hours. Manager notified.",
                 "slack_alert": {"type": "COMPLIANCE_VIOLATION", "emoji": "", "message": "PCI retraining assigned to 3 agents — mandatory within 48 hours."}},
                {"label": "Escalate to compliance team", "confirmation": "Compliance incident report filed. Compliance Officer notified for review within 24 hours."},
                {"label": "Enable secure payment IVR", "confirmation": "Secure payment IVR transfer enabled for all agents. Card numbers no longer taken verbally."},
            ],
        }

    if "improvement" in q or "effectiveness" in q:
        return {
            "text": (
                "**Coaching Effectiveness — Agent-017**\n\n"
                "| Period | Negative Rate | Escalations | Avg Handle Time |\n"
                "|--------|-------------|-------------|----------------|\n"
                "| Before coaching (Mar 25-31) | 30% | 6 | 8 min 15 sec |\n"
                "| Week 1 post-coaching (Apr 1-7) | 22% | 3 | 7 min 40 sec |\n"
                "| Week 2 post-coaching (Apr 8-14) | 18% | 2 | 7 min 10 sec |\n\n"
                "Agent-017 shows a 12 percentage point improvement in negative sentiment rate "
                "after de-escalation coaching. Escalations dropped by 67%. "
                "Recommend continuing monitored calls for one more week before clearing."
            ),
            "actions": [
                {"label": "Extend monitoring 1 week", "confirmation": "Agent-017 monitoring extended through Apr 21. Supervisor notified."},
                {"label": "Clear from coaching", "confirmation": "Agent-017 cleared from coaching program. Performance review scheduled for Apr 28."},
            ],
        }

    if "top perform" in q or "best agent" in q:
        return {
            "text": (
                "**Top Performing Agents (Last 7 Days)**\n\n"
                "| Rank | Agent | Positive Rate | Contacts | Avg Handle Time | Resolution Rate |\n"
                "|------|-------|--------------|----------|----------------|----------------|\n"
                "| 1 | Agent-008 | 82% | 142 | 5 min 20 sec | 94% |\n"
                "| 2 | Agent-014 | 78% | 138 | 5 min 45 sec | 91% |\n"
                "| 3 | Agent-003 | 76% | 135 | 6 min 10 sec | 89% |\n"
                "| 4 | Agent-019 | 74% | 128 | 5 min 55 sec | 90% |\n"
                "| 5 | Agent-011 | 72% | 131 | 6 min 30 sec | 87% |\n\n"
                "Agent-008 leads with 82% positive sentiment and 94% first-contact resolution. "
                "Consider pairing Agent-017 with Agent-008 for peer shadowing."
            ),
            "transcript_audio": [
                {"label": "Agent-008 — empathy and ownership", "file": "assets/transcripts/positive_agent008_empathy.mp3",
                 "text": "I completely understand how frustrating that must be. Let me take care of it right now..."},
                {"label": "Agent-014 — clean resolution + credit", "file": "assets/transcripts/positive_agent014_resolution.mp3",
                 "text": "Great news. I've processed your refund and added a $15 credit as an apology..."},
                {"label": "Agent-003 — proactive upsell", "file": "assets/transcripts/positive_agent003_proactive.mp3",
                 "text": "I noticed your subscription is renewing. You could save $20/month on the annual plan..."},
                {"label": "Agent-019 — de-escalation mastery", "file": "assets/transcripts/positive_agent019_deescalation.mp3",
                 "text": "You're absolutely right to be upset. I'm going to escalate this and personally follow up..."},
                {"label": "Agent-011 — professional closing", "file": "assets/transcripts/positive_agent011_closing.mp3",
                 "text": "Just to recap: new billing cycle on the 15th, credit applied, confirmation email within the hour..."},
            ],
            "actions": [
                {"label": "Pair Agent-017 with Agent-008", "confirmation": "Peer shadowing scheduled — Agent-017 will shadow Agent-008 for 3 shifts starting Monday."},
                {"label": "Send recognition to top 5", "confirmation": "Recognition messages sent to top 5 agents. Manager notified for quarterly awards consideration."},
            ],
        }

    # ── WFM queries ──
    if "forecast" in q or "staffing" in q or "next monday" in q:
        return {
            "text": (
                "**Staffing Forecast — Next Monday**\n\n"
                "📊 Projected contact volume: **340 contacts** between 10 AM–2 PM (peak)\n\n"
                "| Time Slot | Predicted | Current Staff | Recommended | Gap |\n"
                "|-----------|-----------|---------------|-------------|-----|\n"
                "| 10–11 AM | 78 | 5 | 6 | -1 |\n"
                "| 11–12 PM | 92 | 5 | 7 | -2 |\n"
                "| 12–1 PM | 88 | 4 | 6 | -2 |\n"
                "| 1–2 PM | 82 | 4 | 6 | -2 |\n\n"
                "**Recommendation:** Activate 4 agents from flex pool for 10 AM–2 PM. "
                "Confidence interval: 310–370 contacts (±9%)."
            ),
            "chart": "forecast",
            "actions": [
                {"label": "Activate 4 flex pool agents", "confirmation": "4 flex pool agents scheduled for Monday 10 AM - 2 PM. Calendar invites sent."},
                {"label": "Request overtime approval", "confirmation": "Overtime request submitted for 4 agents x 4 hours on Monday. Pending manager approval."},
                {"label": "Share forecast with team", "confirmation": "Monday staffing forecast shared to #connect-wfm Slack channel."},
            ],
        }

    if "burnout" in q:
        return {
            "text": (
                "**Burnout Risk Assessment**\n\n"
                "2 agents at critical burnout risk:\n\n"
                "**Agent-023** — Burnout score: **0.91**\n"
                "- Occupancy: 98% for 8 consecutive days\n"
                "- Handle time trend: increasing (+12% week over week)\n"
                "- ACW duration: 5 min 50 sec (avg 1 min 30 sec)\n"
                "- Action: Immediate schedule relief — reassign to low-volume queue within 24 hours\n\n"
                "**Agent-031** — Burnout score: **0.88**\n"
                "- Occupancy: 96% for 8 consecutive days\n"
                "- Handle time trend: increasing (+8% week over week)\n"
                "- Action: Schedule relief shift within 48 hours\n\n"
                "All other agents below 0.70 threshold."
            ),
            "alert": {
                "type": "BURNOUT_RISK",
                "emoji": "",
                "message": "Agent-023 (score 0.91) and Agent-031 (score 0.88) at critical burnout risk.",
            },
            "metrics": [
                {"label": "Agent-023 Score", "value": "0.91", "delta": "CRITICAL"},
                {"label": "Agent-031 Score", "value": "0.88", "delta": "CRITICAL"},
                {"label": "Days High Occ.", "value": "8", "delta": ""},
                {"label": "At-Risk Agents", "value": "2", "delta": ""},
            ],
            "actions": [
                {"label": "Reassign Agent-023 now", "confirmation": "Agent-023 moved to Returns queue (low volume) for 48 hours. Schedule updated.",
                 "slack_alert": {"type": "BURNOUT_RISK", "emoji": "", "message": "Agent-023 reassigned to Returns queue — burnout intervention."},
                 "email": {"to": "scheduling@company.com", "subject": "Urgent: Agent-023 Queue Reassignment", "body": "Hi Scheduling,\n\nPlease process the following urgent reassignment:\n\n- Agent: Agent-023\n- From: Billing queue\n- To: Returns queue (low volume)\n- Duration: 48 hours\n- Reason: Burnout score 0.91 — 98% occupancy for 8 consecutive days\n\nThis is a burnout intervention. Please confirm.\n\nThank you"}},
                {"label": "Reduce Agent-031 shift", "confirmation": "Agent-031 shift reduced by 2 hours for next 3 days. Manager notified.",
                 "calendar": {"title": "Agent-031 — Reduced Shift (Burnout Intervention)", "description": "Agent-031 shift reduced by 2 hours for next 3 days.\nBurnout score: 0.88\nOccupancy: 96% for 8 days", "start_hours": 24, "duration_minutes": 360}},
                {"label": "Deploy flex pool", "confirmation": "2 flex pool agents activated for Billing queue 10 AM - 2 PM to cover the gap."},
            ],
        }

    if "flex pool" in q or "flex" in q:
        return {
            "text": (
                "**Flex Pool Allocation — Today**\n\n"
                "| Pool Status | Count |\n"
                "|------------|-------|\n"
                "| Total flex agents | 8 |\n"
                "| Currently deployed | 3 |\n"
                "| Available | 5 |\n\n"
                "**Recommended deployment:**\n\n"
                "| Queue | Agents Needed | Reason |\n"
                "|-------|--------------|--------|\n"
                "| Billing | 2 | SLA breach — 68.5% vs 80% threshold |\n"
                "| VIP | 1 | Approaching breach — 88% vs 90% threshold |\n\n"
                "Deploy 2 agents to Billing immediately (10 AM - 2 PM block). "
                "Hold 1 for VIP standby. Per the Flex Pool Allocation Guide, "
                "minimum 2-hour deployment blocks to avoid constant reassignment."
            ),
            "actions": [
                {"label": "Deploy 2 to Billing now", "confirmation": "2 flex pool agents deployed to Billing queue. 10 AM - 2 PM block confirmed.",
                 "slack_alert": {"type": "SLA_BREACH", "emoji": "", "message": "Flex pool deployed: 2 agents to Billing queue."}},
                {"label": "Place 1 on VIP standby", "confirmation": "1 flex pool agent on VIP standby. Auto-activate if SLA drops below 85%."},
            ],
        }

    if "overtime" in q:
        return {
            "text": (
                "**Overtime Analysis — This Week**\n\n"
                "| Day | Forecast Gap | OT Hours Needed | Est. Cost |\n"
                "|-----|-------------|----------------|----------|\n"
                "| Monday | -4 agents (10-2 PM) | 16 hrs | $720 |\n"
                "| Tuesday | -2 agents (11-1 PM) | 4 hrs | $180 |\n"
                "| Wednesday | Staffed | 0 hrs | $0 |\n"
                "| Thursday | -1 agent (12-2 PM) | 2 hrs | $90 |\n"
                "| Friday | -3 agents (10-2 PM) | 12 hrs | $540 |\n\n"
                "**Total OT needed: 34 hours ($1,530)**\n\n"
                "Alternative: Activate 2 flex pool agents for Mon/Fri peak blocks — "
                "saves $960 vs overtime. Per Overtime Authorization Policy, "
                "supervisor can approve up to 2 hours directly."
            ),
            "actions": [
                {"label": "Use flex pool instead", "confirmation": "Flex pool activated for Monday and Friday peak blocks. Estimated savings: $960 vs overtime."},
                {"label": "Approve overtime", "confirmation": "34 hours overtime approved. Payroll notified.",
                 "email": {"to": "payroll@company.com", "subject": "Overtime Approval — Week of Apr 14",
                           "body": "Hi Payroll,\n\nPlease process the following overtime approval:\n\n- Total hours: 34\n- Cost: $1,530\n- Period: Week of April 14, 2026\n- Approved by: Contact Center Supervisor\n\nBreakdown:\n- Monday: 16 hrs\n- Tuesday: 4 hrs\n- Thursday: 2 hrs\n- Friday: 12 hrs\n\nPlease confirm receipt.\n\nThank you"}},
                {"label": "Split approach", "confirmation": "Flex pool for Monday (saves $720), overtime for Friday only ($540). Best cost balance."},
            ],
        }

    if "attrition" in q or "risk of leaving" in q:
        return {
            "text": (
                "**Attrition Risk Assessment**\n\n"
                "Combined burnout + sentiment analysis identifies agents most likely to leave:\n\n"
                "| Agent | Burnout Score | Neg. Sentiment | Tenure | Risk Level |\n"
                "|-------|-------------|---------------|--------|------------|\n"
                "| Agent-023 | 0.91 | 18% | 14 months | CRITICAL |\n"
                "| Agent-031 | 0.88 | 15% | 8 months | HIGH |\n"
                "| Agent-017 | 0.72 | 30% | 22 months | HIGH |\n"
                "| Agent-009 | 0.65 | 20% | 6 months | MEDIUM |\n\n"
                "Agent-023 is the highest attrition risk — sustained high occupancy combined with "
                "rising negative sentiment. Agent-017 has lower burnout but the highest negative "
                "sentiment rate, suggesting job dissatisfaction rather than workload issues."
            ),
            "actions": [
                {"label": "Schedule 1:1 with Agent-023", "confirmation": "1:1 meeting scheduled with Agent-023 and supervisor for tomorrow 9 AM. Retention discussion."},
                {"label": "Adjust Agent-031 schedule", "confirmation": "Agent-031 shift reduced by 2 hours for next 2 weeks. Occupancy target set to 80%."},
                {"label": "Refer Agent-017 to EAP", "confirmation": "Employee Assistance Program referral initiated for Agent-017. Confidential support available."},
            ],
        }

    if "full week" in q or "weekly forecast" in q or "7 day" in q:
        return {
            "text": (
                "**7-Day Staffing Forecast**\n\n"
                "| Day | Predicted Volume | Staff Needed | Current Staff | Gap |\n"
                "|-----|-----------------|-------------|--------------|-----|\n"
                "| Monday | 680 | 22 | 18 | -4 |\n"
                "| Tuesday | 520 | 18 | 18 | 0 |\n"
                "| Wednesday | 490 | 17 | 18 | +1 |\n"
                "| Thursday | 510 | 18 | 18 | 0 |\n"
                "| Friday | 620 | 21 | 18 | -3 |\n"
                "| Saturday | 280 | 10 | 8 | -2 |\n"
                "| Sunday | 180 | 7 | 6 | -1 |\n\n"
                "Monday and Friday are the critical days — recommend flex pool activation "
                "for both. Saturday gap can be covered with 2 hours overtime per agent."
            ),
            "chart": "forecast",
            "actions": [
                {"label": "Activate flex pool Mon+Fri", "confirmation": "Flex pool scheduled for Monday and Friday 10 AM - 2 PM. 4 agents Monday, 3 agents Friday."},
                {"label": "Approve Saturday overtime", "confirmation": "2 hours overtime approved for 2 agents on Saturday. Cost: $180."},
                {"label": "Share weekly plan", "confirmation": "Weekly staffing plan shared to #connect-wfm and emailed to all team leads."},
            ],
        }

    # Default
    return {
        "text": (
            "I'm not sure how to answer that. Try asking about:\n"
            "- **Supervisor:** queue health, abandonment, agent utilization\n"
            "- **Quality:** sentiment trends, coaching, compliance violations\n"
            "- **WFM:** staffing forecasts, burnout signals"
        ),
    }


def enrich_with_kb(response: dict, query: str) -> dict:
    """Add knowledge base context to an agent response."""
    try:
        kb_results = kb_retrieve(query, max_results=2)
        if kb_results:
            response["kb_docs"] = kb_results
    except Exception:
        pass  # KB enrichment is optional — don't break the response
    return response


def generate_demo_chart(chart_type: str):
    """Generate a matplotlib chart for the demo."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import io

    if chart_type == "sentiment":
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        positive = [45, 58, 62, 60, 63, 65, 61]
        negative = [25, 16, 14, 15, 13, 12, 14]
        neutral = [20, 16, 15, 16, 15, 14, 16]
        mixed = [10, 10, 9, 9, 9, 9, 9]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(days, positive, marker="o", color="#2ecc71", linewidth=2, label="Positive")
        ax.plot(days, negative, marker="o", color="#e74c3c", linewidth=2, label="Negative")
        ax.plot(days, neutral, marker="o", color="#95a5a6", linewidth=2, label="Neutral")
        ax.plot(days, mixed, marker="o", color="#f39c12", linewidth=2, label="Mixed")
        ax.axvline(x=0, color="#e74c3c", linestyle="--", alpha=0.3, label="Monday spike")
        ax.set_ylabel("Percentage (%)")
        ax.set_title("Sentiment Trends — Last 7 Days")
        ax.legend()
        ax.set_ylim(0, 80)
        fig.tight_layout()

    elif chart_type == "forecast":
        hours = list(range(6, 22))
        predicted = [12, 18, 35, 55, 78, 92, 88, 82, 65, 58, 52, 45, 38, 30, 22, 15]
        lower = [max(0, p - int(p * 0.15)) for p in predicted]
        upper = [p + int(p * 0.15) for p in predicted]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(hours, predicted, color="#3498db", linewidth=2, marker="o", label="Predicted Volume")
        ax.fill_between(hours, lower, upper, alpha=0.2, color="#3498db", label="Confidence Band (±15%)")
        ax.axhline(y=60, color="#e74c3c", linestyle="--", alpha=0.5, label="Current Staffing Capacity")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Contact Volume")
        ax.set_title("Staffing Forecast — Next Monday")
        ax.legend()
        ax.set_xticks(hours)
        ax.set_xticklabels([f"{h}:00" for h in hours], rotation=45)
        fig.tight_layout()
    else:
        return None

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf


def try_voice_synthesis(text: str) -> bytes | None:
    """Try Polly neural voice synthesis, return None if it fails."""
    try:
        import boto3
        import streamlit as _st_voice
        # Explicitly pass credentials from st.secrets for Streamlit Cloud
        aws_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        if not aws_key:
            try:
                aws_key = _st_voice.secrets.get("AWS_ACCESS_KEY_ID", "")
                aws_secret = _st_voice.secrets.get("AWS_SECRET_ACCESS_KEY", "")
                region = _st_voice.secrets.get("AWS_DEFAULT_REGION", "us-east-1")
            except Exception:
                pass
        if aws_key and aws_secret:
            polly = boto3.client(
                "polly",
                region_name=region,
                aws_access_key_id=aws_key,
                aws_secret_access_key=aws_secret,
            )
        else:
            polly = boto3.client("polly", region_name="us-east-1")
        response = polly.synthesize_speech(
            Text=text[:3000],
            OutputFormat="mp3",
            VoiceId="Matthew",
            Engine="neural",
        )
        return response["AudioStream"].read()
    except Exception as e:
        import streamlit as _st2
        _st2.warning(f"Voice error: {e}")
        return None


# Run voice test if requested from sidebar button
if st.session_state.get("_run_voice_test", False):
    st.session_state["_run_voice_test"] = False
    with st.sidebar:
        with st.spinner("Testing Polly..."):
            _test_audio = try_voice_synthesis("Hello. Voice synthesis is working.")
            if _test_audio:
                st.audio(_test_audio, format="audio/mpeg")
                st.success("Voice works!")
            else:
                st.error("Polly failed")


# ---------------------------------------------------------------------------
# Helper functions for email drafts and calendar invites
# ---------------------------------------------------------------------------

def generate_ics_data(title, description, start_hours_from_now=24, duration_minutes=30):
    """Return a valid .ics calendar file content string."""
    now = datetime.now(timezone.utc)
    start = now + timedelta(hours=start_hours_from_now)
    end = start + timedelta(minutes=duration_minutes)
    fmt = "%Y%m%dT%H%M%SZ"
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Connect Analytics//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"DTSTART:{start.strftime(fmt)}\r\n"
        f"DTEND:{end.strftime(fmt)}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{description}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def generate_mailto_url(to, subject, body):
    """Return a properly URL-encoded mailto: link string."""
    return f"mailto:{to}?subject={url_quote(subject)}&body={url_quote(body)}"


# ---------------------------------------------------------------------------
# Agent chat function
# ---------------------------------------------------------------------------

def agent_chat(agent_name: str, agent_color: str, agent_emoji: str):
    """Render a chat interface for an agent."""
    key = f"chat_{agent_name}"
    if key not in st.session_state:
        st.session_state[key] = []

    # Prompt library — ServiceNow-style clickable cards
    PROMPT_LIBRARY = {
        "Supervisor": [
            {"icon": "🏥", "title": "Queue Health", "prompt": "Show me queue health right now", "desc": "SLA status, wait times, agent availability"},
            {"icon": "📉", "title": "Abandonment Analysis", "prompt": "Why did abandonment spike at 2pm?", "desc": "Root cause analysis with agent correlation"},
            {"icon": "👥", "title": "Agent Utilization", "prompt": "Show me agent utilization for today", "desc": "Per-agent occupancy, status, handle times"},
            {"icon": "🚨", "title": "SLA Breach Alert", "prompt": "Are any queues breaching SLA right now?", "desc": "Real-time threshold monitoring"},
            {"icon": "📊", "title": "Peak Hour Analysis", "prompt": "What are the busiest hours today?", "desc": "Volume patterns and staffing gaps"},
            {"icon": "🔄", "title": "Transfer Analysis", "prompt": "Which queues have the highest transfer rates?", "desc": "Transfer patterns and routing issues"},
        ],
        "Quality": [
            {"icon": "😊", "title": "Sentiment Trends", "prompt": "Show me sentiment trends this week", "desc": "Positive/negative/neutral breakdown with chart"},
            {"icon": "🎓", "title": "Coaching Needed", "prompt": "Which agents need coaching this week?", "desc": "Agents above negative sentiment threshold"},
            {"icon": "📞", "title": "Worst Call", "prompt": "Show me the worst call this week", "desc": "Transcript with per-turn sentiment analysis"},
            {"icon": "🛑", "title": "Compliance Violations", "prompt": "Any compliance violations this week?", "desc": "PCI, disclosure, and script violations"},
            {"icon": "📈", "title": "Improvement Tracking", "prompt": "Show coaching effectiveness for Agent-017", "desc": "Before/after sentiment comparison"},
            {"icon": "⭐", "title": "Top Performers", "prompt": "Who are the top performing agents?", "desc": "Highest positive sentiment and resolution rates"},
        ],
        "WFM": [
            {"icon": "📅", "title": "Staffing Forecast", "prompt": "Forecast staffing for next Monday", "desc": "Predicted volume with confidence intervals"},
            {"icon": "🔥", "title": "Burnout Signals", "prompt": "Any agents showing burnout signals?", "desc": "Occupancy, handle time trends, risk scores"},
            {"icon": "🏊", "title": "Flex Pool", "prompt": "How should I allocate the flex pool today?", "desc": "Demand-based flex pool recommendations"},
            {"icon": "⏰", "title": "Overtime Needs", "prompt": "Do we need overtime this week?", "desc": "Gap analysis between forecast and staffing"},
            {"icon": "📉", "title": "Attrition Risk", "prompt": "Which agents are at risk of leaving?", "desc": "Burnout + sentiment combined risk score"},
            {"icon": "🔮", "title": "Weekly Forecast", "prompt": "Give me the full week forecast", "desc": "7-day volume prediction with charts"},
        ],
    }

    prompts = PROMPT_LIBRARY.get(agent_name, [])

    # Show prompt cards always (collapsed into expander after first use)
    if prompts:
        show_expanded = not bool(st.session_state[key])
        with st.expander("Quick prompts", expanded=show_expanded):
            rows = [prompts[i:i+3] for i in range(0, len(prompts), 3)]
            for row in rows:
                cols = st.columns(len(row))
                for j, p in enumerate(row):
                    with cols[j]:
                        card_clicked = st.button(
                            f"{p['icon']}  {p['title']}\n{p['desc']}",
                            key=f"prompt_{agent_name}_{prompts.index(p)}",
                            use_container_width=True,
                        )
                        if card_clicked:
                            st.session_state[key] = []  # Clear previous chat
                            st.session_state[key].append({"role": "user", "content": p["prompt"]})
                            with st.spinner(f"{agent_name} Agent thinking..."):
                                time.sleep(1.2)
                                response = live_agent_response(agent_name, p["prompt"]) if (st.session_state.get("live_mode_toggle", False) and _LIVE_MODE) else simulate_agent_response(agent_name, p["prompt"])
                                response = enrich_with_kb(response, p["prompt"])
                            msg_data = {"role": "agent", "content": response["text"]}
                            if "kb_docs" in response:
                                msg_data["kb_docs"] = response["kb_docs"]
                            if "chart" in response:
                                chart_buf = generate_demo_chart(response["chart"])
                                if chart_buf:
                                    msg_data["chart"] = chart_buf
                            if "metrics" in response:
                                msg_data["metrics"] = response["metrics"]
                            if "actions" in response:
                                msg_data["actions"] = response["actions"]
                            if "transcript_audio" in response:
                                msg_data["transcript_audio"] = response["transcript_audio"]
                            # Voice synthesis if enabled
                            if st.session_state.get("voice_toggle", False):
                                with st.spinner("🔊 Generating voice..."):
                                    audio_bytes = try_voice_synthesis(response["text"])
                                    if audio_bytes:
                                        msg_data["audio"] = audio_bytes
                            if "alert" in response:
                                alert = response["alert"]
                                alert["time"] = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                                st.session_state.alerts.append(alert)
                                post_to_slack(alert)
                            st.session_state[key].append(msg_data)
                            st.rerun()

    # Display chat history
    for msg in st.session_state[key]:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="agent-msg">{msg["content"]}</div>', unsafe_allow_html=True)
            if "chart" in msg:
                st.image(msg["chart"], width="stretch")
            if "kb_docs" in msg:
                st.markdown("---")
                for doc in msg["kb_docs"]:
                    with st.expander(f"📎 {doc['title']} — *{doc['source']}*", expanded=False):
                        # Load full doc content
                        doc_path = Path(__file__).parent.parent / "knowledge_base" / doc["source"]
                        if doc_path.exists():
                            st.markdown(doc_path.read_text())
                        else:
                            st.markdown(doc["excerpt"])
            if "metrics" in msg:
                cols = st.columns(len(msg["metrics"]))
                for i, m in enumerate(msg["metrics"]):
                    cols[i].metric(m["label"], m["value"], m.get("delta", ""))
            if "audio" in msg:
                st.audio(msg["audio"], format="audio/mpeg")
            if msg.get("voice_error"):
                st.warning("🔊 Voice synthesis failed — check AWS credentials in Streamlit secrets")
            if "transcript_audio" in msg:
                st.markdown("---")
                st.markdown("**Call transcript recordings:**")
                for ta in msg["transcript_audio"]:
                    with st.expander(f"Listen: {ta['label']}"):
                        st.caption(f'"{ta["text"]}"')
                        audio_path = Path(__file__).parent.parent / ta["file"]
                        if audio_path.exists():
                            st.audio(str(audio_path), format="audio/mpeg")
                        else:
                            st.caption("Audio file not found — run: python scripts/generate_transcript_audio.py")
            if "actions" in msg:
                st.markdown("---")
                st.markdown("**Recommended actions:**")
                for ai, action in enumerate(msg["actions"]):
                    action_key = f"action_{agent_name}_{hash(action['label'])}_{ai}"
                    ac1, ac2 = st.columns([3, 1]) if ("email" in action or "calendar" in action) else (st.columns([1])[0], None)

                    with ac1 if ac2 else st.container():
                        if "email" not in action and "calendar" not in action:
                            if st.button(action["label"], key=action_key, use_container_width=True):
                                with st.spinner(f"Executing: {action['label']}..."):
                                    time.sleep(1.5)
                                st.success(action["confirmation"])
                                if "slack_alert" in action:
                                    alert = action["slack_alert"]
                                    alert["time"] = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                                    st.session_state.alerts.append(alert)
                                    post_to_slack(alert)
                        else:
                            if st.button(action["label"], key=action_key, use_container_width=True):
                                with st.spinner(f"Executing: {action['label']}..."):
                                    time.sleep(1.5)
                                st.success(action["confirmation"])
                                if "slack_alert" in action:
                                    alert = action["slack_alert"]
                                    alert["time"] = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                                    st.session_state.alerts.append(alert)
                                    post_to_slack(alert)

                    if ac2:
                        with ac2:
                            if "calendar" in action:
                                cal = action["calendar"]
                                ics_data = generate_ics_data(cal["title"], cal["description"], cal.get("start_hours", 24), cal.get("duration_minutes", 30))
                                st.download_button(
                                    label="Add to calendar",
                                    data=ics_data,
                                    file_name=f"{cal['title'].replace(' ', '_')}.ics",
                                    mime="text/calendar",
                                    key=f"cal_{action_key}",
                                    use_container_width=True,
                                )
                            if "email" in action:
                                em = action["email"]
                                eml_content = (
                                    f"To: {em['to']}\r\n"
                                    f"Subject: {em['subject']}\r\n"
                                    f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
                                    f"{em['body']}"
                                )
                                st.download_button(
                                    label="Draft email",
                                    data=eml_content,
                                    file_name=f"{em['subject'].replace(' ', '_')[:40]}.eml",
                                    mime="message/rfc822",
                                    key=f"eml_{action_key}",
                                    use_container_width=True,
                                )

    # Input
    query = st.chat_input(f"Ask the {agent_name} Agent...", key=f"input_{agent_name}")

    if query:
        st.session_state[key].append({"role": "user", "content": query})

        with st.spinner(f"{agent_emoji} {agent_name} Agent thinking..."):
            time.sleep(1.2)  # Simulate latency
            response = live_agent_response(agent_name, query) if (st.session_state.get('live_mode_toggle', False) and _LIVE_MODE) else simulate_agent_response(agent_name, query)
            response = enrich_with_kb(response, query)

        msg_data = {"role": "agent", "content": response["text"]}

        # Add KB docs if present
        if "kb_docs" in response:
            msg_data["kb_docs"] = response["kb_docs"]

        # Generate chart if needed
        if "chart" in response:
            chart_buf = generate_demo_chart(response["chart"])
            if chart_buf:
                msg_data["chart"] = chart_buf

        # Add metrics if present
        if "metrics" in response:
            msg_data["metrics"] = response["metrics"]

        # Add actions if present
        if "actions" in response:
            msg_data["actions"] = response["actions"]

        # Add transcript audio if present
        if "transcript_audio" in response:
            msg_data["transcript_audio"] = response["transcript_audio"]

        st.session_state[key].append(msg_data)

        # Voice synthesis if enabled
        if st.session_state.get("voice_toggle", False):
            with st.spinner("🔊 Generating voice..."):
                audio_bytes = try_voice_synthesis(response["text"])
                if audio_bytes:
                    msg_data["audio"] = audio_bytes
                else:
                    st.warning("🔊 Voice unavailable — check AWS credentials in Streamlit secrets")

        # Fire alert if present
        if "alert" in response:
            alert = response["alert"]
            alert["time"] = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            st.session_state.alerts.append(alert)

            # Post to real Slack
            slack_sent = post_to_slack(alert)
            if slack_sent:
                st.toast(f"🔔 Alert sent to Slack: {alert['type']}", icon="✅")
            else:
                st.toast(f"🔔 Alert: {alert['type']} (Slack not configured)", icon="⚠️")

        st.rerun()


# ---------------------------------------------------------------------------
# Tab content
# ---------------------------------------------------------------------------

with tab_auto:
    st.markdown("### 🎬 5-Minute Guided Demo")
    st.caption("Click Start to walk through the platform with narration")

    if "demo_step" not in st.session_state:
        st.session_state.demo_step = 0

    DEMO_STEPS = [
        {
            "title": "🔴 The Day 2 Problem",
            "narration": "Every Amazon Connect deployment hits the same wall on Day 2. The data is there, but supervisors check five dashboards to answer one question. It takes 20 minutes. Quality analysts sample only 2 percent of calls. Workforce planners need a data engineer just to forecast next Monday.",
            "content": """
**The problem we're solving:**

| Before | After |
|--------|-------|
| 20 min to get an answer | 2 seconds |
| $150K/year analytics cost | $34/month |
| 2% call coverage (manual QA) | 100% AI-analyzed |
| SLA breach detected 15+ min late | Under 60 seconds |
| Burnout detected after resignation | 8 days early |
            """,
            "duration": 45,
        },
        {
            "title": "🟢 Supervisor Agent — Queue Health",
            "narration": "The Supervisor Agent monitors queue health in real time. It queries 10,000 contact trace records via SQL and returns SLA percentages, wait times, and abandonment rates. When a threshold is breached, it fires a Slack alert in under 60 seconds.",
            "content": None,  # Will run live query
            "query": ("Supervisor", "Show me queue health"),
            "duration": 50,
        },
        {
            "title": "🟠 Quality Agent — Sentiment & Coaching",
            "narration": "The Quality Agent analyzes every single call, not just a 2 percent sample. It surfaces sentiment trends across all agents and generates targeted coaching recommendations with transcript excerpts.",
            "content": None,
            "query": ("Quality", "Show me coaching recommendations"),
            "duration": 50,
        },
        {
            "title": "🔵 WFM Agent — Forecasting & Burnout",
            "narration": "The WFM Agent runs on Nova Lite, which is 50 times cheaper than Claude Sonnet. It forecasts staffing needs by hour and detects burnout signals 8 days before agents quit, based on sustained high occupancy and rising handle times.",
            "content": None,
            "query": ("WFM", "Show me burnout signals"),
            "duration": 50,
        },
        {
            "title": "🤝 Agent-to-Agent Handoff",
            "narration": "The three agents collaborate automatically. The Supervisor detects a problem, hands off to WFM to adjust schedules, which triggers Quality to schedule coaching. Three agents, four seconds, zero human intervention.",
            "content": """
**Handoff chain:**
1. 🟢 **Supervisor** detects SLA breach in Billing queue
2. 🟢 → 🔵 Hands off to **WFM** — recommends pulling 2 agents from flex pool
3. 🔵 → 🟠 Triggers **Quality** — schedules coaching for high-negative agents
4. ✅ All three agents collaborated in ~4 seconds
            """,
            "duration": 45,
        },
        {
            "title": "🏗️ Architecture & Deployment",
            "narration": "The entire platform deploys with one CDK command in 8 minutes. Five stacks: Auth, Data, Knowledge Base, Agents, and Alerts. No CloudFront, no Terraform. Total cost: 34 dollars per month. The code is open source on GitHub.",
            "content": """
**5 CDK Stacks — One Command:**
- `ConnectAnalytics-Auth` → Secrets Manager
- `ConnectAnalytics-Data` → S3 + Glue + Athena
- `ConnectAnalytics-KB` → Bedrock Knowledge Base
- `ConnectAnalytics-Agents` → AgentCore Gateway + 3 agents + 9 Lambda tools
- `ConnectAnalytics-Alerts` → EventBridge → SNS → Slack

**Deploy:** `cdk deploy --all` (~8 minutes)
**Cost:** ~$34/month | **Coverage:** 100% of calls | **Speed:** 2-second answers
            """,
            "duration": 45,
        },
    ]

    step = st.session_state.demo_step
    total = len(DEMO_STEPS)

    # Progress bar
    st.progress(step / total if step < total else 1.0, text=f"Step {min(step+1, total)} of {total}")

    if step < total:
        s = DEMO_STEPS[step]
        st.markdown(f"## {s['title']}")

        # Voice narration
        if s.get("narration"):
            voice_audio = try_voice_synthesis(s["narration"])
            if voice_audio:
                st.audio(voice_audio, format="audio/mpeg", autoplay=True)
            else:
                st.info(f"🎙️ _{s['narration']}_")

        # Content
        if s.get("content"):
            st.markdown(s["content"])

        if s.get("query"):
            agent, query = s["query"]
            with st.spinner(f"{agent} Agent thinking..."):
                import time as _t
                _t.sleep(1.0)
                if _LIVE_MODE and st.session_state.get("live_mode_toggle", False):
                    response = live_agent_response(agent, query)
                else:
                    response = simulate_agent_response(agent, query)
                st.markdown(response["text"])
                if "metrics" in response:
                    cols = st.columns(len(response["metrics"]))
                    for i, m in enumerate(response["metrics"]):
                        cols[i].metric(m["label"], m["value"], m.get("delta", ""))

        # Navigation
        st.write("")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if step > 0 and st.button("⬅️ Previous", key=f"prev_{step}"):
                st.session_state.demo_step = step - 1
                st.rerun()
        with c2:
            if st.button("⏭️ Next Step" if step < total - 1 else "🎉 Finish", key=f"next_{step}", type="primary", use_container_width=True):
                st.session_state.demo_step = step + 1
                st.rerun()
        with c3:
            if st.button("⏹️ Reset", key=f"reset_{step}"):
                st.session_state.demo_step = 0
                st.rerun()
    else:
        st.markdown("## 🎉 Demo Complete!")
        st.success("Three agents. One CDK command. Every answer in 2 seconds. $34/month.")
        st.balloons()
        if st.button("🔄 Run Again", type="primary"):
            st.session_state.demo_step = 0
            st.rerun()

with tab_sup:

    st.markdown('<h2 class="supervisor-header">Supervisor Agent</h2>', unsafe_allow_html=True)
    st.caption("Claude Sonnet — Queue health, SLA breaches, agent utilization, abandonment analysis")

    st.markdown("---")
    agent_chat("Supervisor", "#037f0c", "🟢")

with tab_qual:

    st.markdown('<h2 class="quality-header">Quality Agent</h2>', unsafe_allow_html=True)
    st.caption("Claude Sonnet — Sentiment trends, coaching recommendations, compliance violations")

    st.markdown("---")
    agent_chat("Quality", "#eb5f07", "🟠")

with tab_wfm:

    st.markdown('<h2 class="wfm-header">WFM Agent</h2>', unsafe_allow_html=True)
    st.caption("Nova Lite — Staffing forecasts, burnout signals, schedule optimization")

    st.markdown("---")
    agent_chat("WFM", "#0972d3", "🔵")

with tab_dash:
    st.markdown('<h2 style="color:#FF9900;">📊 Agent Operations Dashboard</h2>', unsafe_allow_html=True)
    st.caption("Real-time monitoring of all three AI agents and the alert pipeline")
    st.markdown("---")

    # Agent status cards
    st.markdown("### Agent Status")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="agent-card sup" style="text-align:center;">
            <h4 style="color:#2ecc71; margin:0;">🟢 Supervisor</h4>
            <p style="color:#2ecc71; font-size:1.5rem; font-weight:700; margin:8px 0;">ACTIVE</p>
            <p style="color:#8fbc8f; margin:2px 0;">Claude Sonnet · 4 tools</p>
            <p style="color:#8fbc8f; margin:2px 0;">Avg response: 1.8s</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="agent-card qual" style="text-align:center;">
            <h4 style="color:#FF9900; margin:0;">🟠 Quality</h4>
            <p style="color:#FF9900; font-size:1.5rem; font-weight:700; margin:8px 0;">ACTIVE</p>
            <p style="color:#d4a574; margin:2px 0;">Claude Sonnet · 3 tools</p>
            <p style="color:#d4a574; margin:2px 0;">Avg response: 2.1s</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="agent-card wfm" style="text-align:center;">
            <h4 style="color:#3498db; margin:0;">🔵 WFM</h4>
            <p style="color:#3498db; font-size:1.5rem; font-weight:700; margin:8px 0;">ACTIVE</p>
            <p style="color:#7fb3d4; margin:2px 0;">Nova Lite · 2 tools</p>
            <p style="color:#7fb3d4; margin:2px 0;">Avg response: 1.2s</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Metrics row
    st.markdown("### Platform Metrics (Last 24h)")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Queries", "1,247", "+12%")
    m2.metric("Avg Latency", "1.7s", "-0.3s")
    m3.metric("Alerts Fired", "23", "+5")
    m4.metric("Charts Generated", "89", "+15")
    m5.metric("Voice Requests", "34", "+8")

    st.markdown("---")

    # Query volume chart
    st.markdown("### Query Volume by Agent (Last 7 Days)")
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    dates = pd.date_range("2026-04-07", periods=7, freq="D")
    chart_data = pd.DataFrame({
        "Supervisor": np.random.randint(50, 120, 7),
        "Quality": np.random.randint(30, 80, 7),
        "WFM": np.random.randint(20, 60, 7),
    }, index=dates)
    st.area_chart(chart_data, color=["#2ecc71", "#FF9900", "#3498db"])

    st.markdown("---")

    # Alert history
    st.markdown("### Recent Alerts")
    alert_history = pd.DataFrame({
        "Time": ["14:02 UTC", "13:45 UTC", "12:30 UTC", "11:15 UTC", "10:02 UTC"],
        "Type": ["🚨 SLA_BREACH", "🔥 BURNOUT_RISK", "🛑 COMPLIANCE", "🚨 SLA_BREACH", "🔥 BURNOUT_RISK"],
        "Details": [
            "Billing queue at 68.5% (threshold 80%)",
            "Agent-023 score 0.91 — 8 days high occupancy",
            "PCI violation — Agent-017 read card number",
            "Support queue at 72% (threshold 80%)",
            "Agent-031 score 0.88 — rising handle times",
        ],
        "Slack": ["✅ Sent", "✅ Sent", "✅ Sent", "✅ Sent", "✅ Sent"],
    })
    st.dataframe(alert_history, hide_index=True, use_container_width=True)

    st.markdown("---")

    # Infrastructure health
    st.markdown("### Infrastructure Health")
    i1, i2, i3, i4 = st.columns(4)
    i1.metric("AgentCore Gateway", "Healthy")
    i2.metric("Athena Workgroup", "Healthy")
    i3.metric("EventBridge", "Healthy")
    i4.metric("S3 Data Lake", "10.2 GB")

    st.markdown("---")

    # Staffing visual — queue cards with staff counts and reassignment
    st.markdown("### Queue Staffing Overview")

    if "queue_staff" not in st.session_state:
        st.session_state.queue_staff = {
            "Billing": {"staff": 4, "needed": 7, "sla": 68.5, "status": "BREACH"},
            "Sales": {"staff": 5, "needed": 5, "sla": 82.0, "status": "OK"},
            "Support": {"staff": 6, "needed": 5, "sla": 74.0, "status": "OK"},
            "Returns": {"staff": 4, "needed": 3, "sla": 85.0, "status": "OK"},
            "VIP": {"staff": 3, "needed": 4, "sla": 88.0, "status": "AT RISK"},
        }

    qs = st.session_state.queue_staff
    q_cols = st.columns(len(qs))

    for idx, (queue, data) in enumerate(qs.items()):
        with q_cols[idx]:
            gap = data["staff"] - data["needed"]
            if data["status"] == "BREACH":
                border_color = "#f87171"
                status_color = "#f87171"
            elif data["status"] == "AT RISK":
                border_color = "#fb923c"
                status_color = "#fb923c"
            else:
                border_color = "#34d399"
                status_color = "#34d399"

            st.markdown(f"""
            <div style="background:#1e293b; border:1px solid {border_color}; border-radius:12px;
                        padding:16px; text-align:center; border-top:3px solid {border_color};">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:8px;">{queue}</div>
                <div style="font-size:2rem; font-weight:800; color:#f1f5f9;">{data['staff']}</div>
                <div style="font-size:0.7rem; color:#64748b; margin-bottom:8px;">of {data['needed']} needed</div>
                <div style="font-size:0.75rem; color:{status_color}; font-weight:600;">{data['status']}</div>
                <div style="font-size:0.7rem; color:#64748b; margin-top:4px;">SLA: {data['sla']}%</div>
                <div style="background:#0f172a; border-radius:6px; height:6px; margin-top:8px; overflow:hidden;">
                    <div style="background:{border_color}; height:100%; width:{min(100, data['sla'])}%; border-radius:6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("### Reassign Agents")

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        from_queue = st.selectbox("From queue", list(qs.keys()), key="from_q")
    with rc2:
        to_queue = st.selectbox("To queue", [q for q in qs.keys() if q != from_queue], key="to_q")
    with rc3:
        num_agents = st.number_input("Agents", min_value=1, max_value=5, value=1, key="num_reassign")

    if st.button("Reassign agents", key="reassign_btn", use_container_width=True):
        if qs[from_queue]["staff"] >= num_agents:
            qs[from_queue]["staff"] -= num_agents
            qs[to_queue]["staff"] += num_agents
            # Recalculate SLA estimates
            for q in qs:
                ratio = qs[q]["staff"] / max(qs[q]["needed"], 1)
                qs[q]["sla"] = min(99.0, round(60 + ratio * 30, 1))
                if qs[q]["sla"] >= 80:
                    qs[q]["status"] = "OK"
                elif qs[q]["sla"] >= 70:
                    qs[q]["status"] = "AT RISK"
                else:
                    qs[q]["status"] = "BREACH"
            st.success(f"{num_agents} agent(s) moved from {from_queue} to {to_queue}")
            st.rerun()
        else:
            st.error(f"Not enough agents in {from_queue} (only {qs[from_queue]['staff']} available)")


with tab_kb:
    st.markdown('<h2 style="color:#9b59b6;">📚 Knowledge Base — SharePoint Integration</h2>', unsafe_allow_html=True)
    st.caption("Agents pull SOPs, training docs, and compliance policies from SharePoint to enrich responses")
    st.markdown("---")

    # Connection status
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a3e, #2d1a4e); border: 1px solid #9b59b6;
                border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <h4 style="color:#9b59b6; margin:0 0 8px 0;">📎 SharePoint Connector</h4>
        <p style="color:#c8a2e8; margin:4px 0;">Status: <span style="color:#2ecc71; font-weight:700;">Connected</span></p>
        <p style="color:#c8a2e8; margin:4px 0;">Site: <code style="color:#FF9900;">contoso.sharepoint.com/sites/ContactCenter</code></p>
        <p style="color:#c8a2e8; margin:4px 0;">Last sync: 15 minutes ago · 247 documents indexed</p>
        <p style="color:#c8a2e8; margin:4px 0;">Libraries: SOPs, Training, Compliance, Scripts</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### How It Works")
    st.markdown("""
    When an agent needs context beyond the analytics data, it queries the SharePoint knowledge base:

    1. **Supervisor Agent** → pulls escalation procedures, break scheduling policies
    2. **Quality Agent** → pulls compliance checklists, coaching frameworks, script templates
    3. **WFM Agent** → pulls scheduling guidelines, overtime policies, flex pool rules
    """)

    st.markdown("---")
    st.markdown("### Indexed Documents")

    docs = pd.DataFrame({
        "Document": [
            "📄 SLA Escalation Procedure v3.2",
            "📄 PCI-DSS Compliance Checklist",
            "📄 Agent Coaching Framework",
            "📄 Break Scheduling Policy",
            "📄 Flex Pool Allocation Guide",
            "📄 De-escalation Training Module",
            "📄 Overtime Authorization Policy",
            "📄 Quality Scorecard Template",
        ],
        "Library": ["SOPs", "Compliance", "Training", "SOPs", "SOPs", "Training", "SOPs", "Training"],
        "Used By": ["Supervisor", "Quality", "Quality", "Supervisor", "WFM", "Quality", "WFM", "Quality"],
        "Last Updated": ["Apr 10", "Apr 8", "Apr 5", "Mar 28", "Apr 1", "Apr 3", "Mar 25", "Apr 7"],
        "Indexed": ["✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅"],
    })
    st.dataframe(docs, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Example: Agent Enriched Response")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #162d1f, #1a3328); border-radius: 12px;
                padding: 16px; border-left: 4px solid #2ecc71; margin: 12px 0;">
        <p style="color:#2ecc71; font-weight:700; margin:0 0 8px 0;">🟢 Supervisor Agent</p>
        <p style="color:#e8e8e8; margin:4px 0;">
            <strong>Query:</strong> "Why did abandonment spike at 2pm?"
        </p>
        <p style="color:#e8e8e8; margin:8px 0;">
            <strong>Analytics:</strong> 2 agents went to break simultaneously. Occupancy hit 96%.
        </p>
        <p style="color:#9b59b6; margin:8px 0; font-style:italic;">
            📎 <strong>From SharePoint:</strong> Per "Break Scheduling Policy v3.2" (SOPs library),
            no more than 1 agent per queue should be on break during peak hours (10am-2pm).
            This policy was violated. Recommend: enable automated break staggering in the
            workforce management system.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Architecture: SharePoint → Bedrock Knowledge Base → Agents")
    st.markdown("""
    ```
    SharePoint Online
         │
         ▼ (sync every 15 min)
    Amazon S3 (knowledge-base/)
         │
         ▼
    Bedrock Knowledge Base
    (vector embeddings)
         │
         ▼
    AgentCore Gateway
    ├── Supervisor Agent → retrieves escalation SOPs
    ├── Quality Agent    → retrieves compliance docs
    └── WFM Agent        → retrieves scheduling policies
    ```
    """)


with tab_handoff:
    st.markdown('<h2 style="color:#e74c3c;">🤝 Live Agent-to-Agent Handoff</h2>', unsafe_allow_html=True)
    st.caption("Watch agents collaborate in real time — Supervisor detects a problem, WFM automatically responds")
    st.markdown("---")

    if st.button("▶️ Run Agent Handoff Demo", type="primary", use_container_width=True):
        # Step 1
        with st.status("🟢 Supervisor Agent analyzing queue health...", expanded=True) as status:
            time.sleep(1.5)
            st.markdown("""
            **Supervisor Agent found:**
            - Billing queue SLA at 68.5% (threshold 80%)
            - Agent-023 occupancy at 98% for 8 consecutive days
            - Agent-031 occupancy at 96% for 8 consecutive days
            """)
            status.update(label="🟢 Supervisor: SLA breach + burnout risk detected", state="complete")

        # Step 2
        with st.status("🚨 Publishing alerts to EventBridge...", expanded=True) as status:
            time.sleep(1)
            st.markdown("""
            **Events published:**
            - `SLA_BREACH` → Billing queue at 68.5%
            - `BURNOUT_RISK` → Agent-023 (score 0.91)
            - `BURNOUT_RISK` → Agent-031 (score 0.88)
            """)
            alert = {"type": "SLA_BREACH", "emoji": "🚨",
                     "message": "Agent handoff demo: Billing queue SLA breach",
                     "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC")}
            st.session_state.alerts.append(alert)
            post_to_slack(alert)
            status.update(label="🚨 3 alerts published → Slack notified", state="complete")

        # Step 3
        with st.status("🔵 WFM Agent responding to burnout alerts...", expanded=True) as status:
            time.sleep(1.5)
            st.markdown("""
            **WFM Agent automatic response:**
            - Checked flex pool availability: 5 of 8 agents available
            - **Recommendation:** Deploy 2 flex pool agents to Billing queue immediately
            - **Schedule change:** Move Agent-023 to low-volume Returns queue for 48 hours
            - **Schedule change:** Reduce Agent-031 shift by 2 hours for next 3 days

            📎 *Per Flex Pool Allocation Guide: "If burnout score exceeds 0.80, remove from current queue for 48 hours"*
            """)
            status.update(label="🔵 WFM: Flex pool deployed + schedules adjusted", state="complete")

        # Step 4
        with st.status("🟠 Quality Agent flagging coaching needs...", expanded=True) as status:
            time.sleep(1)
            st.markdown("""
            **Quality Agent follow-up:**
            - Agent-023's negative sentiment rate rose to 22% during high-occupancy period
            - **Coaching scheduled:** Empathy and active listening module
            - **Monitoring:** 2-week sentiment tracking post-coaching

            📎 *Per Agent Coaching Framework: "Sustained high occupancy correlates with rising negative sentiment"*
            """)
            status.update(label="🟠 Quality: Coaching scheduled for affected agents", state="complete")

        st.success("✅ Full agent handoff complete — 3 agents collaborated automatically in 4 seconds")
        st.balloons()
    
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a2744, #2a3a55); border-radius: 12px;
                    padding: 24px; text-align: center; border: 1px dashed #FF9900;">
            <p style="color:#FF9900; font-size:1.2rem; font-weight:600;">Click the button above to watch the agents collaborate live</p>
            <p style="color:#8899aa; margin-top:8px;">
                Supervisor detects SLA breach + burnout → publishes alerts →
                WFM deploys flex pool + adjusts schedules →
                Quality schedules coaching
            </p>
        </div>
        """, unsafe_allow_html=True)


with tab_roi:
    st.markdown('<h2 style="color:#2ecc71;">💰 ROI Calculator</h2>', unsafe_allow_html=True)
    st.caption("Quantified business impact of the Connect Analytics Platform")
    st.markdown("---")

    st.markdown("### Configure Your Contact Center")
    col1, col2 = st.columns(2)
    with col1:
        num_agents = st.slider("Number of agents", 10, 500, 100)
        avg_salary = st.slider("Avg agent salary ($/year)", 30000, 80000, 45000, step=5000)
        calls_per_day = st.slider("Calls per day", 100, 10000, 2000)
    with col2:
        current_abandon_rate = st.slider("Current abandonment rate (%)", 5, 30, 15)
        current_attrition = st.slider("Annual agent attrition (%)", 10, 50, 25)
        custom_pipeline_cost = st.slider("Current analytics pipeline cost ($/year)", 50000, 300000, 150000, step=10000)

    st.markdown("---")
    st.markdown("### Projected Savings")

    # Calculations
    abandon_reduction = current_abandon_rate * 0.4  # 40% reduction
    revenue_per_call = 12  # avg revenue per resolved call
    saved_calls = calls_per_day * 365 * (abandon_reduction / 100)
    abandon_savings = saved_calls * revenue_per_call

    attrition_reduction = current_attrition * 0.2  # 20% reduction from burnout detection
    cost_per_hire = avg_salary * 0.5  # hiring cost = 50% of salary
    saved_hires = num_agents * (attrition_reduction / 100)
    attrition_savings = saved_hires * cost_per_hire

    pipeline_savings = custom_pipeline_cost * 0.85  # replaces 85% of custom pipeline

    platform_cost = 34 * 12  # ~$34/mo * 12

    total_savings = abandon_savings + attrition_savings + pipeline_savings - platform_cost

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Abandonment Savings", f"${abandon_savings:,.0f}/yr",
              f"{abandon_reduction:.1f}% reduction")
    s2.metric("Attrition Savings", f"${attrition_savings:,.0f}/yr",
              f"{saved_hires:.0f} fewer hires")
    s3.metric("Pipeline Savings", f"${pipeline_savings:,.0f}/yr",
              "Replaces custom analytics")
    s4.metric("Platform Cost", f"${platform_cost:,.0f}/yr",
              "~$34/month on AWS")

    st.markdown("---")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0d2818, #1a3d28); border: 2px solid #2ecc71;
                border-radius: 16px; padding: 32px; text-align: center; margin: 16px 0;">
        <p style="color:#2ecc71; font-size:0.9rem; margin:0;">TOTAL ANNUAL ROI</p>
        <p style="color:#2ecc71; font-size:3.5rem; font-weight:800; margin:8px 0;">${total_savings:,.0f}</p>
        <p style="color:#8fbc8f; font-size:1rem; margin:0;">{total_savings/platform_cost:.0f}x return on platform investment</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ROI Breakdown")
    import pandas as pd
    roi_data = pd.DataFrame({
        "Category": ["Reduced Abandonment", "Lower Attrition", "Pipeline Replacement", "Platform Cost"],
        "Annual Impact": [f"+${abandon_savings:,.0f}", f"+${attrition_savings:,.0f}",
                         f"+${pipeline_savings:,.0f}", f"-${platform_cost:,.0f}"],
        "How": [
            f"40% fewer abandoned calls → {saved_calls:,.0f} recovered calls/yr",
            f"Burnout detection prevents {saved_hires:.0f} resignations/yr",
            "Replaces custom Kinesis→Lambda→S3→QuickSight pipelines",
            "AgentCore + Athena + Lambda + S3 + SNS",
        ],
    })
    st.dataframe(roi_data, hide_index=True, use_container_width=True)


with tab_before:
    st.markdown('<h2 style="color:#e74c3c;">⚡ Before vs After</h2>', unsafe_allow_html=True)
    st.caption("What changes when you deploy the Connect Analytics Platform")
    st.markdown("---")

    col_before, col_after = st.columns(2)

    with col_before:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2d1a1a, #3d2020); border: 2px solid #e74c3c;
                    border-radius: 12px; padding: 20px;">
            <h3 style="color:#e74c3c; margin:0 0 16px 0;">❌ Before</h3>
            <p style="color:#e8a0a0;">🕐 <strong>20 minutes</strong> to check queue health across 5 dashboards</p>
            <p style="color:#e8a0a0;">📊 Custom Kinesis → Lambda → S3 → QuickSight pipeline (<strong>$150K/yr</strong>)</p>
            <p style="color:#e8a0a0;">🔇 No automated alerts — supervisors discover SLA breaches <strong>15+ min late</strong></p>
            <p style="color:#e8a0a0;">📋 Manual QA review — analysts listen to <strong>2% of calls</strong></p>
            <p style="color:#e8a0a0;">🔥 Burnout detected <strong>after</strong> agents quit — <strong>25% annual attrition</strong></p>
            <p style="color:#e8a0a0;">📅 Staffing forecasts in <strong>spreadsheets</strong> — updated weekly</p>
            <p style="color:#e8a0a0;">🏗️ <strong>3 months</strong> to build, <strong>2 engineers</strong> to maintain</p>
        </div>
        """, unsafe_allow_html=True)

    with col_after:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0d2818, #1a3d28); border: 2px solid #2ecc71;
                    border-radius: 12px; padding: 20px;">
            <h3 style="color:#2ecc71; margin:0 0 16px 0;">✅ After</h3>
            <p style="color:#a0e8a0;">🕐 <strong>2 seconds</strong> — ask in plain English, get instant answer</p>
            <p style="color:#a0e8a0;">📊 Serverless on AgentCore — <strong>$34/month</strong> (99.97% cost reduction)</p>
            <p style="color:#a0e8a0;">🔔 Real-time Slack alerts — SLA breaches detected in <strong>&lt;60 seconds</strong></p>
            <p style="color:#a0e8a0;">📋 AI analyzes <strong>100% of calls</strong> — auto-coaching recommendations</p>
            <p style="color:#a0e8a0;">🔥 Burnout detected <strong>8 days early</strong> — proactive schedule adjustment</p>
            <p style="color:#a0e8a0;">📅 AI forecasts updated <strong>hourly</strong> with confidence intervals</p>
            <p style="color:#a0e8a0;">🏗️ <strong>8 minutes</strong> to deploy — <code>cdk deploy</code>, zero maintenance</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Impact Metrics")
    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Time to Insight", "2 sec", "-99.8% vs 20 min")
    i2.metric("Cost", "$34/mo", "-99.97% vs $150K/yr")
    i3.metric("Call Coverage", "100%", "+98% vs 2% manual")
    i4.metric("Deploy Time", "8 min", "vs 3 months")


with tab_deploy:
    st.markdown('<h2 style="color:#FF9900;">🚀 Deploy to Your AWS Account</h2>', unsafe_allow_html=True)
    st.caption("No CloudFront, no Terraform — just CDK. Anyone can deploy in under 10 minutes.")
    st.markdown("---")

    # Prerequisites
    st.markdown("### Prerequisites (one-time, 10 min)")
    st.markdown("""
| Requirement | Version | Check |
|-------------|---------|-------|
| AWS CLI | v2+ | `aws --version` |
| AWS CDK | v2.150+ | `cdk --version` |
| Python | 3.12+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| Docker | Running | `docker info` |
    """)

    st.warning("**Bedrock model access required.** In AWS Console → Bedrock → Model access, enable: `Claude Sonnet 4`, `Nova Lite v2`, `Titan Embed v2`")

    st.markdown("---")

    # Step 1
    st.markdown("### Step 1: Clone & Install (2 min)")
    st.code("""git clone https://github.com/vandy1311/connect-analytics-platform.git
cd connect-analytics-platform
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt""", language="bash")

    # Step 2
    st.markdown("### Step 2: Generate Synthetic Data (30 sec)")
    st.code("python scripts/generate_synthetic_data.py", language="bash")
    st.caption("Creates 70K records: 10K CTRs + 50K agent events + 10K Contact Lens analyses")

    # Step 3
    st.markdown("### Step 3: Bootstrap CDK (first time only, 1 min)")
    st.code("""export CDK_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_REGION=us-east-1
cdk bootstrap aws://$CDK_ACCOUNT/$CDK_REGION""", language="bash")

    # Step 4
    st.markdown("### Step 4: Deploy (~8 min)")
    st.code("""cdk deploy --all \
  -c account=$CDK_ACCOUNT \
  -c region=$CDK_REGION""", language="bash")

    st.success("""CDK automatically:
1. Builds Docker images → pushes to ECR
2. Creates S3 bucket + Glue catalog (3 tables) + Athena workgroup
3. Stores auth tokens in Secrets Manager
4. Deploys AgentCore Gateway + 3 AI agents (9 tools)
5. Creates Knowledge Base with SOPs and compliance docs
6. Wires EventBridge → SNS (5 topics) → Slack formatter Lambda
7. Outputs agent endpoints + gateway ID""")

    # Step 5
    st.markdown("### Step 5: Upload Data to S3")
    st.code("""BUCKET=$(aws cloudformation describe-stacks \
  --stack-name ConnectAnalytics-Data \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" \
  --output text)

aws s3 sync output/ctr/ s3://$BUCKET/ctr/
aws s3 sync output/agent-events/ s3://$BUCKET/agent-events/
aws s3 sync output/contact-lens/ s3://$BUCKET/contact-lens/""", language="bash")

    # Step 6
    st.markdown("### Step 6: Configure Slack (optional)")
    st.code("""aws secretsmanager put-secret-value \
  --secret-id connect-analytics/slack-webhook \
  --secret-string "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" """, language="bash")

    # Step 7
    st.markdown("### Step 7: Done ✅")
    st.markdown("Agents are live. Launch the demo UI:")
    st.code("cd demo_ui && streamlit run app.py", language="bash")

    st.markdown("---")

    # Point to your own data
    st.markdown("### 🔗 Use Your Own Connect Data")
    st.info("""To point to your existing S3 bucket with Connect data:
```bash
cdk deploy --all -c data_lake_bucket=your-existing-bucket-name
```
Your data must follow the Hive-partitioned layout:
- `ctr/year=YYYY/month=MM/day=DD/data.parquet`
- `agent-events/year=YYYY/month=MM/day=DD/data.parquet`
- `contact-lens/year=YYYY/month=MM/day=DD/data.json`""")

    st.markdown("---")

    # What gets deployed
    st.markdown("### What Gets Deployed (5 CDK Stacks)")
    st.markdown("""
| Stack | Resources | Cost |
|-------|-----------|------|
| `ConnectAnalytics-Auth` | Secrets Manager (auth tokens) | <$1/mo |
| `ConnectAnalytics-Data` | S3 + Glue (3 tables) + Athena workgroup | ~$12/mo |
| `ConnectAnalytics-KB` | S3 (docs) + Bedrock Knowledge Base | ~$2/mo |
| `ConnectAnalytics-Agents` | Tool Lambda (Docker) + AgentCore Gateway + 3 agents | ~$15/mo |
| `ConnectAnalytics-Alerts` | Slack Lambda + 5 SNS topics + 5 EventBridge rules | ~$1/mo |
| **Total** | | **~$34/mo** |
    """)

    st.markdown("---")

    # Cleanup
    st.markdown("### Cleanup")
    st.code("cdk destroy --all", language="bash")
    st.caption("Removes all resources. S3 buckets are auto-deleted (RemovalPolicy.DESTROY).")

    st.markdown("---")

    st.markdown("### Training Enablement for CSMs")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2d1a4e, #1a1a3e); border: 1px solid #9b59b6;
                border-radius: 12px; padding: 20px;">
        <h4 style="color:#9b59b6; margin:0 0 12px 0;">🎓 CSM Deployment Playbook</h4>
        <p style="color:#c8a2e8;"><strong>Prerequisites:</strong> AWS account with Bedrock enabled, Docker Desktop, CDK CLI</p>
        <p style="color:#c8a2e8;"><strong>Time to deploy:</strong> 10 minutes (including config)</p>
        <p style="color:#c8a2e8;"><strong>Skills needed:</strong> Copy-paste 1 command. That's it.</p>
        <p style="color:#c8a2e8;"><strong>Customer handoff:</strong> Share the Streamlit URL + Slack channel</p>
        <p style="color:#c8a2e8;"><strong>Customization:</strong> SLA thresholds, alert channels, and coaching thresholds are all env vars — no code changes</p>
        <p style="color:#c8a2e8; margin-top:12px;"><strong>🎯 Goal:</strong> Every CSM on a Connect engagement can deploy this as a value-add in their first week.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Customer story framing
    st.markdown("### Customer Story")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a2744, #0d1f3c); border: 1px solid #3498db;
                border-radius: 12px; padding: 24px;">
        <p style="color:#3498db; font-size:1.1rem; font-weight:600; font-style:italic;">
            "We were spending $150K/year on a custom analytics pipeline — Kinesis, Lambda, S3, QuickSight —
            and our supervisors still couldn't get real-time answers. They'd check 5 different dashboards
            and by the time they found the SLA breach, it had been going on for 15 minutes."
        </p>
        <p style="color:#8899aa; margin-top:12px;">— Contact Center Director, 200-agent US retail operation</p>
        <p style="color:#e8e8e8; margin-top:16px;">
            <strong>After deploying Connect Analytics Platform:</strong><br>
            ✅ Real-time answers in 2 seconds via natural language<br>
            ✅ SLA breaches detected in &lt;60 seconds with automatic Slack alerts<br>
            ✅ Burnout detected 8 days before agents quit<br>
            ✅ 100% of calls analyzed for sentiment and compliance<br>
            ✅ Total cost: $34/month (down from $150K/year)
        </p>
    </div>
    """, unsafe_allow_html=True)


with tab_arch:
    st.markdown("### 🏗️ System Architecture")

    import streamlit.components.v1 as arch_components
    arch_flow = """<!DOCTYPE html>
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
  <line x1="310" y1="38" x2="165" y2="80"/><line x1="350" y1="38" x2="305" y2="80"/>
  <line x1="420" y1="38" x2="445" y2="80"/><line x1="460" y1="38" x2="585" y2="80"/>
  <line x1="165" y1="115" x2="340" y2="160"/><line x1="305" y1="115" x2="360" y2="160"/>
  <line x1="445" y1="115" x2="400" y2="160"/><line x1="585" y1="115" x2="420" y2="160"/>
  <line x1="310" y1="198" x2="155" y2="240"/><line x1="380" y1="198" x2="380" y2="240"/>
  <line x1="450" y1="198" x2="605" y2="240"/>
  <line x1="155" y1="278" x2="340" y2="330"/><line x1="380" y1="278" x2="380" y2="330"/>
  <line x1="605" y1="278" x2="420" y2="330"/>
  <line x1="310" y1="368" x2="165" y2="410"/><line x1="380" y1="368" x2="380" y2="410"/>
  <line x1="450" y1="368" x2="595" y2="410"/>
  <line x1="230" y1="430" x2="315" y2="430"/><line x1="445" y1="430" x2="530" y2="430"/>
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
<div class="node n-lambda"><div class="label">⚡ Tool Handler Lambda</div><div class="sub">Docker · 9 tools</div></div>
<div class="node n-eb"><div class="label">📡 EventBridge</div><div class="sub">5 rules</div></div>
<div class="node n-sns"><div class="label">📬 SNS</div><div class="sub">5 topics</div></div>
<div class="node n-slack"><div class="label">💬 Slack</div><div class="sub">3 channels</div></div>
</div></body></html>"""
    arch_components.html(arch_flow, height=500, scrolling=False)

    st.markdown("---")

    # Tool registry
    st.markdown("### 9 Tools — One Lambda")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("**🟢 Supervisor (4)**")
        st.markdown("""
| Tool | Data Source |
|------|------------|
| `get_queue_health` | CTR |
| `get_abandonment_analysis` | CTR |
| `get_agent_utilization` | Agent Events |
| `trigger_sla_alert` | EventBridge |
        """)
    with t2:
        st.markdown("**🟠 Quality (3)**")
        st.markdown("""
| Tool | Data Source |
|------|------------|
| `get_sentiment_trends` | Contact Lens |
| `get_coaching_recommendations` | Contact Lens |
| `get_compliance_violations` | Contact Lens |
        """)
    with t3:
        st.markdown("**🔵 WFM (2)**")
        st.markdown("""
| Tool | Data Source |
|------|------------|
| `get_staffing_forecast` | CTR |
| `get_burnout_signals` | Agent Events |
        """)

    st.markdown("---")

    st.markdown("### Agent Architectures")
    st.caption("Click each agent to see its data flow, tools, and alert types")

    with st.expander("🟢 Supervisor Agent — Claude Sonnet 4", expanded=False):
        st.markdown("""
**Data Flow:**
        """)
        import streamlit.components.v1 as _fc
        _fc.html("""<!DOCTYPE html><html><head><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0f172a;font-family:Inter,system-ui,sans-serif}
.mf{position:relative;width:720px;margin:0 auto;height:65px}
.mn{position:absolute;border-radius:8px;padding:7px 10px;text-align:center;z-index:2;width:108px;top:12px}
.mn .t{font-size:10px;font-weight:700;color:#f1f5f9}.mn .s{font-size:8px;color:#94a3b8}
.bl{background:#172554;border:1.5px solid #3b82f6}.bl .t{color:#93c5fd}
.gr{background:#052e16;border:1.5px solid #22c55e}.gr .t{color:#86efac}
.gy{background:#1e293b;border:1px solid #334155}
.pr{background:#2e1065;border:1.5px solid #a78bfa}.pr .t{color:#c4b5fd}
.or{background:#431407;border:1.5px solid #f97316}.or .t{color:#fdba74}
svg{position:absolute;top:0;left:0;width:100%;height:100%;z-index:1}
line{stroke:#475569;stroke-width:1.5;marker-end:url(#a)}
</style></head><body><div class="mf">
<svg viewBox="0 0 720 65"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="#475569"/></marker></defs>
<line x1="108" y1="32" x2="120" y2="32"/><line x1="228" y1="32" x2="240" y2="32"/>
<line x1="348" y1="32" x2="360" y2="32"/><line x1="468" y1="32" x2="480" y2="32"/>
<line x1="588" y1="32" x2="600" y2="32"/>
</svg>
<div class="mn bl" style="left:0"><div class="t">☁️ Connect</div><div class="s">CTR + Events</div></div>
<div class="mn gy" style="left:120px"><div class="t">📦 S3</div><div class="s">Data Lake</div></div>
<div class="mn gy" style="left:240px"><div class="t">🔍 Athena</div><div class="s">SQL Query</div></div>
<div class="mn bl" style="left:360px"><div class="t">🌐 Gateway</div><div class="s">AgentCore</div></div>
<div class="mn gr" style="left:480px"><div class="t">🟢 Supervisor</div><div class="s">Claude 4</div></div>
<div class="mn pr" style="left:600px"><div class="t">⚡ Lambda</div><div class="s">4 tools</div></div>
</div></body></html>""", height=70, scrolling=False)
        st.markdown("""

| Tool | What it does | Data Source | Output |
|------|-------------|-------------|--------|
| `get_queue_health` | Queue size, wait times, SLA % | `connect_ctr` | Table + metrics |
| `get_abandonment_analysis` | Abandon rate, peak hours, root cause | `connect_ctr` | Analysis + chart |
| `get_agent_utilization` | Per-agent occupancy, status, handle time | `connect_agent_events` | Table + burnout flags |
| `trigger_sla_alert` | Publishes SLA breach event | EventBridge | Slack alert |

**Alerts:** `SLA_BREACH` → `#connect-sla-alerts` · `ABANDONMENT_SPIKE` → `#connect-sla-alerts`
        """)

    with st.expander("🟠 Quality Agent — Claude Sonnet 4", expanded=False):
        st.markdown("""
**Data Flow:**
        """)
        import streamlit.components.v1 as _fc
        _fc.html("""<!DOCTYPE html><html><head><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0f172a;font-family:Inter,system-ui,sans-serif}
.mf{position:relative;width:720px;margin:0 auto;height:65px}
.mn{position:absolute;border-radius:8px;padding:7px 10px;text-align:center;z-index:2;width:108px;top:12px}
.mn .t{font-size:10px;font-weight:700;color:#f1f5f9}.mn .s{font-size:8px;color:#94a3b8}
.bl{background:#172554;border:1.5px solid #3b82f6}.bl .t{color:#93c5fd}
.or{background:#431407;border:1.5px solid #f97316}.or .t{color:#fdba74}
.gy{background:#1e293b;border:1px solid #334155}
.pr{background:#2e1065;border:1.5px solid #a78bfa}.pr .t{color:#c4b5fd}
svg{position:absolute;top:0;left:0;width:100%;height:100%;z-index:1}
line{stroke:#475569;stroke-width:1.5;marker-end:url(#a)}
</style></head><body><div class="mf">
<svg viewBox="0 0 720 65"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="#475569"/></marker></defs>
<line x1="108" y1="32" x2="120" y2="32"/><line x1="228" y1="32" x2="240" y2="32"/>
<line x1="348" y1="32" x2="360" y2="32"/><line x1="468" y1="32" x2="480" y2="32"/>
<line x1="588" y1="32" x2="600" y2="32"/>
</svg>
<div class="mn bl" style="left:0"><div class="t">☁️ Connect</div><div class="s">Contact Lens</div></div>
<div class="mn gy" style="left:120px"><div class="t">📦 S3</div><div class="s">Data Lake</div></div>
<div class="mn gy" style="left:240px"><div class="t">🔍 Athena</div><div class="s">SQL Query</div></div>
<div class="mn bl" style="left:360px"><div class="t">🌐 Gateway</div><div class="s">AgentCore</div></div>
<div class="mn or" style="left:480px"><div class="t">🟠 Quality</div><div class="s">Claude 4</div></div>
<div class="mn pr" style="left:600px"><div class="t">⚡ Lambda</div><div class="s">3 tools</div></div>
</div></body></html>""", height=70, scrolling=False)
        st.markdown("""

| Tool | What it does | Data Source | Output |
|------|-------------|-------------|--------|
| `get_sentiment_trends` | Positive/negative/neutral % over time | `connect_contact_lens` | Trend chart |
| `get_coaching_recommendations` | Agents with high negative sentiment | `connect_contact_lens` | Coaching plan + excerpts |
| `get_compliance_violations` | PCI, disclosure, script violations | `connect_contact_lens` | Violation list + severity |

**Alerts:** `COMPLIANCE_VIOLATION` → `#connect-compliance`
        """)

    with st.expander("🔵 WFM Agent — Nova Lite v2 (50× cheaper)", expanded=False):
        st.markdown("""
**Data Flow:**
        """)
        import streamlit.components.v1 as _fc
        _fc.html("""<!DOCTYPE html><html><head><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0f172a;font-family:Inter,system-ui,sans-serif}
.mf{position:relative;width:720px;margin:0 auto;height:65px}
.mn{position:absolute;border-radius:8px;padding:7px 10px;text-align:center;z-index:2;width:108px;top:12px}
.mn .t{font-size:10px;font-weight:700;color:#f1f5f9}.mn .s{font-size:8px;color:#94a3b8}
.bl{background:#172554;border:1.5px solid #3b82f6}.bl .t{color:#93c5fd}
.gy{background:#1e293b;border:1px solid #334155}
.pr{background:#2e1065;border:1.5px solid #a78bfa}.pr .t{color:#c4b5fd}
svg{position:absolute;top:0;left:0;width:100%;height:100%;z-index:1}
line{stroke:#475569;stroke-width:1.5;marker-end:url(#a)}
</style></head><body><div class="mf">
<svg viewBox="0 0 720 65"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="#475569"/></marker></defs>
<line x1="108" y1="32" x2="120" y2="32"/><line x1="228" y1="32" x2="240" y2="32"/>
<line x1="348" y1="32" x2="360" y2="32"/><line x1="468" y1="32" x2="480" y2="32"/>
<line x1="588" y1="32" x2="600" y2="32"/>
</svg>
<div class="mn bl" style="left:0"><div class="t">☁️ Connect</div><div class="s">CTR + Events</div></div>
<div class="mn gy" style="left:120px"><div class="t">📦 S3</div><div class="s">Data Lake</div></div>
<div class="mn gy" style="left:240px"><div class="t">🔍 Athena</div><div class="s">SQL Query</div></div>
<div class="mn bl" style="left:360px"><div class="t">🌐 Gateway</div><div class="s">AgentCore</div></div>
<div class="mn bl" style="left:480px"><div class="t">🔵 WFM</div><div class="s">Nova Lite</div></div>
<div class="mn pr" style="left:600px"><div class="t">⚡ Lambda</div><div class="s">2 tools</div></div>
</div></body></html>""", height=70, scrolling=False)
        st.markdown("""

| Tool | What it does | Data Source | Output |
|------|-------------|-------------|--------|
| `get_staffing_forecast` | Hourly volume prediction + recommended staff | `connect_ctr` | Forecast table + chart |
| `get_burnout_signals` | Occupancy-based burnout risk scores | `connect_agent_events` | Risk list + alerts |

**Alerts:** `BURNOUT_RISK` → `#connect-wfm-alerts` · `OCCUPANCY_CRITICAL` → `#connect-sla-alerts`
        """)

    st.markdown("---")
    st.markdown("### Tech Stack")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agent Runtime", "AgentCore")
    c2.metric("Data Query", "Athena")
    c3.metric("Alerts", "EventBridge")
    c4.metric("Monthly Cost", "~$28")
