"""Factory for the generic SQL analytics agent."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from app.agents.sql_agent.middleware import SkillMiddleware
from app.config import ensure_openai_key, get_sql_agent_settings
from app.utils.prompt_loader import load_prompt


def create_sql_agent(*, service_tier: str | None = None):
    """Create a LangChain SQL agent configured with enabled SQL skills."""

    ensure_openai_key()
    settings = get_sql_agent_settings()
    prompt = load_prompt("sql_agent", settings.prompt_version)
    model_kwargs = {}
    if settings.reasoning:
        model_kwargs["reasoning"] = settings.reasoning
    effective_service_tier = service_tier if service_tier is not None else settings.service_tier
    if effective_service_tier:
        model_kwargs["service_tier"] = effective_service_tier
    openai_request_kwargs = {}
    if settings.prompt_cache_key:
        openai_request_kwargs["prompt_cache_key"] = settings.prompt_cache_key
    if settings.prompt_cache_retention:
        openai_request_kwargs["prompt_cache_retention"] = settings.prompt_cache_retention
    if openai_request_kwargs:
        model_kwargs["model_kwargs"] = openai_request_kwargs
    model = init_chat_model(settings.model, **model_kwargs)

    return create_agent(
        model,
        system_prompt=prompt.system,
        middleware=[SkillMiddleware()],
    )
