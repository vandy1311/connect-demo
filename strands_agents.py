"""Strands Agents SDK integration — real AI agents with tool use.

Each agent uses Bedrock models and calls tools that query DuckDB over Parquet.
Falls back gracefully if Strands or Bedrock isn't available.
"""

import os
from pathlib import Path

# Ensure AWS creds from st.secrets are in env
try:
    import streamlit as _st
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"):
        v = _st.secrets.get(k, "")
        if v:
            os.environ[k] = v
except Exception:
    pass

from strands import Agent
from strands.models.bedrock import BedrockModel
from strands import tool

# Import DuckDB query functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from live_query import (
        get_queue_health, get_abandonment_analysis, get_agent_utilization,
        get_sentiment_trends, get_coaching_recommendations,
        get_burnout_signals, get_staffing_forecast,
    )
    _DATA_OK = True
except Exception:
    _DATA_OK = False


# ---------------------------------------------------------------------------
# Tool definitions (Strands @tool decorator)
# ---------------------------------------------------------------------------

@tool
def query_queue_health(queue_name: str = "") -> str:
    """Get real-time queue health metrics including queue size, wait times, SLA percentage, and average handle time. Optionally filter by queue name."""
    result = get_queue_health(queue_name or None)
    return result["text"]


@tool
def query_abandonment(queue_name: str = "") -> str:
    """Analyze call abandonment patterns including rate, peak hours, and average wait before abandon."""
    result = get_abandonment_analysis(queue_name or None)
    return result["text"]


@tool
def query_agent_utilization(agent_id: str = "") -> str:
    """Get per-agent utilization metrics: occupancy rate, current status, handle time, and contacts handled."""
    result = get_agent_utilization(agent_id or None)
    return result["text"]


@tool
def query_sentiment_trends() -> str:
    """Get customer sentiment trends showing positive, negative, neutral, and mixed percentages."""
    result = get_sentiment_trends()
    return result["text"]


@tool
def query_coaching_recommendations() -> str:
    """Identify agents with high negative sentiment rates and provide coaching recommendations."""
    result = get_coaching_recommendations()
    return result["text"]


@tool
def query_burnout_signals(threshold: float = 0.85) -> str:
    """Detect agents at risk of burnout based on sustained high occupancy and rising handle times."""
    result = get_burnout_signals(threshold)
    return result["text"]


@tool
def query_staffing_forecast() -> str:
    """Analyze historical contact volume patterns and project future staffing needs by hour."""
    result = get_staffing_forecast()
    return result["text"]


# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------

_SUPERVISOR_PROMPT = (
    "You are the Supervisor Agent for an Amazon Connect contact center. "
    "Your domain: queue health, SLA breaches, agent utilization, abandonment analysis. "
    "Use your tools to query real data. Be concise and actionable. "
    "If a question is about sentiment, coaching, compliance, staffing, or burnout, "
    "say it's outside your scope and suggest the Quality or WFM agent."
)

_QUALITY_PROMPT = (
    "You are the Quality Agent for an Amazon Connect contact center. "
    "Your domain: customer sentiment analysis, coaching recommendations, compliance violations. "
    "Use your tools to query real data. Be concise and actionable. "
    "If a question is about queue health, SLA, staffing, or burnout, "
    "say it's outside your scope and suggest the Supervisor or WFM agent."
)

_WFM_PROMPT = (
    "You are the WFM (Workforce Management) Agent for an Amazon Connect contact center. "
    "Your domain: staffing forecasts, burnout detection, schedule optimization. "
    "Use your tools to query real data. Be concise and actionable. "
    "If a question is about queue health, SLA, sentiment, or compliance, "
    "say it's outside your scope and suggest the Supervisor or Quality agent."
)

_agents = {}


def _get_agent(name: str) -> Agent:
    """Lazy-create and cache Strands agents."""
    if name in _agents:
        return _agents[name]

    if name == "Supervisor":
        model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")
        agent = Agent(
            model=model,
            system_prompt=_SUPERVISOR_PROMPT,
            tools=[query_queue_health, query_abandonment, query_agent_utilization],
        )
    elif name == "Quality":
        model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")
        agent = Agent(
            model=model,
            system_prompt=_QUALITY_PROMPT,
            tools=[query_sentiment_trends, query_coaching_recommendations],
        )
    elif name == "WFM":
        model = BedrockModel(model_id="us.amazon.nova-lite-v1:0")
        agent = Agent(
            model=model,
            system_prompt=_WFM_PROMPT,
            tools=[query_burnout_signals, query_staffing_forecast],
        )
    else:
        raise ValueError(f"Unknown agent: {name}")

    _agents[name] = agent
    return agent


def strands_agent_response(agent_name: str, query: str) -> dict:
    """Call a Strands agent with a natural language query.

    Returns dict with 'text' key containing the agent's response.
    """
    agent = _get_agent(agent_name)
    result = agent(query)
    return {"text": str(result)}
