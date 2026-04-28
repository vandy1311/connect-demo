"""Live query engine — DuckDB over local Parquet files.

Replaces canned responses with real SQL queries against synthetic data.
Uses the same SQL patterns as the Lambda tools but via DuckDB instead of Athena.
"""

import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb

# Real-time simulation seed — changes every 30 seconds for "live" feel
_RT_SEED = int(time.time() // 30)
random.seed(_RT_SEED)

def _rt_jitter(base: float, pct: float = 0.15) -> float:
    """Add realistic jitter to a value (±pct%)."""
    return round(base * (1 + random.uniform(-pct, pct)), 2)

def _rt_int_jitter(base: int, pct: float = 0.2) -> int:
    """Add jitter to an integer value."""
    return max(0, int(base * (1 + random.uniform(-pct, pct))))

def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

# Auto-detect data directory
_DATA_DIR = os.environ.get("DATA_DIR", "")
if not _DATA_DIR:
    # Try common locations
    for candidate in [
        Path(__file__).parent.parent.parent / "output",  # repo root/output
        Path("/Users/vtewanie/AIDLC/output"),
        Path("/mount/src/connect-demo/output"),
    ]:
        if candidate.exists():
            _DATA_DIR = str(candidate)
            break

CTR_PATH = f"{_DATA_DIR}/ctr/**/*.parquet"
AGENT_EVENTS_PATH = f"{_DATA_DIR}/agent-events/**/*.parquet"
CONTACT_LENS_PATH = f"{_DATA_DIR}/contact-lens/**/*.json"


def _query(sql: str) -> list[dict]:
    """Execute SQL via DuckDB and return list of dicts."""
    con = duckdb.connect()
    try:
        result = con.execute(sql)
        columns = [desc[0] for desc in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def _safe_param(value: str | None, allowed: list[str] | None = None) -> str | None:
    """Sanitize a parameter to prevent SQL injection."""
    if value is None:
        return None
    value = value.strip().replace("'", "").replace(";", "").replace("--", "")
    if allowed and value not in allowed:
        return None
    return value


VALID_QUEUES = ["Billing", "Support", "Sales", "Returns", "VIP"]


def get_queue_health(queue_name: str | None = None, time_range: str = "24h") -> dict:
    """Live query: queue health metrics from CTR data."""
    where = "WHERE 1=1"
    q = _safe_param(queue_name, VALID_QUEUES)
    if q:
        where += f" AND queue_name = '{q}'"

    sql = f"""
    SELECT
        queue_name,
        COUNT(*) AS queue_size,
        MAX(queue_duration_seconds) AS longest_wait_seconds,
        ROUND(100.0 * SUM(CASE WHEN service_level_met = true THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0), 2) AS service_level_pct,
        ROUND(AVG(handle_time_seconds), 2) AS avg_handle_time
    FROM read_parquet('{CTR_PATH}', hive_partitioning=true)
    {where}
    GROUP BY queue_name
    ORDER BY service_level_pct ASC
    """
    rows = _query(sql)

    # Add real-time "current" stats on top of historical
    lines = [f"**Queue Health — Live at {_now_str()}**\n"]
    lines.append("| Queue | Contacts | Longest Wait | SLA % | Avg Handle Time |")
    lines.append("|-------|----------|-------------|-------|-----------------|")
    breach = False
    for r in rows:
        sla = r["service_level_pct"]
        flag = " ⚠️" if sla < 80 else ""
        if sla < 80:
            breach = True
        wait_min = int(r["longest_wait_seconds"]) // 60
        wait_sec = int(r["longest_wait_seconds"]) % 60
        aht_min = int(r["avg_handle_time"]) // 60
        aht_sec = int(r["avg_handle_time"]) % 60
        lines.append(
            f"| {r['queue_name']} | {r['queue_size']} | "
            f"{wait_min}m {wait_sec}s | **{sla}%**{flag} | "
            f"{aht_min}m {aht_sec}s |"
        )

    result = {"text": "\n".join(lines), "metrics": []}
    if rows:
        worst = rows[0]
        result["metrics"] = [
            {"label": f"{worst['queue_name']} SLA", "value": f"{worst['service_level_pct']}%", "delta": ""},
            {"label": "Queues", "value": str(len(rows)), "delta": ""},
            {"label": "Total Contacts", "value": str(sum(r["queue_size"] for r in rows)), "delta": ""},
        ]
    if breach:
        result["alert"] = {
            "type": "SLA_BREACH",
            "emoji": "🚨",
            "message": f"SLA breach detected — {rows[0]['queue_name']} at {rows[0]['service_level_pct']}%",
        }
    return result


def get_abandonment_analysis(queue_name: str | None = None) -> dict:
    """Live query: abandonment patterns from CTR data with real-time jitter."""
    where = "WHERE outcome = 'ABANDONED'"
    q = _safe_param(queue_name, VALID_QUEUES)
    if q:
        where += f" AND queue_name = '{q}'"

    sql = f"""
    SELECT
        COUNT(*) as total_abandoned,
        (SELECT COUNT(*) FROM read_parquet('{CTR_PATH}', hive_partitioning=true)) as total_contacts,
        ROUND(AVG(queue_duration_seconds), 2) as avg_wait_before_abandon,
        EXTRACT(HOUR FROM initiation_timestamp) as peak_hour,
        COUNT(*) as hour_count
    FROM read_parquet('{CTR_PATH}', hive_partitioning=true)
    {where}
    GROUP BY EXTRACT(HOUR FROM initiation_timestamp)
    ORDER BY hour_count DESC
    LIMIT 1
    """
    rows = _query(sql)

    # Also get overall rate
    rate_sql = f"""
    SELECT
        COUNT(*) FILTER (WHERE outcome = 'ABANDONED') as abandoned,
        COUNT(*) as total,
        ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'ABANDONED') / COUNT(*), 2) as rate
    FROM read_parquet('{CTR_PATH}', hive_partitioning=true)
    """
    rate = _query(rate_sql)[0]

    # Apply real-time jitter
    rt_rate = _rt_jitter(float(rate['rate']), 0.1)
    rt_abandoned = _rt_int_jitter(int(rate['abandoned']), 0.1)
    text = f"""**Abandonment Analysis — Live at {_now_str()}**

- **Abandonment rate:** {rt_rate}% (~{rt_abandoned} of {rate['total']} contacts)
"""
    if rows:
        r = rows[0]
        wait_min = int(r["avg_wait_before_abandon"]) // 60
        wait_sec = int(r["avg_wait_before_abandon"]) % 60
        text += f"- **Peak hour:** {int(r['peak_hour'])}:00 ({r['hour_count']} abandons)\n"
        text += f"- **Avg wait before abandon:** {wait_min}m {wait_sec}s\n"

    return {
        "text": text,
        "metrics": [
            {"label": "Abandon Rate", "value": f"{rate['rate']}%", "delta": ""},
            {"label": "Total Abandoned", "value": str(rate["abandoned"]), "delta": ""},
            {"label": "Total Contacts", "value": str(rate["total"]), "delta": ""},
        ],
    }


def get_agent_utilization(agent_id: str | None = None) -> dict:
    """Live query: agent utilization from agent events data."""
    sql = f"""
    SELECT
        agent_id,
        ROUND(AVG(occupancy_rate), 4) as avg_occupancy,
        MODE(agent_status) as most_common_status,
        ROUND(AVG(handle_time_seconds), 2) as avg_handle_time,
        COUNT(*) as event_count
    FROM read_parquet('{AGENT_EVENTS_PATH}', hive_partitioning=true)
    GROUP BY agent_id
    ORDER BY avg_occupancy DESC
    LIMIT 10
    """
    rows = _query(sql)

    lines = ["**Agent Utilization — Live at {_now_str()}**\n"]
    lines.append("| Agent | Occupancy | Status | Avg Handle Time | Events |")
    lines.append("|-------|-----------|--------|-----------------|--------|")
    for r in rows:
        occ = round(r["avg_occupancy"] * 100, 1)
        icon = "🔴" if occ >= 90 else "🟡" if occ >= 80 else "🟢"
        aht_min = int(r["avg_handle_time"]) // 60
        aht_sec = int(r["avg_handle_time"]) % 60
        lines.append(
            f"| {r['agent_id']} | {occ}% {icon} | {r['most_common_status']} | "
            f"{aht_min}m {aht_sec}s | {r['event_count']} |"
        )

    burnout_agents = [r for r in rows if r["avg_occupancy"] >= 0.90]
    result = {"text": "\n".join(lines)}
    if burnout_agents:
        result["alert"] = {
            "type": "BURNOUT_RISK",
            "emoji": "🔥",
            "message": f"{len(burnout_agents)} agents above 90% occupancy",
        }
    return result


def get_sentiment_trends() -> dict:
    """Live query: sentiment from Contact Lens data."""
    sql = f"""
    SELECT
        overall_sentiment,
        COUNT(*) as cnt,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct
    FROM read_json_auto('{CONTACT_LENS_PATH}')
    GROUP BY overall_sentiment
    ORDER BY cnt DESC
    """
    rows = _query(sql)

    lines = [f"**Sentiment Trends — Live at {_now_str()}**\n"]
    lines.append("| Sentiment | Count | % |")
    lines.append("|-----------|-------|---|")
    for r in rows:
        lines.append(f"| {r['overall_sentiment']} | {r['cnt']} | {r['pct']}% |")

    return {"text": "\n".join(lines), "chart": "sentiment"}


def get_coaching_recommendations() -> dict:
    """Live query: agents with high negative sentiment."""
    sql = f"""
    SELECT
        agent_id,
        COUNT(*) as total_calls,
        COUNT(*) FILTER (WHERE overall_sentiment = 'NEGATIVE') as negative_calls,
        ROUND(100.0 * COUNT(*) FILTER (WHERE overall_sentiment = 'NEGATIVE') / COUNT(*), 1) as negative_pct
    FROM read_json_auto('{CONTACT_LENS_PATH}')
    GROUP BY agent_id
    HAVING COUNT(*) >= 10
    ORDER BY negative_pct DESC
    LIMIT 5
    """
    rows = _query(sql)

    lines = [f"**Coaching Recommendations — Live at {_now_str()}**\n"]
    for r in rows:
        icon = "🔴" if r["negative_pct"] >= 25 else "🟡" if r["negative_pct"] >= 20 else "🟢"
        lines.append(f"{icon} **{r['agent_id']}** — {r['negative_pct']}% negative ({r['negative_calls']}/{r['total_calls']} calls)")
        if r["negative_pct"] >= 25:
            lines.append("→ Recommend: De-escalation coaching + active listening module\n")
        elif r["negative_pct"] >= 20:
            lines.append("→ Recommend: Empathy refresher training\n")
        else:
            lines.append("→ Monitor for next review cycle\n")

    return {"text": "\n".join(lines)}


def get_burnout_signals(threshold: float = 0.85) -> dict:
    """Live query: burnout risk from agent events."""
    sql = f"""
    SELECT
        agent_id,
        ROUND(AVG(occupancy_rate), 4) as avg_occupancy,
        ROUND(AVG(handle_time_seconds), 2) as avg_handle_time,
        COUNT(*) as shifts
    FROM read_parquet('{AGENT_EVENTS_PATH}', hive_partitioning=true)
    GROUP BY agent_id
    HAVING AVG(occupancy_rate) >= {threshold}
    ORDER BY avg_occupancy DESC
    """
    rows = _query(sql)

    lines = [f"**Burnout Risk Assessment — Live at {_now_str()}**\n"]
    if not rows:
        lines.append(f"No agents above {threshold} occupancy threshold.")
    for r in rows:
        occ = round(r["avg_occupancy"] * 100, 1)
        score = round(r["avg_occupancy"], 2)
        icon = "🔴 CRITICAL" if score >= 0.92 else "🟡 WARNING"
        lines.append(f"{icon} **{r['agent_id']}** — Score: **{score}**, Occupancy: {occ}%")
        lines.append(f"→ {r['shifts']} shifts tracked, Avg handle time: {int(r['avg_handle_time'])}s\n")

    result = {"text": "\n".join(lines)}
    critical = [r for r in rows if r["avg_occupancy"] >= 0.92]
    if critical:
        result["alert"] = {
            "type": "BURNOUT_RISK",
            "emoji": "🔥",
            "message": f"{len(critical)} agents at critical burnout risk",
        }
    return result


def get_staffing_forecast() -> dict:
    """Live query: hourly volume patterns for forecasting."""
    sql = f"""
    SELECT
        EXTRACT(HOUR FROM initiation_timestamp) as hour,
        COUNT(*) as volume,
        ROUND(AVG(handle_time_seconds), 0) as avg_handle_time
    FROM read_parquet('{CTR_PATH}', hive_partitioning=true)
    GROUP BY EXTRACT(HOUR FROM initiation_timestamp)
    ORDER BY hour
    """
    rows = _query(sql)

    lines = [f"**Staffing Forecast — Live at {_now_str()}**\n"]
    lines.append("| Hour | Volume | Avg Handle Time | Recommended Staff |")
    lines.append("|------|--------|-----------------|-------------------|")
    for r in rows:
        vol = r["volume"]
        staff = max(1, vol // 15)  # ~15 contacts per agent per hour
        lines.append(f"| {int(r['hour'])}:00 | {vol} | {int(r['avg_handle_time'])}s | {staff} |")

    return {"text": "\n".join(lines), "chart": "forecast"}


def live_agent_response(agent: str, query: str) -> dict:
    """Route a query to the appropriate live data function."""
    q = query.lower()

    if agent == "Supervisor":
        if "queue" in q or "health" in q or "sla" in q:
            return get_queue_health()
        if "abandon" in q or "spike" in q:
            return get_abandonment_analysis()
        if "utilization" in q or "who" in q or "available" in q or "agent" in q:
            return get_agent_utilization()
        return get_queue_health()  # default

    if agent == "Quality":
        if "sentiment" in q or "trend" in q:
            return get_sentiment_trends()
        if "coaching" in q or "recommend" in q or "worst" in q:
            return get_coaching_recommendations()
        if "compliance" in q or "violation" in q:
            return get_sentiment_trends()  # fallback
        return get_sentiment_trends()  # default

    if agent == "WFM":
        if "burnout" in q or "risk" in q:
            return get_burnout_signals()
        if "forecast" in q or "staffing" in q or "next" in q:
            return get_staffing_forecast()
        return get_staffing_forecast()  # default

    return {"text": "I'm not sure how to help with that. Try asking about queue health, sentiment, or staffing."}
