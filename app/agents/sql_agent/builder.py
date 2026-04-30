"""Factory for the generic SQL analytics agent."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from app.agents.sql_agent.middleware import SkillMiddleware
from app.config import ensure_openai_key, get_sql_agent_settings
from app.utils.prompt_loader import load_prompt


def create_sql_agent():
    """Create a LangChain SQL agent configured with enabled SQL skills."""

    ensure_openai_key()
    settings = get_sql_agent_settings()
    prompt = load_prompt("sql_agent", settings.prompt_version)
    model = init_chat_model(settings.model)

    return create_agent(
        model,
        system_prompt=prompt.system,
        middleware=[SkillMiddleware()],
    )
