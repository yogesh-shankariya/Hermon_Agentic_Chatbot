"""Factory for the single-lead Lead 360 agent."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from app.config import ensure_openai_key, get_sql_agent_settings
from app.tools import get_lead_360_tool
from app.utils.skill_loader import load_skill_body


LEAD_360_TOOLS = [get_lead_360_tool]


def load_lead_360_prompt() -> str:
    """Load the Lead 360 instructions from the dedicated skill module."""

    return load_skill_body("lead_360").strip()


def create_lead_360_agent(
    *,
    service_tier: str | None = None,
    timeout_seconds: float | None = None,
):
    """Create a LangChain agent with only the Lead 360 context tool."""

    ensure_openai_key()
    settings = get_sql_agent_settings()
    model_kwargs = {}
    if settings.reasoning:
        model_kwargs["reasoning"] = settings.reasoning
    effective_service_tier = service_tier if service_tier is not None else settings.service_tier
    if effective_service_tier:
        model_kwargs["service_tier"] = effective_service_tier
    if timeout_seconds is not None:
        model_kwargs["timeout"] = timeout_seconds
    model = init_chat_model(settings.model, **model_kwargs)

    return create_agent(
        model,
        tools=LEAD_360_TOOLS,
        system_prompt=load_lead_360_prompt(),
    )
