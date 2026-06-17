"""Factory for the Diagnostic Analytics agent."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from app.config import ensure_openai_key, get_sql_agent_settings
from app.tools.diagnostic_tools import DIAGNOSTIC_TOOLS
from app.utils.skill_loader import load_skill_body


def load_diagnostic_prompt() -> str:
    """Load the Diagnostic Analytics instructions from the dedicated skill module."""

    return load_skill_body("diagnostic_analytics").strip()


def create_diagnostic_agent(
    *,
    service_tier: str | None = None,
    timeout_seconds: float | None = None,
):
    """Create a LangChain agent with only the diagnostic analytics tools."""

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
        tools=DIAGNOSTIC_TOOLS,
        system_prompt=load_diagnostic_prompt(),
    )
